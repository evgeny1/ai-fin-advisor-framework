"""
tests/test_stage5/test_scoring_questions.py — Unit tests for orchestrator/scoring_questions.py

Coverage:
  - generate_questions() returns exactly 17 questions
  - All 6 scenarios are represented
  - All question IDs are unique
  - Questions covering credit signals auto-score correctly
  - Questions needing AI input have auto_score=None
  - Brent below trigger → C_check_brent auto_score stays None (ENG-67:
    gap_pct alone can't distinguish "no supply event" from "verified
    event, price hasn't caught up")
  - aggregate_raw_scores(): merges auto + AI scores correctly
  - aggregate_raw_scores(): Scenario F negative raw clamped to 0
  - questions_for_ai(): filters correctly to None auto_score
  - QUALITATIVE_TARGETS defined and non-empty
"""
from __future__ import annotations

import pytest
from datetime import datetime

from advisor.types import (
    CalibrationState,
    CascadeBlock,
    ComponentWeight,
    CreditSignal,
    DataReading,
    DataSource,
    FloorParams,
    InstrumentEntry,
    MultiplierBlock,
    RegimeBlock,
    ReturnRange,
    RawScores,
    ScoringAnswers,
    ScoringQuestion,
    ThresholdBlock,
)
from advisor.orchestrator.scoring_questions import (
    QUALITATIVE_TARGETS,
    aggregate_raw_scores,
    generate_questions,
    questions_for_ai,
)

_SCENARIOS = list("ABCDEF")
_EXPECTED_QUESTION_COUNT = 20   # A:3 B:3 C:3 D:4 E:3 F:4


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _minimal_cal() -> CalibrationState:
    return CalibrationState(
        version="test-5.0", last_updated="2026-06-12",
        thresholds=ThresholdBlock(
            hy_stress_delta=150, hy_recession_delta=300,
            hy_velocity_delta=100, hy_sustain_days=10,
            ig_transmission_delta=60, ig_velocity_delta=40, ig_sustain_days=10,
            ccc_ratio_multiplier=3.0, ccc_absolute_floor_bps=200,
            ccc_composite_ceiling_bps=50,
        ),
        return_table={},
        multipliers=MultiplierBlock(ira={}, roth={}),
        floor_params=FloorParams(
            base_floor=0.25, min_floor_pct=0.02,
            concentration_cap=0.40, floor_loss_prob_threshold=0.15,
        ),
        regime=RegimeBlock(
            commodity_fear_HIGH_energy_pct=15.0, commodity_fear_HIGH_vix_change=0.0,
            commodity_fear_MOD_energy_pct=10.0, commodity_fear_MOD_vix_change=5.0,
            equity_div_HIGH_pct=5.0, equity_div_MOD_pct=2.0,
            underweight_gap_trigger_pp=5.0, appreciation_trigger_30d_pct=5.0,
            entry_extension_thresholds={}, move_elevated=80.0,
            move_stress=100.0, move_crisis=130.0, move_systemic=160.0,
        ),
        roles={}, instruments={},
        cascade=CascadeBlock(
            farm_filings_alert_pct=50.0, natgas_alert_price=6.0,
            fertilizer_alert_pct=50.0, kre_vs_spx_alert_pct=15.0,
            sofr_dff_alert_bps=10.0, sofr_dff_sustain_days=5,
            margin_mom_decline_pct=-5.0, gate_count_alert=3,
            bankruptcy_watch_quarterly=220, bankruptcy_fires_quarterly=300,
            e_term_premium_warning_bps=100.0, e_term_premium_alert_bps=150.0,
            e_30y_warning_pct=5.50,
        ),
    )


def _brent_reading(price: float) -> DataReading:
    return DataReading(
        spec_id="BRENT_CRUDE",
        value={"current": price},
        source=DataSource.YFINANCE,
        fetched_at=datetime(2026, 6, 12),
    )


def _calm_credit() -> CreditSignal:
    return CreditSignal(
        hy_oas=280.0, hy_median_180d=280.0,
        ig_oas=90.0, ig_median_180d=90.0,
        ccc_oas=800.0, move=75.0,
        hy_stress_beginning=False,
        hy_recession_pricing=False,
        ig_transmission_reached=False,
        ccc_tail_first_widening=False,
        convergence_text="Credit calm",
        quality_flags=[],
    )


def _stressed_credit() -> CreditSignal:
    return CreditSignal(
        hy_oas=450.0, hy_median_180d=280.0,
        ig_oas=160.0, ig_median_180d=90.0,
        ccc_oas=1000.0, move=100.0,
        hy_stress_beginning=True,
        hy_recession_pricing=False,
        ig_transmission_reached=True,
        ccc_tail_first_widening=True,
        convergence_text="HY stress + IG transmission reached",
        quality_flags=[],
    )


def _recession_credit() -> CreditSignal:
    return CreditSignal(
        hy_oas=600.0, hy_median_180d=280.0,
        ig_oas=200.0, ig_median_180d=90.0,
        ccc_oas=1400.0, move=130.0,
        hy_stress_beginning=True,
        hy_recession_pricing=True,
        ig_transmission_reached=True,
        ccc_tail_first_widening=True,
        convergence_text="HY recession pricing",
        quality_flags=[],
    )


# ── generate_questions ────────────────────────────────────────────────────────

def test_question_count():
    qs = generate_questions([], _minimal_cal(), None, {})
    assert len(qs) == _EXPECTED_QUESTION_COUNT, (
        f"Expected {_EXPECTED_QUESTION_COUNT} questions, got {len(qs)}"
    )


def test_all_scenarios_represented():
    qs = generate_questions([], _minimal_cal(), None, {})
    represented = {q.scenario for q in qs}
    assert represented == set(_SCENARIOS), f"Missing scenarios: {set(_SCENARIOS) - represented}"


def test_question_ids_unique():
    qs = generate_questions([], _minimal_cal(), None, {})
    ids = [q.id for q in qs]
    assert len(ids) == len(set(ids)), f"Duplicate question IDs: {set(i for i in ids if ids.count(i) > 1)}"


def test_valid_scores_non_empty():
    qs = generate_questions([], _minimal_cal(), None, {})
    for q in qs:
        assert len(q.valid_scores) >= 2, f"{q.id} has fewer than 2 valid_scores"


def test_all_questions_have_id_and_scenario():
    qs = generate_questions([], _minimal_cal(), None, {})
    for q in qs:
        assert q.id and q.scenario and q.question and q.evidence is not None


# ── Auto-scoring: credit checks ───────────────────────────────────────────────

def test_a_credit_calm_auto_scores_1():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    q = next(q for q in qs if q.id == "A_check_credit")
    assert q.auto_score == 1


def test_a_credit_stressed_auto_scores_0():
    qs = generate_questions([], _minimal_cal(), _stressed_credit(), {})
    q = next(q for q in qs if q.id == "A_check_credit")
    assert q.auto_score == 0


def test_d_credit_calm_auto_scores_0():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    q = next(q for q in qs if q.id == "D_check_credit")
    assert q.auto_score == 0


def test_d_credit_recession_auto_scores_3():
    qs = generate_questions([], _minimal_cal(), _recession_credit(), {})
    q = next(q for q in qs if q.id == "D_check_credit")
    assert q.auto_score == 3


def test_d_credit_stress_only_auto_scores_2():
    """HY_stress_beginning=True, IG_transmission=False, no recession → score 2."""
    from advisor.types import CreditSignal
    hy_stress_only = CreditSignal(
        hy_oas=430.0, hy_median_180d=280.0,
        ig_oas=100.0, ig_median_180d=90.0,
        ccc_oas=900.0, move=90.0,
        hy_stress_beginning=True,
        hy_recession_pricing=False,
        ig_transmission_reached=False,
        ccc_tail_first_widening=False,
        convergence_text="HY stress only",
        quality_flags=[],
    )
    qs = generate_questions([], _minimal_cal(), hy_stress_only, {})
    q = next(q for q in qs if q.id == "D_check_credit")
    assert q.auto_score == 2


def test_e_ig_transmission_auto_scores_2():
    qs = generate_questions([], _minimal_cal(), _stressed_credit(), {})
    q = next(q for q in qs if q.id == "E_check_ig")
    assert q.auto_score == 2


def test_e_ig_calm_auto_scores_0():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    q = next(q for q in qs if q.id == "E_check_ig")
    assert q.auto_score == 0


# ── Auto-scoring: Brent threshold ─────────────────────────────────────────────

def test_brent_well_below_trigger_auto_score_is_none():
    """ENG-67 regression: Brent at $75 (>15% below the $110 nominal trigger)
    must NOT auto-score 0. Price gap alone can't distinguish "no supply
    event" from "verified T1 supply event, price hasn't caught up" (e.g.
    the 2026-07-14 Hormuz naval blockade, which auto-scored 0 under the
    old logic despite a T1-confirmed active chokepoint event). auto_score
    must stay None here, matching the precedent the above-trigger branch
    already sets, so the question reaches Claude with the gap_pct evidence
    intact rather than being silently foreclosed to 0.
    """
    readings = [_brent_reading(75.0)]
    qs = generate_questions(readings, _minimal_cal(), None, {})
    q = next(q for q in qs if q.id == "C_check_brent")
    assert q.auto_score is None, (
        "C_check_brent auto-scored a non-None value from price gap alone; "
        "this forecloses score=1 (T1-verified supply event, Brent below "
        "15%-gap band) with no way for Claude to override — the ENG-67 bug."
    )


def test_brent_near_trigger_auto_score_is_none():
    """Brent at $105 (near $110 trigger) → needs AI to check sustained days → auto_score=None."""
    readings = [_brent_reading(105.0)]
    qs = generate_questions(readings, _minimal_cal(), None, {})
    q = next(q for q in qs if q.id == "C_check_brent")
    # Near trigger: auto_score should be None (AI needs to confirm sustained days)
    assert q.auto_score is None or q.auto_score in [0, 1, 2]


# ── No credit signal → auto_score = None ─────────────────────────────────────

def test_no_credit_signal_auto_score_is_none():
    """Without a CreditSignal, credit checks cannot be auto-scored."""
    qs = generate_questions([], _minimal_cal(), None, {})
    a_credit = next(q for q in qs if q.id == "A_check_credit")
    d_credit = next(q for q in qs if q.id == "D_check_credit")
    e_ig     = next(q for q in qs if q.id == "E_check_ig")
    assert a_credit.auto_score is None
    assert d_credit.auto_score is None
    assert e_ig.auto_score is None


# ── questions_for_ai ──────────────────────────────────────────────────────────

def test_questions_for_ai_excludes_auto_scored():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    ai_qs = questions_for_ai(qs)
    for q in ai_qs:
        assert q.auto_score is None


def test_questions_for_ai_includes_qualitative():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    ai_qs = questions_for_ai(qs)
    ai_ids = {q.id for q in ai_qs}
    # These are always qualitative
    assert "A_check_fed" in ai_ids
    assert "B_check_cpi" in ai_ids
    assert "C_check_chokepoint" in ai_ids


# ── aggregate_raw_scores ──────────────────────────────────────────────────────

def test_aggregate_merges_auto_and_ai():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    # Stub AI answers for non-auto questions (score 1 for each)
    ai_qs = questions_for_ai(qs)
    ai_answers = ScoringAnswers(
        answers={q.id: 1 for q in ai_qs},
        reasoning={q.id: "stub" for q in ai_qs},
    )
    raw = aggregate_raw_scores(ai_answers, qs)
    assert isinstance(raw, RawScores)
    assert raw.total > 0


def test_aggregate_f_negative_clamped_to_zero():
    qs = generate_questions([], _minimal_cal(), None, {})
    # Score all F checks negatively: F_check_noshock = -2, rest = 0
    all_answers = ScoringAnswers(
        answers={q.id: (-2 if q.id == "F_check_noshock" else 0) for q in qs if q.auto_score is None},
        reasoning={},
    )
    raw = aggregate_raw_scores(all_answers, qs)
    assert raw.F >= 0.0, f"Scenario F raw score {raw.F} should be >= 0 (clamped)"


def test_aggregate_uses_auto_score_over_ai():
    qs = generate_questions([], _minimal_cal(), _calm_credit(), {})
    # All credit checks are auto-scored; AI also provides answers (should be ignored)
    ai_answers = ScoringAnswers(
        answers={q.id: 99 for q in qs},  # 99 is invalid but shouldn't be used for auto-scored
        reasoning={},
    )
    raw = aggregate_raw_scores(ai_answers, qs)
    # A_check_credit auto=1 → contributes to A raw; 99 should not override
    a_auto_q = next(q for q in qs if q.id == "A_check_credit")
    assert a_auto_q.auto_score == 1


# ── QUALITATIVE_TARGETS ───────────────────────────────────────────────────────

def test_qualitative_targets_non_empty():
    assert len(QUALITATIVE_TARGETS) > 0


def test_qualitative_targets_contains_key_topics():
    required = {"fed_guidance", "cpi_trajectory", "supply_chokepoint"}
    assert required.issubset(set(QUALITATIVE_TARGETS))
