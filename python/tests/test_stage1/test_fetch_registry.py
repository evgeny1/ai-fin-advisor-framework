"""
Unit tests for fetch_registry.py — parallel fetch orchestration,
error propagation, and fetch_one() for ON_DEMAND specs.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from advisor.data.fetch_registry import FetchRegistry
from advisor.types import DataReading, DataSource, FetchSpec, UpdateFrequency


def _spec(spec_id: str, source: DataSource = DataSource.YFINANCE,
          freq: UpdateFrequency = UpdateFrequency.DAILY) -> FetchSpec:
    return FetchSpec(id=spec_id, source=source, description="test",
                     update_frequency=freq, acceptable_lag_days=1)


def _reading(spec_id: str) -> DataReading:
    return DataReading(spec_id=spec_id, value=1.0, source=DataSource.YFINANCE,
                       fetched_at=datetime.utcnow())


def _ok_fetcher(spec: FetchSpec) -> List[DataReading]:
    return [_reading(spec.id)]


def _failing_fetcher(spec: FetchSpec) -> List[DataReading]:
    raise RuntimeError(f"simulated fetch failure for {spec.id}")


# ── fetch_one (ON_DEMAND path) ────────────────────────────────────────────────

class TestFetchOne:

    def test_fetch_one_returns_readings_for_known_spec(self):
        registry = FetchRegistry()
        registry.register(_spec("HISTORICAL_INSTRUMENT_PRICES",
                                freq=UpdateFrequency.ON_DEMAND))
        registry.register_fetcher(DataSource.YFINANCE, _ok_fetcher)
        readings = registry.fetch_one("HISTORICAL_INSTRUMENT_PRICES")
        assert len(readings) == 1
        assert readings[0].spec_id == "HISTORICAL_INSTRUMENT_PRICES"

    def test_fetch_one_raises_for_unknown_spec_id(self):
        registry = FetchRegistry()
        with pytest.raises(KeyError, match="UNKNOWN"):
            registry.fetch_one("UNKNOWN")

    def test_fetch_one_works_for_standard_frequency_spec_too(self):
        """fetch_one() is not restricted to ON_DEMAND — it's just the explicit path."""
        registry = FetchRegistry()
        registry.register(_spec("VIX"))
        registry.register_fetcher(DataSource.YFINANCE, _ok_fetcher)
        readings = registry.fetch_one("VIX")
        assert readings[0].spec_id == "VIX"


# ── Error propagation ─────────────────────────────────────────────────────────

class TestFetchAllErrorPropagation:

    def test_failing_fetcher_produces_flagged_reading_not_exception(self):
        """fetch_all() must never raise — failures become FETCH_FAILED readings."""
        registry = FetchRegistry()
        registry.register(_spec("VIX"))
        registry.register_fetcher(DataSource.YFINANCE, _failing_fetcher)
        readings = registry.fetch_all()
        assert len(readings) == 1
        r = readings[0]
        assert not r.is_valid
        assert any("FETCH_FAILED" in f for f in r.quality_flags)
        assert "simulated fetch failure" in r.quality_flags[0]

    def test_one_failure_does_not_block_others(self):
        """A failing spec must not prevent other specs from being fetched."""
        registry = FetchRegistry()
        registry.register(_spec("VIX",  source=DataSource.YFINANCE))
        registry.register(_spec("MOVE", source=DataSource.FMP_INDEXES))
        registry.register_fetcher(DataSource.YFINANCE,   _failing_fetcher)
        registry.register_fetcher(DataSource.FMP_INDEXES, _ok_fetcher)
        readings = registry.fetch_all()
        assert len(readings) == 2
        valid   = [r for r in readings if r.is_valid]
        invalid = [r for r in readings if not r.is_valid]
        assert len(valid)   == 1 and valid[0].spec_id   == "MOVE"
        assert len(invalid) == 1 and invalid[0].spec_id == "VIX"

    def test_no_fetcher_registered_produces_unavailable_reading(self):
        """Spec with no registered fetcher gets FETCH_FAILED, not an exception."""
        registry = FetchRegistry()
        registry.register(_spec("DXY"))
        # No fetcher registered for YFINANCE
        readings = registry.fetch_all()
        assert len(readings) == 1
        assert not readings[0].is_valid
        assert any("FETCH_FAILED" in f for f in readings[0].quality_flags)


# ── readings_dict helper ──────────────────────────────────────────────────────

class TestReadingsDict:

    def test_indexes_by_spec_id(self):
        registry = FetchRegistry()
        readings = [_reading("VIX"), _reading("DXY"), _reading("MOVE")]
        d = registry.readings_dict(readings)
        assert set(d.keys()) == {"VIX", "DXY", "MOVE"}
        assert d["VIX"].spec_id == "VIX"

    def test_last_reading_wins_on_duplicate_spec_id(self):
        """Holdings specs produce HOLDINGS_PRICES:MLPX etc. — dict uses last."""
        registry = FetchRegistry()
        r1 = DataReading("VIX", 15.0, DataSource.YFINANCE, datetime.utcnow())
        r2 = DataReading("VIX", 16.0, DataSource.YFINANCE, datetime.utcnow())
        d = registry.readings_dict([r1, r2])
        assert d["VIX"].value == 16.0


# ── summary output ────────────────────────────────────────────────────────────

class TestSummary:

    def test_summary_lists_sources_and_fetchers(self):
        registry = FetchRegistry()
        registry.register(_spec("VIX",  source=DataSource.YFINANCE))
        registry.register(_spec("MOVE", source=DataSource.FMP_INDEXES))
        registry.register_fetcher(DataSource.YFINANCE, _ok_fetcher)
        summary = registry.summary()
        assert "YFINANCE" in summary
        assert "FMP_INDEXES" in summary
        assert "NO FETCHER" in summary   # FMP_INDEXES has no fetcher

    def test_summary_shows_spec_count(self):
        registry = FetchRegistry()
        for i in range(5):
            registry.register(_spec(f"SPEC_{i}"))
        assert "5 spec" in registry.summary()
