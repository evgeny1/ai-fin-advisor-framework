"""
analysis/range_position.py — M15/M19 within-scenario range-position advisory.

Closes GAP-16 (Calibration_State.md §6 item 40): the framework's EV math
(M15.blendedScenarioReturn) uses a single conservative value per role per
scenario; nothing previously flagged whether CURRENT conditions favor the
upper or lower end of a wide [conservative, upside] band. This module is
ADVISORY ONLY — it NEVER touches blendedScenarioReturn(), idealAllocation(),
FeasibilityCheck(), or any EV/allocation computation. It only annotates the
briefing for roles REGISTERED below (see _SUB_CONDITION_EVALUATORS) whose
§4.1 range clears that role's OWN width gate (see
_WIDE_RANGE_THRESHOLD_PP_BY_ROLE — not a single flat threshold, since
GAP-18 below) and whose sub-condition drivers are documented.

Scope:
  inflation_hedge_precious_metals (SGOL/SIVR) — the original GAP-16 role
  (design note, June 18 2026 companion session). Sub-conditions: real yield
  (DGS10 minus T10YIE breakeven inflation -- REAL_YIELD_10Y_TREND) direction
  and DXY direction. The DXY half is already tracked for M19 §13 SGOL/SIVR
  sustaining conditions (analysis/thesis.py) — the DXY_TREND DataReading is
  reused here, not re-fetched. The real-yield half originally reused
  THREEFYTP10_TREND (10Y term premium) as a proxy; corrected 2026-06-21
  (GAP-16 follow-up) to use REAL_YIELD_10Y_TREND instead — term premium is
  bond-supply/demand duration compensation, not the Fed-path-driven real
  rate that actually sets precious metals' opportunity cost, and the two
  series can and do diverge. See data/fetchers/fred_fetcher.py
  (_fetch_real_yield_trend) for the computation. Width gate: 6.0pp.

  inflation_linked_sovereign (VTIP) — added GAP-18 (Calibration_State.md §6
  item 48 / v1.70, 2026-08-14; FRAMEWORK_BACKLOG ENG-72). Reuses the SAME
  real-yield + DXY sub-condition pair and sign convention as IHP above —
  confirmed via a 2yr/104-weekly-observation correlation analysis
  (market_data_mcp + FRED), NOT assumed: DXY's correlation with VTIP's
  weekly returns (-0.328, p=0.0007) was not weaker than real yield's
  (-0.300, p=0.0020), the two signals were only weakly collinear with each
  other (+0.148), and DXY retained ~8pp of incremental R^2 in a joint OLS.
  The working hypothesis this item opened with ("DXY doesn't matter for a
  TIPS fund, drop it") was wrong — see Calibration_State.md §3 log entry
  2026-08-14 for the full data. What DOES differ from IHP: the width gate.
  VTIP's own §4.1 ranges (e.g. Scenario C, 3pp wide) sit below IHP's 6.0pp
  gate, so porting IHP's flat threshold verbatim would silently never fire
  for this role — hence a ROLE-SPECIFIC gate (2.0pp, PROVISIONAL pending
  audit — Calibration_State.md §6 item 48) rather than one shared constant.

  Other wide-range roles named in the original GAP-16 note
  (systematic_trend_following, real_asset_contracted_revenue,
  inflation_hedge_commodity_linked) have CANDIDATE sub-condition drivers
  documented (§6 item 44 — STF: DXY_TREND + cross-asset trend breadth;
  RAC: Brent + HY OAS trend; IHC: DXY_TREND + Brent as an imperfect
  commodity-complex proxy) but are explicitly OUT of scope here — none of
  them share IHP/ILS's real-yield+DXY pair, so wiring them needs their own
  sub-condition function registered below, not just a width-gate entry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ..types import CalibrationState, DataReading, ReturnRange, ScenarioProbabilities
from .trend import directional_trend

_IHP_ROLE = "inflation_hedge_precious_metals"
_ILS_ROLE = "inflation_linked_sovereign"

# Per-role width gate (pp). A role's §4.1 range must be at least this wide,
# in the session's dominant scenario, for a within-range advisory to mean
# anything. GAP-16 originally hardcoded one flat 6.0pp threshold for every
# role; GAP-18 (2026-08-14, Calibration_State.md §6 item 48 / v1.70) found
# that doesn't generalize — VTIP's own ranges sit below 6.0pp, so a
# role-specific, narrower gate was needed rather than forcing VTIP through
# IHP's bar (which would mean the mechanism silently never fires for it).
# inflation_linked_sovereign's 2.0pp value is PROVISIONAL, not run through
# M16.CalibrationMethodology() — same treatment the original 25%/3pp GAP-16
# adjustment-magnitude parameters below got. _DEFAULT_WIDE_RANGE_THRESHOLD_PP
# is a fail-safe fallback only (GAP-16's original bar) for a role registered
# in _SUB_CONDITION_EVALUATORS below without its own entry here — should not
# happen in practice, but fails toward the stricter bar, not toward 0.
_WIDE_RANGE_THRESHOLD_PP_BY_ROLE: Dict[str, float] = {
    _IHP_ROLE: 6.0,
    _ILS_ROLE: 2.0,
}
_DEFAULT_WIDE_RANGE_THRESHOLD_PP = 6.0


def _width_gate_for_role(role_id: str) -> float:
    return _WIDE_RANGE_THRESHOLD_PP_BY_ROLE.get(role_id, _DEFAULT_WIDE_RANGE_THRESHOLD_PP)


# Materiality threshold for "trending" on real yield/DXY — same tier as
# other provisional M14/M19 thresholds (e.g. §9.5 role-repricing pp
# thresholds); review at the next formal audit alongside those.
_TREND_THRESHOLD_PCT = 5.0

# GAP-16 promotion (v1.46, June 29, 2026): bounded EV adjustment magnitude.
# When both sub-condition drivers agree (signal == "favorable" or
# "unfavorable" — never "mixed"/"inconclusive"), shift the conservative
# value used in blendedScenarioReturn() by this fraction of the §4.1 range
# width, capped in absolute terms. Deliberately small and one-sided-only-on-
# agreement: this is a confirmed-headwind/tailwind discount, not a forecast,
# and must never let the live signal move the value outside the documented
# [conservative, upside] table range. PROVISIONAL pending formal M16 4-layer
# calibration of the magnitude itself at the next audit — the MECHANISM
# (bounded, agreement-gated, table-range-clamped) is the GAP-16 fix; the
# specific 25%/3pp parameters below are a conservative starting point, not
# yet empirically validated, and should be revisited alongside the rest of
# §9 GAP-16 follow-up work.
_RANGE_ADJUSTMENT_FRACTION = 0.25
_RANGE_ADJUSTMENT_CAP_PP = 3.0


@dataclass
class RangePositionAdvisory:
    """One ticker's within-scenario range-position advisory note for the current session (GAP-16/GAP-18)."""
    ticker:             str
    role_id:            str
    scenario:           str
    range_conservative: float
    range_upside:       float
    range_width_pp:     float
    signal:             str            # "favorable" | "unfavorable" | "mixed" | "inconclusive"
    drivers:            List[str] = field(default_factory=list)
    note:               str = ""
    quality_flags:      List[str] = field(default_factory=list)


def _trend_closes(readings: Dict[str, DataReading], spec_id: str) -> Optional[List[float]]:
    r = readings.get(spec_id)
    if r is None or not r.is_valid:
        return None
    v = r.value
    if isinstance(v, dict) and isinstance(v.get("closes"), list):
        return [float(x) for x in v["closes"] if x is not None]
    return None


def _real_yield_dxy_sub_conditions(
    readings: Dict[str, DataReading],
    flags: List[str],
) -> "tuple[str, List[str]]":
    """
    Shared two-signal sub-condition evaluator, registered below (see
    _SUB_CONDITION_EVALUATORS) against both inflation_hedge_precious_metals
    (§11 SGOL/SIVR notes, GAP-16 original) and inflation_linked_sovereign
    (GAP-18, 2026-08-14 — same pair and sign convention, confirmed via real
    data for VTIP specifically, not just ported from IHP on assumption; see
    module docstring):
      - real yield (REAL_YIELD_10Y_TREND = DGS10 - T10YIE) direction:
        rising = headwind, falling = tailwind
      - DXY direction: appreciating = headwind, weakening = tailwind
    Returns (overall_signal, driver_notes). Formerly named
    _ihp_sub_conditions before GAP-18 registered a second role against it —
    logic below is unchanged from that version, name/docstring only.
    """
    signals: List[str] = []
    drivers: List[str] = []

    real_yield = _trend_closes(readings, "REAL_YIELD_10Y_TREND")
    if real_yield is not None:
        d = directional_trend(real_yield, _TREND_THRESHOLD_PCT)
        if d == "up":
            signals.append("unfavorable")
            drivers.append("real yield (10Y, DGS10−T10YIE) trending up — headwind")
        elif d == "down":
            signals.append("favorable")
            drivers.append("real yield (10Y, DGS10−T10YIE) trending down — tailwind")
        else:
            # Data WAS available — it just didn't clear the materiality
            # threshold in either direction. Distinct from the unavailable
            # case below; previously both fell through to the same silent
            # no-op, which made the caller's "no trend data available"
            # fallback note fire even when data existed and was simply flat
            # (found 2026-06-20: DXY +2.6%/8wk, THREEFYTP10 +0.6%/8wk, both
            # under the 5% threshold, quality_flags empty, note still said
            # "no trend data available this session").
            drivers.append(
                f"real yield (10Y, DGS10−T10YIE) flat over the window (move below "
                f"{_TREND_THRESHOLD_PCT:.0f}% materiality threshold) — no lean"
            )
    else:
        flags.append("REAL_YIELD_10Y_TREND unavailable — real yield sub-condition not evaluated")

    dxy = _trend_closes(readings, "DXY_TREND")
    if dxy is not None:
        d = directional_trend(dxy, _TREND_THRESHOLD_PCT)
        if d == "up":
            signals.append("unfavorable")
            drivers.append("DXY appreciating — headwind")
        elif d == "down":
            signals.append("favorable")
            drivers.append("DXY weakening — tailwind")
        else:
            drivers.append(
                f"DXY flat over the window (move below {_TREND_THRESHOLD_PCT:.0f}% "
                "materiality threshold) — no lean"
            )
    else:
        flags.append("DXY_TREND unavailable — dollar sub-condition not evaluated")

    if not signals:
        overall = "inconclusive"
    elif all(s == "unfavorable" for s in signals):
        overall = "unfavorable"
    elif all(s == "favorable" for s in signals):
        overall = "favorable"
    else:
        overall = "mixed"
    return overall, drivers


# Roles this module knows how to evaluate, and which sub-condition function
# to use for each. GAP-16 originally hardcoded exactly one role (IHP) inline;
# GAP-18 (2026-08-14) generalized this to a registry so a second role
# (inflation_linked_sovereign) could reuse the same real-yield+DXY evaluator
# without duplicating it. Both currently-registered roles share one
# evaluator because both were confirmed (not assumed) to use the same
# signal pair — see module docstring. A future role with a DIFFERENT
# sub-condition pair (e.g. STF's DXY+trend-breadth per §6 item 44) would
# register its OWN function here, not be forced through this one.
_SUB_CONDITION_EVALUATORS: Dict[
    str, Callable[[Dict[str, DataReading], List[str]], Tuple[str, List[str]]]
] = {
    _IHP_ROLE: _real_yield_dxy_sub_conditions,
    _ILS_ROLE: _real_yield_dxy_sub_conditions,
}


def evaluate_range_position_advisories(
    held_tickers: List[str],
    probs: ScenarioProbabilities,
    cal: CalibrationState,
    readings: Dict[str, DataReading],
) -> List[RangePositionAdvisory]:
    """
    GAP-16 (original)/GAP-18 (generalized, 2026-08-14). For each held ticker
    with a material component in a role registered in
    _SUB_CONDITION_EVALUATORS above, in the session's dominant scenario, flag
    whether that role's sub-condition read currently favors the upper or
    lower end of that scenario's §4.1 range -- gated by the role's OWN width
    threshold (_WIDE_RANGE_THRESHOLD_PP_BY_ROLE), not a single flat one.

    Produces the RangePositionAdvisory list consumed two ways:
      1. Briefing narrative (always — this was GAP-16's original v1.42 scope).
      2. clean_signal_role_map() below extracts agreement-only signals from
         this same list for CalibrationState.range_position_signals, which
         apply_range_position_adjustment() / blended_scenario_return() then
         use to apply a small, bounded, table-clamped EV adjustment (v1.46
         GAP-16 promotion). This function itself still computes nothing
         beyond the advisory — it remains the single source of truth for
         the signal; v1.46 just stopped discarding the result after the
         briefing read it.
    """
    scenario = max(("A", "B", "C", "D", "E", "F"), key=lambda s: getattr(probs, s))
    results: List[RangePositionAdvisory] = []

    for ticker in held_tickers:
        entry = cal.instruments.get(ticker)
        if entry is None:
            continue

        for component in entry.components:
            role_id = component.role_id
            evaluator = _SUB_CONDITION_EVALUATORS.get(role_id)
            if evaluator is None or component.weight <= 0:
                continue

            range_ = cal.return_table.get(role_id, {}).get(scenario)
            if range_ is None:
                continue
            width = range_.upside - range_.conservative
            if width < _width_gate_for_role(role_id):
                continue

            flags: List[str] = []
            signal, drivers = evaluator(readings, flags)
            driver_text = "; ".join(drivers) if drivers else "no trend data available this session"
            note = (
                f"{ticker} ({role_id} weight {component.weight:.0%}) — Scenario {scenario} range "
                f"[{range_.conservative:+.0f}%, {range_.upside:+.0f}%] ({width:.0f}pp wide). "
                f"Sub-condition read: {signal}. {driver_text}."
            )

            results.append(RangePositionAdvisory(
                ticker=ticker, role_id=role_id, scenario=scenario,
                range_conservative=range_.conservative, range_upside=range_.upside,
                range_width_pp=width, signal=signal, drivers=drivers,
                note=note, quality_flags=flags,
            ))

    return results


# ── GAP-16 promotion (v1.46): bounded EV adjustment ────────────────────────────

def clean_signal_role_map(advisories: List[RangePositionAdvisory]) -> Dict[str, str]:
    """
    Reduce a session's RangePositionAdvisory list to {role_id: signal} for
    CalibrationState.range_position_signals, keeping ONLY roles where the
    signal is "favorable" or "unfavorable" (both sub-conditions agreed).
    "mixed" and "inconclusive" are deliberately dropped, not mapped to a
    neutral value — blended_scenario_return()'s lookup is a plain dict.get(),
    so a role absent from this map is treated identically to a role that was
    never evaluated at all (no adjustment), which is the correct behavior for
    "the two drivers disagree" or "no trend data this session": absence of
    evidence is not evidence of a tailwind OR a headwind.

    Multiple tickers can report the same role_id (e.g. SGOL and SIVR both
    carry inflation_hedge_precious_metals); they will always agree on signal
    since both come from the same dominant-scenario sub-condition read, but
    if conftest/test fixtures ever construct a disagreeing pair, last-write-
    wins is acceptable here — there is no principled way to resolve two
    advisories for the same role disagreeing on the same session's macro
    data, and this would itself indicate a code defect upstream, not a real
    state to adjudicate.
    """
    return {
        a.role_id: a.signal
        for a in advisories
        if a.signal in ("favorable", "unfavorable")
    }


def apply_range_position_adjustment(
    role_id: str,
    scenario: str,
    base_conservative: float,
    range_: ReturnRange,
    range_position_signals: Dict[str, str],
) -> float:
    """
    GAP-16 promotion (v1.46). Given a role's table conservative value and its
    full [conservative, upside] range for this scenario, return the value to
    actually use in blended_scenario_return() — adjusted by a small, bounded
    amount when range_position_signals confirms a clean (non-mixed) headwind
    or tailwind for this role, otherwise returned unchanged.

    Guarantees (all enforced below, not just documented):
      - role_id absent from range_position_signals → base_conservative,
        byte-for-byte unchanged. This is the default for every role and
        every session that hasn't populated the dict, which is every call
        site and every test that existed before v1.46.
      - Adjustment magnitude is bounded to
        min(_RANGE_ADJUSTMENT_FRACTION * range_width, _RANGE_ADJUSTMENT_CAP_PP).
      - Result is clamped to stay within [range_.conservative - cap, range_.upside]
        for "unfavorable", and within [range_.conservative, range_.upside] for
        "favorable" — the adjustment can push BELOW the documented conservative
        floor (that is the entire point: a confirmed headwind means the table's
        own conservative estimate is now optimistic), but it can never push
        above the documented upside, and the headwind discount itself is capped
        so a single session's trend read can't dominate the multi-year §4.1
        calibration the table represents.
      - Range width below that role's OWN width gate
        (_WIDE_RANGE_THRESHOLD_PP_BY_ROLE, GAP-18) is not adjusted — GAP-16
        only ever applied to ranges wide enough for "position within the
        range" to be a meaningful question, and GAP-18 found that bar is not
        the same for every role (VTIP's own ranges are narrower than IHP's).
        This check is intentionally independent of, and redundant with,
        evaluate_range_position_advisories()'s own width gate above (design
        principle: redundant validation here is defense in depth, not
        duplication to clean up) — it must use the SAME per-role gate, not a
        second hardcoded threshold, or the two checks could silently
        disagree for a role like VTIP whose gate differs from the default.
    """
    signal = range_position_signals.get(role_id)
    if signal not in ("favorable", "unfavorable"):
        return base_conservative

    width = range_.upside - range_.conservative
    if width < _width_gate_for_role(role_id):
        return base_conservative

    delta = min(_RANGE_ADJUSTMENT_FRACTION * width, _RANGE_ADJUSTMENT_CAP_PP)

    if signal == "unfavorable":
        return base_conservative - delta
    # favorable — clamp so the nudge never exceeds the table's own upside
    return min(base_conservative + delta, range_.upside)
