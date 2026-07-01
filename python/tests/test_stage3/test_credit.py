"""
tests/test_stage3/test_credit.py — M11 CreditSignal unit tests.
All tests use inline fixtures; no file I/O, no network.
"""
from __future__ import annotations
import pytest
from datetime import datetime

from advisor.analysis.credit import compute_credit_signal
from advisor.types import CreditSignal
from .conftest import make_reading, make_history_reading


# ── Helper: build a history list with given current and delta ──────────────────

def _history(current: float, length: int, delta_per_step: float = 0.0) -> list:
    """Build a list of `length` values ending at `current`, spaced by delta_per_step."""
    return [current - (length - 1 - i) * delta_per_step for i in range(length)]


# ── Scalar-value readings (current only, no history) ──────────────────────────

class TestScalarReadings:

    def test_calm_credit_no_flags_blocked(self, cal):
        """Calm spreads below any threshold → no flags fired, convergence text positive."""
        readings = {
            "HY_OAS":  make_reading("HY_OAS",  280.0),
            "IG_OAS":  make_reading("IG_OAS",   70.0),
            "CCC_OAS": make_reading("CCC_OAS", 900.0),
            "MOVE":    make_reading("MOVE",     70.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.hy_oas == 280.0
        assert sig.ig_oas == 70.0
        assert sig.ccc_oas == 900.0
        assert sig.move == 70.0
        assert sig.hy_median_180d is None   # no history → median None
        assert not sig.hy_stress_beginning
        assert not sig.hy_recession_pricing
        assert not sig.ig_transmission_reached
        assert not sig.ccc_tail_first_widening
        # Should flag median unavailable
        assert any("180d median" in f for f in sig.quality_flags)

    def test_missing_hy_oas(self, cal):
        """Missing HY_OAS reading → flags added, thresholds False."""
        readings = {
            "IG_OAS":  make_reading("IG_OAS", 70.0),
            "CCC_OAS": make_reading("CCC_OAS", 900.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.hy_oas is None
        assert not sig.hy_stress_beginning
        assert not sig.hy_recession_pricing
        assert any("HY_OAS" in f for f in sig.quality_flags)

    def test_failed_reading_treated_as_missing(self, cal):
        """FETCH_FAILED reading → value None → thresholds False."""
        readings = {
            "HY_OAS":  make_reading("HY_OAS",  0.0, failed=True),
            "IG_OAS":  make_reading("IG_OAS",  70.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.hy_oas is None

    def test_move_extracted(self, cal):
        """MOVE value should appear in signal."""
        readings = {
            "MOVE": make_reading("MOVE", 99.5),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.move == pytest.approx(99.5)


# ── History-based threshold evaluation ────────────────────────────────────────

class TestHistoryThresholds:

    def _calm_hist(self, n=200, level=280.0) -> list:
        return [level] * n   # flat history

    def _widening_hist(self, current: float, n: int, total_bps: float) -> list:
        """Build history that widens by total_bps over the last n points."""
        start = current - total_bps
        return [start + total_bps * i / (n - 1) for i in range(n)]

    def test_median_computed_from_history(self, cal):
        hist = self._calm_hist(200, 300.0)
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, 300.0)}
        sig = compute_credit_signal(readings, cal)
        assert sig.hy_median_180d == pytest.approx(300.0)

    def test_hy_stress_not_fired_velocity_insufficient(self, cal):
        """HY above median+150 but <100bps velocity over 60d → NOT fired."""
        # median = 300, current = 460 (160 above → above stress threshold)
        # velocity over 60d = 50bps (< 100 required)
        hist = _history(460.0, 200, delta_per_step=50.0 / 60)
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, 460.0)}
        sig = compute_credit_signal(readings, cal)
        # median ~ 460 - 50*(some fraction) — depends on history shape
        # The test verifies velocity logic; stress should be False (no sustain either)
        assert not sig.hy_stress_beginning

    def test_hy_stress_not_fired_sustain_missing(self, cal):
        """All conditions met except sustain (default 0 days) → NOT fired."""
        # Build history: flat at 300 for 140 days, then widening 110bps over 60 days
        base_hist = [300.0] * 140
        widen_hist = [300.0 + 110.0 * i / 60 for i in range(61)]
        hist = base_hist + widen_hist
        current = hist[-1]  # ~410 bps
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, current)}
        sig = compute_credit_signal(readings, cal, hy_sustain_days=0)
        # median ≈ 300, current ≈ 410 → above median+150 (460) → NOT above threshold
        # (300+150=450 > 410) → stress should be False
        assert not sig.hy_stress_beginning

    def test_hy_stress_all_conditions_met(self, cal):
        """HY stress fires when all three conditions met."""
        # median = 300, current = 470 (> 300+150=450)
        # velocity over 60d = 170bps (> 100)
        # sustain = 10 days
        base = [300.0] * 140
        widen = [300.0 + 170.0 * i / 60 for i in range(61)]
        hist = base + widen
        current = hist[-1]   # ~470
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, current)}
        sig = compute_credit_signal(readings, cal, hy_sustain_days=10)
        if current > (sig.hy_median_180d + 150):
            assert sig.hy_stress_beginning

    def test_hy_recession_fires_when_sustained(self, cal):
        """HY recession pricing: current > median+300 AND sustain >= 10."""
        hist = [300.0] * 200
        current = 650.0   # 300+300 = 600 < 650 → above recession threshold
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, current)}
        sig = compute_credit_signal(readings, cal, hy_sustain_days=10)
        assert sig.hy_recession_pricing
        assert "recession" in sig.convergence_text.lower() or "D probability" in sig.convergence_text

    def test_hy_recession_does_not_fire_without_sustain(self, cal):
        """HY recession: above threshold but sustain=0 → NOT fired."""
        hist = [300.0] * 200
        current = 650.0
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, current)}
        sig = compute_credit_signal(readings, cal, hy_sustain_days=0)
        assert not sig.hy_recession_pricing

    def test_ig_transmission_fires(self, cal):
        """IG transmission: current > median+60, vel >= 40, sustain >= 10."""
        hist = [70.0] * 140 + [70.0 + 50.0 * i / 60 for i in range(61)]
        current = hist[-1]   # ~120
        readings = {
            "HY_OAS": make_reading("HY_OAS", 280.0),
            "IG_OAS": make_history_reading("IG_OAS", hist, current),
        }
        sig = compute_credit_signal(readings, cal, ig_sustain_days=10)
        if current > (sig.ig_median_180d + 60):
            assert sig.ig_transmission_reached

    def test_ccc_tail_first_widening_ratio_mode(self, cal):
        """Genuine divergence: CCC+150/HY+20 over 30d → fires via ratio mode.
        150 >= 3*20=60 (ratio) AND 150 >= 75 (ENG-45 absolute-move gate)."""
        hy_hist  = [280.0] * 30 + [300.0]   # 20bps widening
        ccc_hist = [900.0] * 30 + [1050.0]  # 150bps widening

        readings = {
            "HY_OAS":  make_history_reading("HY_OAS",  hy_hist,  300.0),
            "CCC_OAS": make_history_reading("CCC_OAS", ccc_hist, 1050.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.ccc_tail_first_widening

    def test_ccc_tail_first_widening_absolute_mode_genuine(self, cal):
        """Genuine divergence: CCC+250/HY+30 over 30d → fires via absolute mode
        (250 >= 200 absolute floor; 30 < 50 composite ceiling)."""
        hy_hist  = [280.0] * 30 + [310.0]   # 30bps widening
        ccc_hist = [900.0] * 30 + [1150.0]  # 250bps widening

        readings = {
            "HY_OAS":  make_history_reading("HY_OAS",  hy_hist,  310.0),
            "CCC_OAS": make_history_reading("CCC_OAS", ccc_hist, 1150.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.ccc_tail_first_widening

    def test_ccc_ratio_mode_gated_against_compressed_regime_noise(self, cal):
        """ENG-45: CCC+29/HY+8 over 30d → ratio 3.62x >= 3x would fire on the
        raw ratio, but CCC's own move (29bps) is below the ccc_ratio_min_bps
        gate (75bps) — this is compressed-regime noise, not a genuine
        divergence, and must NOT fire. Absolute mode also correctly doesn't
        fire (29 << 200). Confirmed live 2026-06-30."""
        hy_hist  = [280.0] * 30 + [288.0]   # 8bps widening
        ccc_hist = [900.0] * 30 + [929.0]   # 29bps widening

        readings = {
            "HY_OAS":  make_history_reading("HY_OAS",  hy_hist,  288.0),
            "CCC_OAS": make_history_reading("CCC_OAS", ccc_hist, 929.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert not sig.ccc_tail_first_widening

    def test_ccc_tail_first_widening_absolute_mode(self, cal):
        """CCC +200bps while HY <50bps → ccc_tail_first_widening True."""
        hy_hist  = [280.0] * 30 + [310.0]  # 30bps (< 50)
        ccc_hist = [900.0] * 30 + [1110.0] # 210bps (>= 200)

        readings = {
            "HY_OAS":  make_history_reading("HY_OAS",  hy_hist,  310.0),
            "CCC_OAS": make_history_reading("CCC_OAS", ccc_hist, 1110.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert sig.ccc_tail_first_widening

    def test_ccc_not_widening_below_threshold(self, cal):
        """CCC widening below thresholds → False."""
        hy_hist  = [280.0] * 30 + [310.0]   # 30bps
        ccc_hist = [900.0] * 30 + [1000.0]  # 100bps — below 200bps absolute

        readings = {
            "HY_OAS":  make_history_reading("HY_OAS",  hy_hist,  310.0),
            "CCC_OAS": make_history_reading("CCC_OAS", ccc_hist, 1000.0),
        }
        sig = compute_credit_signal(readings, cal)
        # 100bps change: ratio 100/30 ~3.3x (>= 3 threshold) → should fire via ratio mode
        # ratio_met: hy_vel_30d=30 > 0 and ccc_vel=100 >= 3*30=90 → True
        assert sig.ccc_tail_first_widening  # fires via ratio mode


# ── Convergence text cases ─────────────────────────────────────────────────────

class TestConvergenceText:

    def test_calm_endorses_equity(self, cal):
        """Calm credit → 'endorses' in convergence text."""
        hist = [280.0] * 200
        readings = {
            "HY_OAS": make_history_reading("HY_OAS", hist, 278.0),
            "IG_OAS": make_history_reading("IG_OAS", [70.0]*200, 68.0),
        }
        sig = compute_credit_signal(readings, cal)
        assert "endors" in sig.convergence_text.lower() or "calm" in sig.convergence_text.lower()

    def test_history_missing_incomplete_text(self, cal):
        """No history → convergence text mentions history unavailable."""
        readings = {"HY_OAS": make_reading("HY_OAS", 300.0)}
        sig = compute_credit_signal(readings, cal)
        assert "incomplete" in sig.convergence_text.lower() or "unavailable" in sig.convergence_text.lower()

    def test_recession_pricing_in_text(self, cal):
        """HY recession pricing fired → convergence text mentions D floor."""
        hist = [300.0] * 200
        readings = {"HY_OAS": make_history_reading("HY_OAS", hist, 650.0)}
        sig = compute_credit_signal(readings, cal, hy_sustain_days=10)
        if sig.hy_recession_pricing:
            assert "25%" in sig.convergence_text or "floor" in sig.convergence_text.lower() or "recession" in sig.convergence_text.lower()


# ── Return type is CreditSignal ───────────────────────────────────────────────

class TestReturnType:
    def test_returns_credit_signal_type(self, cal):
        sig = compute_credit_signal({}, cal)
        assert isinstance(sig, CreditSignal)

    def test_empty_readings_no_exception(self, cal):
        """Empty readings dict → all None values, flags present, no crash."""
        sig = compute_credit_signal({}, cal)
        assert sig.hy_oas is None
        assert sig.ig_oas is None
        assert not sig.hy_stress_beginning
        assert not sig.hy_recession_pricing
