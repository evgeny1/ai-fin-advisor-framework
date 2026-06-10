"""
Tests for fred_fetcher.py — FRED REST API yield curve fetcher.

Why FRED and not FMP or yfinance for the yield curve:
- yfinance: provides ^TNX (10Y), ^TYX (30Y), ^IRX (3M) but NOT 2Y
- FMP REST: treasury-rates endpoint returns 403 with standalone API key
- FRED REST: free API key, provides DGS2/DGS5/DGS10/DGS30/DGS3MO — full curve

The 10Y-2Y spread is required by M17.computeYieldCurveSignal().
Without year2, spread_10y_2y is None and M17 signal is incomplete.
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from advisor.types import DataReading, DataSource, FetchSpec, UpdateFrequency


def _yield_curve_spec() -> FetchSpec:
    return FetchSpec(
        id="YIELD_CURVE", source=DataSource.FRED_SPREADSHEET_TAB,
        description="test", update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=2,
    )


class TestFredFetcherNoKey:
    """Behaviour when FRED_API_KEY is absent — must degrade gracefully."""

    def test_returns_unavailable_reading_without_key(self, monkeypatch):
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        from advisor.data.fetchers.fred_fetcher import fetch_yield_curve_fred
        readings = fetch_yield_curve_fred(_yield_curve_spec())
        assert len(readings) == 1
        r = readings[0]
        assert r.value is None
        assert any("FRED_API_KEY" in f for f in r.quality_flags), (
            "Missing key should produce a quality flag explaining the gap"
        )

    def test_unavailable_reading_is_not_valid(self, monkeypatch):
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        from advisor.data.fetchers.fred_fetcher import fetch_yield_curve_fred
        readings = fetch_yield_curve_fred(_yield_curve_spec())
        assert not readings[0].is_valid


class TestFredFetcherMocked:
    """Unit tests using mocked HTTP responses — no network required."""

    def _mock_response(self, value: str) -> MagicMock:
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = {
            "observations": [{"date": "2026-06-10", "value": value}]
        }
        return mock

    def _mock_missing(self) -> MagicMock:
        """Simulate FRED returning '.' for a missing observation."""
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = {
            "observations": [{"date": "2026-06-10", "value": "."}]
        }
        return mock

    def test_full_curve_computes_spreads(self, monkeypatch):
        """When all tenors are available, spreads are computed correctly."""
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        from advisor.data.fetchers import fred_fetcher as m

        series_values = {
            "DGS3MO": "5.25", "DGS2": "4.50", "DGS5": "4.30",
            "DGS10": "4.55", "DGS30": "4.97",
        }

        def fake_get(url, params=None, timeout=None):
            sid = (params or {}).get("series_id", "")
            return self._mock_response(series_values.get(sid, "."))

        with patch("advisor.data.fetchers.fred_fetcher.requests.get", side_effect=fake_get):
            readings = m.fetch_yield_curve_fred(_yield_curve_spec())

        assert len(readings) == 1
        r = readings[0]
        assert r.is_valid
        val = r.value
        assert val["year2"]  == 4.50
        assert val["year10"] == 4.55
        assert val["month3"] == 5.25
        # 10Y-2Y spread
        assert val["spread_10y_2y"] == round(4.55 - 4.50, 4)
        # 10Y-3M spread
        assert val["spread_10y_3m"] == round(4.55 - 5.25, 4)

    def test_missing_tenor_sets_none_and_flags(self, monkeypatch):
        """If a FRED series returns '.', that tenor is None and a quality flag is set."""
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        from advisor.data.fetchers import fred_fetcher as m

        def fake_get(url, params=None, timeout=None):
            sid = (params or {}).get("series_id", "")
            if sid == "DGS2":
                return self._mock_missing()  # 2Y missing
            return self._mock_response("4.55")

        with patch("advisor.data.fetchers.fred_fetcher.requests.get", side_effect=fake_get):
            readings = m.fetch_yield_curve_fred(_yield_curve_spec())

        val = readings[0].value
        assert val["year2"] is None
        assert val["spread_10y_2y"] is None
        assert any("PARTIAL" in f for f in readings[0].quality_flags)

    def test_spec_id_preserved(self, monkeypatch):
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        from advisor.data.fetchers import fred_fetcher as m

        with patch("advisor.data.fetchers.fred_fetcher.requests.get",
                   return_value=self._mock_response("4.55")):
            readings = m.fetch_yield_curve_fred(_yield_curve_spec())

        assert readings[0].spec_id == "YIELD_CURVE"
        assert readings[0].source == DataSource.FRED_SPREADSHEET_TAB


class TestFredFetcherIntegration:
    """Live FRED API calls — require FRED_API_KEY in environment."""

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set")
    def test_live_yield_curve_has_year2(self):
        """Confirms DGS2 is available and spread_10y_2y is computable."""
        from advisor.data.fetchers.fred_fetcher import fetch_yield_curve_fred
        readings = fetch_yield_curve_fred(_yield_curve_spec())
        assert len(readings) == 1
        r = readings[0]
        assert r.is_valid, f"FRED yield curve invalid: {r.quality_flags}"
        val = r.value
        assert val["year2"]  is not None, "2Y yield missing — check FRED_API_KEY tier"
        assert val["year10"] is not None
        assert val["spread_10y_2y"] is not None, "10Y-2Y spread requires year2"
        assert -5 < val["spread_10y_2y"] < 5, f"Spread {val['spread_10y_2y']} implausible"
        assert 0 < val["year10"] < 15, f"10Y yield {val['year10']} implausible"
