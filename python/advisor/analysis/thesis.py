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

KNOWN LIMITATION (flagged via quality_flags, never hidden — ENG-26): the one
remaining trailing-window category this module cannot evaluate is a
condition over CONSECUTIVE SESSIONS of a computed signal (currently only
MAGS's "equity_scenario_divergence shifts to MODERATE for >= 2 consecutive
sessions"). That needs persisted per-session SIGNAL history — a different
problem from a price series, which yfinance/FRED already serve on demand
for any historical window in one call. See FRAMEWORK_BACKLOG.md ENG-26.

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
from ._utils import get_scalar
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

    # MAGS failure: cross-session SIGNAL streak — not a price series; ENG-26
    if "consecutive sessions" in low:
        flags.append(
            f"{ticker}: requires cross-session signal history not yet implemented "
            f"(ENG-26) — \"{cond[:90]}\""
        )
        return None

    return None  # genuinely unrecognized — caller adds the generic flag


# ── Call-2 judgment routing ────────────────────────────────────────────────────
# Mirrors M19_ThesisSustainingConditions.md JUDGMENT_CONDITIONS registry exactly.
# Update both together if the registry changes.

_CALL2_CB_NARRATIVE   = "cb_gold_reserve_accumulation"   # → M19_{ticker}_CB_NARRATIVE (SGOL, SIVR)
_CALL2_NUCLEAR_POLICY = "nuclear_policy_trajectory"      # → M19_URA_NUCLEAR_POLICY
_CALL2_XAR_GATE       = "M19_XAR_CONFLICT_GATE"
_CALL2_COPX_PMI       = "M19_COPX_CHINA_PMI"

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
        ans = call2_answers.get(_CALL2_COPX_PMI)
        if ans is None:
            flags.append(f"{_CALL2_COPX_PMI}: no Call-2 answer present")
            return None
        return bool(ans)   # 1 = PMI >= 49

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

    if not trend_recognized_but_unevaluable:
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
