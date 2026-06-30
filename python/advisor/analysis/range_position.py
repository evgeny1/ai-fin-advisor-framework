"""
analysis/range_position.py — M15/M19 within-scenario range-position advisory.

Closes GAP-16 (Calibration_State.md §6): the framework's EV math
(M15.blendedScenarioReturn) uses a single conservative value per role per
scenario; nothing previously flagged whether CURRENT conditions favor the
upper or lower end of a wide [conservative, upside] band. This module is
ADVISORY ONLY — it NEVER touches blendedScenarioReturn(), idealAllocation(),
FeasibilityCheck(), or any EV/allocation computation. It only annotates the
briefing for roles whose §4.1 range is wide (>=6pp) and whose sub-condition
drivers are documented.

Scope (per the originating design note, June 18, 2026 companion session):
  inflation_hedge_precious_metals — sub-conditions: real yield (DGS10 minus
  T10YIE breakeven inflation -- REAL_YIELD_10Y_TREND) direction and DXY
  direction. The DXY half is already tracked for M19 §13 SGOL/SIVR
  sustaining conditions (analysis/thesis.py) — the DXY_TREND DataReading is
  reused here, not re-fetched. The real-yield half originally reused
  THREEFYTP10_TREND (10Y term premium) as a proxy; corrected 2026-06-21
  (GAP-16 follow-up) to use REAL_YIELD_10Y_TREND instead — term premium is
  bond-supply/demand duration compensation, not the Fed-path-driven real
  rate that actually sets precious metals' opportunity cost, and the two
  series can and do diverge. See data/fetchers/fred_fetcher.py
  (_fetch_real_yield_trend) for the computation.

  Other wide-range roles named in the original note (systematic_trend_following,
  real_asset_contracted_revenue, inflation_hedge_commodity_linked) are
  explicitly OUT of scope for this pass — their sub-condition drivers have
  not been identified/documented yet. Extending this module to them is a
  §11 documentation task (one sub_condition_drivers note per role, mirroring
  the SGOL/SIVR §11 notes added alongside this module) followed by a small
  per-role branch here — not a structural code change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..types import CalibrationState, DataReading, ReturnRange, ScenarioProbabilities
from .trend import directional_trend

_WIDE_RANGE_THRESHOLD_PP = 6.0
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

_IHP_ROLE = "inflation_hedge_precious_metals"


@dataclass
class RangePositionAdvisory:
    """One ticker's GAP-16 advisory note for the current session."""
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


def _ihp_sub_conditions(
    readings: Dict[str, DataReading],
    flags: List[str],
) -> "tuple[str, List[str]]":
    """
    IHP's two documented sub-condition drivers (§11 SGOL/SIVR notes, GAP-16):
      - real yield (REAL_YIELD_10Y_TREND = DGS10 - T10YIE) direction:
        rising = headwind, falling = tailwind
      - DXY direction: appreciating = headwind, weakening = tailwind
    Returns (overall_signal, driver_notes).
    """
    signals: List[str] = []
    drivers: List[str] = []

    real_yield = _trend_closes(readings, "REAL_YIELD_10Y_TREND")
    if real_yield is not None:
        d = directional_trend(real_yield, _TREND_THRESHOLD_PCT)
        if d == "up":
            signals.append("unfavorable")
            drivers.append("real yield (10Y, DGS10−T10YIE) trending up — headwind for precious metals")
        elif d == "down":
            signals.append("favorable")
            drivers.append("real yield (10Y, DGS10−T10YIE) trending down — tailwind for precious metals")
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
            drivers.append("DXY appreciating — headwind for precious metals")
        elif d == "down":
            signals.append("favorable")
            drivers.append("DXY weakening — tailwind for precious metals")
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


def evaluate_range_position_advisories(
    held_tickers: List[str],
    probs: ScenarioProbabilities,
    cal: CalibrationState,
    readings: Dict[str, DataReading],
) -> List[RangePositionAdvisory]:
    """
    GAP-16. For each held ticker with a material inflation_hedge_precious_metals
    component, in the session's dominant scenario, flag whether real-yield/DXY
    conditions currently favor the upper or lower end of that scenario's §4.1
    range.

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
        ihp_weight = next(
            (c.weight for c in entry.components if c.role_id == _IHP_ROLE), 0.0
        )
        if ihp_weight <= 0:
            continue

        range_ = cal.return_table.get(_IHP_ROLE, {}).get(scenario)
        if range_ is None:
            continue
        width = range_.upside - range_.conservative
        if width < _WIDE_RANGE_THRESHOLD_PP:
            continue

        flags: List[str] = []
        signal, drivers = _ihp_sub_conditions(readings, flags)
        driver_text = "; ".join(drivers) if drivers else "no trend data available this session"
        note = (
            f"{ticker} ({_IHP_ROLE} weight {ihp_weight:.0%}) — Scenario {scenario} range "
            f"[{range_.conservative:+.0f}%, {range_.upside:+.0f}%] ({width:.0f}pp wide). "
            f"Sub-condition read: {signal}. {driver_text}."
        )

        results.append(RangePositionAdvisory(
            ticker=ticker, role_id=_IHP_ROLE, scenario=scenario,
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
      - Range width below _WIDE_RANGE_THRESHOLD_PP is not adjusted (GAP-16 only
        ever applied to ranges wide enough for "position within the range" to
        be a meaningful question — narrow ranges don't have room for a within-
        range read to mean anything).
    """
    signal = range_position_signals.get(role_id)
    if signal not in ("favorable", "unfavorable"):
        return base_conservative

    width = range_.upside - range_.conservative
    if width < _WIDE_RANGE_THRESHOLD_PP:
        return base_conservative

    delta = min(_RANGE_ADJUSTMENT_FRACTION * width, _RANGE_ADJUSTMENT_CAP_PP)

    if signal == "unfavorable":
        return base_conservative - delta
    # favorable — clamp so the nudge never exceeds the table's own upside
    return min(base_conservative + delta, range_.upside)
