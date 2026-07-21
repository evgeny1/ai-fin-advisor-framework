"""
analysis/thesis.py — M19 Thesis Sustaining Conditions evaluation engine.

Maps to: M19_ThesisSustainingConditions.md MODULE ThesisSustainingConditions

evaluate_thesis_conditions() reads §13 ThesisConditionEntry blocks (already
parsed into CalibrationState.thesis_conditions by config/calibration.py) and
resolves each held ticker's condition strings against live data:
ScenarioProbabilities, DataReadings, M14's DivergenceSignal, and AI Call-2
judgment answers (M19_ThesisSustainingConditions.md JUDGMENT_CONDITIONS).

Condition strings are natural language — calibration-dated in
Calibration_State.md §13, human-reviewable — and this module owns the mapping
from recognized phrasings to live data. It does NOT hardcode any threshold
VALUE; those are parsed from the condition text itself or read from cal/
readings/probs at call time.

KNOWN LIMITATION (flagged via quality_flags, never hidden): a genuinely
unrecognized condition phrasing, or one whose persisted history isn't deep
enough yet, always surfaces as UNKNOWN with an explicit flag — never
silently guessed at.

ENG-26/31/66 (2026-07-14): §13 conditions over a COMPUTED SIGNAL's value
across multiple sessions/months/quarters (MAGS's consecutive-sessions
divergence check, AIPO's consecutive-quarters capex-guidance check, COPX's
consecutive-months PMI check) are now evaluated via _eval_persisted_streak()
below, reading persisted history from data/signal_history_store.py — a
different problem from a price series, which yfinance/FRED already serve
on demand for any historical window in one call (see analysis/trend.py).
The session's own reading is recorded to that store separately, in
mcp_server.py right after regime_signal/call2_answers are computed, so this
module stays a pure, read-only consumer like every other _eval_* function.

All other §13 conditions containing "sustained"/"consecutive"/"rolling"/
"trend"/"reversal" (DBMF, SGOL, SIVR, MLPX, URA, COPX) ARE evaluated this
pass, using the *_TREND DataReadings registered in data/m18_registry.py and
the pure functions in analysis/trend.py — this closes ENG-13's original
scope (previously every condition matching those keywords was unconditionally
skipped regardless of whether data existed to evaluate it).

NEVER feeds output into M03.DeriveScenarioProbabilities() — read-only consumer.
UNKNOWN is never silently treated as ACTIVE by any caller of this function.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..types import (
    CalibrationState,
    DataReading,
    DivergenceLevel,
    DivergenceSignal,
    ScenarioProbabilities,
    ThesisConditionEntry,
    ThesisEvaluation,
    ThesisStatus,
)
from ..data.signal_history_store import get_history
from ._utils import get_scalar
from .signal_history import (
    consecutive_calendar_streak,
    consecutive_session_streak,
    next_month_period,
    next_quarter_period,
)
from .trend import (
    all_weeks_meet,
    decline_from_high_pct,
    directional_trend,
    mean_reversion_mode,
)

# ── Trailing-window / multi-period detection ───────────────────────────────────

_SKIP_KEYWORDS = ("sustained", "consecutive", "rolling", "trend", "reversal")


def _needs_trailing_window(cond: str) -> bool:
    low = cond.lower()
    return any(k in low for k in _SKIP_KEYWORDS)

# ── Point-in-time numeric condition patterns ────────────────────────────────────

def _cmp(op: str, lhs: float, rhs: float) -> bool:
    return {">=": lhs >= rhs, "<=": lhs <= rhs, ">": lhs > rhs, "<": lhs < rhs}[op]


_BC_PROB_RE       = re.compile(r"B\+C combined probability\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)%")
_SCENARIO_PROB_RE = re.compile(r"Scenario ([A-F]) probability\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)%")
_BZUSD_RE         = re.compile(r"^BZUSD\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)\b")
_TP10_RE          = re.compile(r"THREEFYTP10\)?\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)%")
_HYOAS_RE         = re.compile(r"HY OAS\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)\s*bps")
_NASDAQ_30D_RE    = re.compile(r"Nasdaq 30d return\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)%")
# ENG-30: a COMPOUND AND of two clauses in one condition string — DBMF's
# own 3-month return AND the B+C probability, both parsed from the text
# itself (not hardcoded). Deliberately separate from _BC_PROB_RE above:
# this condition's B+C clause is phrased "B+C >= 55%" (no "combined
# probability" wording), so it needs its own capture rather than reusing
# that regex, which requires the longer phrase and won't match here.
_DBMF_3M_RETURN_RE = re.compile(
    r"DBMF_3M_return\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)%\s*while\s*B\+C\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)%"
)


def _eval_simple_numeric(
    cond: str,
    readings: Dict[str, DataReading],
    probs: ScenarioProbabilities,
    flags: List[str],
) -> Optional[bool]:
    """Point-in-time numeric checks only. Caller has already filtered out
    trailing-window conditions via _needs_trailing_window() and regime-signal
    conditions via _eval_regime()."""
    m = _BC_PROB_RE.search(cond)
    if m:
        return _cmp(m.group(1), probs.B + probs.C, float(m.group(2)))

    m = _SCENARIO_PROB_RE.search(cond)
    if m:
        return _cmp(m.group(2), getattr(probs, m.group(1)), float(m.group(3)))

    m = _BZUSD_RE.match(cond.strip())
    if m:
        price = get_scalar(readings.get("BRENT_CRUDE"), flags, "BRENT_CRUDE")
        return None if price is None else _cmp(m.group(1), price, float(m.group(2)))

    m = _TP10_RE.search(cond)
    if m:
        val = get_scalar(readings.get("THREEFYTP10"), flags, "THREEFYTP10")
        return None if val is None else _cmp(m.group(1), val, float(m.group(2)))

    m = _HYOAS_RE.search(cond)
    if m:
        val = get_scalar(readings.get("HY_OAS"), flags, "HY_OAS")
        return None if val is None else _cmp(m.group(1), val, float(m.group(2)))

    m = _NASDAQ_30D_RE.search(cond)
    if m:
        r = readings.get("NASDAQ_30D_RETURN")
        if r is None or not r.is_valid:
            flags.append("NASDAQ_30D_RETURN: reading unavailable")
            return None
        val = r.value.get("return_30d_pct") if isinstance(r.value, dict) else None
        return None if val is None else _cmp(m.group(1), val, float(m.group(2)))

    m = _DBMF_3M_RETURN_RE.search(cond)
    if m:
        return_op, return_thresh = m.group(1), float(m.group(2))
        bc_op, bc_thresh = m.group(3), float(m.group(4))
        # ENG-68: derive from TREND_SIGNAL_HISTORY:DBMF's already-fetched
        # closes rather than a second, dedicated yf.download("DBMF", ...)
        # call. The old dedicated DBMF_3M_RETURN FetchSpec raced against
        # this same batch fetch inside yfinance's own shared._DFS global
        # (confirmed: yfinance/multi.py resets shared._DFS = {} per
        # download() call and waits on `len(shared._DFS) < len(tickers)` —
        # a COUNT check, not a key check — so a straggler worker thread
        # from one download() finishing late can satisfy a DIFFERENT,
        # concurrent download()'s wait condition with the wrong ticker's
        # data. DBMF was uniquely exposed because it was fetched via BOTH
        # a solo call and as one of the 8 held instruments in the
        # TREND_SIGNAL_HISTORY batch, in the same fetch_all() run.
        # Fetching it only once, via the batch, removes the race outright
        # rather than trying to lock around a bug inside yfinance itself).
        r = readings.get("TREND_SIGNAL_HISTORY:DBMF")
        if r is None or not r.is_valid:
            flags.append("TREND_SIGNAL_HISTORY:DBMF: reading unavailable (DBMF_3M_return)")
            return None
        closes = r.value.get("closes") if isinstance(r.value, dict) else None
        if not closes:
            flags.append("TREND_SIGNAL_HISTORY:DBMF: reading malformed (no closes)")
            return None
        n = min(64, len(closes))
        if n < 2 or closes[-n] == 0:
            flags.append("TREND_SIGNAL_HISTORY:DBMF: insufficient history for 3m return")
            return None
        dbmf_return = round((closes[-1] / closes[-n] - 1) * 100, 2)
        return_hit = _cmp(return_op, dbmf_return, return_thresh)
        bc_hit = _cmp(bc_op, probs.B + probs.C, bc_thresh)
        return return_hit and bc_hit

    return None  # not recognized — caller flags as such


def _eval_regime(cond: str, regime_signal: Optional[DivergenceSignal]) -> Optional[bool]:
    if regime_signal is None or "equity_scenario_divergence" not in cond:
        return None
    if "== HIGH" in cond or "==HIGH" in cond:
        return regime_signal.equity_scenario_divergence == DivergenceLevel.HIGH
    return None  # the ">=2 consecutive sessions" MODERATE variant is caught
                 # upstream by _needs_trailing_window — never reaches here


# ── Trailing-window evaluation (ENG-13) ───────────────────────────────────────
# Each branch below corresponds to one recognized §13 condition phrasing.
# All read *_TREND DataReadings (registered in data/m18_registry.py) and
# dispatch to the pure functions in analysis/trend.py. None means "data
# unavailable this session" (flagged) — never a silent False.

_DBMF_DIRECTIONAL_THRESHOLD = 8.0   # §13's own stated threshold
_DXY_APPRECIATION_THRESHOLD = 8.0   # §13's own stated threshold
_COPPER_DECLINE_THRESHOLD   = 15.0
_BZUSD_FLOOR                = 65.0


def _trend_closes(readings: Dict[str, DataReading], spec_id: str) -> Optional[List[float]]:
    r = readings.get(spec_id)
    if r is None or not r.is_valid:
        return None
    v = r.value
    if isinstance(v, dict) and isinstance(v.get("closes"), list):
        return [float(x) for x in v["closes"] if x is not None]
    return None


def _eval_trend(
    ticker: str,
    cond: str,
    readings: Dict[str, DataReading],
    flags: List[str],
) -> Optional[bool]:
    """Evaluate trailing-window §13 conditions. Returns None (no flag of its
    own — caller adds the generic message) only for phrasings genuinely not
    recognized here, e.g. MAGS's consecutive-sessions case (ENG-26)."""
    low = cond.lower()

    # DBMF sustaining: >=2 of {BZUSD,GCUSD,DXY,^GSPC} trending directionally, 8wk
    if "trending directionally" in low and "rolling 8-week" in low:
        series = {"BZUSD": "BRENT_TREND", "GCUSD": "GOLD_TREND",
                  "DXY": "DXY_TREND", "^GSPC": "SP500_TREND"}
        trending = 0
        any_data = False
        for name, spec_id in series.items():
            closes = _trend_closes(readings, spec_id)
            if closes is None:
                flags.append(f"{ticker}: {spec_id} unavailable for DBMF directional check")
                continue
            any_data = True
            if directional_trend(closes, _DBMF_DIRECTIONAL_THRESHOLD, require_no_reversal=True) is not None:
                trending += 1
        return (trending >= 2) if any_data else None

    # DBMF failure: all 4 markets mean-reversion mode >= 4 consecutive weeks
    if "mean-reversion mode" in low:
        results = []
        for spec_id in ("BRENT_TREND", "GOLD_TREND", "DXY_TREND", "SP500_TREND"):
            closes = _trend_closes(readings, spec_id)
            if closes is None:
                flags.append(f"{ticker}: {spec_id} unavailable for mean-reversion check")
                continue
            results.append(mean_reversion_mode(closes, _DBMF_DIRECTIONAL_THRESHOLD, require_no_reversal=True))
        if not results or any(r is None for r in results):
            return None
        return all(results)

    # SGOL/SIVR sustaining: DXY not in sustained appreciation trend >= 8wk
    if "dxy not in sustained appreciation" in low:
        closes = _trend_closes(readings, "DXY_TREND")
        if closes is None:
            flags.append(f"{ticker}: DXY_TREND unavailable")
            return None
        return directional_trend(closes, _DXY_APPRECIATION_THRESHOLD) != "up"

    # SGOL/SIVR failure: DXY appreciation > 8% over 8 weeks
    if "dxy appreciation" in low and "over 8 weeks" in low:
        closes = _trend_closes(readings, "DXY_TREND")
        if closes is None:
            flags.append(f"{ticker}: DXY_TREND unavailable")
            return None
        return directional_trend(closes, _DXY_APPRECIATION_THRESHOLD) == "up"

    # SGOL/SIVR failure: THREEFYTP10 > 2.0% sustained >= 4 weeks
    if "threefytp10" in low and "sustained" in low:
        closes = _trend_closes(readings, "THREEFYTP10_TREND")
        if closes is None:
            flags.append(f"{ticker}: THREEFYTP10_TREND unavailable")
            return None
        return all_weeks_meet(closes[-4:], ">", 2.0)

    # SIVR failure: COPX sustained decline > 15% over 8 weeks
    if "copx sustained decline" in low:
        closes = _trend_closes(readings, "COPX_PRICE_TREND")
        if closes is None:
            flags.append(f"{ticker}: COPX_PRICE_TREND unavailable")
            return None
        return directional_trend(closes, _COPPER_DECLINE_THRESHOLD) == "down"

    # MLPX failure: BZUSD sustained < 65 for >= 6 consecutive weeks
    if "bzusd sustained < 65" in low:
        closes = _trend_closes(readings, "BRENT_TREND")
        if closes is None:
            flags.append(f"{ticker}: BRENT_TREND unavailable")
            return None
        return all_weeks_meet(closes[-6:], "<", _BZUSD_FLOOR)

    # URA sustaining: uranium spot stable or in upward trend
    if "uranium spot price stable or in upward trend" in low:
        closes = _trend_closes(readings, "URANIUM_TREND")
        if closes is None:
            flags.append(f"{ticker}: URANIUM_TREND unavailable (UX=F illiquid — known limitation)")
            return None
        return directional_trend(closes, _DBMF_DIRECTIONAL_THRESHOLD) != "down"

    # URA failure: uranium sustained decline > 20% from most recent high, 12wk
    if "uranium spot sustained decline" in low:
        closes = _trend_closes(readings, "URANIUM_TREND")
        if closes is None:
            flags.append(f"{ticker}: URANIUM_TREND unavailable (UX=F illiquid — known limitation)")
            return None
        decl = decline_from_high_pct(closes)
        return None if decl is None else decl > 20.0

    # COPX sustaining: copper spot stable or in upward trend, 8wk
    if "copper spot price stable or in upward trend" in low:
        closes = _trend_closes(readings, "COPPER_TREND")
        if closes is None:
            flags.append(f"{ticker}: COPPER_TREND unavailable")
            return None
        return directional_trend(closes[-8:], _DBMF_DIRECTIONAL_THRESHOLD) != "down"

    # COPX failure: copper spot sustained decline > 15% over 8 weeks
    if "copper spot sustained decline" in low:
        closes = _trend_closes(readings, "COPPER_TREND")
        if closes is None:
            flags.append(f"{ticker}: COPPER_TREND unavailable")
            return None
        return directional_trend(closes[-8:], _COPPER_DECLINE_THRESHOLD) == "down"

    return None  # genuinely unrecognized — caller adds the generic flag


# ── Persisted cross-period streak evaluation (ENG-26/31/66) ────────────────────
# §13 conditions over a COMPUTED SIGNAL's or Call-2 judgment's value across
# multiple sessions/months/quarters — a different problem from _eval_trend's
# price-series conditions above (yfinance/FRED serve those on demand for any
# historical window in one call; a computed signal's own history has to be
# persisted somewhere, since nothing else remembers "what was it last time").
#
# Read-only here, by design: this function only reads persisted history via
# data/signal_history_store.get_history(). The session's own reading is
# recorded separately in mcp_server.py, right after regime_signal/
# call2_answers are computed — keeps every _eval_* function in this module a
# pure consumer, matching the module's own read-only-consumer contract.

def _eval_persisted_streak(
    ticker: str,
    cond: str,
    call2_answers: Dict[str, int],
    flags: List[str],
) -> Optional[bool]:
    low = cond.lower()

    # MAGS failure: equity_scenario_divergence == MODERATE, >=2 consecutive
    # sessions (ENG-26). Session-granularity — consecutive_session_streak()
    # just checks the last 2 RECORDED entries, since each entry is one
    # session by construction.
    if "consecutive sessions" in low and "equity_scenario_divergence" in low:
        history = get_history(ticker, "equity_scenario_divergence")
        result = consecutive_session_streak(history, lambda v: v == "MODERATE", min_count=2)
        if result is None:
            flags.append(
                f"{ticker}: not enough session history yet for the "
                f"2-consecutive-session MODERATE check (ENG-26)"
            )
        return result

    # COPX failure: China demand collapse, T1 PMI < 47 for >= 2 consecutive
    # MONTHS (ENG-66). Calendar-granularity — the two most recent recorded
    # months must be genuinely back-to-back, not just the last 2 readings
    # (which could span a gap if a session was skipped that month).
    if "china demand collapse" in low:
        history = get_history(ticker, "china_pmi_below_47")
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_month_period,
        )
        if result is None:
            flags.append(
                f"{ticker}: not enough month-over-month PMI history yet, or "
                f"a month was skipped, for the 2-consecutive-month check (ENG-66)"
            )
        return result

    # AIPO failure: hyperscaler capex guidance revised down, >=2 consecutive
    # QUARTERS (ENG-31's harder leg — the sustaining condition is a plain
    # single-session Call-2 judgment, handled in _eval_call2 below).
    if "hyperscaler capex guidance revised down" in low and "consecutive quarters" in low:
        history = get_history(ticker, "capex_guidance_negative")
        result = consecutive_calendar_streak(
            history, lambda v: v is True, min_count=2, step=next_quarter_period,
        )
        if result is None:
            flags.append(
                f"{ticker}: not enough quarter-over-quarter capex guidance "
                f"history yet, or a quarter was skipped, for the "
                f"2-consecutive-quarter check (ENG-31)"
            )
        return result

    return None  # not a persisted-streak condition — caller tries other evaluators


# ── Call-2 judgment routing ────────────────────────────────────────────────────
# Mirrors M19_ThesisSustainingConditions.md JUDGMENT_CONDITIONS registry exactly.
# Update both together if the registry changes.

_CALL2_CB_NARRATIVE   = "cb_gold_reserve_accumulation"   # → M19_{ticker}_CB_NARRATIVE (SGOL, SIVR)
_CALL2_NUCLEAR_POLICY = "nuclear_policy_trajectory"      # → M19_URA_NUCLEAR_POLICY
_CALL2_XAR_GATE       = "M19_XAR_CONFLICT_GATE"
_CALL2_COPX_PMI       = "M19_COPX_CHINA_PMI"
_CALL2_AIPO_CAPEX     = "M19_AIPO_CAPEX_GUIDANCE"

def _eval_call2(
    ticker: str,
    cond: str,
    call2_answers: Dict[str, int],
    flags: List[str],
) -> Optional[bool]:
    """Order matters: check the most specific marker first. XAR's sustaining
    condition text and failure condition text both reference
    'M02.active_conflict_status' (one directly, one via "fed by ..."), so
    "de-escalation event" — unique to the failure phrasing — must be checked
    before the more general active_conflict_status marker."""

    if _CALL2_CB_NARRATIVE in cond:
        qid = f"M19_{ticker}_CB_NARRATIVE"
        ans = call2_answers.get(qid)
        if ans is None:
            flags.append(f"{qid}: no Call-2 answer present")
            return None
        return bool(ans)

    if _CALL2_NUCLEAR_POLICY in cond or "Nuclear policy support intact" in cond:
        ans = call2_answers.get("M19_URA_NUCLEAR_POLICY")
        if ans is None:
            flags.append("M19_URA_NUCLEAR_POLICY: no Call-2 answer present")
            return None
        return ans >= 2   # "intact in >=2 of {US, EU, Japan, UK}"

    if "Major nuclear policy reversal" in cond:
        # Same underlying judgment as M19_URA_NUCLEAR_POLICY but the INVERSE
        # direction is not a true reversal detector — that needs prior-session
        # comparison, which isn't wired. Not computable; do not reuse the
        # count as a false proxy for "a reversal occurred this session."
        return None

    if "de-escalation event" in cond or "Hormuz traffic confirmed reopened" in cond:
        # The second phrasing ("Iran MOU signed AND Hormuz traffic confirmed
        # reopened (T1 verified)") is a separate failure_signals entry in
        # XAR's §13 block using different wording for the same underlying
        # judgment as the de-escalation gate -- found 2026-06-20 falling
        # through to "no evaluator recognizes condition" because only the
        # first phrasing was matched. Routes to the same Call-2 answer.
        ans = call2_answers.get(_CALL2_XAR_GATE)
        if ans is None:
            flags.append(f"{_CALL2_XAR_GATE}: no Call-2 answer present")
            return None
        return ans == 1

    if "active_conflict_status" in cond or "Active US-Iran conflict" in cond:
        ans = call2_answers.get(_CALL2_XAR_GATE)
        if ans is None:
            flags.append(f"{_CALL2_XAR_GATE}: no Call-2 answer present")
            return None
        return ans == 0   # gate NOT fired → conflict premise still active

    if "China PMI Manufacturing" in cond:
        # ENG-66 (2026-07-14): widened from a 0/1 binary to a 3-way scale
        # (0/1/2) so ONE Call-2 answer can drive both this sustaining
        # condition's 49-threshold AND the failure_signals' separate
        # 47-threshold ("China demand collapse", routed through
        # _eval_persisted_streak above) without redefining either
        # threshold or asking two overlapping questions about the same
        # PMI print. 2 = PMI >= 49; 1 = 47 <= PMI < 49; 0 = PMI < 47.
        ans = call2_answers.get(_CALL2_COPX_PMI)
        if ans is None:
            flags.append(f"{_CALL2_COPX_PMI}: no Call-2 answer present")
            return None
        return ans == 2   # only the top tier meets the >=49 sustaining floor

    if "hyperscaler capex guidance positive" in cond:
        # ENG-31's sustaining leg — a plain single-session Call-2 judgment
        # (cheapest fix per the item's own suggested next step). The
        # failure leg ("revised down >=2 consecutive quarters") needs
        # cross-quarter persistence instead — see _eval_persisted_streak
        # above, which reuses this same answer's negation (ans == 0).
        ans = call2_answers.get(_CALL2_AIPO_CAPEX)
        if ans is None:
            flags.append(f"{_CALL2_AIPO_CAPEX}: no Call-2 answer present")
            return None
        return bool(ans)

    return None

# ── Per-condition dispatch ──────────────────────────────────────────────────────

def _evaluate_one_condition(
    ticker: str,
    cond: str,
    readings: Dict[str, DataReading],
    probs: ScenarioProbabilities,
    regime_signal: Optional[DivergenceSignal],
    call2_answers: Dict[str, int],
    flags: List[str],
) -> Optional[bool]:
    """Dispatch one condition string. Returns None when not evaluable this
    session rather than guessing — caller treats None conservatively."""
    result = _eval_call2(ticker, cond, call2_answers, flags)
    if result is not None:
        return result

    flags_before_streak = len(flags)
    result = _eval_persisted_streak(ticker, cond, call2_answers, flags)
    if result is not None:
        return result
    streak_recognized_but_unevaluable = len(flags) > flags_before_streak

    flags_before = len(flags)
    result = _eval_trend(ticker, cond, readings, flags)
    if result is not None:
        return result
    trend_recognized_but_unevaluable = len(flags) > flags_before

    result = _eval_regime(cond, regime_signal)
    if result is not None:
        return result

    result = _eval_simple_numeric(cond, readings, probs, flags)
    if result is not None:
        return result

    if not (trend_recognized_but_unevaluable or streak_recognized_but_unevaluable):
        if _needs_trailing_window(cond):
            flags.append(
                f"{ticker}: requires trailing-window analysis not evaluable "
                f"this session — \"{cond[:90]}\""
            )
        else:
            flags.append(f"{ticker}: no evaluator recognizes condition — \"{cond[:90]}\"")
    return None

# ── Top-level entry point ───────────────────────────────────────────────────────

def evaluate_thesis_conditions(
    held_tickers: List[str],
    readings: Dict[str, DataReading],
    probs: ScenarioProbabilities,
    regime_signal: Optional[DivergenceSignal],
    cal: CalibrationState,
    call2_answers: Dict[str, int],
) -> List[ThesisEvaluation]:
    """
    M19.evaluateThesisConditions(). One ThesisEvaluation per held ticker that
    has a §13 entry. Tickers without one (defensive/floor-sleeve roles) are
    silently skipped — that's §13's documented scope boundary, not a data gap.

    Resolution order per ticker:
      1. Any evaluable failure_signals condition True   → FAILED
      2. Else any evaluable degraded_signals condition True → DEGRADED
      3. Else (sustaining conditions held, where evaluable, or were
         inconclusive but nothing fired)                 → ACTIVE
      4. Special case: NONE of a ticker's conditions were evaluable this
         session                                          → UNKNOWN
         (never silently treated as ACTIVE — §13's own taxonomy rule)
    """
    results: List[ThesisEvaluation] = []

    for ticker in held_tickers:
        entry: Optional[ThesisConditionEntry] = cal.thesis_conditions.get(ticker)
        if entry is None:
            continue  # no §13 entry — out of scope, not a gap

        flags: List[str] = []
        any_evaluated = False

        failure_hits: List[str] = []
        for cond in entry.failure_signals:
            r = _evaluate_one_condition(ticker, cond, readings, probs,
                                        regime_signal, call2_answers, flags)
            if r is not None:
                any_evaluated = True
                if r:
                    failure_hits.append(cond)

        if failure_hits:
            results.append(ThesisEvaluation(
                ticker=ticker, status=ThesisStatus.FAILED,
                fired_condition_text=failure_hits[0],
                quality_flags=flags,
            ))
            continue

        degraded_hits: List[str] = []
        for cond in entry.degraded_signals:
            r = _evaluate_one_condition(ticker, cond, readings, probs,
                                        regime_signal, call2_answers, flags)
            if r is not None:
                any_evaluated = True
                if r:
                    degraded_hits.append(cond)

        if degraded_hits:
            results.append(ThesisEvaluation(
                ticker=ticker, status=ThesisStatus.DEGRADED,
                fired_condition_text=degraded_hits[0],
                quality_flags=flags,
            ))
            continue

        sustaining_unevaluable: List[str] = []
        for cond in entry.sustaining_conditions:
            r = _evaluate_one_condition(ticker, cond, readings, probs,
                                        regime_signal, call2_answers, flags)
            if r is not None:
                any_evaluated = True
            else:
                sustaining_unevaluable.append(cond)

        if not any_evaluated:
            results.append(ThesisEvaluation(
                ticker=ticker, status=ThesisStatus.UNKNOWN,
                missing_dependencies=(
                    entry.sustaining_conditions
                    + entry.degraded_signals
                    + entry.failure_signals
                ),
                quality_flags=flags,
            ))
            continue

        results.append(ThesisEvaluation(
            ticker=ticker, status=ThesisStatus.ACTIVE,
            missing_dependencies=sustaining_unevaluable,
            quality_flags=flags,
        ))

    return results
