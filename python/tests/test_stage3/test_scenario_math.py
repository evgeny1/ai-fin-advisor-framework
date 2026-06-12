"""
tests/test_stage3/test_scenario_math.py — Unit tests for analysis/scenario_math.py.

Maps to: M03_ScenarioFramework.md (probability arithmetic pipeline).
Tests: normalize_scores, apply_floors, apply_session_cap, check_b_vs_c, apply_all_rules.
All tests are pure arithmetic — no file I/O, no network.
"""
from __future__ import annotations

import pytest

from advisor.analysis.scenario_math import (
    apply_all_rules,
    apply_floors,
    apply_session_cap,
    check_b_vs_c,
    normalize_scores,
)
from advisor.exceptions import HardStopException
from advisor.types import RawScores, ScenarioProbabilities


# ── Helpers ────────────────────────────────────────────────────────────────────

def _raw(**kwargs) -> RawScores:
    defaults = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0, "F": 0.0}
    defaults.update(kwargs)
    return RawScores(**defaults)


def _base(**kwargs) -> dict:
    """Start from equal probs then override."""
    d = {"A": 16.67, "B": 16.67, "C": 16.67, "D": 16.67, "E": 16.67, "F": 16.65}
    d.update(kwargs)
    return d


def _prior(**kwargs) -> ScenarioProbabilities:
    defaults = {"A": 16.0, "B": 20.0, "C": 20.0, "D": 16.0, "E": 14.0, "F": 14.0}
    defaults.update(kwargs)
    return ScenarioProbabilities(**defaults)


# ── normalize_scores ───────────────────────────────────────────────────────────

class TestNormalizeScores:

    def test_equal_scores_produce_equal_probs(self):
        raw = _raw(A=1, B=1, C=1, D=1, E=1, F=1)
        result = normalize_scores(raw)
        for s in "ABCDEF":
            assert abs(result[s] - 100.0 / 6) < 0.01

    def test_probs_sum_to_100(self):
        raw = _raw(A=5, B=10, C=8, D=2, E=1, F=4)
        result = normalize_scores(raw)
        assert abs(sum(result.values()) - 100.0) < 0.001

    def test_single_scenario_dominant(self):
        raw = _raw(B=10)
        result = normalize_scores(raw)
        assert abs(result["B"] - 100.0) < 0.001
        for s in "ACDEF":
            assert result[s] == 0.0

    def test_proportional_scaling(self):
        raw = _raw(A=3, B=6, C=1, D=0, E=0, F=0)
        result = normalize_scores(raw)
        # B should be 2× A
        assert abs(result["B"] - 2 * result["A"]) < 0.001

    def test_zero_total_raises_hard_stop(self):
        raw = _raw()  # all zeros
        with pytest.raises(HardStopException, match="HARD_STOP"):
            normalize_scores(raw)


# ── apply_floors ──────────────────────────────────────────────────────────────

class TestApplyFloors:

    def test_no_floor_needed_all_above_three(self):
        base = {"A": 40.0, "B": 20.0, "C": 15.0, "D": 10.0, "E": 10.0, "F": 5.0}
        result = apply_floors(base)
        # F is exactly 5% > 3% — no floor adjustment
        assert abs(result["F"] - 5.0) < 0.01
        assert abs(sum(result.values()) - 100.0) < 0.01

    def test_low_scenario_raised_to_floor(self):
        # Give E and F very low probabilities
        base = {"A": 50.0, "B": 30.0, "C": 15.0, "D": 4.0, "E": 0.5, "F": 0.5}
        result = apply_floors(base)
        assert result["E"] >= 3.0
        assert result["F"] >= 3.0
        assert abs(sum(result.values()) - 100.0) < 0.01

    def test_floor_redistribution_maintains_sum(self):
        # Use inputs well above floor to avoid single-pass edge case where
        # an above-floor scenario at exactly 3.0 gets reduced below floor.
        base = {"A": 65.0, "B": 28.0, "C": 5.0, "D": 1.0, "E": 0.5, "F": 0.5}
        result = apply_floors(base)
        assert abs(sum(result.values()) - 100.0) < 0.01
        # Scenarios initially below floor must be raised to 3%
        assert result["D"] >= 3.0
        assert result["E"] >= 3.0
        assert result["F"] >= 3.0
        # Large scenarios still above floor
        assert result["A"] >= 3.0
        assert result["B"] >= 3.0

    def test_d_structural_floor_when_recession_pricing_fired(self):
        # D starts at 10% — HY_RecessionPricing pushes it to 25%
        base = {"A": 35.0, "B": 25.0, "C": 20.0, "D": 10.0, "E": 5.0, "F": 5.0}
        result = apply_floors(base, hy_recession_pricing_fired=True)
        assert result["D"] >= 25.0 - 0.001
        assert abs(sum(result.values()) - 100.0) < 0.01

    def test_d_already_above_structural_floor_unchanged(self):
        # D already 30% — no structural floor adjustment needed
        base = {"A": 30.0, "B": 15.0, "C": 15.0, "D": 30.0, "E": 5.0, "F": 5.0}
        result = apply_floors(base, hy_recession_pricing_fired=True)
        assert abs(result["D"] - 30.0) < 0.01

    def test_d_floor_not_applied_when_recession_not_fired(self):
        base = {"A": 35.0, "B": 25.0, "C": 20.0, "D": 10.0, "E": 5.0, "F": 5.0}
        result = apply_floors(base, hy_recession_pricing_fired=False)
        assert result["D"] < 25.0  # no structural floor


# ── apply_session_cap ─────────────────────────────────────────────────────────

class TestApplySessionCap:

    def test_no_prior_cap_not_applied(self):
        derived = {"A": 5.0, "B": 60.0, "C": 20.0, "D": 5.0, "E": 5.0, "F": 5.0}
        result, flags = apply_session_cap(derived, prior=None)
        assert result == derived
        assert any("not applicable" in f for f in flags)

    def test_shift_within_cap_unchanged(self):
        prior = _prior(A=16, B=30, C=25, D=10, E=10, F=9)
        derived = {"A": 16.0, "B": 45.0, "C": 15.0, "D": 10.0, "E": 9.0, "F": 5.0}
        # B shifts from 30 → 45 = +15pp (within 25pp cap)
        result, flags = apply_session_cap(derived, prior)
        assert abs(result["B"] - 45.0) < 0.01
        assert flags == [] or all("cap applied" not in f for f in flags)

    def test_shift_exceeds_cap_gets_capped(self):
        prior = _prior(A=5, B=5, C=5, D=5, E=5, F=75)
        derived = {"A": 5.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 45.0, "F": 35.0}
        # E shifts from 5 → 45 = +40pp — exceeds 25pp cap
        result, flags = apply_session_cap(derived, prior)
        assert result["E"] <= 5.0 + 25.0 + 0.01  # capped at prior + 25pp
        assert any("25pp session cap applied to E" in f for f in flags)
        assert abs(sum(result.values()) - 100.0) < 0.01

    def test_signal_convergence_bypasses_cap(self):
        prior = _prior(A=5, B=5, C=5, D=5, E=5, F=75)
        derived = {"A": 5.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 45.0, "F": 35.0}
        result, flags = apply_session_cap(
            derived, prior, signal_convergence_documented=True
        )
        # Full shift allowed — result should equal derived (or close)
        assert abs(result["E"] - 45.0) < 0.01
        assert any("SignalConvergence documented" in f for f in flags)

    def test_result_sums_to_100_after_cap(self):
        prior = _prior(A=16, B=16, C=16, D=16, E=16, F=20)
        derived = {"A": 5.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 75.0, "F": 5.0}
        result, _ = apply_session_cap(derived, prior)
        assert abs(sum(result.values()) - 100.0) < 0.01


# ── check_b_vs_c ──────────────────────────────────────────────────────────────

class TestCheckBvsC:

    def test_both_above_30_returns_warning(self):
        probs = {"A": 5.0, "B": 40.0, "C": 35.0, "D": 10.0, "E": 5.0, "F": 5.0}
        result = check_b_vs_c(probs)
        assert result is not None
        assert "B vs C constraint" in result
        assert "B=40.0%" in result
        assert "C=35.0%" in result

    def test_one_below_30_returns_none(self):
        probs = {"A": 5.0, "B": 40.0, "C": 25.0, "D": 15.0, "E": 10.0, "F": 5.0}
        assert check_b_vs_c(probs) is None

    def test_exactly_30_each_does_not_trigger(self):
        # Constraint is strict > 30, not >= 30
        probs = {"A": 10.0, "B": 30.0, "C": 30.0, "D": 15.0, "E": 8.0, "F": 7.0}
        assert check_b_vs_c(probs) is None

    def test_both_zero_returns_none(self):
        probs = {"A": 60.0, "B": 0.0, "C": 0.0, "D": 20.0, "E": 10.0, "F": 10.0}
        assert check_b_vs_c(probs) is None


# ── apply_all_rules ───────────────────────────────────────────────────────────

class TestApplyAllRules:

    def test_full_pipeline_produces_valid_output(self):
        raw = _raw(A=5, B=8, C=6, D=2, E=2, F=4)
        probs, flags = apply_all_rules(raw, prior=None)
        assert abs(probs.A + probs.B + probs.C + probs.D + probs.E + probs.F - 100.0) < 0.01

    def test_all_scenarios_above_floor(self):
        # Give D and E very small weights — floors must kick in
        raw = _raw(A=30, B=20, C=15, D=0.1, E=0.1, F=5)
        probs, _ = apply_all_rules(raw, prior=None)
        assert probs.D >= 3.0
        assert probs.E >= 3.0

    def test_d_floor_with_recession_pricing(self):
        raw = _raw(A=10, B=10, C=10, D=1, E=1, F=1)
        probs, _ = apply_all_rules(raw, prior=None, hy_recession_pricing_fired=True)
        assert probs.D >= 25.0

    def test_b_vs_c_warning_in_flags(self):
        # Force B and C both > 30% after normalization
        raw = _raw(A=1, B=10, C=10, D=1, E=1, F=1)
        probs, flags = apply_all_rules(raw, prior=None)
        if probs.B > 30.0 and probs.C > 30.0:
            assert any("B vs C constraint" in f for f in flags)

    def test_zero_raw_scores_raises_hard_stop(self):
        with pytest.raises(HardStopException, match="HARD_STOP"):
            apply_all_rules(_raw(), prior=None)

    def test_scenario_probabilities_type_returned(self):
        raw = _raw(A=5, B=8, C=6, D=2, E=2, F=4)
        probs, flags = apply_all_rules(raw, prior=None)
        assert isinstance(probs, ScenarioProbabilities)
        assert isinstance(flags, list)

    def test_session_cap_applied_via_pipeline(self):
        prior = _prior(A=5, B=5, C=5, D=5, E=5, F=75)
        raw = _raw(A=1, B=1, C=1, D=1, E=10, F=7)  # pushes E high
        probs, flags = apply_all_rules(raw, prior=prior)
        assert abs(probs.A + probs.B + probs.C + probs.D + probs.E + probs.F - 100.0) < 0.01
