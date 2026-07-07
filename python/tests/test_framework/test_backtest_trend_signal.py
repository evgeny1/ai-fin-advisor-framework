"""
Tests for tools/backtest_trend_signal.py's pure date-handling helpers
(FRAMEWORK_BACKLOG ENG-50 backtest capability, 2026-07-07). The heavy
lifting (the actual signal formula) is analysis/trend_signal.py's own
already-tested evaluate_all_trend_signals() -- this file only covers the
two small helpers this script adds on top: ISO-week resampling with an
as-of cutoff, and the MLPX HY-OAS window truncation.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from backtest_trend_signal import _iso_week_resample_asof, _hy_oas_window  # noqa: E402


class TestIsoWeekResampleAsof:
    def test_filters_out_dates_after_as_of(self):
        pairs = [("2026-01-05", 1.0), ("2026-01-12", 2.0), ("2026-01-19", 3.0)]
        result = _iso_week_resample_asof(pairs, as_of_date="2026-01-12", weeks=8)
        assert result == [1.0, 2.0]  # 2026-01-19 excluded -- it's after as_of

    def test_caps_to_requested_weeks(self):
        pairs = [(f"2026-01-{d:02d}", float(d)) for d in range(1, 29, 7)]  # 4 distinct weeks
        result = _iso_week_resample_asof(pairs, as_of_date="2026-01-28", weeks=2)
        assert len(result) == 2

    def test_empty_input_returns_empty(self):
        assert _iso_week_resample_asof([], as_of_date="2026-01-01", weeks=8) == []


class TestHyOasWindow:
    def test_converts_percent_to_bps_int(self):
        pairs = [("2026-06-20", 2.80)]
        result = _hy_oas_window(pairs, as_of_date="2026-06-25")
        assert result == [("2026-06-20", 280)]

    def test_excludes_dates_outside_35_day_window(self):
        pairs = [("2026-01-01", 2.80), ("2026-06-20", 2.90)]
        result = _hy_oas_window(pairs, as_of_date="2026-06-25")
        dates = [d for d, _ in result]
        assert "2026-01-01" not in dates
        assert "2026-06-20" in dates

    def test_excludes_dates_after_as_of(self):
        pairs = [("2026-06-20", 2.80), ("2026-06-30", 2.90)]
        result = _hy_oas_window(pairs, as_of_date="2026-06-25")
        dates = [d for d, _ in result]
        assert "2026-06-30" not in dates
