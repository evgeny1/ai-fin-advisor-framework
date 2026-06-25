"""
Unit tests for the computation functions in yfinance_fetcher.py.

These mock yfinance's download/Ticker APIs to test the arithmetic logic
in isolation: rolling averages, return calculations, spread computation,
and the None-handling in fetch_yield_curve_partial.

Recreated 2026-06-24 after the original file was lost to a Google Drive
Cloud Files sync lock mid-session (ENG-40 follow-up work) -- rebuilt from
the same test names/coverage, verified against the current
yfinance_fetcher.py source rather than reconstructed from memory of old
assertions.
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


def _mock_download(closes: list) -> pd.DataFrame:
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
        assert readings[0].value["avg"] == pytest.approx(20.0)
        assert readings[0].value["n_days"] == 30

    def test_90d_avg_uses_up_to_62_days(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        # Only 50 closes available -- 90d window (62) clamps to what exists.
        closes = [15.0] * 50
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_90D_AVG"))
        assert readings[0].value["n_days"] == 50
        assert readings[0].value["avg"] == pytest.approx(15.0)

    def test_change_pts_is_last_minus_first(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        closes = [10.0] * 29 + [25.0]  # last 30 window: starts 10.0, ends 25.0
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_30D_AVG"))
        assert readings[0].value["change_pts"] == pytest.approx(15.0)

    def test_fewer_closes_than_window_uses_all_available(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_vix_history
        closes = [12.0, 14.0, 16.0]  # far fewer than 30
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_vix_history(_spec("VIX_30D_AVG"))
        assert readings[0].value["n_days"] == 3
        assert readings[0].value["avg"] == pytest.approx((12.0 + 14.0 + 16.0) / 3)

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
        closes = [100.0] * 43 + [110.0] * 21  # +10% over the 22-trading-day window
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))
        assert readings[0].value["return_30d_pct"] == pytest.approx(10.0, abs=0.1)

    def test_90d_return_computed(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        closes = [100.0] * 64 + [105.0]  # current vs close 64 back
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))
        assert readings[0].value["return_90d_pct"] == pytest.approx(5.0, abs=0.1)

    def test_current_price_is_last_close(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        closes = [100.0] * 70 + [123.45]
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))
        assert readings[0].value["current"] == pytest.approx(123.45)

    def test_empty_history_raises(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_broad_equity_trailing
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=pd.DataFrame()):
            with pytest.raises(RuntimeError, match="empty"):
                fetch_broad_equity_trailing(_spec("BROAD_EQUITY_TRAILING"))


# ── Yield curve (partial, yfinance-sourced tenors only) ───────────────────────

class TestFetchYieldCurvePartial:

    def test_spreads_computed_when_tenors_available(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_yield_curve_partial

        def _ticker(sym):
            m = MagicMock()
            prices = {"^TNX": 4.20, "^TYX": 4.80, "^IRX": 5.10}
            m.fast_info.last_price = prices[sym]
            return m

        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker", side_effect=_ticker):
            readings = fetch_yield_curve_partial(_spec("YIELD_CURVE"))
        v = readings[0].value
        assert v["year10"] == pytest.approx(4.20)
        assert v["year30"] == pytest.approx(4.80)
        assert v["month3"] == pytest.approx(5.10)
        assert v["year2"] is None
        assert v["spread_10y_2y"] is None
        assert v["spread_10y_3m"] == pytest.approx(4.20 - 5.10, abs=1e-4)

    def test_partial_flag_present(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_yield_curve_partial

        def _ticker(sym):
            m = MagicMock()
            m.fast_info.last_price = 4.0
            return m

        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker", side_effect=_ticker):
            readings = fetch_yield_curve_partial(_spec("YIELD_CURVE"))
        assert any("PARTIAL" in f and "year2" in f for f in readings[0].quality_flags)

    def test_failed_tenor_becomes_none_not_exception(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_yield_curve_partial

        def _ticker(sym):
            if sym == "^TYX":
                raise RuntimeError("simulated fetch failure")
            m = MagicMock()
            m.fast_info.last_price = 4.0
            return m

        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker", side_effect=_ticker):
            readings = fetch_yield_curve_partial(_spec("YIELD_CURVE"))
        assert readings[0].value["year30"] is None
        assert readings[0].value["year10"] == pytest.approx(4.0)


# ── Single-quote fetch via _SYMBOL_MAP ────────────────────────────────────────

class TestFetchSingle:

    def test_price_and_change_pct_correct(self):
        from advisor.data.fetchers.yfinance_fetcher import _fetch_single

        m = MagicMock()
        m.fast_info.last_price = 110.0
        m.fast_info.previous_close = 100.0
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.Ticker", return_value=m):
            readings = _fetch_single(_spec("DXY"))
        assert readings[0].value["price"] == pytest.approx(110.0)
        assert readings[0].value["day_change_pct"] == pytest.approx(10.0)

    def test_symbol_map_coverage(self):
        from advisor.data.fetchers.yfinance_fetcher import _SYMBOL_MAP
        # Spot-check a representative cross-section rather than every
        # entry -- this is a coverage sanity check, not an exhaustive list.
        for spec_id in ("GOLD_SPOT", "SILVER", "SP500", "VIX", "DXY"):
            assert spec_id in _SYMBOL_MAP
            assert isinstance(_SYMBOL_MAP[spec_id], str) and _SYMBOL_MAP[spec_id]


# ── Generic N-week trend history ──────────────────────────────────────────────

class TestFetchWeeklyTrend:

    def test_returns_closes_list(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_weekly_trend
        closes = [float(i) for i in range(10)]
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_weekly_trend(_spec("GOLD_TREND"), "GC=F", weeks=8)
        assert readings[0].value["closes"] == closes[-8:]
        assert readings[0].value["symbol"] == "GC=F"

    def test_trims_to_requested_window(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_weekly_trend
        closes = [float(i) for i in range(20)]
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_weekly_trend(_spec("DXY_TREND"), "DX-Y.NYB", weeks=8)
        assert len(readings[0].value["closes"]) == 8
        assert readings[0].value["n_weeks"] == 8

    def test_partial_history_flagged_not_failed(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_weekly_trend
        closes = [1.0, 2.0, 3.0]  # fewer than the requested 8 weeks
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_weekly_trend(_spec("GOLD_TREND"), "GC=F", weeks=8)
        assert readings[0].value is not None
        assert readings[0].value["n_weeks"] == 3
        assert any("PARTIAL" in f for f in readings[0].quality_flags)

    def test_empty_history_degrades_gracefully(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_weekly_trend
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=pd.DataFrame()):
            readings = fetch_weekly_trend(_spec("URANIUM_TREND"), "UX=F", weeks=12)
        assert readings[0].value is None
        assert any("UNAVAILABLE" in f for f in readings[0].quality_flags)

    def test_download_exception_degrades_gracefully(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_weekly_trend
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   side_effect=RuntimeError("simulated network failure")):
            readings = fetch_weekly_trend(_spec("GOLD_TREND"), "GC=F", weeks=8)
        assert readings[0].value is None
        assert any("FETCH_FAILED" in f for f in readings[0].quality_flags)


# ── NASDAQ 30d trailing return (MAGS §13 failure signal) ──────────────────────

class TestFetchNasdaqTrailing:

    def test_30d_return_computed(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_nasdaq_trailing
        closes = [100.0] * 29 + [89.0] * 21   # -11% over the trailing window
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=_mock_download(closes)):
            readings = fetch_nasdaq_trailing(_spec("NASDAQ_30D_RETURN"))
        assert readings[0].value["return_30d_pct"] == pytest.approx(-11.0, abs=0.1)

    def test_empty_history_raises(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_nasdaq_trailing
        with patch("advisor.data.fetchers.yfinance_fetcher.yf.download",
                   return_value=pd.DataFrame()):
            with pytest.raises(RuntimeError, match="empty"):
                fetch_nasdaq_trailing(_spec("NASDAQ_30D_RETURN"))


# ── Bounded lock acquisition (ENG-40) ─────────────────────────────────────────
# _YF_LOCK is a single process-wide lock (see module docstring note on the
# 2026-06-20 thread-safety fix). A fetch stuck inside yfinance/Yahoo Finance
# must not also permanently block every *other* yfinance-sourced spec for
# the rest of the MCP server process's life — acquisition itself needs a
# bound. Observed 2026-06-24: one illiquid-symbol fetch hung 25+ minutes.

class TestYfLockGuard:

    def test_acquires_immediately_when_free(self):
        from advisor.data.fetchers.yfinance_fetcher import _YF_LOCK, _yf_lock_guard
        with _yf_lock_guard(timeout=1.0):
            assert _YF_LOCK.locked()
        assert not _YF_LOCK.locked()

    def test_raises_timeout_error_when_held_elsewhere(self):
        from advisor.data.fetchers.yfinance_fetcher import _YF_LOCK, _yf_lock_guard
        _YF_LOCK.acquire()
        try:
            with pytest.raises(TimeoutError, match="lock busy"):
                with _yf_lock_guard(timeout=0.2):
                    pass  # pragma: no cover -- must not be reached
        finally:
            _YF_LOCK.release()

    def test_releases_lock_even_when_body_raises(self):
        from advisor.data.fetchers.yfinance_fetcher import _YF_LOCK, _yf_lock_guard
        with pytest.raises(ValueError):
            with _yf_lock_guard(timeout=1.0):
                raise ValueError("simulated fetch failure inside the guard")
        assert not _YF_LOCK.locked()
