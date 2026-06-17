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

KNOWN LIMITATION (flagged via quality_flags, never hidden): conditions
containing "sustained", "consecutive", "rolling", "trend"/"trending", or
"reversal" describe multi-period behavior this pass cannot evaluate from a
single-session snapshot — no historical trend-tracking infrastructure exists
yet for BZUSD/GCUSD/COPPER_SPOT/URANIUM_SPOT/DBMF/NASDAQ at the window lengths
§13 specifies (6-12 weeks). These conditions never contribute a silent pass.
Follow-up: extend yfinance_fetcher's history-based pattern (already used for
VIX_30D_AVG/VIX_90D_AVG/BROAD_EQUITY_TRAILING) to the §13 series, then wire
the trailing-window checks below.

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

    return None  # not recognized — caller flags as such


def _eval_regime(cond: str, regime_signal: Optional[DivergenceSignal]) -> Optional[bool]:
    if regime_signal is None or "equity_scenario_divergence" not in cond:
        return None
    if "== HIGH" in cond or "==HIGH" in cond:
        return regime_signal.equity_scenario_divergence == DivergenceLevel.HIGH
    return None  # the ">=2 consecutive sessions" MODERATE variant is caught
                 # upstream by _needs_trailing_window — never reaches here


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

    if "de-escalation event" in cond:
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

    if _needs_trailing_window(cond):
        flags.append(
            f"{ticker}: requires trailing-window analysis not yet implemented "
            f"— \"{cond[:90]}\""
        )
        return None

    result = _eval_regime(cond, regime_signal)
    if result is not None:
        return result

    result = _eval_simple_numeric(cond, readings, probs, flags)
    if result is not None:
        return result

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
