"""
tests/test_stage3/conftest.py — shared fixtures for Stage 3 unit tests.

All fixtures build CalibrationState objects directly from dataclass constructors.
No file I/O — all tests pass without network access.
"""
from __future__ import annotations
import pytest
from datetime import datetime

from advisor.types import (
    CalibrationState,
    CascadeBlock,
    ComponentWeight,
    DataReading,
    DataSource,
    FloorParams,
    InstrumentEntry,
    MultiplierBlock,
    RegimeBlock,
    ReturnRange,
    ThresholdBlock,
    UpdateFrequency,
)


# ── Minimal ThresholdBlock (§1) ────────────────────────────────────────────────

def _threshold_block() -> ThresholdBlock:
    return ThresholdBlock(
        hy_stress_delta=150,
        hy_recession_delta=300,
        hy_velocity_delta=100,
        hy_sustain_days=10,
        ig_transmission_delta=60,
        ig_velocity_delta=40,
        ig_sustain_days=10,
        ccc_ratio_multiplier=3.0,
        ccc_absolute_floor_bps=200,
        ccc_composite_ceiling_bps=50,
    )


# ── Minimal RegimeBlock (§9) ───────────────────────────────────────────────────

def _regime_block() -> RegimeBlock:
    return RegimeBlock(
        commodity_fear_HIGH_energy_pct=15.0,   # %
        commodity_fear_HIGH_vix_change=0.0,    # pts (<=0)
        commodity_fear_MOD_energy_pct=10.0,
        commodity_fear_MOD_vix_change=5.0,
        equity_div_HIGH_pct=5.0,               # %
        equity_div_MOD_pct=2.0,
        underweight_gap_trigger_pp=5.0,
        appreciation_trigger_30d_pct=5.0,
        entry_extension_thresholds={
            "broad_market_equity_domestic":       15.0,
            "broad_market_equity_international":  15.0,
            "thematic_sector_equity":             20.0,
            "geopolitical_premium":               20.0,
            "commodity_linked":                   20.0,
            "inflation_hedge_precious_metals":    20.0,
            "real_asset_contracted_revenue":      15.0,
            "secular_technology_growth":          20.0,
            "emerging_market_equity":             15.0,
            "real_estate_equity_income":          15.0,
            "policy_driven_thematic_equity":      20.0,
            # N/A roles
            "consumer_defensive_equity":          None,
            "healthcare_defensive_equity":        None,
            "systematic_trend_following":         None,
            "floating_rate_credit_income":        None,
            "inflation_linked_sovereign":         None,
            "rate_sensitive_income_short_duration": None,
            "rate_sensitive_income_long_duration":  None,
        },
        move_elevated=80.0,
        move_stress=100.0,
        move_crisis=130.0,
        move_systemic=160.0,
    )


# ── Minimal CascadeBlock (§12) ─────────────────────────────────────────────────

def _cascade_block() -> CascadeBlock:
    return CascadeBlock(
        farm_filings_alert_pct=50.0,        # % YoY
        natgas_alert_price=6.00,            # $/mmBtu
        fertilizer_alert_pct=50.0,          # % above 12mo avg
        kre_vs_spx_alert_pct=15.0,          # pp underperformance (positive = underperform)
        sofr_dff_alert_bps=10.0,            # bps
        sofr_dff_sustain_days=5,
        margin_mom_decline_pct=-5.0,        # % MoM (threshold for FIRES)
        gate_count_alert=3,
        bankruptcy_watch_quarterly=220,
        bankruptcy_fires_quarterly=300,
        e_term_premium_warning_bps=100.0,   # stored as bps; divide by 100 for %
        e_term_premium_alert_bps=150.0,
        e_30y_warning_pct=5.50,
    )


# ── Minimal return table (§4.1) ────────────────────────────────────────────────

def _return_table() -> dict:
    """Minimal §4.1 return table with a few roles for testing."""
    SCENARIOS = ["A", "B", "C", "D", "E", "F"]
    roles = {
        "broad_market_equity_domestic":        [5, -8, -4, -12, -8, 7],
        "real_asset_contracted_revenue":        [3,  6,  8,  -6, -10, 3],
        "secular_technology_growth":            [6, -2,  2, -14, -10, 4],
        "inflation_hedge_precious_metals":      [-2, 6, -2,  -3,  10, -3],
        "geopolitical_premium":                 [-4,  4,  12, -8,  8, -2],
        "policy_driven_thematic_equity":        [4, -3, -1,  -5,  -6, 4],
        "consumer_defensive_equity":            [0,  5,  2,  -5,   2, -2],
        "systematic_trend_following":           [-2,  4, 4,   -5,  4, -3],
        "rate_sensitive_income_short_duration": [1,  1,  1,   1,  -2,  1],
    }
    table = {}
    for role, conservs in roles.items():
        table[role] = {
            s: ReturnRange(conservative=conservs[i], upside=conservs[i]+4, confidence="HIGH")
            for i, s in enumerate(SCENARIOS)
        }
    return table


# ── Minimal instrument entries (§11) ──────────────────────────────────────────

def _instruments() -> dict:
    return {
        "VTI": InstrumentEntry(
            ticker="VTI",
            components=[ComponentWeight(role_id="broad_market_equity_domestic", weight=1.0)],
            tax_placement="ALL",
        ),
        "AIPO": InstrumentEntry(
            ticker="AIPO",
            components=[
                ComponentWeight(role_id="real_asset_contracted_revenue",   weight=0.69),
                ComponentWeight(role_id="secular_technology_growth",        weight=0.16),
                ComponentWeight(role_id="inflation_hedge_commodity_linked", weight=0.11),
                ComponentWeight(role_id="policy_driven_thematic_equity",    weight=0.04),
            ],
            tax_placement="ALL",
        ),
        "SGOL": InstrumentEntry(
            ticker="SGOL",
            components=[ComponentWeight(role_id="inflation_hedge_precious_metals", weight=1.0)],
            tax_placement="ALL",
        ),
        "SGOV": InstrumentEntry(
            ticker="SGOV",
            components=[ComponentWeight(role_id="rate_sensitive_income_short_duration", weight=1.0)],
            tax_placement="ALL",
        ),
        "XLP": InstrumentEntry(
            ticker="XLP",
            components=[ComponentWeight(role_id="consumer_defensive_equity", weight=1.0)],
            tax_placement="ALL",
        ),
        "DBMF": InstrumentEntry(
            ticker="DBMF",
            components=[ComponentWeight(role_id="systematic_trend_following", weight=1.0)],
            tax_placement="ALL",
        ),
    }


# ── Full CalibrationState fixture ──────────────────────────────────────────────

@pytest.fixture
def cal() -> CalibrationState:
    """Minimal but internally consistent CalibrationState for Stage 3 tests."""
    # Add inflation_hedge_commodity_linked to return table for AIPO
    rt = _return_table()
    rt["inflation_hedge_commodity_linked"] = {
        s: ReturnRange(conservative=v, upside=v+4, confidence="HIGH")
        for s, v in zip("ABCDEF", [2, 6, 7, -8, 2, -2])
    }
    return CalibrationState(
        version="test-9.99",
        last_updated="2026-01-01",
        thresholds=_threshold_block(),
        return_table=rt,
        multipliers=MultiplierBlock(
            ira={"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0, "E": 1.0, "F": 1.0},
            roth={"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0, "E": 1.0, "F": 1.0},
        ),
        floor_params=FloorParams(
            base_floor=0.25,
            min_floor_pct=0.02,
            concentration_cap=0.40,
            floor_loss_prob_threshold=0.15,
        ),
        regime=_regime_block(),
        roles={
            "broad_market_equity_domestic":        "equity risk premium",
            "real_asset_contracted_revenue":        "contracted cash flows",
            "secular_technology_growth":            "AI revenue growth",
            "inflation_hedge_precious_metals":      "monetary hedge",
            "geopolitical_premium":                 "conflict premium",
            "policy_driven_thematic_equity":        "legislative mandate",
            "consumer_defensive_equity":            "demand inelasticity",
            "systematic_trend_following":           "trend alpha",
            "rate_sensitive_income_short_duration": "short duration income",
            "floating_rate_credit_income":          "floating rate",
            "inflation_hedge_commodity_linked":     "commodity beta",
        },
        instruments=_instruments(),
        cascade=_cascade_block(),
    )


# ── DataReading factory ────────────────────────────────────────────────────────

def make_reading(spec_id: str, value, *, failed: bool = False) -> DataReading:
    """Create a DataReading for tests."""
    r = DataReading(
        spec_id=spec_id,
        value=value,
        source=DataSource.YFINANCE,
        fetched_at=datetime(2026, 6, 12),
        quality_flags=["FETCH_FAILED"] if failed else [],
    )
    return r


def make_history_reading(spec_id: str, history: list, current: float) -> DataReading:
    """Create a DataReading with a history list (oldest-first)."""
    return DataReading(
        spec_id=spec_id,
        value={"current": current, "history": history},
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime(2026, 6, 12),
    )
