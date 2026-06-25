"""
tests/e2e/test_evaluate_allocation.py

End-to-end test for advisor_evaluate_allocation() and
advisor_check_instrument_candidate() — the two MCP tools added 2026-06-17
to close ENG-16 (M13/M15/M08 portfolio math was implemented and unit-tested
in python/advisor/portfolio/ and analysis/instruments.py, but no MCP tool
ever called it — Claude re-derived all of it by hand from the M13/M15/M08
.md spec every session).

This is deliberately an END-TO-END test, not another unit test: the
underlying functions (scenario_weighted_allocation, feasibility_check,
classify_instrument, dominant_directive, dual_role_conflict, auto_disqualify)
already have unit test coverage in tests/test_stage4/. What that coverage
does NOT exercise is the MCP tool wrapper itself — JSON serialization,
account_profile dict parsing, the _cache precondition checks, and multiple
functions composed together for one ticker the way a real session would
call them. That composition is exactly what shipped untested and unwired
before this fix, so it's what this file targets.

Placed under tests/e2e/ rather than a new tests/test_stageN/ folder —
first step toward the eventual unit/e2e/integration reorganization of the
whole test suite (tracked, not done wholesale here: see ENG-22).
"""
from __future__ import annotations

import json

import pytest

from advisor import mcp_server
from advisor.types import (
    CalibrationState,
    CascadeBlock,
    ComponentWeight,
    FloorParams,
    InstrumentEntry,
    MultiplierBlock,
    RegimeBlock,
    ReturnRange,
    ScenarioProbabilities,
    ThresholdBlock,
)

_SCENARIOS = ("A", "B", "C", "D", "E", "F")


# ── Minimal CalibrationState (mirrors tests/test_stage4/conftest.py's shape,
#    kept local and self-contained rather than importing across test
#    directories — this file should be runnable on its own) ──────────────────

def _build_cal() -> CalibrationState:
    return_table_rows = {
        # (A,   B,  C,   D,   E,  F)
        "geopolitical_premium":                 [-2,  2,  4,  -4,   1,   1],
        "rate_sensitive_income_short_duration":  [ 1,  1,  1,   1,  -2,   1],
        "broad_market_equity_domestic":          [ 5, -8, -4, -12,  -8,   7],
        "inflation_hedge_precious_metals":       [-2,  6, -2,  -3,  10,  -3],
    }
    return_table = {
        role: {
            s: ReturnRange(conservative=vals[i], upside=vals[i] + 4, confidence="HIGH")
            for i, s in enumerate(_SCENARIOS)
        }
        for role, vals in return_table_rows.items()
    }

    instruments = {
        "SGOV": InstrumentEntry(
            ticker="SGOV",
            components=[ComponentWeight("rate_sensitive_income_short_duration", 1.0)],
            tax_placement="ALL",
        ),
        "SGOL": InstrumentEntry(
            ticker="SGOL",
            components=[ComponentWeight("inflation_hedge_precious_metals", 1.0)],
            tax_placement="ALL",
        ),
        # Composite with conflicting directions in scenario C:
        # broad_market_equity_domestic → REDUCE_TO_MIN, geopolitical_premium → ADD
        "CONFLICT_TEST": InstrumentEntry(
            ticker="CONFLICT_TEST",
            components=[
                ComponentWeight("broad_market_equity_domestic", 0.60),
                ComponentWeight("geopolitical_premium", 0.40),
            ],
            tax_placement="ALL",
        ),
    }

    return CalibrationState(
        version="e2e-test-1.0",
        last_updated="2026-06-17",
        thresholds=ThresholdBlock(
            hy_stress_delta=150, hy_recession_delta=300,
            hy_velocity_delta=100, hy_sustain_days=10,
            ig_transmission_delta=60, ig_velocity_delta=40, ig_sustain_days=10,
            ccc_ratio_multiplier=3.0, ccc_absolute_floor_bps=200,
            ccc_composite_ceiling_bps=50,
        ),
        return_table=return_table,
        multipliers=MultiplierBlock(
            ira={"A": 2.0, "B": 1.3, "C": 1.3, "D": 1.3, "E": 1.2, "F": 2.0},
            roth={"A": 3.1, "B": 1.3, "C": 1.3, "D": 1.6, "E": 1.4, "F": 3.1},
            ira_floor=1.3, roth_floor=1.3,
        ),
        floor_params=FloorParams(
            base_floor=0.25, min_floor_pct=0.02,
            concentration_cap=0.40, floor_loss_prob_threshold=0.15,
        ),
        regime=RegimeBlock(
            commodity_fear_HIGH_energy_pct=15.0, commodity_fear_HIGH_vix_change=0.0,
            commodity_fear_MOD_energy_pct=10.0, commodity_fear_MOD_vix_change=5.0,
            equity_div_HIGH_pct=5.0, equity_div_MOD_pct=2.0,
            underweight_gap_trigger_pp=5.0, appreciation_trigger_30d_pct=5.0,
            entry_extension_thresholds={},
            move_elevated=80.0, move_stress=100.0, move_crisis=130.0, move_systemic=160.0,
        ),
        roles={
            "geopolitical_premium": "conflict premium",
            "rate_sensitive_income_short_duration": "short duration income",
            "broad_market_equity_domestic": "equity risk premium",
            "inflation_hedge_precious_metals": "monetary hedge",
        },
        instruments=instruments,
        cascade=CascadeBlock(
            farm_filings_alert_pct=50.0, natgas_alert_price=6.00,
            fertilizer_alert_pct=50.0, kre_vs_spx_alert_pct=15.0,
            sofr_dff_alert_bps=10.0, sofr_dff_sustain_days=5,
            margin_mom_decline_pct=-5.0, gate_count_alert=3,
            bankruptcy_watch_quarterly=220, bankruptcy_fires_quarterly=300,
            e_term_premium_warning_bps=100.0, e_term_premium_alert_bps=150.0,
            e_30y_warning_pct=5.50,
        ),
    )

_IRA_PROFILE = {
    "account_id": "Primary_IRA_test",
    "owner": "primary",
    "planning_horizon_years": 10,
    "objective_type": "TARGET_THEN_RETURN",
    "concentration_cap": 0.40,
    "drawdown_tolerance": 0.35,
}

_CURRENT_WEIGHTS = {"SGOV": 0.30, "SGOL": 0.15, "CONFLICT_TEST": 0.20}


@pytest.fixture
def cached_session():
    """Populate mcp_server._cache the way advisor_run_computation() +
    advisor_apply_scoring() would have, without running either — this
    test targets advisor_evaluate_allocation() in isolation."""
    mcp_server._cache["cal"] = _build_cal()
    # C-dominant distribution — exercises the CONFLICT_TEST composite's
    # ADD-vs-REDUCE conflict in scenario C.
    mcp_server._cache["scenario_probs"] = ScenarioProbabilities(
        A=5, B=15, C=50, D=10, E=10, F=10
    )
    yield
    for key in ("cal", "scenario_probs"):
        mcp_server._cache.pop(key, None)


# ── Precondition checks ────────────────────────────────────────────────────

def test_errors_without_run_computation():
    """No cal cached at all → clear error, not a crash."""
    mcp_server._cache.pop("cal", None)
    mcp_server._cache.pop("scenario_probs", None)
    result = mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
    )
    assert '"status": "ERROR"' in result
    assert "advisor_run_computation" in result


def test_errors_without_apply_scoring():
    """cal cached but scenario_probs not → clear error naming the right tool."""
    mcp_server._cache["cal"] = _build_cal()
    mcp_server._cache.pop("scenario_probs", None)
    try:
        result = mcp_server._tool_evaluate_allocation(
            account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
        )
        assert '"status": "ERROR"' in result
        assert "advisor_apply_scoring" in result
    finally:
        mcp_server._cache.pop("cal", None)


def test_invalid_objective_type_is_a_clean_error(cached_session):
    bad_profile = dict(_IRA_PROFILE, objective_type="NOT_A_REAL_TYPE")
    result = mcp_server._tool_evaluate_allocation(
        account_profile=bad_profile, current_weights=_CURRENT_WEIGHTS,
    )
    assert '"status": "ERROR"' in result
    assert "objective_type" in result


# ── ENG-33 fallback: explicit cal/probs override ────────────────────────────
# `python -m advisor evaluate-allocation` (the CLI fallback for when the
# MCP tool hangs — see __main__.py) is a fresh process with nothing
# cached, so it must be able to call this with zero _cache dependency.

def test_explicit_cal_and_probs_work_with_empty_cache():
    """The CLI path's whole reason for existing: this must work with
    _cache completely empty, proving no hidden cache dependency remains."""
    saved = dict(mcp_server._cache)
    mcp_server._cache.clear()
    try:
        result = json.loads(mcp_server._tool_evaluate_allocation(
            account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
            tickers=["SGOV"],
            cal=_build_cal(),
            probs=ScenarioProbabilities(A=5, B=15, C=50, D=10, E=10, F=10),
        ))
        assert result["status"] == "OK"
        assert "scenario_weighted_weight" in result["instruments"]["SGOV"]
    finally:
        mcp_server._cache.clear()
        mcp_server._cache.update(saved)


def test_explicit_probs_override_stale_cached_probs(cached_session):
    """cached_session sets cache probs to C=50-dominant. Passing a
    different, explicit A-dominant probs must actually take effect —
    not just fill in when the cache is empty, a true override."""
    explicit_probs = ScenarioProbabilities(A=70, B=10, C=5, D=5, E=5, F=5)
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
        probs=explicit_probs,
    ))
    assert result["dominant_scenario"] == "A"  # not "C" — cache's value


def test_explicit_cal_overrides_stale_cached_cal(cached_session):
    """Same override proof for cal: an instrument only present in the
    explicit cal, absent from cached_session's fixture, must resolve."""
    alt_cal = _build_cal()
    alt_cal.instruments["ONLY_IN_OVERRIDE"] = alt_cal.instruments["SGOV"]
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights={"ONLY_IN_OVERRIDE": 1.0},
        cal=alt_cal,
    ))
    assert "error" not in result["instruments"]["ONLY_IN_OVERRIDE"]


# ── Core computation shape ──────────────────────────────────────────────────

def test_returns_full_per_scenario_breakdown(cached_session):
    """Per M03/M06: NEVER present allocation numbers without the full
    scenario-weighted breakdown. This is the field that breakdown comes from."""
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
        tickers=["SGOV"],
    ))
    assert result["status"] == "OK"
    sgov = result["instruments"]["SGOV"]
    assert set(sgov["per_scenario"].keys()) == set(_SCENARIOS)
    assert "scenario_weighted_weight" in sgov
    assert "blended_conservative_return_pct" in sgov
    assert "directive" in sgov
    assert "floor" in sgov
    assert sgov["dual_role_conflict"] is None  # single-role instrument


def test_dominant_scenario_matches_highest_probability(cached_session):
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
    ))
    assert result["dominant_scenario"] == "C"  # fixture sets C=50, the max


def test_composite_instrument_components_sum_to_one(cached_session):
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
        tickers=["CONFLICT_TEST"],
    ))
    comps = result["instruments"]["CONFLICT_TEST"]["components"]
    assert len(comps) == 2
    total = sum(c["weight"] for c in comps)
    assert total == pytest.approx(1.0)


def test_dual_role_conflict_detected_for_composite_in_scenario_c(cached_session):
    """CONFLICT_TEST: broad_market_equity_domestic → REDUCE_TO_MIN in C,
    geopolitical_premium → ADD in C. Dominant scenario is C (fixture).
    This is exactly the M08.DualRoleConflict() case the framework's
    own conftest.py fixture (test_stage4) was built to exercise."""
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
        tickers=["CONFLICT_TEST"],
    ))
    conflict = result["instruments"]["CONFLICT_TEST"]["dual_role_conflict"]
    assert conflict is not None
    assert "CONFLICT_TEST" in conflict
    assert "scenario C" in conflict


def test_unclassified_ticker_does_not_crash_other_tickers(cached_session):
    """One bad ticker shouldn't take down the whole call — confirms the
    per-ticker try/except actually isolates failures."""
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights={**_CURRENT_WEIGHTS, "NOT_IN_REGISTRY": 0.05},
        tickers=["SGOV", "NOT_IN_REGISTRY"],
    ))
    assert result["status"] == "OK"
    assert "error" in result["instruments"]["NOT_IN_REGISTRY"]
    assert "scenario_weighted_weight" in result["instruments"]["SGOV"]


# ── FeasibilityCheck wiring ──────────────────────────────────────────────────

def test_feasibility_skipped_without_proposed_allocations(cached_session):
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
    ))
    assert "feasibility" not in result
    assert any("FeasibilityCheck skipped" in f for f in result["flags"])


def test_feasibility_runs_when_proposed_allocations_given(cached_session):
    proposed = {"SGOV": 0.30, "SGOL": 0.15, "CONFLICT_TEST": 0.55}
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE, current_weights=_CURRENT_WEIGHTS,
        proposed_allocations=proposed,
    ))
    assert "feasibility" in result
    assert result["feasibility"]["objective_type"] == "TARGET_THEN_RETURN"
    assert isinstance(result["feasibility"]["feasible"], bool)
    assert "portfolio_return_pct" in result["feasibility"]


# ── M07 candidate check (no session precondition) ───────────────────────────

def test_candidate_check_disqualifies_on_low_aum_long_horizon():
    result = json.loads(mcp_server._tool_check_instrument_candidate(
        ticker="TINYFUND",
        aum_millions=40.0,
        track_record_years=5.0,
        instrument_type="active_fund",
        revenue_type="fee_based",
        hold_horizon_years=10,
    ))
    assert result["disqualified"] is True
    assert "AUM" in result["reason"]


def test_candidate_check_passes_clean_instrument():
    result = json.loads(mcp_server._tool_check_instrument_candidate(
        ticker="CLEANFUND",
        aum_millions=5000.0,
        track_record_years=12.0,
        foreign_concentration_pct=10.0,
        instrument_type="passive_broad",
        revenue_type="fee_based",
        hold_horizon_years=10,
    ))
    assert result["disqualified"] is False


def test_candidate_check_requires_no_cache_at_all():
    """Confirms the M07 check really has no session precondition —
    runs cleanly even with an empty _cache."""
    saved = dict(mcp_server._cache)
    mcp_server._cache.clear()
    try:
        result = json.loads(mcp_server._tool_check_instrument_candidate(
            ticker="NOCACHE", aum_millions=500.0, track_record_years=5.0,
        ))
        assert result["status"] == "OK"
    finally:
        mcp_server._cache.clear()
        mcp_server._cache.update(saved)


# \u2500\u2500 RecalibrationSequence MCP wiring (ENG-24) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_LOW_EV_ALLOCS = {"SGOV": 0.30, "SGOL": 0.15, "CONFLICT_TEST": 0.55}
# CONFLICT_TEST primary role is broad_market_equity_domestic (0.60 weight)
# In C-dominant distribution: broad_market = REDUCE_TO_MIN, geo_prem = ADD
# Blended conservative return for this portfolio is low → infeasible for IRA


def test_recalibration_block_present_when_infeasible(cached_session):
    """When feasibility fails, result must include a 'recalibration' block."""
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights=_CURRENT_WEIGHTS,
        proposed_allocations=_LOW_EV_ALLOCS,
    ))
    assert "feasibility" in result
    feasible = result["feasibility"]["feasible"]
    if not feasible:
        assert "recalibration" in result
        rec = result["recalibration"]
        assert "shortfall_pp" in rec
        assert "anchor_tickers" in rec
        assert "gap_closed_by_reallocation" in rec
        assert "revised_portfolio_return_pct" in rec
        assert "revised_gap_pp" in rec


def test_recalibration_block_absent_when_feasible(cached_session):
    """When portfolio is feasible, no recalibration block."""
    # SGOV-only: rate-short income, likely feasible for IRA at C-dominant distribution
    proposed = {"SGOV": 0.30, "SGOL": 0.70}
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights=_CURRENT_WEIGHTS,
        proposed_allocations=proposed,
    ))
    if result.get("feasibility", {}).get("feasible"):
        assert "recalibration" not in result


def test_recalibration_block_absent_without_proposed_allocations(cached_session):
    """No proposed_allocations → no feasibility check → no recalibration."""
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights=_CURRENT_WEIGHTS,
    ))
    assert "recalibration" not in result


def test_recalibration_priority_is_target_for_ira(cached_session):
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights=_CURRENT_WEIGHTS,
        proposed_allocations=_LOW_EV_ALLOCS,
    ))
    if not result.get("feasibility", {}).get("feasible") and "recalibration" in result:
        assert result["recalibration"]["priority"] == "TARGET"


def test_recalibration_revised_gap_non_negative(cached_session):
    result = json.loads(mcp_server._tool_evaluate_allocation(
        account_profile=_IRA_PROFILE,
        current_weights=_CURRENT_WEIGHTS,
        proposed_allocations=_LOW_EV_ALLOCS,
    ))
    if "recalibration" in result:
        assert result["recalibration"]["revised_gap_pp"] >= 0.0
