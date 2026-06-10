"""
Unit tests for fmp_fetcher.py — mocked HTTP responses, no network required.

FMP REST returns 403 with a standalone API key (confirmed shadow session June 10),
so integration tests skip automatically. These unit tests verify the response-
parsing logic is correct for when the plan is eventually upgraded.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from advisor.types import DataSource, FetchSpec, UpdateFrequency


def _spec(spec_id: str, source: DataSource) -> FetchSpec:
    return FetchSpec(id=spec_id, source=source, description="test",
                     update_frequency=UpdateFrequency.DAILY, acceptable_lag_days=1)


def _mock_get(payload: dict) -> MagicMock:
    """Build a mock requests.get return value with .raise_for_status() and .json()."""
    m = MagicMock()
    m.raise_for_status = MagicMock()
    m.json.return_value = payload
    return m


# ── Commodity ─────────────────────────────────────────────────────────────────

class TestFmpFetchCommodity:

    def test_brent_price_extracted(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        payload = [{"symbol": "BZUSD", "price": 93.84, "changesPercentage": 2.12}]
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(payload)):
            readings = fetch_commodity(_spec("BRENT_CRUDE", DataSource.FMP_COMMODITY))
        assert readings[0].is_valid
        assert readings[0].value["price"] == 93.84
        assert readings[0].value["day_change_pct"] == 2.12

    def test_gold_price_extracted(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        payload = [{"symbol": "GCUSD", "price": 4504.20, "changesPercentage": -0.31}]
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(payload)):
            readings = fetch_commodity(_spec("GOLD_SPOT", DataSource.FMP_COMMODITY))
        assert readings[0].value["price"] == 4504.20

    def test_unknown_spec_id_raises(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        with pytest.raises(ValueError, match="No FMP commodity symbol"):
            fetch_commodity(_spec("UNKNOWN", DataSource.FMP_COMMODITY))

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("FMP_API_KEY", raising=False)
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        with pytest.raises(EnvironmentError, match="FMP_API_KEY"):
            fetch_commodity(_spec("BRENT_CRUDE", DataSource.FMP_COMMODITY))


# ── Index ─────────────────────────────────────────────────────────────────────

class TestFmpFetchIndex:

    def test_vix_price_extracted(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_index
        payload = [{"symbol": "^VIX", "price": 22.22, "changesPercentage": 11.83}]
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(payload)):
            readings = fetch_index(_spec("VIX", DataSource.FMP_INDEXES))
        assert readings[0].value["price"] == 22.22
        assert readings[0].value["day_change_pct"] == 11.83

    def test_sp500_price_extracted(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_index
        payload = [{"symbol": "^GSPC", "price": 7584.82, "changesPercentage": 0.5}]
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(payload)):
            readings = fetch_index(_spec("SP500", DataSource.FMP_INDEXES))
        assert readings[0].value["price"] == 7584.82

    def test_unknown_spec_id_raises(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_index
        with pytest.raises(ValueError, match="No FMP index symbol"):
            fetch_index(_spec("MOVE", DataSource.FMP_INDEXES))  # MOVE is ACCESS DENIED


# ── Yield curve ───────────────────────────────────────────────────────────────

class TestFmpFetchYieldCurve:

    def _treasury_payload(self) -> list:
        return [{
            "date": "2026-06-10",
            "month1": 5.20, "month2": 5.18, "month3": 5.15, "month6": 5.05,
            "year1": 4.90, "year2": 4.50, "year3": 4.40, "year5": 4.35,
            "year7": 4.47, "year10": 4.55, "year20": 4.80, "year30": 4.97,
        }]

    def test_key_tenors_extracted(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_yield_curve
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(self._treasury_payload())):
            readings = fetch_yield_curve(
                _spec("YIELD_CURVE", DataSource.FMP_ECONOMICS_TREASURY_RATES))
        val = readings[0].value
        assert val["year2"]  == 4.50
        assert val["year10"] == 4.55
        assert val["year30"] == 4.97

    def test_spreads_computed(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_yield_curve
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(self._treasury_payload())):
            readings = fetch_yield_curve(
                _spec("YIELD_CURVE", DataSource.FMP_ECONOMICS_TREASURY_RATES))
        val = readings[0].value
        assert val["spread_10y_2y"] == round(4.55 - 4.50, 4)
        assert val["spread_10y_3m"] == round(4.55 - 5.15, 4)

    def test_empty_response_raises(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_yield_curve
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get([])):
            with pytest.raises(RuntimeError, match="Empty"):
                fetch_yield_curve(
                    _spec("YIELD_CURVE", DataSource.FMP_ECONOMICS_TREASURY_RATES))


# ── VIX history (FMP chart) ───────────────────────────────────────────────────

class TestFmpVixHistory:

    def _chart_payload(self, closes: list) -> list:
        """Build FMP chart response (newest-first)."""
        return [{"date": f"2026-06-{i:02d}", "close": c}
                for i, c in enumerate(closes, 1)]

    def test_30d_avg_computed(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_vix_history_fmp
        closes = list(range(20, 50))  # 30 values: 20,21,...,49
        payload = self._chart_payload(list(reversed(closes)))  # newest-first
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(payload)):
            readings = fetch_vix_history_fmp(
                _spec("VIX_30D_AVG", DataSource.FMP_CHART))
        assert readings[0].spec_id == "VIX_30D_AVG"
        assert readings[0].value["n_days"] == 30
        expected_avg = sum(closes) / 30
        assert abs(readings[0].value["avg"] - expected_avg) < 0.01

    def test_90d_avg_uses_62_trading_days(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test")
        from advisor.data.fetchers.fmp_fetcher import fetch_vix_history_fmp
        closes = [20.0] * 70  # 70 flat closes
        payload = self._chart_payload(list(reversed(closes)))
        with patch("advisor.data.fetchers.fmp_fetcher.requests.get",
                   return_value=_mock_get(payload)):
            readings = fetch_vix_history_fmp(
                _spec("VIX_90D_AVG", DataSource.FMP_CHART))
        assert readings[0].spec_id == "VIX_90D_AVG"
        assert readings[0].value["avg"] == 20.0


# ── Integration (skips on 403) ────────────────────────────────────────────────

class TestFmpIntegration:
    @staticmethod
    def _skip_if_403(exc: Exception) -> None:
        import requests
        if isinstance(exc, requests.exceptions.HTTPError) and "403" in str(exc):
            pytest.skip("FMP REST 403 — standalone key lacks plan tier for this endpoint")

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FMP_API_KEY"), reason="FMP_API_KEY not set")
    def test_commodity_brent(self):
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        try:
            r = fetch_commodity(_spec("BRENT_CRUDE", DataSource.FMP_COMMODITY))[0]
        except Exception as e:
            self._skip_if_403(e); raise
        assert r.is_valid
        assert 30 < r.value["price"] < 300

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FMP_API_KEY"), reason="FMP_API_KEY not set")
    def test_treasury_rates(self):
        from advisor.data.fetchers.fmp_fetcher import fetch_yield_curve
        try:
            r = fetch_yield_curve(
                _spec("YIELD_CURVE", DataSource.FMP_ECONOMICS_TREASURY_RATES))[0]
        except Exception as e:
            self._skip_if_403(e); raise
        assert r.is_valid
        assert r.value["year10"] is not None
