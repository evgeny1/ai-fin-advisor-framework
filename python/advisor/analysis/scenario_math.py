"""
analysis/scenario_math.py — M03 probability arithmetic (Python side of the AI boundary).

Maps to: M03_ScenarioFramework.md MODULE ScenarioFramework.DeriveScenarioProbabilities

This module handles ALL arithmetic in the M03 pipeline:
  normalize_scores()     — raw scores → base probabilities (sum to 100%)
  apply_floors()         — 3% floor + D structural floor if HY_RecessionPricing fired
  apply_session_cap()    — 25pp per-session cap from prior SessionLogState §8
  check_b_vs_c()         — simultaneous >30% constraint check

The AI boundary contract:
  - Python builds List[ScoringQuestion] from M03 check definitions + DataReadings.
  - AI fills ScoringAnswers (question_id → integer score).
  - Python calls this module to run all arithmetic from there.

ScoringQuestion generation from DataReadings is in analysis/scoring_questions.py (Stage 5).
This module only does the pure arithmetic given pre-filled ScoringAnswers.

Stage 3 provides two entry points:
  1. derive_from_raw_scores(raw) — for unit-testable arithmetic only (no AI needed).
  2. apply_all_rules(raw, prior, hy_recession_pricing) — full pipeline.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..exceptions import HardStopException
from ..types import RawScores, ScenarioProbabilities, SessionLogState

# Structural constants (M03 — fixed, not calibration-dated)
_FLOOR_VALUE       = 3.0    # minimum probability for any scenario (%)
_SESSION_CAP_PP    = 25.0   # maximum per-session probability shift (pp)
_SESSION_CAP_DAYS  = 7      # cap applies only when prior entry <= 7 calendar days old
_D_STRUCTURAL_FLOOR = 25.0  # D floor when HY_RecessionPricing fires (%)
_B_C_CONSTRAINT     = 30.0  # B and C both > this% → requires justification


# ── Normalization ──────────────────────────────────────────────────────────────

def normalize_scores(raw: RawScores) -> Dict[str, float]:
    """
    M03 Normalize step: raw scores → base probabilities summing to 100%.

    Raises HardStopException if total is 0 (data fetch incomplete per M03 spec).
    """
    total = raw.total
    if total == 0.0:
        raise HardStopException(
            "HARD_STOP — DeriveScenarioProbabilities.Normalize: all scenario scores are zero. "
            "Data fetch likely incomplete. NEVER produce probabilities from zero-total. "
            "Re-run intel gathering."
        )
    d = raw.as_dict()
    return {s: (d[s] / total) * 100.0 for s in d}


# ── Apply structural floors ────────────────────────────────────────────────────

def apply_floors(
    base: Dict[str, float],
    hy_recession_pricing_fired: bool = False,
) -> Dict[str, float]:
    """
    M03 ApplyFloors step.

    1. Universal floor: no scenario below _FLOOR_VALUE (3%).
       Shortfall redistributed proportionally from above-floor scenarios
       (descending by raw score contribution — approximated by current probability).

    2. D structural floor: if HY_RecessionPricing fired, D >= 25%.
       Excess D increase drawn proportionally from all other scenarios.

    Returns normalised probability dict summing to 100%.
    Raises HardStopException if result cannot be normalised.
    """
    probs = dict(base)

    # Step 1: universal 3% floor
    under_floor = {s: _FLOOR_VALUE - p for s, p in probs.items() if p < _FLOOR_VALUE}
    if under_floor:
        total_shortfall = sum(under_floor.values())
        for s in under_floor:
            probs[s] = _FLOOR_VALUE
        # Reduce above-floor scenarios proportionally
        above = {s: p for s, p in probs.items() if s not in under_floor}
        above_total = sum(above.values())
        if above_total > 0:
            for s in above:
                probs[s] -= total_shortfall * (above[s] / above_total)

    # Step 2: D structural floor (HY_RecessionPricing)
    if hy_recession_pricing_fired and probs.get("D", 0.0) < _D_STRUCTURAL_FLOOR:
        excess = _D_STRUCTURAL_FLOOR - probs["D"]
        probs["D"] = _D_STRUCTURAL_FLOOR
        non_d = {s: p for s, p in probs.items() if s != "D"}
        non_d_total = sum(non_d.values())
        if non_d_total > 0:
            for s in non_d:
                probs[s] -= excess * (non_d[s] / non_d_total)
        else:
            raise HardStopException(
                "HARD_STOP — apply_floors: D structural floor cannot be satisfied "
                "(non-D probability total is 0 after prior adjustments)"
            )

    # Verify sum
    _verify_sum(probs, context="apply_floors")
    return probs


# ── Apply session cap ──────────────────────────────────────────────────────────

def apply_session_cap(
    derived: Dict[str, float],
    prior: Optional[ScenarioProbabilities],
    *,
    signal_convergence_documented: bool = False,
) -> Tuple[Dict[str, float], List[str]]:
    """
    M03 ApplySessionCap step.

    Limits each scenario's shift from prior to +/- 25pp unless
    SignalConvergence is documented (3+ T1 signals within 72h).

    Parameters
    ----------
    derived:
        Output of apply_floors() — probabilities summing to 100%.
    prior:
        Prior ScenarioProbabilities from SessionLogState.latest_probs.
        None → cap not applicable (initial derivation or prior > 7 days old).
    signal_convergence_documented:
        True when ≥3 independent T1 signals confirm same direction within 72h.
        Allows full derived shift (no cap applied).

    Returns
    -------
    (capped_probs, flags)
    capped_probs: probability dict summing to 100%
    flags: list of cap-applied messages (empty if no cap triggered)
    """
    flags: List[str] = []

    if prior is None:
        flags.append(
            "25pp session cap: not applicable (no recent §8 entry — initial derivation)"
        )
        return dict(derived), flags

    prior_dict = {s: getattr(prior, s) for s in ("A", "B", "C", "D", "E", "F")}
    probs = dict(derived)
    any_capped = False

    for s in ("A", "B", "C", "D", "E", "F"):
        delta = probs[s] - prior_dict[s]
        if abs(delta) > _SESSION_CAP_PP:
            if signal_convergence_documented:
                # Allow full shift — log it
                flags.append(
                    f"Scenario {s}: shift {delta:+.1f}pp allowed (SignalConvergence documented)"
                )
            else:
                direction = 1 if delta > 0 else -1
                capped = prior_dict[s] + direction * _SESSION_CAP_PP
                flags.append(
                    f"25pp session cap applied to {s}: "
                    f"derived {probs[s]:.1f}% | prior {prior_dict[s]:.1f}% | "
                    f"capped at {capped:.1f}%. "
                    f"Full shift requires SignalConvergence: 3+ T1 signals within 72h."
                )
                probs[s] = capped
                any_capped = True

    if any_capped:
        probs = _renormalize(probs)
        _verify_sum(probs, context="apply_session_cap")

    return probs, flags


# ── B vs C constraint check ────────────────────────────────────────────────────

def check_b_vs_c(probs: Dict[str, float]) -> Optional[str]:
    """
    M03 CheckBvsC: return warning string if B > 30% AND C > 30%, else None.
    Caller must document justification in session briefing when this fires.
    """
    b = probs.get("B", 0.0)
    c = probs.get("C", 0.0)
    if b > _B_C_CONSTRAINT and c > _B_C_CONSTRAINT:
        return (
            f"B vs C constraint: B={b:.1f}% AND C={c:.1f}% both > {_B_C_CONSTRAINT:.0f}%. "
            f"REQUIRED: explicit documented justification in session briefing per M03.BvsCRule."
        )
    return None


# ── Full pipeline ──────────────────────────────────────────────────────────────

def apply_all_rules(
    raw: RawScores,
    prior: Optional[ScenarioProbabilities],
    *,
    hy_recession_pricing_fired: bool = False,
    signal_convergence_documented: bool = False,
) -> Tuple[ScenarioProbabilities, List[str]]:
    """
    Execute the full M03 DeriveScenarioProbabilities arithmetic pipeline:
      1. Normalize
      2. ApplyFloors
      3. ApplySessionCap
      4. CheckBvsC (surfaces warning in flags; does not block)
      5. Return ScenarioProbabilities + diagnostic flags

    Parameters
    ----------
    raw:
        Scenario raw scores from ScoringAnswers (AI fills; Python sums by check).
    prior:
        Prior ScenarioProbabilities from SessionLogState.latest_probs.
        Pass None for initial derivation (cap not applicable).
    hy_recession_pricing_fired:
        True when M11.HY_RecessionPricing threshold has fired.
        Activates D structural floor at 25%.
    signal_convergence_documented:
        True when ≥3 T1 signals confirm direction within 72h (M03.SignalConvergence).

    Returns
    -------
    (ScenarioProbabilities, flags)

    Raises
    ------
    HardStopException if raw total is 0.
    """
    all_flags: List[str] = []

    base    = normalize_scores(raw)
    floored = apply_floors(base, hy_recession_pricing_fired=hy_recession_pricing_fired)
    capped, cap_flags = apply_session_cap(
        floored, prior, signal_convergence_documented=signal_convergence_documented
    )
    all_flags.extend(cap_flags)

    b_vs_c_warning = check_b_vs_c(capped)
    if b_vs_c_warning:
        all_flags.append(b_vs_c_warning)

    probs = ScenarioProbabilities(
        A=round(capped["A"], 4),
        B=round(capped["B"], 4),
        C=round(capped["C"], 4),
        D=round(capped["D"], 4),
        E=round(capped["E"], 4),
        F=round(capped["F"], 4),
    )
    return probs, all_flags


# ── Private helpers ────────────────────────────────────────────────────────────

def _renormalize(probs: Dict[str, float]) -> Dict[str, float]:
    """Re-scale all values so they sum to 100.0."""
    total = sum(probs.values())
    if total == 0:
        raise HardStopException(
            "HARD_STOP — _renormalize: probability total is 0 after cap application"
        )
    factor = 100.0 / total
    return {s: p * factor for s, p in probs.items()}


def _verify_sum(probs: Dict[str, float], context: str = "") -> None:
    """Raise HardStopException if probabilities do not sum to 100% within tolerance."""
    total = sum(probs.values())
    if abs(total - 100.0) > 0.05:
        raise HardStopException(
            f"HARD_STOP — {context}: probabilities sum to {total:.4f}% (expected 100.0%). "
            "Internal arithmetic error — review apply_floors / apply_session_cap."
        )
