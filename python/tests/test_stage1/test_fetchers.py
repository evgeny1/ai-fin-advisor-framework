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
        # 31 specs defined in M18 (update this when adding new series)
        assert len(_ALL_SPECS) == 31, (
            f"Expected 31 specs, found {len(_ALL_SPECS)}. "
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
    def test_fetch_macro_vix(self):
        from advisor.data.fetchers.yfinance_fetcher import fetch_macro
        spec = FetchSpec("VIX", DataSource.YFINANCE, "test", UpdateFrequency.DAILY, 1)
        # Temporarily set id to match _MACRO_SYMBOLS
        spec_vix = FetchSpec("VIX", DataSource.YFINANCE, "test", UpdateFrequency.DAILY, 1)
        # patch _MACRO_SYMBOLS lookup
        import advisor.data.fetchers.yfinance_fetcher as m
        original = m._MACRO_SYMBOLS.copy()
        m._MACRO_SYMBOLS["VIX"] = "^VIX"
        readings = fetch_macro(spec_vix)
        m._MACRO_SYMBOLS.update(original)
        assert readings
        assert readings[0].is_valid
        assert isinstance(readings[0].value["price"], float)

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


# ── FMP fetcher ───────────────────────────────────────────────────────────────

class TestFmpFetcher:
    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FMP_API_KEY"), reason="FMP_API_KEY not set")
    def test_fetch_brent(self):
        from advisor.data.fetchers.fmp_fetcher import fetch_commodity
        spec = FetchSpec("BRENT_CRUDE", DataSource.FMP_COMMODITY, "test",
                         UpdateFrequency.DAILY, 1)
        readings = fetch_commodity(spec)
        assert readings[0].is_valid
        price = readings[0].value["price"]
        assert 50 < price < 300, f"Brent price {price} outside plausible range"

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("FMP_API_KEY"), reason="FMP_API_KEY not set")
    def test_fetch_yield_curve(self):
        from advisor.data.fetchers.fmp_fetcher import fetch_yield_curve
        spec = FetchSpec("YIELD_CURVE", DataSource.FMP_ECONOMICS_TREASURY_RATES, "test",
                         UpdateFrequency.DAILY, 2)
        readings = fetch_yield_curve(spec)
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
