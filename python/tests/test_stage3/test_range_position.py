"""
tests/test_stage3/test_range_position.py — unit tests for GAP-16's
analysis/range_position.py (within-scenario sub-condition advisory).
GAP-18 (2026-08-14) generalized this from IHP-only to a per-role registry
(inflation_hedge_precious_metals + inflation_linked_sovereign); see
TestRoleSpecificWidthGate / TestInflationLinkedSovereign below for that
generalization's own coverage, and the "regression" tests throughout for
confirmation IHP/SGOL/SIVR behavior is unchanged by it.
"""
from __future__ import annotations

from datetime import datetime

from advisor.analysis.range_position import (
    _DEFAULT_WIDE_RANGE_THRESHOLD_PP,
    _width_gate_for_role,
    _WIDE_RANGE_THRESHOLD_PP_BY_ROLE,
    apply_range_position_adjustment,
    clean_signal_role_map,
    evaluate_range_position_advisories,
)
from advisor.types import (
    ComponentWeight,
    DataReading,
    DataSource,
    InstrumentEntry,
    ReturnRange,
    ScenarioProbabilities,
)


def _trend_reading(closes: list) -> DataReading:
    return DataReading(spec_id="x", value={"closes": closes, "n_weeks": len(closes)},
                       source=DataSource.YFINANCE, fetched_at=datetime(2026, 6, 20))


def _probs(**kw) -> ScenarioProbabilities:
    base = {"A": 10.0, "B": 50.0, "C": 20.0, "D": 10.0, "E": 5.0, "F": 5.0}
    base.update(kw)
    return ScenarioProbabilities(**base)


def _widen_b_range(cal):
    """Fixture's default IHP rows are all 4pp wide (below the 6pp
    threshold) — widen scenario B to mirror the real [6,12] B row so
    the GAP-16 width gate actually opens. Module-level (not a method) so
    both TestRangePositionAdvisory and GAP-18's TestInflationLinkedSovereign
    below can share it without duplicating it."""
    cal.return_table["inflation_hedge_precious_metals"]["B"] = ReturnRange(
        conservative=6.0, upside=12.0, confidence="HIGH"
    )


class TestRangePositionAdvisory:

    def _widen_b_range(self, cal):
        _widen_b_range(cal)

    def test_below_width_threshold_is_skipped(self, cal):
        """Default A-row is only 4pp wide -> no advisory emitted."""
        results = evaluate_range_position_advisories(
            ["SGOL"], _probs(A=60, B=10, C=10, D=10, E=5, F=5), cal, {}
        )
        assert results == []

    def test_unfavorable_signal_when_both_drivers_headwind(self, cal):
        self._widen_b_range(cal)
        readings = {
            "REAL_YIELD_10Y_TREND": _trend_reading([1.0, 1.2, 1.4, 1.6, 1.8]),  # rising
            "DXY_TREND":            _trend_reading([95, 97, 99, 101, 103, 105, 107, 109]),  # appreciating
        }
        results = evaluate_range_position_advisories(["SGOL"], _probs(), cal, readings)
        assert len(results) == 1
        adv = results[0]
        assert adv.scenario == "B"
        assert adv.range_width_pp == 6.0
        assert adv.signal == "unfavorable"
        assert len(adv.drivers) == 2

    def test_favorable_signal_when_both_drivers_tailwind(self, cal):
        self._widen_b_range(cal)
        readings = {
            "REAL_YIELD_10Y_TREND": _trend_reading([1.8, 1.6, 1.4, 1.2, 1.0]),  # falling
            "DXY_TREND":            _trend_reading([109, 107, 105, 103, 101, 99, 97, 95]),  # weakening
        }
        results = evaluate_range_position_advisories(["SGOL"], _probs(), cal, readings)
        assert results[0].signal == "favorable"

    def test_mixed_signal_when_drivers_disagree(self, cal):
        self._widen_b_range(cal)
        readings = {
            "REAL_YIELD_10Y_TREND": _trend_reading([1.0, 1.2, 1.4, 1.6, 1.8]),  # rising -> unfavorable
            "DXY_TREND":            _trend_reading([109, 107, 105, 103, 101, 99, 97, 95]),  # weakening -> favorable
        }
        results = evaluate_range_position_advisories(["SGOL"], _probs(), cal, readings)
        assert results[0].signal == "mixed"

    def test_no_trend_data_is_inconclusive_not_silently_neutral(self, cal):
        self._widen_b_range(cal)
        results = evaluate_range_position_advisories(["SGOL"], _probs(), cal, {})
        adv = results[0]
        assert adv.signal == "inconclusive"
        assert len(adv.quality_flags) == 2

    def test_non_ihp_instrument_is_skipped(self, cal):
        self._widen_b_range(cal)
        results = evaluate_range_position_advisories(["SGOV"], _probs(), cal, {})
        assert results == []

    def test_never_touches_ev_inputs(self, cal):
        """Advisory output carries no field that any EV/allocation function
        reads from — confirms this stays a pure annotation, not a gate."""
        self._widen_b_range(cal)
        readings = {"REAL_YIELD_10Y_TREND": _trend_reading([1.0, 1.8])}
        results = evaluate_range_position_advisories(["SGOL"], _probs(), cal, readings)
        adv = results[0]
        # range bounds reported match §4.1 exactly -- nothing recomputed
        assert (adv.range_conservative, adv.range_upside) == (6.0, 12.0)


# ── GAP-16 promotion (v1.46): clean_signal_role_map ────────────────────────────

class TestCleanSignalRoleMap:

    def test_drops_mixed_and_inconclusive(self):
        from advisor.analysis.range_position import RangePositionAdvisory as A
        advisories = [
            A(ticker="SGOL", role_id="inflation_hedge_precious_metals", scenario="B",
              range_conservative=6, range_upside=12, range_width_pp=6, signal="mixed"),
            A(ticker="XLP", role_id="consumer_defensive_equity", scenario="B",
              range_conservative=2, range_upside=6, range_width_pp=4, signal="inconclusive"),
        ]
        assert clean_signal_role_map(advisories) == {}

    def test_keeps_favorable_and_unfavorable(self):
        from advisor.analysis.range_position import RangePositionAdvisory as A
        advisories = [
            A(ticker="SGOL", role_id="inflation_hedge_precious_metals", scenario="B",
              range_conservative=6, range_upside=12, range_width_pp=6, signal="unfavorable"),
        ]
        assert clean_signal_role_map(advisories) == {
            "inflation_hedge_precious_metals": "unfavorable"
        }

    def test_empty_advisories_list_yields_empty_map(self):
        assert clean_signal_role_map([]) == {}


# ── GAP-16 promotion (v1.46): apply_range_position_adjustment ─────────────────

class TestApplyRangePositionAdjustment:

    def _range(self, conservative=6.0, upside=12.0):
        return ReturnRange(conservative=conservative, upside=upside, confidence="HIGH")

    def test_role_absent_from_signals_is_unchanged(self):
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0, self._range(), {}
        )
        assert result == 6.0

    def test_mixed_or_inconclusive_signal_is_unchanged(self):
        signals = {"inflation_hedge_precious_metals": "mixed"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0, self._range(), signals
        )
        assert result == 6.0

    def test_unfavorable_pulls_value_down_by_bounded_amount(self):
        # width=6pp, fraction=0.25 -> delta=1.5pp (below the 3pp cap)
        signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0, self._range(), signals
        )
        assert abs(result - (6.0 - 1.5)) < 0.001

    def test_favorable_pushes_value_up_by_bounded_amount(self):
        signals = {"inflation_hedge_precious_metals": "favorable"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0, self._range(), signals
        )
        assert abs(result - (6.0 + 1.5)) < 0.001

    def test_unfavorable_adjustment_is_capped_on_a_wide_range(self):
        # width=20pp -> 0.25*20=5pp uncapped, but cap is 3pp
        signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0,
            self._range(conservative=6.0, upside=26.0), signals,
        )
        assert abs(result - (6.0 - 3.0)) < 0.001

    def test_favorable_adjustment_never_exceeds_table_upside(self):
        # base already close to upside -- nudge would overshoot without the clamp
        signals = {"inflation_hedge_precious_metals": "favorable"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 11.0, self._range(), signals
        )
        assert result == 12.0  # clamped to upside, not 11.0 + 1.5 = 12.5

    def test_narrow_range_below_threshold_is_never_adjusted(self):
        # width=4pp < 6pp gate -- even a clean unfavorable signal is ignored
        signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0,
            self._range(conservative=6.0, upside=10.0), signals,
        )
        assert result == 6.0

    def test_unfavorable_can_go_below_table_conservative(self):
        """This is the entire point of the fix, stated as a test: a confirmed
        headwind means the table's own conservative floor is now optimistic,
        so the adjusted value going below it is intentional, not a bug."""
        signals = {"inflation_hedge_precious_metals": "unfavorable"}
        result = apply_range_position_adjustment(
            "inflation_hedge_precious_metals", "B", 6.0, self._range(), signals
        )
        assert result < 6.0


# ── GAP-18 (2026-08-14): role-specific width gate ──────────────────────────────

class TestRoleSpecificWidthGate:
    """_width_gate_for_role() itself, and the registry it reads from."""

    def test_ihp_gate_unchanged_at_6pp(self):
        assert _width_gate_for_role("inflation_hedge_precious_metals") == 6.0

    def test_ils_gate_is_2pp_not_ihp_default(self):
        assert _width_gate_for_role("inflation_linked_sovereign") == 2.0

    def test_unregistered_role_falls_back_to_default(self):
        # Fails safe toward the stricter original GAP-16 bar, not 0 -- see
        # module docstring/comment above _DEFAULT_WIDE_RANGE_THRESHOLD_PP.
        assert _width_gate_for_role("some_future_role_not_yet_registered") == \
            _DEFAULT_WIDE_RANGE_THRESHOLD_PP == 6.0

    def test_registry_contains_exactly_the_two_documented_roles(self):
        # Guards against silently registering a role here without also
        # registering a sub-condition evaluator for it (or vice versa) --
        # see _SUB_CONDITION_EVALUATORS in the module itself.
        assert set(_WIDE_RANGE_THRESHOLD_PP_BY_ROLE) == {
            "inflation_hedge_precious_metals",
            "inflation_linked_sovereign",
        }


# ── GAP-18 (2026-08-14): inflation_linked_sovereign (VTIP) ─────────────────────

class TestInflationLinkedSovereign:
    """
    VTIP's real §4.1 Scenario C range ([1,4]%, 3pp wide) sits BELOW IHP's
    6.0pp gate but ABOVE its own 2.0pp gate -- these tests exist specifically
    to prove the role-specific gate (not just the role_id plumbing) is what
    makes GAP-18 actually fire, since a shared-evaluator/wrong-gate bug here
    would silently never trigger for VTIP (see FRAMEWORK_BACKLOG ENG-72 /
    Calibration_State.md §6 item 48 for why this matters).
    """

    def _add_vtip(self, cal, *, conservative=1.0, upside=4.0, scenario="C"):
        """Mirrors VTIP's real single-role composition and its real, narrow
        Scenario C range -- not a widened fixture like IHP's _widen_b_range,
        since the whole point of this role's gate is that it should fire
        WITHOUT widening."""
        cal.instruments["VTIP"] = InstrumentEntry(
            ticker="VTIP",
            components=[ComponentWeight(role_id="inflation_linked_sovereign", weight=1.0)],
            tax_placement="RETIREMENT",
        )
        cal.return_table["inflation_linked_sovereign"] = {
            # 1pp wide -- deliberately BELOW ILS's own 2.0pp gate, so only
            # the scenario explicitly set below (real VTIP width) fires.
            s: ReturnRange(conservative=-3.0, upside=-2.0, confidence="HIGH")
            for s in "ABDEF"
        }
        cal.return_table["inflation_linked_sovereign"][scenario] = ReturnRange(
            conservative=conservative, upside=upside, confidence="HIGH"
        )
        return cal

    def test_3pp_range_fires_under_ils_gate_but_would_not_under_ihp_gate(self, cal):
        self._add_vtip(cal)  # 3pp wide -- below 6.0 (IHP), above 2.0 (ILS)
        results = evaluate_range_position_advisories(
            ["VTIP"], _probs(A=10, B=10, C=60, D=10, E=5, F=5), cal, {}
        )
        assert len(results) == 1
        adv = results[0]
        assert adv.role_id == "inflation_linked_sovereign"
        assert adv.range_width_pp == 3.0
        assert adv.scenario == "C"

    def test_below_ils_own_gate_is_still_skipped(self, cal):
        # 1.5pp wide -- below EVEN the narrower 2.0pp ILS gate
        self._add_vtip(cal, conservative=1.0, upside=2.5)
        results = evaluate_range_position_advisories(
            ["VTIP"], _probs(A=10, B=10, C=60, D=10, E=5, F=5), cal, {}
        )
        assert results == []

    def test_signal_direction_matches_ihp_sign_convention(self, cal):
        """Confirmed via real data (Calibration_State.md §3 2026-08-14) that
        VTIP uses the SAME real-yield-up/DXY-up = headwind convention as
        SGOL/SIVR, not an inverted one -- this locks that in."""
        self._add_vtip(cal)
        readings = {
            "REAL_YIELD_10Y_TREND": _trend_reading([1.0, 1.2, 1.4, 1.6, 1.8]),  # rising
            "DXY_TREND":            _trend_reading([95, 97, 99, 101, 103, 105, 107, 109]),  # appreciating
        }
        results = evaluate_range_position_advisories(
            ["VTIP"], _probs(A=10, B=10, C=60, D=10, E=5, F=5), cal, readings
        )
        assert results[0].signal == "unfavorable"

    def test_ihp_and_ils_evaluated_independently_in_same_call(self, cal):
        """SGOL (IHP, needs the widened B row) and VTIP (ILS, real 3pp C row)
        held simultaneously -- confirms per-role gating doesn't cross-talk."""
        _widen_b_range(cal)
        self._add_vtip(cal)
        results = evaluate_range_position_advisories(
            ["SGOL", "VTIP"], _probs(), cal, {}  # dominant scenario is B here
        )
        # Only SGOL/IHP fires -- VTIP's row lives in Scenario C, not B, and
        # B is dominant this call (see _probs() default), so ILS correctly
        # produces nothing this session -- same "one dominant scenario"
        # behavior GAP-16 always had, now proven to hold across two roles.
        assert len(results) == 1
        assert results[0].role_id == "inflation_hedge_precious_metals"

    def test_clean_signal_role_map_and_ev_adjustment_both_generalize(self, cal):
        """End-to-end: ILS's favorable/unfavorable signal survives into
        clean_signal_role_map() and apply_range_position_adjustment()
        actually applies it -- this is the exact bug this session found and
        fixed (apply_range_position_adjustment still gated on the OLD flat
        6.0pp constant even after evaluate_range_position_advisories() was
        generalized, which would have silently no-op'd VTIP's adjustment)."""
        self._add_vtip(cal)
        readings = {
            "REAL_YIELD_10Y_TREND": _trend_reading([1.0, 1.2, 1.4, 1.6, 1.8]),  # rising -> unfavorable
        }
        advisories = evaluate_range_position_advisories(
            ["VTIP"], _probs(A=10, B=10, C=60, D=10, E=5, F=5), cal, readings
        )
        signals = clean_signal_role_map(advisories)
        assert signals == {"inflation_linked_sovereign": "unfavorable"}

        range_ = cal.return_table["inflation_linked_sovereign"]["C"]
        adjusted = apply_range_position_adjustment(
            "inflation_linked_sovereign", "C", range_.conservative, range_, signals
        )
        # width=3pp, fraction=0.25 -> delta=0.75pp (below the 3pp cap)
        assert adjusted < range_.conservative
        assert abs(adjusted - (range_.conservative - 0.75)) < 0.001
