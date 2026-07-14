"""
tests/test_stage3/test_trend.py — unit tests for analysis/trend.py.

Closes the test-coverage gap for FRAMEWORK_BACKLOG.md ENG-13's resolution:
these are pure-function tests with no CalibrationState/network dependency.
"""
from __future__ import annotations

import pytest

from advisor.analysis.trend import (
    all_weeks_meet,
    decline_from_high_pct,
    directional_trend,
    mean_reversion_mode,
    net_change_pct,
)


class TestNetChangePct:
    def test_simple_up(self):
        assert net_change_pct([100.0, 110.0]) == pytest.approx(10.0)

    def test_simple_down(self):
        assert net_change_pct([100.0, 90.0]) == pytest.approx(-10.0)

    def test_too_short_returns_none(self):
        assert net_change_pct([100.0]) is None
        assert net_change_pct([]) is None

    def test_zero_base_returns_none(self):
        assert net_change_pct([0.0, 50.0]) is None


class TestDirectionalTrend:
    def test_clean_uptrend_fires_up(self):
        closes = [100, 102, 104, 106, 108, 110]
        assert directional_trend(closes, threshold_pct=8.0) == "up"

    def test_clean_downtrend_fires_down(self):
        closes = [100, 98, 96, 94, 92, 90]
        assert directional_trend(closes, threshold_pct=8.0) == "down"

    def test_below_threshold_returns_none(self):
        closes = [100, 101, 102, 103]   # +3%, below an 8% threshold
        assert directional_trend(closes, threshold_pct=8.0) is None

    def test_default_ignores_path_only_net_change_matters(self):
        """ENG-65: the default (require_no_reversal=False) is plain
        time-series momentum -- sign of the net change over the window,
        gated by materiality. A real, material move that merely dipped
        below its own starting value partway through must still resolve,
        since the path taken doesn't change the net outcome. This is the
        exact 2026-07-13 live finding: a real-yield series and gold/silver's
        own price were both genuinely trending but got nulled by the old
        unconditional veto."""
        closes = [100, 95, 90, 95, 109]   # net +9%, dipped well below 100 along the way
        assert directional_trend(closes, threshold_pct=8.0) == "up"
        closes_down = [100, 105, 110, 105, 91]   # net -9%, popped well above 100 along the way
        assert directional_trend(closes_down, threshold_pct=8.0) == "down"

    def test_require_no_reversal_true_restores_dbmf_specific_veto(self):
        """FRAMEWORK_BACKLOG.md ENG-65: require_no_reversal=True is the
        explicit opt-in preserving Calibration_State.md 13's own DBMF text
        ("directional = net move >= 8% in one direction without full
        reversal"). Net move ends up +9% (clears threshold) but dipped
        well below the starting value along the way — with the flag set,
        this must NOT count as sustained. Only DBMF's own §13 breadth
        conditions (thesis.py, trend_signal.py's _dbmf_macro_confirms)
        should ever pass this flag."""
        closes = [100, 95, 90, 95, 109]
        assert directional_trend(closes, threshold_pct=8.0, require_no_reversal=True) is None

    def test_require_no_reversal_true_down_direction(self):
        closes = [100, 105, 110, 105, 91]
        assert directional_trend(closes, threshold_pct=8.0, require_no_reversal=True) is None

    def test_dip_that_never_crosses_start_still_counts_as_up(self):
        # Net +10%, and even though week 2 dips, it never goes BELOW
        # the starting value (100) — no full reversal either way, so this
        # is "up" whether or not require_no_reversal is set.
        closes = [100, 101, 100.5, 105, 110]
        assert directional_trend(closes, threshold_pct=8.0) == "up"
        assert directional_trend(closes, threshold_pct=8.0, require_no_reversal=True) == "up"

    def test_empty_or_single_point_returns_none(self):
        assert directional_trend([], threshold_pct=8.0) is None
        assert directional_trend([100.0], threshold_pct=8.0) is None


class TestAllWeeksMeet:
    def test_all_below_threshold_true(self):
        assert all_weeks_meet([60, 62, 64, 63], "<", 65.0) is True

    def test_one_week_breaks_it_false(self):
        assert all_weeks_meet([60, 66, 64, 63], "<", 65.0) is False

    def test_gte_comparator(self):
        assert all_weeks_meet([2.1, 2.2, 2.0], ">=", 2.0) is True
        assert all_weeks_meet([2.1, 1.9, 2.0], ">=", 2.0) is False

    def test_empty_returns_none(self):
        assert all_weeks_meet([], "<", 65.0) is None

    def test_invalid_comparator_raises(self):
        import pytest
        with pytest.raises(ValueError):
            all_weeks_meet([1.0], "==", 1.0)


class TestDeclineFromHighPct:
    def test_simple_decline(self):
        closes = [100, 110, 120, 100, 90]   # peak 120, last 90 -> 25% decline
        assert decline_from_high_pct(closes) == 25.0

    def test_at_high_is_zero(self):
        closes = [80, 90, 100]
        assert decline_from_high_pct(closes) == 0.0

    def test_empty_returns_none(self):
        assert decline_from_high_pct([]) is None


class TestMeanReversionMode:
    def test_oscillating_window_is_mean_reversion(self):
        closes = [100, 101, 99, 100, 99, 101, 100]
        assert mean_reversion_mode(closes, threshold_pct=8.0, trailing_weeks=4) is True

    def test_trending_window_is_not_mean_reversion(self):
        closes = [100, 102, 104, 108, 112, 116, 120]
        assert mean_reversion_mode(closes, threshold_pct=8.0, trailing_weeks=4) is False

    def test_insufficient_history_returns_none(self):
        assert mean_reversion_mode([100, 101], threshold_pct=8.0, trailing_weeks=4) is None

    def test_require_no_reversal_threaded_through(self):
        """FRAMEWORK_BACKLOG.md ENG-65: a net-trending-but-reversed-along-
        the-way window is NOT mean-reversion under the default (it's a real
        trend, per plain time-series momentum), but IS mean-reversion under
        require_no_reversal=True (DBMF's own §13 failure condition), since
        that stricter definition doesn't recognize the net move as trending
        at all."""
        closes = [100, 95, 90, 95, 109]
        assert mean_reversion_mode(closes, threshold_pct=8.0) is False
        assert mean_reversion_mode(closes, threshold_pct=8.0, require_no_reversal=True) is True
