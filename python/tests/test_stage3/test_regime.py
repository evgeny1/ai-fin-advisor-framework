"""
tests/test_stage3/test_regime.py — M14 compute_divergence_signal() unit tests.

Coverage focus: ENG-20 — conflict_duration_days / energy_180d extended-conflict
fallback. No file I/O, no network; all readings built inline via conftest helpers.
"""
from __future__ import annotations

from advisor.analysis.regime import compute_divergence_signal
from advisor.types import DivergenceLevel, DivergenceSignal
from .conftest import make_history_reading, make_reading


def _brent_history(window_180_base: float, window_90_base: float, current: float) -> list:
    """
    Build a 200-point oldest-first Brent history where only the two anchor
    points compute_pct_change() actually reads are meaningful:
      history[-1]    = current
      history[-91]   = window_90_base   (90-calendar-day anchor)
      history[-181]  = window_180_base  (180-calendar-day anchor)
    All other points are filler (current) — irrelevant to compute_pct_change.
    """
    hist = [current] * 200
    hist[200 - 91]  = window_90_base
    hist[200 - 181] = window_180_base
    hist[-1] = current
    return hist


class TestNoConflictDuration:
    """conflict_duration_days omitted (default None) -> behavior unchanged from pre-ENG-20."""

    def test_energy_180d_change_is_none_by_default(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal)
        assert sig.energy_90d_change is not None
        assert sig.energy_180d_change is None
        # 90d change alone (5%) is below both thresholds -> NONE
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE

    def test_no_180d_flag_emitted(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {"BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0)}
        sig = compute_divergence_signal(readings, cal)
        assert not any("Conflict > 90d" in f for f in sig.quality_flags)


class TestConflictUnder90Days:
    """conflict_duration_days <= 90 -> no 180d fallback triggered."""

    def test_short_conflict_does_not_trigger_180d(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=45)
        assert sig.energy_180d_change is None
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE


class TestConflictOver90DaysWithSufficientHistory:
    """
    conflict_duration_days > 90 + 181+ points of history -> energy_180d computed
    and the HIGHER of (90d, 180d) drives classification (M14 EXTENDED CONFLICT CAVEAT).
    """

    def test_180d_overrides_understated_90d_signal(self, cal):
        # 90d change: (105-100)/100 = 5% -> below MOD (10%) threshold alone.
        # 180d change: (105-80)/80 = 31.25% -> above HIGH (15%) threshold.
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),         # vix_change = -5 <= HIGH thresh (0)
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_90d_change is not None and sig.energy_90d_change < 0.10
        assert sig.energy_180d_change is not None
        assert sig.energy_180d_change > sig.energy_90d_change
        # Classification driven by the higher (180d) reading -> HIGH, not NONE.
        assert sig.commodity_fear_divergence == DivergenceLevel.HIGH

    def test_both_readings_reported_and_flag_emitted(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {"BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0)}
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_90d_change is not None
        assert sig.energy_180d_change is not None
        assert any("Conflict > 90d" in f and "180d" in f for f in sig.quality_flags)

    def test_90d_reading_unaffected_when_180d_lower(self, cal):
        """If 180d change is LOWER than 90d, the 90d (already-higher) value still governs."""
        # 90d: (105-90)/90 = 16.7% -> already above HIGH (15%) alone.
        # 180d: (105-100)/100 = 5% -> lower than 90d.
        hist = _brent_history(window_180_base=100.0, window_90_base=90.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_90d_change > sig.energy_180d_change
        assert sig.commodity_fear_divergence == DivergenceLevel.HIGH


class TestConflictOver90DaysInsufficientHistory:
    """conflict_duration_days > 90 but < 181 points of Brent history -> graceful flag, no crash."""

    def test_insufficient_history_flags_and_falls_back_to_90d(self, cal):
        # Only 120 points -> 90d window satisfiable (needs 91), 180d window is not (needs 181).
        hist = [100.0] * 119 + [105.0]
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_180d_change is None
        assert sig.energy_90d_change is not None
        assert any("insufficient BRENT_CRUDE history" in f for f in sig.quality_flags)
        # Falls back to 90d-only classification (5% -> below MOD threshold -> NONE).
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE


class TestReturnType:

    def test_returns_divergence_signal(self, cal):
        sig = compute_divergence_signal({}, cal)
        assert isinstance(sig, DivergenceSignal)

    def test_empty_readings_no_exception(self, cal):
        sig = compute_divergence_signal({}, cal, conflict_duration_days=150)
        assert sig.energy_90d_change is None
        assert sig.energy_180d_change is None
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE
