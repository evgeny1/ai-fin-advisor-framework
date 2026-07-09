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
        assert m._agreement_gate(up_a, up_b) is True

    def test_false_when_directions_disagree(self):
        up = _linear(100, 120, 8)
        down = _linear(100, 80, 8)
        assert m._agreement_gate(up, down) is False

    def test_none_when_either_series_missing(self):
        up = _linear(100, 120, 8)
        assert m._agreement_gate(up, None) is None
        assert m._agreement_gate(None, up) is None

    def test_none_when_either_direction_indeterminate(self):
        up = _linear(100, 120, 8)
        flat = [100.0, 100.5, 99.8, 100.2, 100.1, 99.9, 100.3, 100.0]
        assert m._agreement_gate(up, flat) is None


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
        """ENG-60: macro_confirms is None means the confirmation gate itself
        never resolved — DATA_UNAVAILABLE, even though own_short/own_medium
        (returned here) both agree ("up"). Distinct from a real disconfirm
        (macro_confirms=False, covered below) which is a genuine INCONCLUSIVE."""
        instrument = _linear(100, 130, 64)
        code, d1, d2, flags = m.evaluate_own_trend_confirmed("SGOL", instrument, macro_confirms=None)
        assert code == TrendSignalCode.DATA_UNAVAILABLE
        assert d1 == "up" and d2 == "up"  # still populated for display
        assert any("confirmation input unavailable" in f for f in flags)

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
        confirms, flags = m._dbmf_macro_confirms("up", breadth, dxy_closes=trending)
        assert confirms is True

    def test_does_not_confirm_when_breadth_below_threshold(self):
        trending = _linear(100, 120, 8)
        flat = [100.0, 100.1, 99.9, 100.2, 100.0, 99.8, 100.1, 100.0]
        breadth = {"BRENT_TREND": trending, "GOLD_TREND": flat, "SP500_TREND": flat}
        confirms, flags = m._dbmf_macro_confirms("up", breadth, dxy_closes=trending)
        assert confirms is False
        assert any("below the 3/4" in f for f in flags)

    def test_none_when_dxy_missing(self):
        confirms, flags = m._dbmf_macro_confirms("up", {}, dxy_closes=None)
        assert confirms is None

    def test_none_when_own_short_none(self):
        confirms, flags = m._dbmf_macro_confirms(None, {}, dxy_closes=_linear(100, 120, 8))
        assert confirms is None


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
