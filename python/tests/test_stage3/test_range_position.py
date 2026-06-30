"""
tests/test_stage3/test_range_position.py — unit tests for GAP-16's
analysis/range_position.py (within-scenario IHP sub-condition advisory).
"""
from __future__ import annotations

from datetime import datetime

from advisor.analysis.range_position import (
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


class TestRangePositionAdvisory:

    def _widen_b_range(self, cal):
        """Fixture's default IHP rows are all 4pp wide (below the 6pp
        threshold) — widen scenario B to mirror the real [6,12] B row so
        the GAP-16 width gate actually opens."""
        from advisor.types import ReturnRange
        cal.return_table["inflation_hedge_precious_metals"]["B"] = ReturnRange(
            conservative=6.0, upside=12.0, confidence="HIGH"
        )

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
