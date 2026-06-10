"""
Unit tests for the computation functions in yfinance_fetcher.py.

These mock yfinance's download/Ticker APIs to test the arithmetic logic
in isolation: rolling averages, return calculations, spread computation,
and the None-handling in fetch_yield_curve_partial.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from advisor.types import DataSource, FetchSpec, UpdateFrequency


def _spec(spec_id: str) -> FetchSpec:
    return FetchSpec(id=spec_id, source=DataSource.YFINANCE, description="test",
                     update_frequency=UpdateFrequency.DAILY, acceptable_lag_days=1)


def _mock_download(closes: list) -> MagicMock:
    """Build a mock yf.download() return value with a Close column."""
    index = pd.date_range("2026-01-01", periods=len(closes), freq="B")
    df = pd.DataFrame({"Close": closes}, index=index)
    return df


# ── VIX rolling averages ──────────────────────────────────────────────────────

class TestFetchVixHistory:

    def test_30d_avg_is_mean_of_last_30(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        # 60 closes: first 30 are 10.0, last 30 are 20.0
        closes = [10.0] * 30 + [20.0] * 30
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_30D_AVG"))
        assert readings[0].spec_id == "VIX_30D_AVG"
        assert readings[0].value["n_days"] == 30
        # Last 30 values are all 20.0
        assert readings[0].value["avg"] == 20.0

    def test_90d_avg_uses_up_to_62_days(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        closes = [15.0] * 70
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_90D_AVG"))
        assert readings[0].value["n_days"] == 62
        assert readings[0].value["avg"] == 15.0

    def test_change_pts_is_last_minus_first(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        closes = list(range(10, 40))  # 30 values: 10..39
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_30D_AVG"))
        # change = last (39) - first of the 30-day window (10)
        assert readings[0].value["change_pts"] == 39 - 10

    def test_fewer_closes_than_window_uses_all_available(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        closes = [20.0] * 15  # only 15 closes, window wants 30
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_30D_AVG"))
        assert readings[0].value["n_days"] == 15
        assert readings[0].value["avg"] == 20.0

    def test_empty_history_raises(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=pd.DataFrame()):
            with pytest.raises(RuntimeError, match="empty"):
                fetch_vix_history(_spec("VIX_30D_AVG"))


# ── Broad equity trailing returns ─────────────────────────────────────────────

class TestFetchBroadEquityTrailing:

    def test_30d_return_computed(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        # 50 closes: first 29 = 100, last 21 = 110.
        # pct(22): idx = 50-22 = 28, closes[28] = 100 → (110/100 - 1)*100 = 10%
        closes = [100.0] * 29 + [110.0] * 21
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))
        val = readings[0].value
        assert val["return_30d_pct"] == pytest.approx(10.0, abs=0.1)

    def test_90d_return_computed(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        # 70 closes: first 7 = 100, last 63 = 108.
        # pct(64): idx = 70-64 = 6, closes[6] = 100 → (108/100 - 1)*100 = 8%
        closes = [100.0] * 7 + [108.0] * 63
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))
        val = readings[0].value
        assert val["return_90d_pct"] == pytest.approx(8.0, abs=0.1)

    def test_current_price_is_last_close(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        closes = [100.0] * 50 + [123.45]
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))
        assert readings[0].value["current"] == 123.45

    def test_empty_history_raises(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=pd.DataFrame()):
            with pytest.raises(RuntimeError, match="empty"):
                fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))


# ── Partial yield curve ───────────────────────────────────────────────────────

class TestFetchYieldCurvePartial:

    def _mock_ticker(self, price: float) -> MagicMock:
        m = MagicMock()
        m.fast_info.last_price = price
        return m

    def test_spreads_computed_when_tenors_available(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_yield_curve_partial

        ticker_map = {"^TNX": 4.55, "^TYX": 4.97, "^IRX": 5.25}
        def fake_ticker(sym):
            return self._mock_ticker(ticker_map[sym])

        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker", side_effect=fake_ticker):
            readings = fetch_yield_curve_partial(_spec("YIELD_CURVE"))

        val = readings[0].value
        assert val["year10"] == 4.55
        assert val["year30"] == 4.97
        assert val["month3"] == 5.25
        assert val["year2"]  is None          # yfinance cannot provide 2Y
        assert val["spread_10y_2y"] is None   # requires year2
        assert val["spread_10y_3m"] == round(4.55 - 5.25, 4)

    def test_partial_flag_present(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_yield_curve_partial
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker",
                   return_value=self._mock_ticker(4.55)):
            readings = fetch_yield_curve_partial(_spec("YIELD_CURVE"))
        assert any("PARTIAL" in f for f in readings[0].quality_flags)

    def test_failed_tenor_becomes_none_not_exception(self):
        """A failing yfinance call for one tenor must not crash the whole fetch."""
        from advisor.data.fetchers.yfinance_fetcher import fetch_yield_curve_partial

        def flaky_ticker(sym):
            if sym == "^TYX":
                raise RuntimeError("yfinance timeout")
            return self._mock_ticker(4.55)

        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker", side_effect=flaky_ticker):
            readings = fetch_yield_curve_partial(_spec("YIELD_CURVE"))

        assert readings[0].value["year30"] is None
        assert readings[0].value["year10"] == 4.55  # other tenors still present


# ── _fetch_single symbol map ──────────────────────────────────────────────────

class TestFetchSingle:

    def _mock_fast_info(self, price: float, prev_close: float) -> MagicMock:
        info = MagicMock()
        info.last_price = price
        info.previous_close = prev_close
        ticker = MagicMock()
        ticker.fast_info = info
        return ticker

    def test_price_and_change_pct_correct(self):
        from advisor.data.fetchers.yfinance_fetcher import _fetch_single
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker",
                   return_value=self._mock_fast_info(110.0, 100.0)):
            readings = _fetch_single(_spec("DXY"))
        assert readings[0].value["price"] == 110.0
        assert readings[0].value["day_change_pct"] == pytest.approx(10.0, abs=0.01)

    def test_symbol_map_coverage(self):
        """Every spec.id routed to _fetch_single must have a symbol in _SYMBOL_MAP."""
        from advisor.data.fetchers.yfinance_fetcher import _SYMBOL_MAP
        from advisor.data.m18_registry import _ALL_SPECS
        from advisor.types import UpdateFrequency

        # These spec.ids are handled by dedicated functions, not _fetch_single
        dispatcher_handled = {
            "HOLDINGS_PRICES", "VIX_30D_AVG", "VIX_90D_AVG",
            "BROAD_EQUITY_TRAILING", "YIELD_CURVE", "HISTORICAL_INSTRUMENT_PRICES",
        }
        yfinance_specs = [
            s for s in _ALL_SPECS
            if s.source == DataSource.YFINANCE
            and s.id not in dispatcher_handled
            and s.update_frequency != UpdateFrequency.ON_DEMAND
        ]
        missing = [s.id for s in yfinance_specs if s.id not in _SYMBOL_MAP]
        assert missing == [], (
            f"These YFINANCE specs have no entry in _SYMBOL_MAP: {missing}. "
            "Add them to _SYMBOL_MAP in yfinance_fetcher.py."
        )
