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

    def test_full_reversal_through_start_returns_none(self):
        # Net move ends up +9% (clears threshold) but dipped well below
        # the starting value along the way — DBMF's own text requires
        # "without full reversal", so this must NOT count as sustained.
        closes = [100, 95, 90, 95, 109]
        assert directional_trend(closes, threshold_pct=8.0) is None

    def test_down_full_reversal_through_start_returns_none(self):
        closes = [100, 105, 110, 105, 91]
        assert directional_trend(closes, threshold_pct=8.0) is None

    def test_dip_that_never_crosses_start_still_counts_as_up(self):
        # Net +10%, and even though week 2 dips, it never goes BELOW
        # the starting value (100) — no full reversal.
        closes = [100, 101, 100.5, 105, 110]
        assert directional_trend(closes, threshold_pct=8.0) == "up"

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
