"""
Tests for ENG-47: session.py's yield-curve summary/briefing lines crashed
(TypeError: unsupported format string passed to NoneType.__format__) when
YieldCurveSignal.spread_10y_2y (or spread_10y_3m) is None -- a real,
recurring condition whenever the underlying FRED fetch (DGS10) hits a
transient timeout, not an edge case worth ignoring. Fixed via a small
_fmt_bps() helper that degrades to "n/a" instead of crashing the f-string.
"""
from __future__ import annotations

import pytest

from advisor.orchestrator.session import SessionPipeline, _fmt_bps
from advisor.orchestrator.context import SessionContext
from advisor.types import (
    SessionType, YieldCurveSignal, DTimingSignal, EWatchFlag, EPathwayType,
)


class TestFmtBps:
    def test_none_returns_na(self):
        assert _fmt_bps(None) == "n/a"

    def test_formats_positive_value(self):
        assert _fmt_bps(123.456) == "123bps"

    def test_formats_negative_value(self):
        assert _fmt_bps(-45.6) == "-46bps"

    def test_formats_zero(self):
        assert _fmt_bps(0.0) == "0bps"


def _yield_curve_signal(spread_10y_2y=None, spread_10y_3m=None):
    return YieldCurveSignal(
        spread_10y_2y=spread_10y_2y,
        spread_10y_3m=spread_10y_3m,
        curve_state=None,
        d_timing_signal=DTimingSignal.MONITORING,
        d_timing_estimate=None,
        term_premium=None,
        e_watch_flag=EWatchFlag.CLEAR,
        yield_30y=None,
        e_pathway_type=EPathwayType.SYSTEMIC_LIQUIDITY,
        quality_flags=[],
    )


class TestRenderBriefingContextWithNoneSpreads:
    """_render_briefing_context() (used to build AI Call 3's input) must not
    crash when the yield-curve spreads are None -- exactly what a
    transient FRED DGS10 timeout produces (confirmed live, ENG-47)."""

    def _minimal_ctx(self, yc):
        return SessionContext(
            session_type=SessionType.FULL_DESKTOP,
            session_date="2026-07-03",
            dry_run=True,
            yield_curve_signal=yc,
        )

    def test_both_spreads_none_does_not_raise(self):
        pipeline = SessionPipeline(dry_run=True)
        ctx = self._minimal_ctx(_yield_curve_signal(spread_10y_2y=None, spread_10y_3m=None))
        result = pipeline._render_briefing_context(ctx)
        assert "YIELD CURVE" in result
        assert "10Y-2Y=n/a" in result
        assert "10Y-3M=n/a" in result

    def test_one_spread_none_other_present(self):
        pipeline = SessionPipeline(dry_run=True)
        ctx = self._minimal_ctx(_yield_curve_signal(spread_10y_2y=-42.0, spread_10y_3m=None))
        result = pipeline._render_briefing_context(ctx)
        assert "10Y-2Y=-42bps" in result
        assert "10Y-3M=n/a" in result

    def test_both_spreads_present_unchanged_behavior(self):
        """Regression guard: the fix must not alter output when data IS
        available -- still plain "Nbps", not "n/a"."""
        pipeline = SessionPipeline(dry_run=True)
        ctx = self._minimal_ctx(_yield_curve_signal(spread_10y_2y=35.0, spread_10y_3m=-10.0))
        result = pipeline._render_briefing_context(ctx)
        assert "10Y-2Y=35bps" in result
        assert "10Y-3M=-10bps" in result
        assert "n/a" not in result
