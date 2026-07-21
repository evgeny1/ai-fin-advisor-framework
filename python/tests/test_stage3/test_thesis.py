"""
tests/test_stage3/test_thesis.py — unit tests for analysis/thesis.py (M19).

No dedicated test file existed for thesis.py before this — exercised only
via the live-data smoke test mentioned in Calibration_State.md's v1.37 log
entry, never via committed pytest. These tests focus on the ENG-13 fix
(trailing-window conditions now evaluate instead of always skipping) plus
the core FAILED/DEGRADED/ACTIVE/UNKNOWN resolution order.
"""
from __future__ import annotations

from datetime import datetime

from advisor.analysis.thesis import evaluate_thesis_conditions
from advisor.types import (
    DataReading,
    DataSource,
    ScenarioProbabilities,
    ThesisConditionEntry,
    ThesisStatus,
)


def _trend_reading(spec_id: str, closes: list) -> DataReading:
    return DataReading(spec_id=spec_id, value={"closes": closes, "n_weeks": len(closes)},
                       source=DataSource.YFINANCE, fetched_at=datetime(2026, 6, 20))


def _probs(**kw) -> ScenarioProbabilities:
    base = {"A": 10.0, "B": 30.0, "C": 30.0, "D": 10.0, "E": 10.0, "F": 10.0}
    base.update(kw)
    return ScenarioProbabilities(**base)


class TestSgolDxyAndRealYield:
    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="SGOL", primary_driver="precious metals",
            sustaining_conditions=[
                "10Y real yield (THREEFYTP10) <= 1.5%",
                "DXY not in sustained appreciation trend >= 8 consecutive weeks",
            ],
            failure_signals=[
                "THREEFYTP10 > 2.0% sustained >= 4 weeks",
                "DXY appreciation > 8% over 8 weeks",
                "Scenario E probability >= 20%",
            ],
            data_dependencies=["GCUSD", "THREEFYTP10", "DXY_INDEX"],
            last_reviewed="2026-06-17",
        )

    def test_dxy_uptrend_fires_failure(self, cal):
        cal.thesis_conditions["SGOL"] = self._entry()
        readings = {
            "THREEFYTP10": DataReading("THREEFYTP10", {"current": 1.2}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20)),
            "DXY_TREND": _trend_reading("DXY_TREND", [95, 96, 97, 98, 99, 100, 101, 103]),  # +8.4%, no reversal
        }
        results = evaluate_thesis_conditions(["SGOL"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "DXY appreciation" in results[0].fired_condition_text

    def test_dxy_flat_and_low_real_yield_is_active(self, cal):
        cal.thesis_conditions["SGOL"] = self._entry()
        readings = {
            "THREEFYTP10": DataReading("THREEFYTP10", {"current": 1.0}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20)),
            "DXY_TREND": _trend_reading("DXY_TREND", [99, 99.2, 98.9, 99.1, 99.0, 99.3, 99.1, 99.2]),
        }
        results = evaluate_thesis_conditions(["SGOL"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE

    def test_real_yield_sustained_failure_fires(self, cal):
        cal.thesis_conditions["SGOL"] = self._entry()
        readings = {
            "THREEFYTP10": DataReading("THREEFYTP10", {"current": 2.1}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20)),
            "THREEFYTP10_TREND": _trend_reading("THREEFYTP10_TREND", [1.8, 2.1, 2.2, 2.3, 2.4]),
            "DXY_TREND": _trend_reading("DXY_TREND", [99] * 8),
        }
        results = evaluate_thesis_conditions(["SGOL"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "THREEFYTP10" in results[0].fired_condition_text

    def test_missing_trend_data_flagged_not_silently_active(self, cal):
        """No *_TREND readings at all -> sustaining DXY condition unevaluable,
        but the point-in-time real-yield condition still works -> ACTIVE with
        a flag, not a clean pass."""
        cal.thesis_conditions["SGOL"] = self._entry()
        readings = {
            "THREEFYTP10": DataReading("THREEFYTP10", {"current": 1.0}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20)),
        }
        results = evaluate_thesis_conditions(["SGOL"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE
        assert any("DXY_TREND unavailable" in f for f in results[0].quality_flags)


class TestDbmfDirectionalCount:
    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="DBMF", primary_driver="trend following",
            sustaining_conditions=[
                "B+C combined probability >= 55%",
                "2 of {BZUSD, GCUSD, DXY, ^GSPC} trending directionally over "
                "rolling 8-week window (directional = net move >= 8% in one "
                "direction without full reversal)",
            ],
            failure_signals=[
                "All 4 tracked markets in mean-reversion mode simultaneously "
                "for >= 4 consecutive weeks",
            ],
            data_dependencies=["DBMF", "BZUSD", "GCUSD", "DXY_INDEX", "^GSPC"],
            last_reviewed="2026-06-17",
        )

    def test_two_trending_markets_satisfies_sustaining(self, cal):
        cal.thesis_conditions["DBMF"] = self._entry()
        readings = {
            "BRENT_TREND": _trend_reading("BRENT_TREND", [70, 71, 73, 75, 77, 78, 79, 80]),
            "GOLD_TREND":  _trend_reading("GOLD_TREND",  [2000, 2020, 2040, 2060, 2080, 2100, 2120, 2160]),
            "DXY_TREND":   _trend_reading("DXY_TREND",   [99] * 8),
            "SP500_TREND": _trend_reading("SP500_TREND", [5000] * 8),
        }
        results = evaluate_thesis_conditions(["DBMF"], readings, _probs(B=30, C=30), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE

    def test_all_four_mean_reverting_fires_failure(self, cal):
        cal.thesis_conditions["DBMF"] = self._entry()
        flat8 = lambda v: [v, v + 1, v - 1, v, v - 1, v + 1, v, v]
        readings = {
            "BRENT_TREND": _trend_reading("BRENT_TREND", flat8(75.0)),
            "GOLD_TREND":  _trend_reading("GOLD_TREND",  flat8(2000.0)),
            "DXY_TREND":   _trend_reading("DXY_TREND",   flat8(99.0)),
            "SP500_TREND": _trend_reading("SP500_TREND", flat8(5000.0)),
        }
        results = evaluate_thesis_conditions(["DBMF"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED

    def test_no_trend_data_falls_back_to_prob_check_not_silently_unknown(self, cal):
        """With zero *_TREND readings, the directional-trend sustaining
        condition is unevaluable, but the B+C probability condition (needs
        only `probs`, no market data) still resolves — so this is ACTIVE
        with a flagged gap, not a blanket UNKNOWN."""
        cal.thesis_conditions["DBMF"] = self._entry()
        results = evaluate_thesis_conditions(["DBMF"], {}, _probs(B=30, C=30), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE
        assert any("trending directionally" in d for d in results[0].missing_dependencies)


class TestMlpxBzusdFloor:
    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="MLPX", primary_driver="contracted energy infrastructure",
            sustaining_conditions=["BZUSD >= 70", "B+C combined probability >= 50%"],
            failure_signals=["BZUSD sustained < 65 for >= 6 consecutive weeks"],
            data_dependencies=["BZUSD", "MLPX"], last_reviewed="2026-06-17",
        )

    def test_six_weeks_below_floor_fires_failure(self, cal):
        cal.thesis_conditions["MLPX"] = self._entry()
        readings = {"BRENT_TREND": _trend_reading("BRENT_TREND", [68, 64, 63, 62, 61, 60, 59])}
        results = evaluate_thesis_conditions(["MLPX"], readings, _probs(B=30, C=30), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED

    def test_one_week_above_floor_does_not_fire(self, cal):
        cal.thesis_conditions["MLPX"] = self._entry()
        readings = {"BRENT_TREND": _trend_reading("BRENT_TREND", [68, 64, 66, 62, 61, 60, 59])}
        results = evaluate_thesis_conditions(["MLPX"], readings, _probs(B=30, C=30), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE


class TestUraCopxTrendConditions:
    def _ura_entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="URA", primary_driver="nuclear renaissance",
            sustaining_conditions=["Uranium spot price stable or in upward trend (T1 source: Cameco spot or UxC)"],
            failure_signals=["Uranium spot sustained decline > 20% from most recent high over 12 weeks"],
            data_dependencies=["URA", "URANIUM_SPOT"], last_reviewed="2026-06-17",
        )

    def test_decline_over_20pct_from_high_fires_failure(self, cal):
        cal.thesis_conditions["URA"] = self._ura_entry()
        readings = {"URANIUM_TREND": _trend_reading("URANIUM_TREND", [100, 110, 120, 100, 90])}
        results = evaluate_thesis_conditions(["URA"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED

    def test_uranium_data_unavailable_is_unknown(self, cal):
        """Confirms the known illiquid-contract limitation degrades to a
        flagged UNKNOWN rather than guessing — URA has no other condition."""
        cal.thesis_conditions["URA"] = self._ura_entry()
        results = evaluate_thesis_conditions(["URA"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.UNKNOWN
        assert any("illiquid" in f for f in results[0].quality_flags)

    def _copx_entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="COPX", primary_driver="industrial commodity cycle",
            sustaining_conditions=["Copper spot price stable or in upward trend over rolling 8-week window"],
            failure_signals=["Copper spot sustained decline > 15% over 8 weeks"],
            data_dependencies=["COPX", "COPPER_SPOT"], last_reviewed="2026-06-17",
        )

    def test_copper_decline_over_15pct_fires_failure(self, cal):
        cal.thesis_conditions["COPX"] = self._copx_entry()
        closes = [100, 98, 95, 92, 90, 88, 85, 83]   # -17% over the window, no reversal
        readings = {"COPPER_TREND": _trend_reading("COPPER_TREND", closes)}
        results = evaluate_thesis_conditions(["COPX"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED


class TestMagsConsecutiveSessionsStreak:
    """ENG-26: equity_scenario_divergence shifts to MODERATE for >= 2
    consecutive sessions. Solved via persisted per-session history
    (data/signal_history_store.py) — isolated automatically by
    conftest.py's autouse _isolated_signal_history_store fixture, so these
    tests never touch the real SignalHistoryStore.json."""

    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="MAGS", primary_driver="equity divergence from B/C fundamentals",
            sustaining_conditions=["HY OAS <= 350 bps"],
            failure_signals=[
                "equity_scenario_divergence shifts to MODERATE for >= 2 consecutive sessions",
                "Nasdaq 30d return <= -10%",
            ],
            data_dependencies=["MAGS", "^GSPC", "HY_OAS"], last_reviewed="2026-06-17",
        )

    def test_no_history_yet_flags_eng26_not_silently_false(self, cal):
        cal.thesis_conditions["MAGS"] = self._entry()
        readings = {"HY_OAS": DataReading("HY_OAS", {"current": 300.0}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20))}
        results = evaluate_thesis_conditions(["MAGS"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE
        assert any("ENG-26" in f for f in results[0].quality_flags)

    def test_two_consecutive_moderate_sessions_fires_failure(self, cal):
        from advisor.data.signal_history_store import record_signal
        record_signal("MAGS", "equity_scenario_divergence", "2026-07-13", "MODERATE")
        record_signal("MAGS", "equity_scenario_divergence", "2026-07-14", "MODERATE")
        cal.thesis_conditions["MAGS"] = self._entry()
        readings = {"HY_OAS": DataReading("HY_OAS", {"current": 300.0}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20))}
        results = evaluate_thesis_conditions(["MAGS"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "consecutive sessions" in results[0].fired_condition_text

    def test_only_one_moderate_session_does_not_fire(self, cal):
        from advisor.data.signal_history_store import record_signal
        record_signal("MAGS", "equity_scenario_divergence", "2026-07-13", "HIGH")
        record_signal("MAGS", "equity_scenario_divergence", "2026-07-14", "MODERATE")
        cal.thesis_conditions["MAGS"] = self._entry()
        readings = {"HY_OAS": DataReading("HY_OAS", {"current": 300.0}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20))}
        results = evaluate_thesis_conditions(["MAGS"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE

    def test_nasdaq_30d_return_regex_now_fires(self, cal):
        """Previously had no FetchSpec or regex pattern at all — confirms
        the NASDAQ_30D_RETURN fix actually wires through."""
        cal.thesis_conditions["MAGS"] = self._entry()
        readings = {
            "HY_OAS": DataReading("HY_OAS", {"current": 300.0}, DataSource.FRED_SPREADSHEET_TAB, datetime(2026, 6, 20)),
            "NASDAQ_30D_RETURN": DataReading("NASDAQ_30D_RETURN", {"return_30d_pct": -12.0},
                                             DataSource.YFINANCE, datetime(2026, 6, 20)),
        }
        results = evaluate_thesis_conditions(["MAGS"], readings, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "Nasdaq 30d return" in results[0].fired_condition_text


class TestResolutionOrderAndScope:
    def test_ticker_without_entry_is_skipped(self, cal):
        results = evaluate_thesis_conditions(["SGOV"], {}, _probs(), None, cal, {})
        assert results == []

    def test_no_evaluable_condition_anywhere_is_unknown(self, cal):
        cal.thesis_conditions["XYZ"] = ThesisConditionEntry(
            ticker="XYZ", primary_driver="test",
            sustaining_conditions=["Some unrecognized qualitative narrative condition"],
            failure_signals=["Another unrecognized condition"],
            data_dependencies=[], last_reviewed="2026-06-17",
        )
        results = evaluate_thesis_conditions(["XYZ"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.UNKNOWN
        assert any("no evaluator recognizes" in f for f in results[0].quality_flags)


class TestDbmfOwnPerformance:
    """ENG-30: DBMF_3M_return < -3% while B+C >= 55% — a compound AND of
    two clauses in one condition string, both parsed from the text
    itself, not hardcoded.

    ENG-68 (2026-07-21): the underlying reading changed from a dedicated
    DBMF_3M_RETURN FetchSpec (removed — it raced against
    TREND_SIGNAL_HISTORY's own concurrent fetch of DBMF inside yfinance's
    shared._DFS global, a confirmed yfinance thread-safety issue, not a
    bug in this codebase) to a derivation from TREND_SIGNAL_HISTORY:DBMF's
    closes, already fetched as part of the 8-held-instrument batch. These
    tests now feed a synthetic closes list instead of a pre-computed
    return_3m_pct."""

    @staticmethod
    def _closes_for_return(pct: float, n: int = 64) -> list:
        """n-length closes list whose (last/first - 1)*100 == pct exactly,
        matching the same n=min(64, len(closes)) window thesis.py uses."""
        base = 100.0
        last = base * (1 + pct / 100)
        return [base] * (n - 1) + [last]

    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="DBMF", primary_driver="trend following",
            sustaining_conditions=["B+C combined probability >= 55%"],
            failure_signals=[
                "DBMF_3M_return < -3% while B+C >= 55% (instrument underperforming own scenario)",
            ],
            data_dependencies=["DBMF"], last_reviewed="2026-07-03",
        )

    def test_both_clauses_true_fires_failure(self, cal):
        cal.thesis_conditions["DBMF"] = self._entry()
        readings = {"TREND_SIGNAL_HISTORY:DBMF": DataReading(
            "TREND_SIGNAL_HISTORY:DBMF",
            {"symbol": "DBMF", "closes": self._closes_for_return(-5.2), "n_days": 64},
            DataSource.YFINANCE, datetime(2026, 7, 14),
        )}
        results = evaluate_thesis_conditions(["DBMF"], readings, _probs(B=30, C=30), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "DBMF_3M_return" in results[0].fired_condition_text

    def test_return_ok_does_not_fire_even_if_bc_high(self, cal):
        """B+C >= 55% alone must not fire — both clauses are ANDed."""
        cal.thesis_conditions["DBMF"] = self._entry()
        readings = {"TREND_SIGNAL_HISTORY:DBMF": DataReading(
            "TREND_SIGNAL_HISTORY:DBMF",
            {"symbol": "DBMF", "closes": self._closes_for_return(0.5), "n_days": 64},
            DataSource.YFINANCE, datetime(2026, 7, 14),
        )}
        results = evaluate_thesis_conditions(["DBMF"], readings, _probs(B=30, C=30), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE

    def test_bc_below_threshold_does_not_fire_even_if_return_bad(self, cal):
        """DBMF_3M_return < -3% alone must not fire if B+C is below 55% —
        the condition is specifically about underperforming ITS OWN
        scenario, not a bad return in any regime."""
        cal.thesis_conditions["DBMF"] = self._entry()
        readings = {"TREND_SIGNAL_HISTORY:DBMF": DataReading(
            "TREND_SIGNAL_HISTORY:DBMF",
            {"symbol": "DBMF", "closes": self._closes_for_return(-8.0), "n_days": 64},
            DataSource.YFINANCE, datetime(2026, 7, 14),
        )}
        results = evaluate_thesis_conditions(["DBMF"], readings, _probs(A=60, B=10, C=10, D=10, E=5, F=5), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE

    def test_missing_reading_flagged_not_silently_false(self, cal):
        cal.thesis_conditions["DBMF"] = self._entry()
        results = evaluate_thesis_conditions(["DBMF"], {}, _probs(B=30, C=30), None, cal, {})
        assert any("TREND_SIGNAL_HISTORY:DBMF" in f for f in results[0].quality_flags)


class TestCopxChinaDemandCollapseStreak:
    """ENG-66: China demand collapse, T1 PMI < 47 for >= 2 consecutive
    MONTHS. Calendar-granularity — a skipped month must not falsely
    confirm the streak."""

    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="COPX", primary_driver="industrial commodity cycle",
            sustaining_conditions=["China PMI Manufacturing >= 49 (demand floor)"],
            failure_signals=[
                "China demand collapse signal (T1 PMI < 47 for >= 2 consecutive months)",
            ],
            data_dependencies=["COPX"], last_reviewed="2026-07-14",
        )

    def test_two_consecutive_months_below_47_fires_failure(self, cal):
        from advisor.data.signal_history_store import record_signal
        record_signal("COPX", "china_pmi_below_47", "2026-06", True)
        record_signal("COPX", "china_pmi_below_47", "2026-07", True)
        cal.thesis_conditions["COPX"] = self._entry()
        results = evaluate_thesis_conditions(["COPX"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "China demand collapse" in results[0].fired_condition_text

    def test_gap_month_does_not_falsely_confirm_streak(self, cal):
        from advisor.data.signal_history_store import record_signal
        record_signal("COPX", "china_pmi_below_47", "2026-05", True)
        record_signal("COPX", "china_pmi_below_47", "2026-07", True)  # June skipped
        cal.thesis_conditions["COPX"] = self._entry()
        results = evaluate_thesis_conditions(["COPX"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.UNKNOWN
        assert any("ENG-66" in f for f in results[0].quality_flags)

    def test_sustaining_pmi_call2_top_tier_only(self, cal):
        """ENG-66's 3-way scale: only score 2 (PMI >= 49) satisfies the
        sustaining condition — tested directly against _eval_call2, since
        a sustaining condition evaluating to False vs. not-evaluated both
        leave evaluate_thesis_conditions()'s overall status/missing_
        dependencies output identical (only failure_signals affect
        status) — the 2-vs-1 distinction isn't observable at that level."""
        from advisor.analysis.thesis import _eval_call2
        cond = "China PMI Manufacturing >= 49 (demand floor)"
        flags: list = []
        assert _eval_call2("COPX", cond, {"M19_COPX_CHINA_PMI": 1}, flags) is False
        assert _eval_call2("COPX", cond, {"M19_COPX_CHINA_PMI": 0}, flags) is False

    def test_sustaining_pmi_call2_score_two_meets_floor(self, cal):
        cal.thesis_conditions["COPX"] = self._entry()
        results = evaluate_thesis_conditions(
            ["COPX"], {}, _probs(), None, cal, {"M19_COPX_CHINA_PMI": 2},
        )
        assert results[0].status == ThesisStatus.ACTIVE
        assert results[0].missing_dependencies == []


class TestAipoCapexGuidanceStreak:
    """ENG-31: sustaining condition is a plain single-session Call-2
    judgment (cheap leg); failure condition needs >=2 consecutive QUARTERS
    of negative guidance (the hard leg, same persisted-streak mechanism
    as MAGS/COPX)."""

    def _entry(self) -> ThesisConditionEntry:
        return ThesisConditionEntry(
            ticker="AIPO", primary_driver="AI infrastructure",
            sustaining_conditions=[
                "AI infrastructure capital expenditure cycle intact (hyperscaler capex guidance positive)",
            ],
            failure_signals=[
                "Hyperscaler capex guidance revised down \u22652 consecutive quarters",
            ],
            data_dependencies=["AIPO"], last_reviewed="2026-07-14",
        )

    def test_sustaining_call2_positive_is_active(self, cal):
        cal.thesis_conditions["AIPO"] = self._entry()
        results = evaluate_thesis_conditions(
            ["AIPO"], {}, _probs(), None, cal, {"M19_AIPO_CAPEX_GUIDANCE": 1},
        )
        assert results[0].status == ThesisStatus.ACTIVE

    def test_two_consecutive_quarters_negative_fires_failure(self, cal):
        from advisor.data.signal_history_store import record_signal
        record_signal("AIPO", "capex_guidance_negative", "2026-Q2", True)
        record_signal("AIPO", "capex_guidance_negative", "2026-Q3", True)
        cal.thesis_conditions["AIPO"] = self._entry()
        results = evaluate_thesis_conditions(["AIPO"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.FAILED
        assert "consecutive quarters" in results[0].fired_condition_text

    def test_gap_quarter_does_not_falsely_confirm_streak(self, cal):
        from advisor.data.signal_history_store import record_signal
        record_signal("AIPO", "capex_guidance_negative", "2026-Q1", True)
        record_signal("AIPO", "capex_guidance_negative", "2026-Q3", True)  # Q2 skipped
        cal.thesis_conditions["AIPO"] = self._entry()
        results = evaluate_thesis_conditions(["AIPO"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.UNKNOWN
        assert any("ENG-31" in f for f in results[0].quality_flags)

    def test_only_one_negative_quarter_does_not_fire(self, cal):
        """Q2/Q3 are gap-free consecutive quarters, so the streak check
        gets a definite answer (not just 'not enough history') — it's
        definitively False since only one of the two was negative. That
        still evaluates the failure condition (to False), so overall
        status is ACTIVE, not UNKNOWN — contrast with the gap case above,
        where the condition can't be evaluated at all."""
        from advisor.data.signal_history_store import record_signal
        record_signal("AIPO", "capex_guidance_negative", "2026-Q2", False)
        record_signal("AIPO", "capex_guidance_negative", "2026-Q3", True)
        cal.thesis_conditions["AIPO"] = self._entry()
        results = evaluate_thesis_conditions(["AIPO"], {}, _probs(), None, cal, {})
        assert results[0].status == ThesisStatus.ACTIVE
        assert results[0].fired_condition_text is None
