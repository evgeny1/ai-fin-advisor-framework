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
  inflation_hedge_precious_metals — sub-conditions: real yield (THREEFYTP10)
  direction and DXY direction. Both are already tracked for M19 §13
  SGOL/SIVR sustaining conditions (analysis/thesis.py) — the *_TREND
  DataReadings are reused here, not re-fetched.

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

from ..types import CalibrationState, DataReading, ScenarioProbabilities
from .trend import directional_trend

_WIDE_RANGE_THRESHOLD_PP = 6.0
# Materiality threshold for "trending" on THREEFYTP10/DXY — same tier as
# other provisional M14/M19 thresholds (e.g. §9.5 role-repricing pp
# thresholds); review at the next formal audit alongside those.
_TREND_THRESHOLD_PCT = 5.0

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
      - real yield (THREEFYTP10) direction: rising = headwind, falling = tailwind
      - DXY direction: appreciating = headwind, weakening = tailwind
    Returns (overall_signal, driver_notes).
    """
    signals: List[str] = []
    drivers: List[str] = []

    tp10 = _trend_closes(readings, "THREEFYTP10_TREND")
    if tp10 is not None:
        d = directional_trend(tp10, _TREND_THRESHOLD_PCT)
        if d == "up":
            signals.append("unfavorable")
            drivers.append("real yield (THREEFYTP10) trending up — headwind for precious metals")
        elif d == "down":
            signals.append("favorable")
            drivers.append("real yield (THREEFYTP10) trending down — tailwind for precious metals")
    else:
        flags.append("THREEFYTP10_TREND unavailable — real yield sub-condition not evaluated")

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
    range — advisory only, never feeds EV or allocation math.
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
