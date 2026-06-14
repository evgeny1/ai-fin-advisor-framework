"""
analysis/credit.py — M11 CreditSignal computation.

Maps to: M11_CreditAndCalibration.md MODULE CreditSignal

All threshold values loaded from CalibrationState. No hard-coded constants.
Threshold checks requiring 180d history or 60d velocity data degrade gracefully
when history is absent — the check is conservatively set to False and flagged.

Velocity overlays (HY: +100bps/60d; IG: +40bps/60d) are FIXED STRUCTURAL RULES
— they are NOT calibration-dated. Sustain periods (10 trading days) are also fixed.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..types import CalibrationState, CreditSignal, DataReading
from ._utils import (
    compute_change,
    compute_median,
    get_history,
    get_scalar,
)

# ── Fixed structural constants (M11 — not calibration-dated) ──────────────────
_HY_VELOCITY_BPS  = 100   # bps / 60 trading days
_IG_VELOCITY_BPS  =  40   # bps / 60 trading days
_VELOCITY_WINDOW  =  60   # trading days
_SUSTAIN_DAYS     =  10   # trading days
_MEDIAN_WINDOW    = 180   # calendar days (FRED series; close to 130 trading days)


def compute_credit_signal(
    readings: Dict[str, DataReading],
    cal: CalibrationState,
    *,
    hy_sustain_days: int = 0,
    ig_sustain_days: int = 0,
) -> CreditSignal:
    """
    M11 CreditSignal.

    Parameters
    ----------
    readings:
        Dict keyed by M18 spec_id.  Expected keys: HY_OAS, IG_OAS, CCC_OAS, MOVE.
        Each reading.value may be:
          - float/int  → current value only
          - dict       → {"current": float, "history": List[float]} (oldest-first)
                         The history list is used for median and velocity computations.
    cal:
        CalibrationState with credit thresholds.
    hy_sustain_days:
        Trading days HY OAS has been above the stress threshold. Supply from
        SessionLogState or inter-session tracking. Defaults to 0 (conservative).
    ig_sustain_days:
        Same for IG. Defaults to 0 (conservative).

    Returns
    -------
    CreditSignal with threshold flags, convergence text, and quality_flags.
    """
    flags: List[str] = []
    t = cal.thresholds

    # ── 1. Extract current values ──────────────────────────────────────────────
    hy_current  = get_scalar(readings.get("HY_OAS"),  flags, "HY_OAS")
    ig_current  = get_scalar(readings.get("IG_OAS"),  flags, "IG_OAS")
    ccc_current = get_scalar(readings.get("CCC_OAS"), flags, "CCC_OAS")
    move_val    = get_scalar(readings.get("MOVE"),    flags, "MOVE")

    # ── 2. Extract history lists ───────────────────────────────────────────────
    hy_hist  = get_history(readings.get("HY_OAS"))
    ig_hist  = get_history(readings.get("IG_OAS"))
    ccc_hist = get_history(readings.get("CCC_OAS"))

    # ── 3. Compute 180d trailing medians ──────────────────────────────────────
    hy_median  = compute_median(hy_hist,  _MEDIAN_WINDOW, "HY_OAS",  flags)
    ig_median  = compute_median(ig_hist,  _MEDIAN_WINDOW, "IG_OAS",  flags)

    # ── 4. Velocity computations (bps change over prior 60 trading days) ──────
    hy_vel_60d  = compute_change(hy_hist,  _VELOCITY_WINDOW, "HY_OAS 60d velocity",  flags)
    ig_vel_60d  = compute_change(ig_hist,  _VELOCITY_WINDOW, "IG_OAS 60d velocity",  flags)
    ccc_vel_30d = compute_change(ccc_hist, 30, "CCC_OAS 30d change", flags)
    hy_vel_30d  = compute_change(hy_hist,  30, "HY_OAS 30d change",  flags)

    # ── 5. M11 threshold evaluation ───────────────────────────────────────────
    #
    # Guard: when 180d median or velocity unavailable, threshold = False (conservative).
    # All conditions require T1 source — flagged in quality_flags when history absent.

    # HY_StressBeginning
    hy_stress = False
    if hy_current is not None and hy_median is not None:
        above_stress = hy_current > (hy_median + t.hy_stress_delta)
        vel_met      = hy_vel_60d is not None and hy_vel_60d >= _HY_VELOCITY_BPS
        sustained    = hy_sustain_days >= _SUSTAIN_DAYS
        if above_stress and vel_met and sustained:
            hy_stress = True
        elif above_stress:
            parts = []
            if not vel_met:
                parts.append(
                    f"velocity {'unconfirmed (history absent)' if hy_vel_60d is None else f'={hy_vel_60d:.0f}bps < {_HY_VELOCITY_BPS}'}"
                )
            if not sustained:
                parts.append(f"sustain {hy_sustain_days}/{_SUSTAIN_DAYS} days")
            flags.append(
                f"HY_OAS above median+{t.hy_stress_delta}bps: {hy_current:.0f} vs {hy_median:.0f}+{t.hy_stress_delta} "
                f"— threshold NOT fired: {'; '.join(parts)}"
            )
    elif hy_current is not None:
        flags.append("HY_StressBeginning: 180d median unavailable — cannot evaluate")

    # HY_RecessionPricing (no velocity overlay; sustain still required)
    hy_recession = False
    if hy_current is not None and hy_median is not None:
        above_recession = hy_current > (hy_median + t.hy_recession_delta)
        sustained       = hy_sustain_days >= _SUSTAIN_DAYS
        if above_recession and sustained:
            hy_recession = True
        elif above_recession:
            flags.append(
                f"HY_OAS above median+{t.hy_recession_delta}bps: {hy_current:.0f} vs {hy_median:.0f}+{t.hy_recession_delta} "
                f"— sustain not confirmed ({hy_sustain_days}/{_SUSTAIN_DAYS} days)"
            )
    elif hy_current is not None:
        flags.append("HY_RecessionPricing: 180d median unavailable — cannot evaluate")

    # IG_TransmissionReached
    ig_transmission = False
    if ig_current is not None and ig_median is not None:
        above_ig  = ig_current > (ig_median + t.ig_transmission_delta)
        vel_met   = ig_vel_60d is not None and ig_vel_60d >= _IG_VELOCITY_BPS
        sustained = ig_sustain_days >= _SUSTAIN_DAYS
        if above_ig and vel_met and sustained:
            ig_transmission = True
        elif above_ig:
            parts = []
            if not vel_met:
                parts.append(
                    f"velocity {'unconfirmed (history absent)' if ig_vel_60d is None else f'={ig_vel_60d:.0f}bps < {_IG_VELOCITY_BPS}'}"
                )
            if not sustained:
                parts.append(f"sustain {ig_sustain_days}/{_SUSTAIN_DAYS} days")
            flags.append(
                f"IG_OAS above median+{t.ig_transmission_delta}bps: {ig_current:.0f} vs {ig_median:.0f}+{t.ig_transmission_delta} "
                f"— threshold NOT fired: {'; '.join(parts)}"
            )
    elif ig_current is not None:
        flags.append("IG_TransmissionReached: 180d median unavailable — cannot evaluate")

    # CCC_TailFirstWidening (monitoring flag — does not affect D floor alone)
    ccc_widening = False
    if ccc_vel_30d is not None and hy_vel_30d is not None:
        # Mode 1: CCC widens t.ccc_ratio_multiplier × HY composite over 30d
        ratio_met = (
            hy_vel_30d > 0
            and ccc_vel_30d >= t.ccc_ratio_multiplier * hy_vel_30d
        )
        # Mode 2: CCC +≥ t.ccc_absolute_floor_bps while composite +< t.ccc_composite_ceiling_bps
        absolute_met = (
            ccc_vel_30d >= t.ccc_absolute_floor_bps
            and hy_vel_30d < t.ccc_composite_ceiling_bps
        )
        ccc_widening = ratio_met or absolute_met
    elif ccc_vel_30d is None or hy_vel_30d is None:
        flags.append("CCC_TailFirstWidening: 30d velocity data unavailable — cannot evaluate")

    # ── 6. SignalConvergenceTest text ─────────────────────────────────────────
    convergence = _convergence_text(
        hy_current, hy_median, ig_current, ig_median,
        hy_stress, hy_recession, ig_transmission, ccc_widening,
    )

    return CreditSignal(
        hy_oas=hy_current,
        hy_median_180d=hy_median,
        ig_oas=ig_current,
        ig_median_180d=ig_median,
        ccc_oas=ccc_current,
        move=move_val,
        hy_stress_beginning=hy_stress,
        hy_recession_pricing=hy_recession,
        ig_transmission_reached=ig_transmission,
        ccc_tail_first_widening=ccc_widening,
        convergence_text=convergence,
        quality_flags=flags,
    )


def _convergence_text(
    hy: Optional[float], hy_med: Optional[float],
    ig: Optional[float], ig_med: Optional[float],
    hy_stress: bool, hy_recession: bool,
    ig_transmission: bool, ccc_widening: bool,
) -> str:
    """M11.SignalConvergenceTest — returns one-sentence narrative."""
    if hy_transmission := ig_transmission:   # alias for readability
        return "IG transmission reached — recession/credit-event pricing has spread to investment grade."
    if hy_recession:
        return "HY recession pricing confirmed — D probability floor of 25% applies."
    if hy_stress:
        return "Institutional credit dissenting from retail equity bid — HY stress beginning; monitor IG."
    if ccc_widening:
        return "Early-stage stress hidden by aggregation — CCC widening materially while HY composite calm."
    if hy is not None and ig is not None and hy_med is not None and ig_med is not None:
        if hy <= hy_med and ig <= ig_med:
            return "Credit endorses current equity regime — HY and IG calm or tightening vs 180d median."
        if hy > hy_med or ig > ig_med:
            return "Credit spreads above 180d median but below formal stress thresholds — monitoring."
    return "Credit signal assessment incomplete — 180d median history unavailable for threshold checks."
