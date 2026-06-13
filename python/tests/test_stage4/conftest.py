"""
tests/test_stage4/conftest.py — shared fixtures for Stage 4 unit tests.

Builds CalibrationState and AccountProfile objects directly from dataclasses.
No file I/O — all tests pass without network access.

Reuses Stage 3 return table / instrument structure where possible;
adds account profiles for each objective type used in the real portfolio.
"""
from __future__ import annotations
import pytest
from advisor.types import (
    AccountProfile,
    CalibrationState,
    CascadeBlock,
    ComponentWeight,
    FloorParams,
    InstrumentEntry,
    MultiplierBlock,
    ObjectiveType,
    RegimeBlock,
    ReturnRange,
    ScenarioProbabilities,
    ThresholdBlock,
)

_SCENARIOS = ("A", "B", "C", "D", "E", "F")


# ── Minimal CalibrationState sub-blocks ───────────────────────────────────────

def _thresholds() -> ThresholdBlock:
    return ThresholdBlock(
        hy_stress_delta=150, hy_recession_delta=300,
        hy_velocity_delta=100, hy_sustain_days=10,
        ig_transmission_delta=60, ig_velocity_delta=40, ig_sustain_days=10,
        ccc_ratio_multiplier=3.0, ccc_absolute_floor_bps=200,
        ccc_composite_ceiling_bps=50,
    )


def _regime() -> RegimeBlock:
    return RegimeBlock(
        commodity_fear_HIGH_energy_pct=15.0, commodity_fear_HIGH_vix_change=0.0,
        commodity_fear_MOD_energy_pct=10.0,  commodity_fear_MOD_vix_change=5.0,
        equity_div_HIGH_pct=5.0, equity_div_MOD_pct=2.0,
        underweight_gap_trigger_pp=5.0, appreciation_trigger_30d_pct=5.0,
        entry_extension_thresholds={
            "broad_market_equity_domestic": 15.0,
            "geopolitical_premium": 20.0,
            "inflation_hedge_precious_metals": 20.0,
            "inflation_hedge_commodity_linked": 20.0,
            "real_asset_contracted_revenue": 15.0,
            "policy_driven_thematic_equity": 20.0,
            "rate_sensitive_income_short_duration": None,
            "rate_sensitive_income_long_duration": None,
            "broad_market_equity_international": 15.0,
        },
        move_elevated=80.0, move_stress=100.0,
        move_crisis=130.0, move_systemic=160.0,
    )


def _cascade() -> CascadeBlock:
    return CascadeBlock(
        farm_filings_alert_pct=50.0, natgas_alert_price=6.00,
        fertilizer_alert_pct=50.0, kre_vs_spx_alert_pct=15.0,
        sofr_dff_alert_bps=10.0, sofr_dff_sustain_days=5,
        margin_mom_decline_pct=-5.0, gate_count_alert=3,
        bankruptcy_watch_quarterly=220, bankruptcy_fires_quarterly=300,
        e_term_premium_warning_bps=100.0, e_term_premium_alert_bps=150.0,
        e_30y_warning_pct=5.50,
    )


def _return_table() -> dict:
    """Minimal §4.1 table: one row per role needed by fixtures."""
    rows = {
        # (A,  B,  C,   D,   E,   F)
        "geopolitical_premium":                [-2,  2,  4,  -4,   1,   1],
        "inflation_hedge_precious_metals":     [-2,  6, -2,  -3,  10,  -3],
        "inflation_hedge_commodity_linked":    [ 2,  6,  7,  -8,   2,  -2],
        "real_asset_contracted_revenue":       [ 3,  6,  8,  -6, -10,   3],
        "policy_driven_thematic_equity":       [ 4, -3, -1,  -5,  -6,   4],
        "rate_sensitive_income_short_duration":[ 1,  1,  1,   1,  -2,   1],
        "rate_sensitive_income_long_duration": [ 3, -4, -5,   8,  -6,  -5],
        "broad_market_equity_domestic":        [ 5, -8, -4, -12,  -8,   7],
        "broad_market_equity_international":   [ 4, -5, -6,  -8, -10,   3],
        "secular_technology_growth":           [ 6, -2,  2, -14, -10,   4],
        "systematic_trend_following":          [-12, 15, 18,  -5,  -8,  -5],
        "consumer_defensive_equity":           [ 0,  2,  2,  -5,  -8,  -3],
    }
    table = {}
    for role, vals in rows.items():
        table[role] = {
            s: ReturnRange(conservative=vals[i], upside=vals[i] + 4, confidence="HIGH")
            for i, s in enumerate(_SCENARIOS)
        }
    return table


def _instruments() -> dict:
    """§11 instruments used across tests."""
    return {
        # Single-role instruments
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
        "XLP": InstrumentEntry(
            ticker="XLP",
            components=[ComponentWeight("consumer_defensive_equity", 1.0)],
            tax_placement="ALL",
        ),
        "DBMF": InstrumentEntry(
            ticker="DBMF",
            components=[ComponentWeight("systematic_trend_following", 1.0)],
            tax_placement="ALL",
        ),
        # Composite instruments
        "XAR": InstrumentEntry(
            ticker="XAR",
            components=[
                ComponentWeight("geopolitical_premium", 0.90),
                ComponentWeight("broad_market_equity_domestic", 0.10),
            ],
            tax_placement="ALL",
        ),
        "AIPO": InstrumentEntry(
            ticker="AIPO",
            components=[
                ComponentWeight("real_asset_contracted_revenue", 0.55),
                ComponentWeight("secular_technology_growth", 0.16),
                ComponentWeight("inflation_hedge_commodity_linked", 0.11),
                ComponentWeight("policy_driven_thematic_equity", 0.04),
            ],
            tax_placement="ALL",
        ),
        # Conflict test: ADD role (geo_prem in C) + REDUCE role (BMD in C)
        "CONFLICT_TEST": InstrumentEntry(
            ticker="CONFLICT_TEST",
            components=[
                ComponentWeight("broad_market_equity_domestic", 0.60),
                ComponentWeight("geopolitical_premium", 0.40),
            ],
            tax_placement="ALL",
        ),
    }


def _roles() -> dict:
    return {
        "geopolitical_premium":                "conflict premium",
        "inflation_hedge_precious_metals":     "monetary hedge",
        "inflation_hedge_commodity_linked":    "commodity beta",
        "real_asset_contracted_revenue":       "contracted cash flows",
        "policy_driven_thematic_equity":       "legislative mandate",
        "rate_sensitive_income_short_duration":"short duration income",
        "rate_sensitive_income_long_duration": "long duration income",
        "broad_market_equity_domestic":        "equity risk premium",
        "broad_market_equity_international":   "ex-US growth",
        "secular_technology_growth":           "AI revenue growth",
        "systematic_trend_following":          "trend alpha",
        "consumer_defensive_equity":           "demand inelasticity",
    }


@pytest.fixture
def cal() -> CalibrationState:
    """Full CalibrationState for Stage 4 tests."""
    return CalibrationState(
        version="test-4.0",
        last_updated="2026-06-12",
        thresholds=_thresholds(),
        return_table=_return_table(),
        multipliers=MultiplierBlock(
            ira={"A": 2.0, "B": 1.3, "C": 1.3, "D": 1.3, "E": 1.2, "F": 2.0},
            roth={"A": 3.1, "B": 1.3, "C": 1.3, "D": 1.6, "E": 1.4, "F": 3.1},
            ira_floor=1.3,
            roth_floor=1.3,
        ),
        floor_params=FloorParams(
            base_floor=0.25,
            min_floor_pct=0.02,
            concentration_cap=0.40,
            floor_loss_prob_threshold=0.15,
        ),
        regime=_regime(),
        roles=_roles(),
        instruments=_instruments(),
        cascade=_cascade(),
    )


# ── Probability fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def probs_bc() -> ScenarioProbabilities:
    """Current B/C dominant distribution (as per live session state)."""
    return ScenarioProbabilities(A=5, B=41, C=38, D=5, E=4, F=7)


@pytest.fixture
def probs_a_dominant() -> ScenarioProbabilities:
    """A-dominant: for testing soft-landing directives."""
    return ScenarioProbabilities(A=50, B=15, C=10, D=10, E=5, F=10)


# ── Account profile fixtures ───────────────────────────────────────────────────

@pytest.fixture
def ira_account() -> AccountProfile:
    """Primary IRA: TARGET_THEN_RETURN, 10-year horizon."""
    return AccountProfile(
        account_id="IRA_primary",
        owner="primary",
        planning_horizon_years=10,
        objective_type=ObjectiveType.TARGET_THEN_RETURN,
        floor_nominal_loss=False,
        concentration_cap=0.40,
        drawdown_tolerance=0.35,
    )


@pytest.fixture
def roth_account() -> AccountProfile:
    """Primary Roth IRA: TARGET_THEN_RETURN, 15-year horizon."""
    return AccountProfile(
        account_id="Roth_IRA_primary",
        owner="primary",
        planning_horizon_years=15,
        objective_type=ObjectiveType.TARGET_THEN_RETURN,
        floor_nominal_loss=False,
        concentration_cap=0.40,
        drawdown_tolerance=0.35,
    )


@pytest.fixture
def taxable_account() -> AccountProfile:
    """Primary Taxable: RETURN_THEN_TARGET."""
    return AccountProfile(
        account_id="Taxable_primary",
        owner="primary",
        planning_horizon_years=5,
        objective_type=ObjectiveType.RETURN_THEN_TARGET,
        floor_nominal_loss=False,
        concentration_cap=0.40,
        drawdown_tolerance=0.30,
    )


@pytest.fixture
def floor_account() -> AccountProfile:
    """Relative IRA: FLOOR_THEN_RETURN (no nominal loss in high-prob scenarios)."""
    return AccountProfile(
        account_id="IRA_relative",
        owner="relative",
        planning_horizon_years=10,
        objective_type=ObjectiveType.FLOOR_THEN_RETURN,
        floor_nominal_loss=True,
        concentration_cap=0.40,
        drawdown_tolerance=0.20,
    )


@pytest.fixture
def preservation_account() -> AccountProfile:
    """Taxable preservation: PRESERVATION."""
    return AccountProfile(
        account_id="Taxable_preservation",
        owner="primary",
        planning_horizon_years=1,
        objective_type=ObjectiveType.PRESERVATION,
        floor_nominal_loss=True,
        concentration_cap=1.0,
        drawdown_tolerance=0.05,
    )
