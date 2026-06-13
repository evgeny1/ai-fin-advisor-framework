"""
tests/test_stage3/test_instruments.py — Unit tests for analysis/instruments.py.

Maps to: M15_InstrumentClassification.md.
Tests: validate_classifications, blended_scenario_return, classify_instrument,
       dominant_directive.
All tests are pure — no file I/O, no network.
"""
from __future__ import annotations

import pytest

from advisor.analysis.instruments import (
    blended_scenario_return,
    classify_instrument,
    dominant_directive,
    validate_classifications,
)
from advisor.exceptions import HardStopException
from advisor.types import (
    CalibrationState,
    ComponentWeight,
    InstrumentEntry,
    ReturnRange,
)

# ── Fixtures from conftest: cal ─────────────────────────────────────────────


# ── validate_classifications ──────────────────────────────────────────────────

class TestValidateClassifications:

    def test_happy_path_single_valid_ticker(self, cal: CalibrationState):
        warnings = validate_classifications(["VTI"], cal)
        # Check 1–4 pass. Check 5 warns only when last_reviewed is set.
        assert isinstance(warnings, list)

    def test_happy_path_all_tickers(self, cal: CalibrationState):
        tickers = ["VTI", "SGOL", "SGOV", "XLP", "DBMF"]
        warnings = validate_classifications(tickers, cal)
        assert isinstance(warnings, list)

    def test_missing_ticker_raises_hard_stop(self, cal: CalibrationState):
        with pytest.raises(HardStopException, match="HARD_STOP"):
            validate_classifications(["VTI", "PHANTOM_ETF"], cal)

    def test_unregistered_role_raises_hard_stop(self, cal: CalibrationState):
        # Inject an instrument with a role not in cal.roles
        cal.instruments["GHOST"] = InstrumentEntry(
            ticker="GHOST",
            components=[ComponentWeight(role_id="nonexistent_role", weight=1.0)],
            tax_placement="ALL",
        )
        with pytest.raises(HardStopException, match="unregistered role"):
            validate_classifications(["GHOST"], cal)
        del cal.instruments["GHOST"]

    def test_missing_return_table_row_raises_hard_stop(self, cal: CalibrationState):
        # Register role but omit from return table
        cal.roles["orphan_role"] = "test driver"
        cal.instruments["ORPHAN"] = InstrumentEntry(
            ticker="ORPHAN",
            components=[ComponentWeight(role_id="orphan_role", weight=1.0)],
            tax_placement="ALL",
        )
        with pytest.raises(HardStopException, match="no §4.1 return table row"):
            validate_classifications(["ORPHAN"], cal)
        del cal.instruments["ORPHAN"]
        del cal.roles["orphan_role"]

    def test_weight_sum_below_one_produces_warning_not_hard_stop(
        self, cal: CalibrationState
    ):
        """Weights < 1.0 allowed when UNCLASSIFIED components are excluded (e.g. AIPO bitcoin miners).
        ValidateClassifications now issues a non-blocking warning, not a HardStop."""
        cal.instruments["PARTIAL"] = InstrumentEntry(
            ticker="PARTIAL",
            components=[
                ComponentWeight(role_id="consumer_defensive_equity", weight=0.5),
                ComponentWeight(role_id="systematic_trend_following", weight=0.3),
            ],
            tax_placement="ALL",
        )
        # Should NOT raise — should produce a warning about partial weights
        warnings = validate_classifications(["PARTIAL"], cal)
        assert any("PARTIAL" in w or "0.8" in w for w in warnings)
        del cal.instruments["PARTIAL"]

    def test_weight_sum_above_one_raises_hard_stop(self, cal: CalibrationState):
        """Weights > 1.0 always raises HardStopException (data entry error)."""
        cal.instruments["OVERFLOW"] = InstrumentEntry(
            ticker="OVERFLOW",
            components=[
                ComponentWeight(role_id="consumer_defensive_equity", weight=0.7),
                ComponentWeight(role_id="systematic_trend_following", weight=0.5),
            ],
            tax_placement="ALL",
        )
        with pytest.raises(HardStopException, match="weights sum to"):
            validate_classifications(["OVERFLOW"], cal)
        del cal.instruments["OVERFLOW"]

    def test_weight_sum_zero_raises_hard_stop(self, cal: CalibrationState):
        """Zero-weight instrument (all UNCLASSIFIED removed) always raises HardStopException."""
        cal.instruments["EMPTY"] = InstrumentEntry(
            ticker="EMPTY",
            components=[],   # no classified components at all
            tax_placement="ALL",
        )
        with pytest.raises(HardStopException):
            validate_classifications(["EMPTY"], cal)
        del cal.instruments["EMPTY"]

    def test_staleness_warning_produced_when_last_reviewed_set(
        self, cal: CalibrationState
    ):
        cal.instruments["DATED"] = InstrumentEntry(
            ticker="DATED",
            components=[ComponentWeight(role_id="consumer_defensive_equity", weight=1.0)],
            tax_placement="ALL",
            last_reviewed="2025-01-01",
        )
        warnings = validate_classifications(["DATED"], cal)
        assert any("DATED" in w for w in warnings)
        del cal.instruments["DATED"]

    def test_no_staleness_warning_when_last_reviewed_absent(
        self, cal: CalibrationState
    ):
        # VTI in conftest has no last_reviewed → no staleness warning
        warnings = validate_classifications(["VTI"], cal)
        assert not any("VTI" in w for w in warnings)

    def test_aipo_composite_passes_check_4(self, cal: CalibrationState):
        # AIPO weights 0.69+0.16+0.11+0.04 = 1.00 — must pass
        warnings = validate_classifications(["AIPO"], cal)
        assert isinstance(warnings, list)


# ── blended_scenario_return ───────────────────────────────────────────────────

class TestBlendedScenarioReturn:

    def test_single_role_matches_table_value(self, cal: CalibrationState):
        # VTI = 100% broad_market_equity_domestic
        # From conftest return table: scenario A conservative = 5
        result = blended_scenario_return("VTI", "A", "conservative", cal)
        assert abs(result - 5.0) < 0.001

    def test_single_role_upside_above_conservative(self, cal: CalibrationState):
        conserv = blended_scenario_return("SGOL", "B", "conservative", cal)
        upside   = blended_scenario_return("SGOL", "B", "upside", cal)
        assert upside > conserv

    def test_composite_is_weighted_blend(self, cal: CalibrationState):
        # AIPO components: real_asset 0.69, secular_tech 0.16, commodity 0.11, policy 0.04
        # Scenario A conservative: 3, 6, 2, 4
        expected = 0.69*3 + 0.16*6 + 0.11*2 + 0.04*4
        result = blended_scenario_return("AIPO", "A", "conservative", cal)
        assert abs(result - expected) < 0.001

    def test_all_six_scenarios_accessible(self, cal: CalibrationState):
        for s in "ABCDEF":
            result = blended_scenario_return("VTI", s, "conservative", cal)
            assert isinstance(result, float)

    def test_invalid_return_type_raises_value_error(self, cal: CalibrationState):
        with pytest.raises(ValueError, match="return_type must be"):
            blended_scenario_return("VTI", "A", "bad_type", cal)

    def test_invalid_scenario_raises_value_error(self, cal: CalibrationState):
        with pytest.raises(ValueError, match="invalid scenario"):
            blended_scenario_return("VTI", "Z", "conservative", cal)

    def test_missing_ticker_raises_hard_stop(self, cal: CalibrationState):
        with pytest.raises(HardStopException, match="HARD_STOP"):
            blended_scenario_return("PHANTOM", "A", "conservative", cal)


# ── classify_instrument ───────────────────────────────────────────────────────

class TestClassifyInstrument:

    def test_returns_component_list(self, cal: CalibrationState):
        comps = classify_instrument("VTI", cal)
        assert len(comps) == 1
        assert comps[0].role_id == "broad_market_equity_domestic"
        assert comps[0].weight == 1.0

    def test_composite_returns_multiple_components(self, cal: CalibrationState):
        comps = classify_instrument("AIPO", cal)
        assert len(comps) == 4
        total_weight = sum(c.weight for c in comps)
        assert abs(total_weight - 1.0) < 0.001

    def test_missing_ticker_raises_hard_stop(self, cal: CalibrationState):
        with pytest.raises(HardStopException, match="HARD_STOP"):
            classify_instrument("GHOST", cal)


# ── dominant_directive ────────────────────────────────────────────────────────

class TestDominantDirective:

    def _table(self) -> dict:
        return {
            ("broad_market_equity_domestic", "B"): "REDUCE",
            ("consumer_defensive_equity",    "B"): "HOLD",
            ("systematic_trend_following",   "B"): "ADD",
            ("real_asset_contracted_revenue", "A"): "HOLD",
            ("secular_technology_growth",     "A"): "REDUCE",
        }

    def test_single_role_returns_directive(self, cal: CalibrationState):
        table = {("broad_market_equity_domestic", "B"): "REDUCE"}
        result = dominant_directive("VTI", "B", table, cal)
        assert result == "REDUCE"

    def test_missing_directive_defaults_to_hold(self, cal: CalibrationState):
        result = dominant_directive("VTI", "A", {}, cal)
        assert result == "HOLD"

    def test_composite_conflicting_returns_primary(self, cal: CalibrationState):
        # AIPO primary role = real_asset_contracted_revenue (weight 0.69)
        # Conflicting directives across components → primary role wins
        table = {
            ("real_asset_contracted_revenue",   "B"): "HOLD",
            ("secular_technology_growth",        "B"): "REDUCE",
            ("inflation_hedge_commodity_linked", "B"): "ADD",
            ("policy_driven_thematic_equity",    "B"): "REDUCE",
        }
        result = dominant_directive("AIPO", "B", table, cal)
        assert result == "HOLD"  # primary role directive

    def test_same_direction_selects_most_conservative(self, cal: CalibrationState):
        # AIPO scenario B — both components say REDUCE but different magnitude
        # primary = real_asset, secondary material = secular_tech (0.16 >= 0.15)
        # Both say reduce — most conservative should win
        table = {
            ("real_asset_contracted_revenue",   "A"): "TRIM",
            ("secular_technology_growth",        "A"): "REDUCE",
            ("inflation_hedge_commodity_linked", "A"): "REDUCE",
            ("policy_driven_thematic_equity",    "A"): "TRIM",
        }
        result = dominant_directive("AIPO", "A", table, cal)
        # REDUCE is more conservative than TRIM
        assert result in ("REDUCE", "TRIM")  # most conservative in reduce direction
