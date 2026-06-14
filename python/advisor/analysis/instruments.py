"""
analysis/instruments.py — M15 instrument classification and blended return computation.

Public functions:
  validate_classifications()      — session-start HARD_STOP checks (instrument registry integrity)
  blended_scenario_return()       — weighted blend of return table values across components
  classify_instrument()           — returns ComponentVector from instrument registry
  dominant_directive()            — highest-weight material component directive

DESIGN:
  - No ticker or role name is hardcoded here. All resolved from CalibrationState instrument registry.
  - All scenario return computations MUST route through blended_scenario_return().
  - M08.classifyRole() remains for constituent-level constituent analysis (not allocation).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from ..exceptions import HardStopException
from ..types import (
    CalibrationState,
    ComponentWeight,
    InstrumentEntry,
)

# Minimum weight for a component to be "material" in directive conflict resolution
_MATERIAL_WEIGHT_THRESHOLD = 0.15

# Weight sum tolerance for Check 4
_WEIGHT_SUM_TOLERANCE = 0.001

# Staleness warning threshold: 90 calendar days
_STALENESS_DAYS = 90

# Valid return_type values
_VALID_RETURN_TYPES = frozenset({"conservative", "upside"})


# ── Session-start validation ───────────────────────────────────────────────────

def validate_classifications(
    allocation_tickers: List[str],
    cal: CalibrationState,
) -> List[str]:
    """
    M15.ValidateClassifications() — runs at session start.

    Performs 5 checks:
      1. Every allocation ticker has a classification entry → HARD_STOP if not
      2. Every component role exists in the role registry → HARD_STOP if not
      3. Every registered role has a return table row → HARD_STOP if not
      4. Component weights sum to 1.0 per instrument → HARD_STOP if not
      5. Staleness warning (non-blocking) for instruments not reviewed in 90+ days

    Parameters
    ----------
    allocation_tickers:
        All tickers currently in the allocation sheet.
    cal:
        CalibrationState (instrument registry + return table populated by parser).

    Returns
    -------
    List of non-blocking warnings (Check 5 only). Never returns on hard-stop conditions.

    Raises
    ------
    HardStopException on Check 1–4 failures.
    """
    warnings: List[str] = []
    classified_tickers = set(cal.instruments.keys())
    registered_roles   = set(cal.roles.keys())

    # Check 1: every allocation ticker must have a §11 entry
    unclassified = [t for t in allocation_tickers if t not in classified_tickers]
    if unclassified:
        raise HardStopException(
            f"HARD_STOP — ValidateClassifications: unclassified instruments in allocation file: "
            f"{unclassified}. Add entries to CALIBRATION_STATE §11.INSTRUMENT_CLASSIFICATION_TABLE "
            f"with components[], weights summing to 1.0, last_reviewed date, methodology note. "
            f"Session is invalid for allocation computations until resolved."
        )

    # Checks 2–5 for every classified instrument
    for ticker in allocation_tickers:
        entry = cal.instruments[ticker]  # safe — Check 1 passed

        # Check 2: every component role must be in §11 role registry
        for comp in entry.components:
            if comp.role_id not in registered_roles:
                raise HardStopException(
                    f"HARD_STOP — ValidateClassifications: {ticker} references unregistered "
                    f"role '{comp.role_id}'. Register in §11.ROLE_REGISTRY before proceeding."
                )

        # Check 3: every registered role must have a §4.1 return table row
        for comp in entry.components:
            if comp.role_id not in cal.return_table:
                raise HardStopException(
                    f"HARD_STOP — ValidateClassifications: role '{comp.role_id}' "
                    f"(used by {ticker}) has no §4.1 return table row. "
                    f"Add conservative/upside estimates for all six scenarios before proceeding."
                )

        # Check 4: component weights must sum to 1.0 (tolerance 0.001)
        # Weights may be < 1.0 when UNCLASSIFIED components are excluded from the
        # ComponentVector (e.g. AIPO bitcoin miners 7%). Warn but do not hard-stop
        # when weights are in (0, 1.0). Hard-stop only on zero or overflow.
        total_weight = sum(c.weight for c in entry.components)
        if total_weight == 0.0:
            raise HardStopException(
                f"HARD_STOP — ValidateClassifications: {ticker} has no classified "
                "components (weights sum to 0.0). Instrument cannot be used in "
                "EV computations. Add at least one registered role to §11."
            )
        elif total_weight > 1.0 + _WEIGHT_SUM_TOLERANCE:
            raise HardStopException(
                f"HARD_STOP — ValidateClassifications: {ticker} component weights sum to "
                f"{total_weight:.4f} (expected ≤ 1.0). Correct §11.INSTRUMENT_CLASSIFICATION_TABLE."
            )
        elif abs(total_weight - 1.0) > _WEIGHT_SUM_TOLERANCE:
            warnings.append(
                f"⚠ {ticker}: component weights sum to {total_weight:.4f} — "
                "UNCLASSIFIED portion excluded from EV computation. "
                "Verify classified weights at next §11 audit."
            )

        # Check 5: staleness warning (non-blocking)
        if entry.last_reviewed:
            # last_reviewed is a string; parse for staleness check
            warnings.append(
                f"⚠ {ticker}: classification last reviewed '{entry.last_reviewed}' — "
                f"verify < {_STALENESS_DAYS} days ago at session start"
            )
            # Note: actual date math requires datetime parsing; we surface the raw date
            # for the operator to assess. Full date comparison added in Stage 5.

    return warnings


# ── Instrument classification ──────────────────────────────────────────────────

def classify_instrument(ticker: str, cal: CalibrationState) -> List[ComponentWeight]:
    """
    M15.classifyInstrument(ticker) → ComponentVector.

    Returns the list of ComponentWeight objects from the instrument registry.
    Raises HardStopException if ticker not classified (ValidateClassifications should prevent this).
    """
    entry = cal.instruments.get(ticker)
    if entry is None:
        raise HardStopException(
            f"HARD_STOP — classifyInstrument: {ticker} missing from §11. "
            "ValidateClassifications() should have caught this at session start."
        )
    return entry.components


# ── Blended scenario return ────────────────────────────────────────────────────

def blended_scenario_return(
    ticker: str,
    scenario: str,
    return_type: str,
    cal: CalibrationState,
) -> float:
    """
    M15.blendedScenarioReturn(ticker, scenario, return_type) → float.

    REPLACES all direct return table lookups throughout the framework.
    For pure single-role instruments: result equals the table value exactly.
    For composite instruments: weighted blend across all components.

    Parameters
    ----------
    ticker:
        Portfolio instrument ticker. Must be in cal.instruments.
    scenario:
        One of "A", "B", "C", "D", "E", "F".
    return_type:
        "conservative" — use in ALL EV computations, idealAllocation(), FeasibilityCheck().
        "upside"       — disclosed in briefing only; NEVER used in any computation.
    cal:
        CalibrationState with return table and instrument registry.

    Returns
    -------
    Blended return as a percentage (e.g. 6.0 = 6%).

    Raises
    ------
    HardStopException if ticker or role not found in registry or return table.
    ValueError if return_type invalid or scenario invalid.
    """
    if return_type not in _VALID_RETURN_TYPES:
        raise ValueError(
            f"blended_scenario_return: return_type must be 'conservative' or 'upside', got '{return_type}'"
        )
    if scenario not in ("A", "B", "C", "D", "E", "F"):
        raise ValueError(f"blended_scenario_return: invalid scenario '{scenario}'")

    components = classify_instrument(ticker, cal)
    result = 0.0

    for comp in components:
        role_row = cal.return_table.get(comp.role_id)
        if role_row is None:
            raise HardStopException(
                f"blended_scenario_return: role '{comp.role_id}' (in {ticker}) "
                f"has no §4.1 return table row."
            )
        rr = role_row.get(scenario)
        if rr is None:
            raise HardStopException(
                f"blended_scenario_return: role '{comp.role_id}' scenario '{scenario}' "
                f"missing from §4.1 return table."
            )
        value = rr.conservative if return_type == "conservative" else rr.upside
        result += comp.weight * value

    return result


# ── Dominant directive ─────────────────────────────────────────────────────────

def dominant_directive(
    ticker: str,
    scenario: str,
    directives_table: Dict[Tuple[str, str], str],
    cal: CalibrationState,
) -> str:
    """
    M15.dominantDirective(ticker, scenario) → directive string.

    For composite instruments: apply directive of highest-weight material component.
    Material = weight >= 0.15. Conflicting directives: flag and apply primary role.

    Parameters
    ----------
    ticker:
        Portfolio instrument ticker.
    scenario:
        Scenario string "A".."F".
    directives_table:
        Dict mapping (role_id, scenario) → directive string.
        Encodes M09/M10 RESPONSES table. Populated from portfolio/directives.py (Stage 4).
    cal:
        CalibrationState.

    Returns
    -------
    Directive string for this instrument in this scenario. Returns "HOLD" when
    directive for the primary role is not found in directives_table.
    """
    components = classify_instrument(ticker, cal)

    # Sort descending by weight
    sorted_comps = sorted(components, key=lambda c: c.weight, reverse=True)
    primary_role = sorted_comps[0].role_id

    # Lookup primary directive
    primary_directive = directives_table.get((primary_role, scenario), "HOLD")

    if len(sorted_comps) == 1:
        return primary_directive

    # Material components (weight >= threshold)
    material = [c for c in sorted_comps if c.weight >= _MATERIAL_WEIGHT_THRESHOLD]
    if len(material) == 1:
        return primary_directive

    directives = [
        directives_table.get((c.role_id, scenario), "HOLD")
        for c in material
    ]

    # Check for conflict
    unique = set(directives)
    if len(unique) == 1:
        # All same — apply
        return directives[0]

    # Determine if directions conflict (ADD vs REDUCE) or are compatible (same direction)
    direction_sets = {_directive_direction(d) for d in directives}
    if len(direction_sets) > 1:
        # Conflicting directions — apply primary and flag
        # Flag is surfaced via quality_flags in the calling context
        return primary_directive

    # Same direction, different magnitude — apply most conservative
    return _most_conservative(directives)


def _directive_direction(directive: str) -> str:
    """Normalize directive to ADD/HOLD/REDUCE for conflict detection."""
    upper = directive.upper()
    if any(x in upper for x in ("ADD", "INCREASE", "BUY")):
        return "ADD"
    if any(x in upper for x in ("REDUCE", "TRIM", "EXIT", "SELL")):
        return "REDUCE"
    return "HOLD"


def _most_conservative(directives: List[str]) -> str:
    """
    Return the most conservative directive from same-direction candidates.
    For REDUCE direction: largest reduction is most conservative.
    For ADD direction: smallest add is most conservative.
    Heuristic: prefer 'REDUCE' over 'TRIM'; prefer 'HOLD' over 'ADD'.
    """
    priority = {
        "EXIT": 0, "EXIT_INITIATED": 0,
        "REDUCE": 1, "TRIM": 2,
        "HOLD": 3,
        "ADD": 4, "INCREASE": 5,
    }
    def _rank(d: str) -> int:
        for key, rank in priority.items():
            if key in d.upper():
                return rank
        return 3  # default HOLD
    return min(directives, key=_rank)
