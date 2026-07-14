"""
Stage 1 smoke tests.
Run: cd python && python -m pytest tests/test_stage1/ -v

These tests verify:
  1. All M18 FetchSpecs are registered correctly
  2. FetchRegistry wiring is coherent (no orphan specs)
  3. yfinance fetcher returns valid DataReadings for known symbols
  4. FMP fetcher returns valid structure (requires FMP_API_KEY in env)
  5. file_protocol can find local framework files
"""
from __future__ import annotations

import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from advisor.types import DataSource, FetchSpec, UpdateFrequency, DataReading
from advisor.data.fetch_registry import FetchRegistry
from advisor.data.m18_registry import _ALL_SPECS, register_all


# ── Registry coherence tests ──────────────────────────────────────────────────

class TestM18Registry:
    def test_all_specs_have_unique_ids(self):
        ids = [s.id for s in _ALL_SPECS]
        assert len(ids) == len(set(ids)), "Duplicate FetchSpec IDs in M18 registry"

    def test_expected_spec_count(self):
        # 46 specs defined in M18 (update this when adding new series).
        # +1 vs prior count (43): REAL_YIELD_10Y_TREND (GAP-16 follow-up,
        # real-yield proxy correction, 2026-06-21).
        # +1 vs prior count (44): TREND_SIGNAL_HISTORY (ENG-50/ENG-55,
        # 2026-07-07 -- batched daily-close history for the 8 held
        # instruments + 8 ENG-55 comparator tickers).
        # +1 vs prior count (45): DBMF_3M_RETURN (ENG-30, 2026-07-14 --
        # DBMF's own trailing 3-month return, feeds its
        # "DBMF_3M_return < -3% while B+C >= 55%" failure_signal).
        assert len(_ALL_SPECS) == 46, (
            f"Expected 46 specs, found {len(_ALL_SPECS)}. "
            "Update this count when adding/removing series."
        )

    def test_all_specs_have_valid_sources(self):
        valid = set(DataSource)
        for spec in _ALL_SPECS:
            assert spec.source in valid, f"{spec.id}: invalid source {spec.source}"

    def test_on_demand_specs(self):
        on_demand = [s for s in _ALL_SPECS if s.update_frequency == UpdateFrequency.ON_DEMAND]
        assert len(on_demand) == 1
        assert on_demand[0].id == "HISTORICAL_INSTRUMENT_PRICES"

    def test_register_all(self):
        registry = FetchRegistry()
        register_all(registry)
        assert len(registry._specs) == len(_ALL_SPECS)

    def test_fetch_all_skips_on_demand(self):
        """fetch_all should not attempt ON_DEMAND specs."""
        registry = FetchRegistry()
        register_all(registry)
        called_ids = []

        def mock_fetcher(spec: FetchSpec):
            called_ids.append(spec.id)
            return [DataReading(spec_id=spec.id, value=1.0,
                                source=spec.source, fetched_at=datetime.utcnow())]

        for src in DataSource:
            registry.register_fetcher(src, mock_fetcher)

        registry.fetch_all()
        assert "HISTORICAL_INSTRUMENT_PRICES" not in called_ids


# ── yfinance fetcher ──────────────────────────────────────────────────────────

class TestYfinanceFetcher:
    """Integration tests — require network access. Skip with -m 'not integration'."""

    @pytest.mark.integration
    def test_dispatcher_vix(self):
        """Integration: yfinance_dispatcher fetches a live VIX quote via _fetch_single."""
        from advisor.data.fetchers.yfinance_fetcher import yfinance_dispatcher
        spec = FetchSpec("VIX", DataSource.YFINANCE, "test", UpdateFrequency.DAILY, 1)
        readings = yfinance_dispatcher(spec)
        assert len(readings) == 1
        assert readings[0].is_valid, f"VIX reading invalid: {readings[0].quality_flags}"
        price = readings[0].value["price"]
        assert isinstance(price, float)
        assert 5 < price < 100, f"VIX={price} outside plausible range (5–100)"

    @pytest.mark.integration
    def test_fetch_holdings_prices(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_holdings_prices
        spec = FetchSpec("HOLDINGS_PRICES", DataSource.YFINANCE, "test",
                         UpdateFrequency.DAILY, 0)
        readings = fetch_holdings_prices(spec)
        assert len(readings) > 0
        # At least some should be valid
        valid = [r for r in readings if r.is_valid]
        assert len(valid) > 0

    @pytest.mark.integration
    def test_fetch_trend_signal_histories(self):
        """ENG-50/ENG-55: one batched call for all 16 symbols (8 held
        instruments + 8 comparator tickers) — live network, same
        unmocked-integration convention as test_fetch_holdings_prices above."""
        from advisor.data.fetchers.yfinance_fetcher import (
            fetch_trend_signal_histories, _TREND_SIGNAL_SYMBOLS,
        )
        spec = FetchSpec("TREND_SIGNAL_HISTORY", DataSource.YFINANCE, "test",
                         UpdateFrequency.DAILY, 1)
        readings = fetch_trend_signal_histories(spec)
        assert len(readings) == len(_TREND_SIGNAL_SYMBOLS)
        valid = [r for r in readings if r.is_valid]
        assert len(valid) > 0
        for r in valid:
            assert len(r.value["closes"]) >= 60  # ~100 calendar days -> ~65-70 trading days expected


# ── FMP fetcher ───────────────────────────────────────────────────────────────

class TestFmpFetcher:
    """
    FMP REST API integration tests.
    These require FMP_API_KEY AND a plan tier that allows the endpoint.
    FMP REST returns 403 for commodity/indexes/chart with a free/starter key —
    those endpoints work via the FMP MCP connector (higher-tier account) but
    not via a standalone API key. Tests skip gracefully on 403 so they
    automatically activate when the plan is upgraded.
    """

    @staticmethod
    def _skip_if_403(exc: Exception) -> None:
        """Call inside except block: skip the test if it's a plan-tier 403."""
        import requests
        if isinstance(exc, requests.exceptions.HTTPError) and "403" in str(exc):
            pytest.skip(
                "FMP REST returned 403 — endpoint requires higher plan tier than "
                "the current standalone API key. Works via FMP MCP connector. "
                "Will activate automatically when plan is upgraded."
            )

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FMP_API_KEY"), reason="FMP_API_KEY not set")
    def test_fetch_brent(self):
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        spec = FetchSpec("BRENT_CRUDE", DataSource.FMP_COMMODITY, "test",
                         UpdateFrequency.DAILY, 1)
        try:
            readings = fetch_commodity(spec)
        except Exception as e:
            self._skip_if_403(e)
            raise
        assert readings[0].is_valid
        price = readings[0].value["price"]
        assert 50 < price < 300, f"Brent price {price} outside plausible range"

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FMP_API_KEY"), reason="FMP_API_KEY not set")
    def test_fetch_yield_curve(self):
        from advisor.data.fetchers.fmp_fetcher import fetch_yield_curve
        spec = FetchSpec("YIELD_CURVE", DataSource.FMP_ECONOMICS_TREASURY_RATES, "test",
                         UpdateFrequency.DAILY, 2)
        try:
            readings = fetch_yield_curve(spec)
        except Exception as e:
            self._skip_if_403(e)
            raise
        assert readings[0].is_valid
        val = readings[0].value
        assert "year10" in val
        assert "spread_10y_2y" in val


# ── file_protocol ─────────────────────────────────────────────────────────────

class TestFileProtocol:
    def test_framework_path_exists(self):
        from advisor.data.file_protocol import framework_path
        p = framework_path()
        assert p.exists(), f"Framework path not found: {p}"

    def test_read_calibration_state(self):
        from advisor.data.file_protocol import read_calibration_state
        content = read_calibration_state()
        assert "## Section 1" in content or "§1" in content or "HY_STRESS" in content

    def test_read_session_log(self):
        from advisor.data.file_protocol import read_session_log
        content = read_session_log()
        assert len(content) > 100, "Session log suspiciously short"
