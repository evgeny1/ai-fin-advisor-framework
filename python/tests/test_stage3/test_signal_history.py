"""
tests/test_stage3/test_signal_history.py — ENG-26/31/66

Pure-function tests for analysis/signal_history.py: consecutive-period
streak logic shared by MAGS (session-granularity), COPX (month-granularity),
and AIPO (quarter-granularity). No I/O — matches this package's own
"no file I/O" test philosophy; data/signal_history_store.py is tested
separately (tests/test_stage1/test_signal_history_store.py).
"""
from __future__ import annotations

from advisor.analysis.signal_history import (
    consecutive_calendar_streak,
    consecutive_session_streak,
    next_month_period,
    next_quarter_period,
)


class TestNextMonthPeriod:
    def test_normal_increment(self):
        assert next_month_period("2026-07") == "2026-08"

    def test_year_rollover(self):
        assert next_month_period("2026-12") == "2027-01"


class TestNextQuarterPeriod:
    def test_normal_increment(self):
        assert next_quarter_period("2026-Q3") == "2026-Q4"

    def test_year_rollover(self):
        assert next_quarter_period("2026-Q4") == "2027-Q1"


class TestConsecutiveSessionStreak:
    """MAGS-style: last N RECORDED entries, no calendar gap logic —
    each entry IS one session by construction."""

    def test_none_when_not_enough_history(self):
        history = [{"period": "2026-07-13", "value": "MODERATE"}]
        result = consecutive_session_streak(history, lambda v: v == "MODERATE", min_count=2)
        assert result is None

    def test_true_when_last_two_both_match(self):
        history = [
            {"period": "2026-07-08", "value": "HIGH"},
            {"period": "2026-07-13", "value": "MODERATE"},
            {"period": "2026-07-14", "value": "MODERATE"},
        ]
        result = consecutive_session_streak(history, lambda v: v == "MODERATE", min_count=2)
        assert result is True

    def test_false_when_most_recent_breaks_the_streak(self):
        history = [
            {"period": "2026-07-13", "value": "MODERATE"},
            {"period": "2026-07-14", "value": "HIGH"},
        ]
        result = consecutive_session_streak(history, lambda v: v == "MODERATE", min_count=2)
        assert result is False

    def test_only_looks_at_the_tail_not_the_whole_history(self):
        """An older MODERATE streak further back must not count if the
        most recent entries broke it."""
        history = [
            {"period": "2026-07-01", "value": "MODERATE"},
            {"period": "2026-07-02", "value": "MODERATE"},
            {"period": "2026-07-13", "value": "HIGH"},
            {"period": "2026-07-14", "value": "HIGH"},
        ]
        result = consecutive_session_streak(history, lambda v: v == "MODERATE", min_count=2)
        assert result is False


class TestConsecutiveCalendarStreak:
    """COPX/AIPO-style: the last N DISTINCT periods must both satisfy the
    predicate AND be genuinely back-to-back per step() — a skipped period
    means the streak's continuity can't be confirmed."""

    def test_none_when_not_enough_history(self):
        history = [{"period": "2026-06", "value": True}]
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_month_period,
        )
        assert result is None

    def test_true_when_two_consecutive_months_both_match(self):
        history = [
            {"period": "2026-05", "value": False},
            {"period": "2026-06", "value": True},
            {"period": "2026-07", "value": True},
        ]
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_month_period,
        )
        assert result is True

    def test_false_when_most_recent_month_breaks_it(self):
        history = [
            {"period": "2026-06", "value": True},
            {"period": "2026-07", "value": False},
        ]
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_month_period,
        )
        assert result is False

    def test_none_when_a_month_was_skipped(self):
        """June and August both True, but July has no reading — the gap
        means continuity can't be confirmed, so this must NOT return True
        just because the two most recent RECORDED entries both match."""
        history = [
            {"period": "2026-06", "value": True},
            {"period": "2026-08", "value": True},  # July skipped
        ]
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_month_period,
        )
        assert result is None

    def test_quarter_granularity_works_the_same_way(self):
        history = [
            {"period": "2026-Q2", "value": True},
            {"period": "2026-Q3", "value": True},
        ]
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_quarter_period,
        )
        assert result is True

    def test_quarter_gap_is_none(self):
        history = [
            {"period": "2026-Q1", "value": True},
            {"period": "2026-Q3", "value": True},  # Q2 skipped
        ]
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_quarter_period,
        )
        assert result is None
