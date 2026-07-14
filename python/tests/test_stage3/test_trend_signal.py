"""
Tests for analysis/trend_signal.py (FRAMEWORK_BACKLOG ENG-50/ENG-55) --
deterministic trend/rotation signal layer. All functions here are pure
(List[float] in, no I/O) per this codebase's own convention for
analysis/ modules.
"""
from __future__ import annotations

import pytest

from advisor.analysis import trend_signal as m
from advisor.types import ComparatorMode, TrendSignalCode


def _linear(start: float, end: float, n: int) -> list:
    """n points, linearly spaced from start to end inclusive."""
    if n == 1:
        return [start]
    step = (end - start) / (n - 1)
    return [start + step * i for i in range(n)]


# ── _window_pct_change ─────────────────────────────────────────────────────

class TestWindowPctChange:
    def test_computes_pct_change_over_trailing_window(self):
        closes = _linear(100, 122, 22)  # 22 points -> window_days=21 uses all of them
        result = m._window_pct_change(closes, 21)
        assert result == pytest.approx(22.0)

    def test_none_when_insufficient_history(self):
        assert m._window_pct_change([100.0, 101.0], 21) is None


# ── _weighted_composite_closes ─────────────────────────────────────────────

class TestWeightedCompositeCloses:
    def test_blends_two_symbols_by_weight(self):
        histories = {"A": [100.0, 110.0], "B": [200.0, 220.0]}
        result = m._weighted_composite_closes(histories, ["A", "B"], [0.5, 0.5])
        assert result == [150.0, 165.0]

    def test_none_when_any_symbol_missing(self):
        histories = {"A": [100.0, 110.0]}
        assert m._weighted_composite_closes(histories, ["A", "B"], [0.5, 0.5]) is None

    def test_none_when_symbol_history_empty(self):
        histories = {"A": [100.0, 110.0], "B": []}
        assert m._weighted_composite_closes(histories, ["A", "B"], [0.5, 0.5]) is None


# ── _agreement_gate ─────────────────────────────────────────────────────────

class TestAgreementGate:
    def test_true_when_both_trend_same_direction(self):
        up_a = _linear(100, 120, 8)
        up_b = _linear(50, 58, 8)
        confirms, data_available = m._agreement_gate(up_a, up_b)
        assert confirms is True
        assert data_available is True

    def test_false_when_directions_disagree(self):
        up = _linear(100, 120, 8)
        down = _linear(100, 80, 8)
        confirms, data_available = m._agreement_gate(up, down)
        assert confirms is False
        assert data_available is True

    def test_data_unavailable_when_either_series_missing(self):
        up = _linear(100, 120, 8)
        confirms, data_available = m._agreement_gate(up, None)
        assert confirms is None
        assert data_available is False
        confirms, data_available = m._agreement_gate(None, up)
        assert confirms is None
        assert data_available is False

    def test_data_available_but_indeterminate_when_direction_flat(self):
        """ENG-63: a genuinely flat/choppy series is a computed result on
        present data, not a missing input — data_available stays True."""
        up = _linear(100, 120, 8)
        flat = [100.0, 100.5, 99.8, 100.2, 100.1, 99.9, 100.3, 100.0]
        confirms, data_available = m._agreement_gate(up, flat)
        assert confirms is None
        assert data_available is True

    def test_confirms_true_on_2026_07_13_real_yield_scenario_after_eng65_fix(self):
        """ENG-65 regression: this is the exact live scenario from
        2026-07-13. Before ENG-65, directional_trend()'s unconditional
        reversal veto nulled the real-yield leg (a materially strong +7.4%
        net move that merely dipped below its own starting value in week
        2), forcing this gate to report confirms=None even though both
        legs were genuinely, materially trending. _agreement_gate uses the
        default (require_no_reversal=False, plain time-series momentum),
        so both legs now correctly resolve and agree."""
        real_yield = [2.16, 2.07, 2.19, 2.17, 2.21, 2.18, 2.26, 2.32]
        dxy = [98.91, 100.07, 99.75, 100.85, 101.36, 100.86, 100.97, 101.27]
        confirms, data_available = m._agreement_gate(real_yield, dxy)
        assert confirms is True
        assert data_available is True


# ── evaluate_return_spread (Mode 1) ─────────────────────────────────────────

class TestEvaluateReturnSpread:
    def test_strengthening_when_instrument_outperforms_flat_comparator(self):
        instrument = _linear(100, 112.6, 64)
        comparator = [100.0] * 64
        code, d1, d2, flags = m.evaluate_return_spread("XAR", instrument, comparator)
        assert code == TrendSignalCode.STRENGTHENING
        assert flags == []

    def test_weakening_when_instrument_underperforms_flat_comparator(self):
        instrument = _linear(112.6, 100, 64)
        comparator = [100.0] * 64
        code, d1, d2, flags = m.evaluate_return_spread("XAR", instrument, comparator)
        assert code == TrendSignalCode.WEAKENING

    def test_inconclusive_when_short_and_medium_windows_disagree_in_sign(self):
        # Net decline over the full 64-day window, but the trailing 21 days
        # show a rebound of the opposite sign -- short/medium sign mismatch.
        # ENG-60 discovery: this fixture was previously 43+20=63 points --
        # one short of the 64 evaluate_return_spread's MEDIUM_WINDOW_DAYS=63
        # actually needs (len >= window_days+1). It was silently landing in
        # the insufficient-history branch instead of the intended "windows
        # computed and disagree" path -- invisible before ENG-60 because
        # both branches returned INCONCLUSIVE. Fixed to 44+20=64 points so
        # this test actually exercises what its name and comment describe.
        instrument = _linear(150, 90, 44) + _linear(90, 100, 21)[1:]
        comparator = [100.0] * 64
        code, d1, d2, flags = m.evaluate_return_spread("XAR", instrument, comparator)
        assert code == TrendSignalCode.INCONCLUSIVE
        assert flags == []  # a real computation ran -- no missing-input flag

    def test_inconclusive_when_spread_below_noise_floor(self):
        instrument = _linear(100, 100.5, 64)  # ~0.5% move, below NOISE_FLOOR_PCT
        comparator = [100.0] * 64
        code, d1, d2, flags = m.evaluate_return_spread("MAGS", instrument, comparator)
        assert code == TrendSignalCode.INCONCLUSIVE

    def test_data_unavailable_with_flag_on_insufficient_history(self):
        """ENG-60: missing input (not enough history to even compute a
        spread) is DATA_UNAVAILABLE, distinct from a computed INCONCLUSIVE."""
        code, d1, d2, flags = m.evaluate_return_spread("MAGS", [100.0, 101.0], [100.0, 100.5])
        assert code == TrendSignalCode.DATA_UNAVAILABLE
        assert any("insufficient history" in f for f in flags)


# ── evaluate_own_trend_confirmed (Mode 2) ───────────────────────────────────

class TestEvaluateOwnTrendConfirmed:
    def test_strengthening_when_own_trend_up_and_confirmed(self):
        instrument = _linear(100, 130, 64)
        code, d1, d2, flags = m.evaluate_own_trend_confirmed("DBMF", instrument, macro_confirms=True)
        assert code == TrendSignalCode.STRENGTHENING
        assert d1 == "up" and d2 == "up"

    def test_inconclusive_when_not_confirmed_even_if_own_trend_matches(self):
        instrument = _linear(100, 130, 64)
        code, d1, d2, flags = m.evaluate_own_trend_confirmed("DBMF", instrument, macro_confirms=False)
        assert code == TrendSignalCode.INCONCLUSIVE

    def test_data_unavailable_with_flag_when_confirmation_input_unavailable(self):
        """ENG-60: macro_confirms is None with confirm_data_available at its
        default (False) means the confirmation gate's own inputs were
        missing — DATA_UNAVAILABLE, even though own_short/own_medium
        (returned here) both agree ("up"). Distinct from a real disconfirm
        (macro_confirms=False, covered below) which is a genuine INCONCLUSIVE,
        and from the ENG-63 case below where the gate DID run on real data."""
        instrument = _linear(100, 130, 64)
        code, d1, d2, flags = m.evaluate_own_trend_confirmed("SGOL", instrument, macro_confirms=None)
        assert code == TrendSignalCode.DATA_UNAVAILABLE
        assert d1 == "up" and d2 == "up"  # still populated for display
        assert any("confirmation input unavailable" in f for f in flags)

    def test_inconclusive_when_confirmation_gate_computed_but_no_agreement(self):
        """ENG-63: macro_confirms is None but confirm_data_available=True —
        the gate ran on real, present data and genuinely found no agreeing
        direction. This must be INCONCLUSIVE, not DATA_UNAVAILABLE — the
        exact distinction that was missing for SGOL/SIVR on 2026-07-13."""
        instrument = _linear(100, 130, 64)
        code, d1, d2, flags = m.evaluate_own_trend_confirmed(
            "SGOL", instrument, macro_confirms=None, confirm_data_available=True
        )
        assert code == TrendSignalCode.INCONCLUSIVE
        assert d1 == "up" and d2 == "up"
        assert any("no clear agreement" in f for f in flags)

    def test_data_unavailable_on_insufficient_history(self):
        """ENG-60: no own-price basis at all — DATA_UNAVAILABLE."""
        code, d1, d2, flags = m.evaluate_own_trend_confirmed("SGOL", [100.0, 101.0], macro_confirms=True)
        assert code == TrendSignalCode.DATA_UNAVAILABLE
        assert any("insufficient own-price history" in f for f in flags)


# ── DBMF breadth confirmation ────────────────────────────────────────────────

class TestDbmfMacroConfirms:
    def test_confirms_when_dxy_agrees_and_breadth_at_least_3_of_4(self):
        trending = _linear(100, 120, 8)
        breadth = {"BRENT_TREND": trending, "GOLD_TREND": trending, "SP500_TREND": trending}
        confirms, flags, data_available = m._dbmf_macro_confirms(
            "up", True, breadth, dxy_closes=trending
        )
        assert confirms is True
        assert data_available is True

    def test_does_not_confirm_when_breadth_below_threshold(self):
        trending = _linear(100, 120, 8)
        flat = [100.0, 100.1, 99.9, 100.2, 100.0, 99.8, 100.1, 100.0]
        breadth = {"BRENT_TREND": trending, "GOLD_TREND": flat, "SP500_TREND": flat}
        confirms, flags, data_available = m._dbmf_macro_confirms(
            "up", True, breadth, dxy_closes=trending
        )
        assert confirms is False
        assert data_available is True
        assert any("below the 3/4" in f for f in flags)

    def test_data_unavailable_when_dxy_missing(self):
        confirms, flags, data_available = m._dbmf_macro_confirms("up", True, {}, dxy_closes=None)
        assert confirms is None
        assert data_available is False

    def test_data_unavailable_when_own_short_history_insufficient(self):
        """ENG-63: own_short_data_available=False is the genuine data gap
        (not enough own-price history to even attempt a short-window read)."""
        confirms, flags, data_available = m._dbmf_macro_confirms(
            None, False, {}, dxy_closes=_linear(100, 120, 8)
        )
        assert confirms is None
        assert data_available is False

    def test_inconclusive_basis_when_own_short_indeterminate_on_present_data(self):
        """ENG-63: own price history WAS long enough (own_short_data_available
        =True) but its own directional_trend came back None (e.g. a sub-
        threshold move, exactly DBMF's 2026-07-13 case: +0.57% over 21 days,
        below the 2% floor) — a computed result, not a missing input."""
        confirms, flags, data_available = m._dbmf_macro_confirms(
            None, True, {}, dxy_closes=_linear(100, 120, 8)
        )
        assert confirms is None
        assert data_available is True

    def test_inconclusive_basis_when_dxy_direction_indeterminate(self):
        """ENG-63: DXY_TREND itself was present but its own directional_trend
        came back None — also a computed result, not a missing input."""
        flat_dxy = [100.0, 100.1, 99.9, 100.2, 100.0, 99.8, 100.1, 100.0]
        confirms, flags, data_available = m._dbmf_macro_confirms(
            "up", True, {}, dxy_closes=flat_dxy
        )
        assert confirms is None
        assert data_available is True
        assert any("DXY_TREND direction indeterminate" in f for f in flags)

    def test_dxy_breadth_check_keeps_no_reversal_veto_internally(self):
        """ENG-65: this breadth check is the explicit reuse of
        Calibration_State.md 13's own DBMF sustaining-condition concept, so
        it keeps require_no_reversal=True internally even though the
        general-purpose directional_trend() default no longer vetoes on a
        reversal. A DXY series with a real net move that dipped through its
        own starting value must still read as indeterminate here."""
        dxy_with_early_dip = [100, 95, 90, 95, 96, 98, 100, 109]  # net +9%, dipped below 100
        confirms, flags, data_available = m._dbmf_macro_confirms(
            "up", True, {}, dxy_closes=dxy_with_early_dip
        )
        assert confirms is None
        assert data_available is True
        assert any("DXY_TREND direction indeterminate" in f for f in flags)


# ── MLPX HY OAS confirmation ─────────────────────────────────────────────────

class TestMlpxHyOasConfirms:
    def test_confirms_on_tightening(self):
        confirms, flags = m._mlpx_hy_oas_confirms([("2026-06-10", 320), ("2026-07-10", 290)])
        assert confirms is True
        assert any("v1 simplification" in f for f in flags)

    def test_does_not_confirm_on_widening(self):
        confirms, flags = m._mlpx_hy_oas_confirms([("2026-06-10", 290), ("2026-07-10", 320)])
        assert confirms is False

    def test_none_on_insufficient_history(self):
        confirms, flags = m._mlpx_hy_oas_confirms([("2026-07-10", 290)])
        assert confirms is None

    def test_none_values_filtered_out(self):
        confirms, flags = m._mlpx_hy_oas_confirms(
            [("2026-06-01", None), ("2026-06-10", 320), ("2026-07-10", 290)]
        )
        assert confirms is True


# ── evaluate_all_trend_signals (wiring) ─────────────────────────────────────

class TestEvaluateAllTrendSignals:
    def test_return_spread_ticker_wired_end_to_end(self):
        histories = {
            "MAGS": _linear(100, 112.6, 64),
            "QQQM": [100.0] * 64,
        }
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MAGS"],
            daily_histories=histories,
            weekly_trend_readings={},
            hy_oas_session_history=[],
            dominant_directives={"MAGS": "HOLD"},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.STRENGTHENING
        assert signals[0].dominant_directive_conflict_aware == "HOLD"
        assert signals[0].margin_debt_fragility_flag is None  # not STRENGTHENING-gated w/o a flag supplied

    def test_margin_debt_flag_attached_only_when_strengthening(self):
        histories = {"MAGS": _linear(100, 112.6, 64), "QQQM": [100.0] * 64}
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MAGS"], daily_histories=histories,
            weekly_trend_readings={}, hy_oas_session_history={},
            dominant_directives={}, margin_debt_fragility_flag="ELEVATED",
        )
        assert signals[0].margin_debt_fragility_flag == "ELEVATED"

    def test_missing_own_history_produces_data_unavailable_reading_not_a_crash(self):
        """ENG-60: no own-price data at all is DATA_UNAVAILABLE, not INCONCLUSIVE."""
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MAGS"], daily_histories={},
            weekly_trend_readings={}, hy_oas_session_history=[],
            dominant_directives={},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.DATA_UNAVAILABLE
        assert signals[0].price_at_signal is None
        assert any("no own-price daily history" in f for f in signals[0].quality_flags)

    def test_missing_comparator_history_produces_data_unavailable_return_spread(self):
        """ENG-60: own price present, but the RETURN_SPREAD comparator basket
        is missing — DATA_UNAVAILABLE, not INCONCLUSIVE (own price data alone
        never lets evaluate_return_spread run)."""
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MAGS"], daily_histories={"MAGS": _linear(100, 112.6, 64)},
            weekly_trend_readings={}, hy_oas_session_history=[],
            dominant_directives={},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.DATA_UNAVAILABLE
        assert any("comparator history unavailable" in f for f in signals[0].quality_flags)

    def test_missing_brent_comparator_produces_data_unavailable_hybrid(self):
        """ENG-60: MLPX (HYBRID) with own price present but no Brent
        comparator — DATA_UNAVAILABLE, same missing-input treatment as the
        RETURN_SPREAD case above."""
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MLPX"], daily_histories={"MLPX": _linear(100, 112.6, 64)},
            weekly_trend_readings={}, hy_oas_session_history=[],
            dominant_directives={},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.DATA_UNAVAILABLE
        assert any("Brent comparator history unavailable" in f for f in signals[0].quality_flags)

    def test_hybrid_downgrades_to_data_unavailable_when_hy_oas_confirmation_missing(self):
        """ENG-60: MLPX's Brent spread finds a real STRENGTHENING call, but
        the HY_OAS confirmation gate itself is unavailable (< 2 valid
        readings) — the call must downgrade to DATA_UNAVAILABLE, not pass
        through unconfirmed. Previously this case fell through with no
        downgrade at all (only hy_confirms is False was handled)."""
        histories = {"MLPX": _linear(100, 130, 64), "BZ=F": [100.0] * 64}
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MLPX"], daily_histories=histories,
            weekly_trend_readings={}, hy_oas_session_history=[],  # < 2 readings -> None
            dominant_directives={},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.DATA_UNAVAILABLE
        assert any("HY_OAS confirmation input unavailable" in f for f in signals[0].quality_flags)

    def test_hybrid_downgrades_to_inconclusive_when_hy_oas_widens(self):
        """A real STRENGTHENING call, genuinely disconfirmed (widening HY
        OAS) — INCONCLUSIVE, not DATA_UNAVAILABLE, since the gate DID run."""
        histories = {"MLPX": _linear(100, 130, 64), "BZ=F": [100.0] * 64}
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MLPX"], daily_histories=histories,
            weekly_trend_readings={},
            hy_oas_session_history=[("2026-06-10", 290), ("2026-07-10", 320)],  # widening
            dominant_directives={},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.INCONCLUSIVE
        assert any("HY_OAS widening" in f for f in signals[0].quality_flags)

    def test_hybrid_strengthening_confirmed_by_hy_oas_tightening(self):
        """Sanity check the happy path still works after the gating rewrite:
        a real STRENGTHENING call, confirmed by tightening HY OAS, stays
        STRENGTHENING."""
        histories = {"MLPX": _linear(100, 130, 64), "BZ=F": [100.0] * 64}
        signals = m.evaluate_all_trend_signals(
            held_tickers=["MLPX"], daily_histories=histories,
            weekly_trend_readings={},
            hy_oas_session_history=[("2026-06-10", 320), ("2026-07-10", 290)],  # tightening
            dominant_directives={},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.STRENGTHENING

    def test_ticker_without_config_entry_silently_skipped(self):
        signals = m.evaluate_all_trend_signals(
            held_tickers=["NOT_IN_SCOPE"], daily_histories={"NOT_IN_SCOPE": _linear(100, 110, 64)},
            weekly_trend_readings={}, hy_oas_session_history=[], dominant_directives={},
        )
        assert signals == []

    def test_sgol_weakening_on_2026_07_13_real_scenario_after_eng65_fix(self):
        """ENG-65 end-to-end regression: the exact live scenario from
        2026-07-13, using SGOL's REAL own daily closes (genuinely down
        -13.89% over the 63-day window, -3.53% over 21 days — both past
        NOISE_FLOOR_PCT, both dipped briefly above their own starting value
        early on) alongside the real REAL_YIELD_10Y_TREND/DXY_TREND weekly
        series. Before ENG-65 this produced INCONCLUSIVE twice over (the
        confirmation gate AND SGOL's own price were both nulled by the
        reversal veto). After the fix, both legs resolve for real: real
        yield up, DXY up (confirms=True); SGOL's own price down/down
        (agrees) -> a genuine, confirmed WEAKENING call, matching gold's
        actual observed decline."""
        sgol_63d_closes = [
            45.43, 45.34, 45.17, 46.16, 45.68, 45.65, 46.24, 45.84, 44.56, 45.14,
            44.72, 44.94, 44.58, 43.76, 43.3, 43.96, 43.9, 43.02, 43.38, 44.68,
            44.77, 44.99, 45.09, 44.91, 44.66, 44.3, 43.28, 43.4, 42.69, 43.3,
            43.24, 42.94, 42.93, 42.38, 42.83, 43.28, 42.66, 42.72, 42.3, 42.66,
            41.12, 41.21, 40.55, 38.88, 40.06, 40.1, 41.15, 41.27, 40.32, 40.16,
            39.89, 39.15, 37.96, 38.34, 38.77, 38.24, 38.23, 38.45, 39.24, 39.65,
            39.18, 38.85, 39.23, 39.12,
        ]
        histories = {"SGOL": sgol_63d_closes}
        weekly = {
            "REAL_YIELD_10Y_TREND": [2.16, 2.07, 2.19, 2.17, 2.21, 2.18, 2.26, 2.32],
            "DXY_TREND": [98.91, 100.07, 99.75, 100.85, 101.36, 100.86, 100.97, 101.27],
        }
        signals = m.evaluate_all_trend_signals(
            held_tickers=["SGOL"], daily_histories=histories,
            weekly_trend_readings=weekly, hy_oas_session_history=[],
            dominant_directives={"SGOL": "ADD"},
        )
        assert len(signals) == 1
        assert signals[0].own_short_dir == "down"
        assert signals[0].own_medium_dir == "down"
        assert signals[0].rs_signal == TrendSignalCode.WEAKENING

    def test_sgol_data_unavailable_when_real_yield_genuinely_missing(self):
        """Sanity check the DATA_UNAVAILABLE path still fires correctly when
        a weekly reading is genuinely absent (contrast with the test above)."""
        histories = {"SGOL": _linear(100, 130, 64)}
        weekly = {
            "REAL_YIELD_10Y_TREND": None,
            "DXY_TREND": [98.91, 100.07, 99.75, 100.85, 101.36, 100.86, 100.97, 101.27],
        }
        signals = m.evaluate_all_trend_signals(
            held_tickers=["SGOL"], daily_histories=histories,
            weekly_trend_readings=weekly, hy_oas_session_history=[],
            dominant_directives={"SGOL": "ADD"},
        )
        assert len(signals) == 1
        assert signals[0].rs_signal == TrendSignalCode.DATA_UNAVAILABLE
        assert any("unavailable this session" in f for f in signals[0].quality_flags)

    def test_dbmf_own_price_uses_plain_trend_not_no_reversal_veto(self):
        """ENG-65: DBMF's OWN price is a plain instrument trend read (no
        require_no_reversal) — only the breadth CONFIRMATION check (other
        markets' trends, as a strategy-backdrop proxy) keeps the DBMF-
        specific veto. Both the trailing 22-point (short) and full 64-point
        (medium) windows here have their own early dip below their own
        respective starting value, each followed by a real, material rise
        — under the corrected default neither window should be nulled."""
        dbmf_closes = (
            [100, 95, 90, 95]           # idx 0-3: dips below idx0=100 (tests medium's guard)
            + _linear(96, 102, 38)      # idx 4-41: gentle rise
            + [103, 98, 95, 100]        # idx 42-45: dips below idx42=103 (tests short's guard)
            + _linear(101, 115, 18)     # idx 46-63: rise to the end
        )
        assert len(dbmf_closes) == 64
        histories = {"DBMF": dbmf_closes}
        weekly = {
            "DXY_TREND": _linear(100, 96, 8),
            "BRENT_TREND": _linear(70, 75, 8),
            "GOLD_TREND": _linear(2000, 2100, 8),
            "SP500_TREND": _linear(5000, 5200, 8),
        }
        signals = m.evaluate_all_trend_signals(
            held_tickers=["DBMF"], daily_histories=histories,
            weekly_trend_readings=weekly, hy_oas_session_history=[],
            dominant_directives={"DBMF": "ADD"},
        )
        assert len(signals) == 1
        # DBMF's own price is genuinely "up" net in both windows -- the
        # early dip in each must not suppress it, since own price never
        # gets require_no_reversal.
        assert signals[0].own_short_dir == "up"
        assert signals[0].own_medium_dir == "up"
