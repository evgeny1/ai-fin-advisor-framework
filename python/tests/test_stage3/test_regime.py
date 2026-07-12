"""
tests/test_stage3/test_regime.py — M14 compute_divergence_signal() unit tests.

Coverage focus: ENG-20 — conflict_duration_days / energy_180d extended-conflict
fallback. No file I/O, no network; all readings built inline via conftest helpers.
"""
from __future__ import annotations

import dataclasses

import pytest

from advisor.analysis.regime import compute_divergence_signal, role_repricing_divergence
from advisor.types import DivergenceLevel, DivergenceSignal
from .conftest import make_history_reading, make_reading


def _cal_with_role_repricing_thresholds(cal, thresholds):
    """cal fixture's RegimeBlock has no §9.5 thresholds set (empty dict default)
    -- override just that field via dataclasses.replace rather than editing the
    shared fixture, so other tests' RegimeBlock stays untouched."""
    new_regime = dataclasses.replace(cal.regime, role_repricing_thresholds=thresholds)
    return dataclasses.replace(cal, regime=new_regime)


def _brent_history(window_180_base: float, window_90_base: float, current: float) -> list:
    """
    Build a 200-point oldest-first Brent history where only the two anchor
    points compute_pct_change() actually reads are meaningful:
      history[-1]    = current
      history[-91]   = window_90_base   (90-calendar-day anchor)
      history[-181]  = window_180_base  (180-calendar-day anchor)
    All other points are filler (current) — irrelevant to compute_pct_change.
    """
    hist = [current] * 200
    hist[200 - 91]  = window_90_base
    hist[200 - 181] = window_180_base
    hist[-1] = current
    return hist


class TestNoConflictDuration:
    """conflict_duration_days omitted (default None) -> behavior unchanged from pre-ENG-20."""

    def test_energy_180d_change_is_none_by_default(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal)
        assert sig.energy_90d_change is not None
        assert sig.energy_180d_change is None
        # 90d change alone (5%) is below both thresholds -> NONE
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE

    def test_no_180d_flag_emitted(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {"BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0)}
        sig = compute_divergence_signal(readings, cal)
        assert not any("Conflict > 90d" in f for f in sig.quality_flags)


class TestConflictUnder90Days:
    """conflict_duration_days <= 90 -> no 180d fallback triggered."""

    def test_short_conflict_does_not_trigger_180d(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=45)
        assert sig.energy_180d_change is None
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE


class TestConflictOver90DaysWithSufficientHistory:
    """
    conflict_duration_days > 90 + 181+ points of history -> energy_180d computed
    and the HIGHER of (90d, 180d) drives classification (M14 EXTENDED CONFLICT CAVEAT).
    """

    def test_180d_overrides_understated_90d_signal(self, cal):
        # 90d change: (105-100)/100 = 5% -> below MOD (10%) threshold alone.
        # 180d change: (105-80)/80 = 31.25% -> above HIGH (15%) threshold.
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),         # vix_change = -5 <= HIGH thresh (0)
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_90d_change is not None and sig.energy_90d_change < 0.10
        assert sig.energy_180d_change is not None
        assert sig.energy_180d_change > sig.energy_90d_change
        # Classification driven by the higher (180d) reading -> HIGH, not NONE.
        assert sig.commodity_fear_divergence == DivergenceLevel.HIGH

    def test_both_readings_reported_and_flag_emitted(self, cal):
        hist = _brent_history(window_180_base=80.0, window_90_base=100.0, current=105.0)
        readings = {"BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0)}
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_90d_change is not None
        assert sig.energy_180d_change is not None
        assert any("Conflict > 90d" in f and "180d" in f for f in sig.quality_flags)

    def test_90d_reading_unaffected_when_180d_lower(self, cal):
        """If 180d change is LOWER than 90d, the 90d (already-higher) value still governs."""
        # 90d: (105-90)/90 = 16.7% -> already above HIGH (15%) alone.
        # 180d: (105-100)/100 = 5% -> lower than 90d.
        hist = _brent_history(window_180_base=100.0, window_90_base=90.0, current=105.0)
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_90d_change > sig.energy_180d_change
        assert sig.commodity_fear_divergence == DivergenceLevel.HIGH


class TestConflictOver90DaysInsufficientHistory:
    """conflict_duration_days > 90 but < 181 points of Brent history -> graceful flag, no crash."""

    def test_insufficient_history_flags_and_falls_back_to_90d(self, cal):
        # Only 120 points -> 90d window satisfiable (needs 91), 180d window is not (needs 181).
        hist = [100.0] * 119 + [105.0]
        readings = {
            "BRENT_CRUDE": make_history_reading("BRENT_CRUDE", hist, 105.0),
            "VIX":         make_reading("VIX", 15.0),
            "VIX_90D_AVG": make_reading("VIX_90D_AVG", 20.0),
        }
        sig = compute_divergence_signal(readings, cal, conflict_duration_days=120)
        assert sig.energy_180d_change is None
        assert sig.energy_90d_change is not None
        assert any("insufficient BRENT_CRUDE history" in f for f in sig.quality_flags)
        # Falls back to 90d-only classification (5% -> below MOD threshold -> NONE).
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE


class TestReturnType:

    def test_returns_divergence_signal(self, cal):
        sig = compute_divergence_signal({}, cal)
        assert isinstance(sig, DivergenceSignal)

    def test_empty_readings_no_exception(self, cal):
        sig = compute_divergence_signal({}, cal, conflict_duration_days=150)
        assert sig.energy_90d_change is None
        assert sig.energy_180d_change is None
        assert sig.commodity_fear_divergence == DivergenceLevel.NONE


class TestBroadEquityTrailingKeyExtraction:
    """
    Regression coverage for the RoleRepricingDivergence "always skipped" bug
    (2026-07-12 session fix): fetch_broad_equity_trailing() in both
    fmp_fetcher.py and yfinance_fetcher.py produces
    value={"return_30d_pct": X, "return_90d_pct": Y, "current": Z} — a
    percentage number, e.g. 2.56 == 2.56%. compute_divergence_signal() was
    only checking for "change_30d"/"pct_30d"/"pct_change_30d", none of which
    any fetcher has ever produced, so broad_equity_30d silently fell through
    to a history-based fallback that also can't succeed for this reading
    shape (no attached series) — broad_equity_30d was always None in
    production, and RoleRepricingDivergence (mcp_server.py) always skipped
    as a result. This is exactly the "write real fetcher shape, assert real
    parsed value" case the round-trip-testing rule (README §8) exists for —
    a hand-written fixture using the guessed key names would have kept
    passing right through this bug.
    """

    def test_return_30d_pct_key_is_recognized_and_converted_to_fraction(self, cal):
        reading = make_reading(
            "BROAD_EQUITY_TRAILING",
            {"return_30d_pct": 2.56, "return_90d_pct": 11.0, "current": 7575.39},
        )
        sig = compute_divergence_signal({"BROAD_EQUITY_TRAILING": reading}, cal)
        assert sig.broad_equity_30d == pytest.approx(0.0256)

    def test_negative_return_30d_pct(self, cal):
        reading = make_reading(
            "BROAD_EQUITY_TRAILING",
            {"return_30d_pct": -5.0, "return_90d_pct": -8.0, "current": 7000.0},
        )
        sig = compute_divergence_signal({"BROAD_EQUITY_TRAILING": reading}, cal)
        assert sig.broad_equity_30d == pytest.approx(-0.05)

    def test_missing_broad_equity_trailing_still_flags_gracefully(self, cal):
        sig = compute_divergence_signal({}, cal)
        assert sig.broad_equity_30d is None
        assert any("BROAD_EQUITY_TRAILING: unavailable" in f for f in sig.quality_flags)

    def test_feeds_equity_scenario_divergence_when_directive_reductive(self, cal):
        """End-to-end: a real-shaped reading should actually drive classification,
        not just populate the field and stop there."""
        reading = make_reading(
            "BROAD_EQUITY_TRAILING",
            {"return_30d_pct": 6.0, "return_90d_pct": 10.0, "current": 7600.0},
        )
        sig = compute_divergence_signal(
            {"BROAD_EQUITY_TRAILING": reading},
            cal,
            equity_directive_for_dominant_scenario="REDUCE",
        )
        # 6% >= equity_div_HIGH_pct (5.0) -> HIGH
        assert sig.equity_scenario_divergence == DivergenceLevel.HIGH


class TestRoleRepricingDivergence:
    """
    role_repricing_divergence() (§9.5) had zero test coverage before this
    session's fix — added alongside the compute_divergence_signal() fix
    since both feed the same previously-always-skipped briefing section.
    Threshold values (10/15/20pp) mirror Calibration_State.md §9.5 as of
    v1.64. SGOL's case below uses the exact real figures from the 2026-07-12
    session (broad market +2.56%, SGOL -8.87%) that motivated this fix —
    confirms the corrected broad_equity_30d extraction does NOT, by itself,
    produce a warning here: 11.43pp underperformance is genuinely below
    SGOL's calibrated 15pp threshold. The fix corrects a real bug; it does
    not retroactively make this specific session's SGOL move cross the bar.
    """

    def test_underperformance_at_or_above_threshold_fires(self, cal):
        cal2 = _cal_with_role_repricing_thresholds(
            cal, {"inflation_hedge_precious_metals": 15.0}
        )
        # broad +2.56%, SGOL -22.55% (SIVR's actual 2026-07-12 figure, reused
        # here on SGOL's entry to isolate the threshold-boundary logic from
        # instrument identity) -> underperformance 25.11pp >= 15pp -> fires.
        warnings = role_repricing_divergence(
            holdings_30d_returns={"SGOL": -0.2255},
            broad_market_30d=0.0256,
            cal=cal2,
        )
        assert len(warnings) == 1
        w = warnings[0]
        assert w.ticker == "SGOL"
        assert w.primary_role_id == "inflation_hedge_precious_metals"
        assert w.underperformance_pp == pytest.approx(25.11, abs=0.01)
        assert w.threshold_pp == 15.0

    def test_real_sgol_figures_do_not_cross_threshold(self, cal):
        """The actual 2026-07-12 SGOL numbers: real decline, but below threshold."""
        cal2 = _cal_with_role_repricing_thresholds(
            cal, {"inflation_hedge_precious_metals": 15.0}
        )
        warnings = role_repricing_divergence(
            holdings_30d_returns={"SGOL": -0.0887},
            broad_market_30d=0.0256,
            cal=cal2,
        )
        assert warnings == []

    def test_role_with_no_threshold_defined_never_fires(self, cal):
        """DBMF's role (systematic_trend_following) has no §9.5 entry at all."""
        cal2 = _cal_with_role_repricing_thresholds(
            cal, {"inflation_hedge_precious_metals": 15.0}
        )
        warnings = role_repricing_divergence(
            holdings_30d_returns={"DBMF": -0.50},  # extreme decline, still no signal
            broad_market_30d=0.0256,
            cal=cal2,
        )
        assert warnings == []

    def test_broad_market_30d_none_returns_empty(self, cal):
        cal2 = _cal_with_role_repricing_thresholds(
            cal, {"inflation_hedge_precious_metals": 15.0}
        )
        warnings = role_repricing_divergence(
            holdings_30d_returns={"SGOL": -0.30},
            broad_market_30d=None,
            cal=cal2,
        )
        assert warnings == []

    def test_no_thresholds_configured_returns_empty(self, cal):
        """Default cal fixture has an empty role_repricing_thresholds dict."""
        warnings = role_repricing_divergence(
            holdings_30d_returns={"SGOL": -0.30},
            broad_market_30d=0.0256,
            cal=cal,
        )
        assert warnings == []

    def test_none_instrument_return_skipped_not_crashed(self, cal):
        cal2 = _cal_with_role_repricing_thresholds(
            cal, {"inflation_hedge_precious_metals": 15.0}
        )
        warnings = role_repricing_divergence(
            holdings_30d_returns={"SGOL": None},
            broad_market_30d=0.0256,
            cal=cal2,
        )
        assert warnings == []
