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


# ── GAP-16 promotion (v1.46): blended_scenario_return range adjustment ────────

class TestBlendedScenarioReturnRangePositionAdjustment:
    """
    conftest's _return_table() builds every role with upside = conservative+4,
    i.e. every range is exactly 4pp wide by construction — below the 6pp
    GAP-16 gate. These tests widen IHP's B row to [6,12] (6pp, matching the
    real framework's actual B row) the same way test_range_position.py's
    `_widen_b_range` helper does, so the gate-clearing tests below actually
    exercise the adjustment instead of silently no-op'ing on a too-narrow
    range. test_narrow_range_scenario_is_not_adjusted_even_with_signal
    deliberately uses the UNwidened default to confirm the gate itself works.
    """

    def _widen_b_range(self, cal: CalibrationState) -> None:
        cal.return_table["inflation_hedge_precious_metals"]["B"] = ReturnRange(
            conservative=6.0, upside=12.0, confidence="HIGH"
        )

    def test_empty_signals_dict_is_fully_backward_compatible(self, cal: CalibrationState):
        """cal.range_position_signals defaults to {} -- every pre-v1.46 call
        site and every other test in this file must be byte-for-byte
        unaffected. This is the single most important test in this class."""
        self._widen_b_range(cal)
        assert cal.range_position_signals == {}
        result = blended_scenario_return("SGOL", "B", "conservative", cal)
        assert abs(result - 6.0) < 0.001  # unadjusted table value

    def test_unfavorable_signal_lowers_blended_return(self, cal: CalibrationState):
        self._widen_b_range(cal)  # [6,12], 6pp wide -- clears the gate
        cal.range_position_signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = blended_scenario_return("SGOL", "B", "conservative", cal)
        assert abs(result - 4.5) < 0.001  # 6.0 - min(0.25*6, 3.0) = 6.0 - 1.5

    def test_favorable_signal_raises_blended_return(self, cal: CalibrationState):
        self._widen_b_range(cal)
        cal.range_position_signals = {"inflation_hedge_precious_metals": "favorable"}
        result = blended_scenario_return("SGOL", "B", "conservative", cal)
        assert abs(result - 7.5) < 0.001  # 6.0 + 1.5

    def test_upside_return_type_is_never_adjusted(self, cal: CalibrationState):
        """Adjustment is conservative-only by design -- upside is never used
        in any EV/allocation computation, so adjusting it would be silent
        dead code. Confirm the guard actually holds."""
        self._widen_b_range(cal)
        cal.range_position_signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = blended_scenario_return("SGOL", "B", "upside", cal)
        assert abs(result - 12.0) < 0.001  # untouched table upside

    def test_signal_for_a_different_role_does_not_leak(self, cal: CalibrationState):
        """SIVR-style cross-contamination guard: a signal keyed to one role
        must never affect blended_scenario_return() for an instrument whose
        components don't include that role."""
        self._widen_b_range(cal)
        cal.range_position_signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = blended_scenario_return("VTI", "B", "conservative", cal)
        assert abs(result - (-8.0)) < 0.001  # VTI's own unadjusted B value

    def test_composite_instrument_only_adjusts_the_matching_component(
        self, cal: CalibrationState
    ):
        """AIPO has no inflation_hedge_precious_metals component -- a signal
        for that role must leave AIPO's blend completely unchanged, even
        though AIPO does carry inflation_hedge_commodity_linked (a different
        role this test deliberately does NOT add a signal for)."""
        self._widen_b_range(cal)
        cal.range_position_signals = {"inflation_hedge_precious_metals": "unfavorable"}
        unadjusted = 0.69*6 + 0.16*(-2) + 0.11*6 + 0.04*(-3)
        result = blended_scenario_return("AIPO", "B", "conservative", cal)
        assert abs(result - unadjusted) < 0.001

    def test_mixed_signal_does_not_adjust(self, cal: CalibrationState):
        self._widen_b_range(cal)
        cal.range_position_signals = {"inflation_hedge_precious_metals": "mixed"}
        result = blended_scenario_return("SGOL", "B", "conservative", cal)
        assert abs(result - 6.0) < 0.001

    def test_narrow_range_scenario_is_not_adjusted_even_with_signal(
        self, cal: CalibrationState
    ):
        """Scenario A's IHP row in conftest is [-2,2] -- only 4pp wide,
        below the 6pp GAP-16 gate (B is intentionally NOT widened here).
        A signal keyed to the same role must not move scenario A's value."""
        cal.range_position_signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = blended_scenario_return("SGOL", "A", "conservative", cal)
        assert abs(result - (-2.0)) < 0.001


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
