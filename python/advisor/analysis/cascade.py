"""
analysis/cascade.py — M17 systemic cascade early warning.

Maps to: M17_SystemicCascadeWarning.md MODULE SystemicCascadeWarning

Three public functions:
  sector_stress_score()      → int 0–3 (M17 §2)
  compute_yield_curve_signal() → YieldCurveSignal (M17 §3)
  assess_cascade_level()     → CascadeSignal (M17 §5 + §4)

NEVER routes signals into M03.DeriveScenarioProbabilities().
CHAIN_4 score contribution = 0 until T1 AACER/PACER source confirmed (per M17 NEVER list).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..types import (
    CalibrationState,
    CascadeLevel,
    CascadeSignal,
    CreditSignal,
    CurveState,
    DataReading,
    DTimingSignal,
    EPathwayType,
    EWatchFlag,
    YieldCurveSignal,
)
from ._utils import get_history, get_scalar


# ── §2 Sector Stress Score ─────────────────────────────────────────────────────

def sector_stress_score(
    readings: Dict[str, DataReading],
    cal: CalibrationState,
    *,
    chain_4_t1_confirmed: bool = False,
) -> tuple[int, Dict[str, bool], Dict[str, bool], List[str]]:
    """
    M17 §2 sectorStressScore().

    Returns
    -------
    (score, chain_fires, chain_watch, quality_flags)

    score         : int 0–3 (capped at 3)
    chain_fires   : dict "CHAIN_1".."CHAIN_4" → True if that chain fires (+1 score)
    chain_watch   : dict "CHAIN_3" → True if WATCH (record loaded; not firing)
    quality_flags : data gap / partial evaluation messages

    Notes
    -----
    CHAIN_4 score contribution is always 0 until chain_4_t1_confirmed=True,
    per M17 NEVER: score_Chain_4_without_T1_source.
    Pass chain_4_t1_confirmed=True when ABI/Epiq AACER data has been verified as T1.
    """
    flags: List[str]      = []
    fires: Dict[str, bool] = {f"CHAIN_{i}": False for i in range(1, 5)}
    watch: Dict[str, bool] = {"CHAIN_3": False}
    c = cal.cascade
    score = 0

    # ── CHAIN_1 — Agriculture / Fertilizer ────────────────────────────────────
    farm_yoy_r    = readings.get("FARM_FILINGS_YOY")
    natgas_r      = readings.get("NATGAS_HENRY_HUB") or readings.get("NATURAL_GAS")
    farm_yoy      = get_scalar(farm_yoy_r,  flags, "FARM_FILINGS_YOY")
    natgas        = get_scalar(natgas_r,    flags, "NATGAS_HENRY_HUB")

    if farm_yoy is not None:
        farm_alert = farm_yoy >= c.farm_filings_alert_pct
        natgas_alert = natgas is not None and natgas >= c.natgas_alert_price
        # fertilizer_alert requires qualitative input (USDA/DTN) — not in automated readings
        if farm_alert and natgas_alert:
            fires["CHAIN_1"] = True
            score += 1
        elif farm_alert:
            flags.append(
                f"CHAIN_1: farm filings +{farm_yoy:.0f}% YoY (alert: +{c.farm_filings_alert_pct:.0f}%) "
                f"but natgas {'unavailable' if natgas is None else f'${natgas:.2f} < ${c.natgas_alert_price:.2f}'} "
                f"— CHAIN_1 NOT fired"
            )
    else:
        flags.append("FARM_FILINGS_YOY: unavailable — CHAIN_1 cannot be scored")

    # ── CHAIN_2 — CRE / Regional Bank ─────────────────────────────────────────
    # Requires KRE vs SPX 90d relative performance + SOFR-DFF spread
    kre_r    = readings.get("KRE")
    sp500_r  = readings.get("BROAD_EQUITY_TRAILING") or readings.get("SP500")
    sofr_r   = readings.get("SOFR")
    dff_r    = readings.get("DFF")

    sofr = get_scalar(sofr_r, flags, "SOFR")
    dff  = get_scalar(dff_r,  flags, "DFF")

    kre_90d_return  = _extract_trailing_return(kre_r,   "KRE",   90, flags)
    spx_90d_return  = _extract_trailing_return(sp500_r, "SP500", 90, flags)

    chain2_fires = False
    if kre_90d_return is not None and spx_90d_return is not None:
        kre_vs_spx = (kre_90d_return - spx_90d_return) * 100.0  # pp (percentage points)
        kre_underperf = kre_vs_spx <= -c.kre_vs_spx_alert_pct   # alert threshold is positive e.g. 15
        if sofr is not None and dff is not None:
            sofr_dff_bps = (sofr - dff) * 100.0                 # convert % to bps
            sofr_alert   = sofr_dff_bps >= c.sofr_dff_alert_bps
            if kre_underperf and sofr_alert:
                fires["CHAIN_2"] = True
                score += 1
                chain2_fires = True
            elif kre_underperf:
                flags.append(
                    f"CHAIN_2: KRE vs SPX 90d = {kre_vs_spx:.1f}pp (alert: <-{c.kre_vs_spx_alert_pct:.0f}pp) "
                    f"but SOFR-DFF = {sofr_dff_bps:.0f}bps (alert: ≥{c.sofr_dff_alert_bps:.0f}bps) — NOT fired"
                )
        else:
            flags.append("SOFR or DFF: unavailable — CHAIN_2 SOFR-DFF condition cannot be evaluated")
    elif kre_90d_return is None or spx_90d_return is None:
        flags.append("KRE or SP500 90d returns unavailable — CHAIN_2 KRE relative performance cannot be scored")

    # ── CHAIN_3 — Private Credit / Margin Cascade (two-mode, M17 v1.3) ────────
    margin_r = readings.get("FINRA_MARGIN_DEBT")

    chain3_watch = False
    chain3_fires = False

    if margin_r and margin_r.is_valid:
        v = margin_r.value
        margin_current: Optional[float] = None
        margin_mom_pct: Optional[float] = None
        at_record:      Optional[bool]  = None

        if isinstance(v, dict):
            margin_current = v.get("current") or v.get("value")
            margin_mom_pct = v.get("mom_pct") or v.get("mom_change_pct")
            at_record      = v.get("at_nominal_record")
        else:
            try:
                margin_current = float(v)
            except (TypeError, ValueError):
                pass

        # Mode 1 WATCH: margin at nominal record
        if at_record is True:
            chain3_watch = True
            watch["CHAIN_3"] = True
            flags.append("CHAIN_3 WATCH: FINRA margin debt at all-time nominal record — precursor loaded")

        # Mode 2 FIRES: MoM decline ≥ threshold after record
        if margin_mom_pct is not None:
            if margin_mom_pct <= c.margin_mom_decline_pct:
                chain3_fires = True
                fires["CHAIN_3"] = True
                score += 1
                flags.append(
                    f"CHAIN_3 FIRES: margin debt MoM change {margin_mom_pct:.1f}% "
                    f"≤ {c.margin_mom_decline_pct:.1f}% threshold — cascade onset signal"
                )
        else:
            flags.append("CHAIN_3: margin MoM change unavailable — FIRES condition cannot be evaluated for MoM mode")
    else:
        flags.append("FINRA_MARGIN_DEBT: unavailable — CHAIN_3 cannot be scored")

    # Gate count mode (qualitative — must be passed in as dict value)
    if margin_r and isinstance(margin_r.value, dict):
        gate_count = margin_r.value.get("gate_count_90d")
        if gate_count is not None and int(gate_count) >= c.gate_count_alert:
            if not fires["CHAIN_3"]:
                fires["CHAIN_3"] = True
                score += 1
            chain3_fires = True
            flags.append(
                f"CHAIN_3 FIRES: {int(gate_count)} redemption gate/suspension events "
                f"≥ {c.gate_count_alert} threshold in 90 days"
            )

    # ── CHAIN_4 — Manufacturing / Corporate Stress ────────────────────────────
    # Score contribution = 0 until T1 AACER/PACER source confirmed
    # ABI/Epiq AACER press releases qualify as T1-equivalent per §12.4 v1.24
    if chain_4_t1_confirmed:
        bankrupt_r = readings.get("CORP_BANKRUPTCY_QUARTERLY")
        bankrupt_q = get_scalar(bankrupt_r, flags, "CORP_BANKRUPTCY_QUARTERLY")
        if bankrupt_q is not None:
            if bankrupt_q >= c.bankruptcy_fires_quarterly:
                fires["CHAIN_4"] = True
                score += 1
            elif bankrupt_q >= c.bankruptcy_watch_quarterly:
                flags.append(
                    f"CHAIN_4 WATCH: {bankrupt_q:.0f}/quarter — "
                    f"above WATCH ({c.bankruptcy_watch_quarterly}) but below FIRES ({c.bankruptcy_fires_quarterly})"
                )
        else:
            flags.append("CORP_BANKRUPTCY_QUARTERLY: T1 confirmed but reading unavailable")
    else:
        flags.append(
            "CHAIN_4: T1 source not confirmed — score contribution = 0 "
            "(supply chain_4_t1_confirmed=True with ABI/Epiq AACER data to activate)"
        )

    final_score = min(score, 3)
    return final_score, fires, watch, flags


def _extract_trailing_return(
    reading: Optional[DataReading],
    label: str,
    window: int,
    flags: List[str],
) -> Optional[float]:
    """
    Extract a trailing pct return from a DataReading (as fraction).
    Looks for dict keys: change_{window}d, pct_{window}d, pct_change_{window}d.
    Falls back to computing from history list if available.
    """
    if reading is None or not reading.is_valid:
        flags.append(f"{label}: reading unavailable — {window}d return not available")
        return None
    v = reading.value
    if isinstance(v, dict):
        for key in (f"change_{window}d", f"pct_{window}d", f"pct_change_{window}d"):
            if key in v and v[key] is not None:
                return float(v[key])
        # Try history
        from ._utils import get_history, compute_pct_change
        hist = get_history(reading)
        result = compute_pct_change(hist, window, label, flags)
        if result is None:
            flags.append(f"{label}: {window}d return unavailable (no pre-computed key or sufficient history)")
        return result
    else:
        flags.append(f"{label}: scalar value — {window}d return requires dict or history")
        return None


# ── §3 Yield Curve Signal ──────────────────────────────────────────────────────

def compute_yield_curve_signal(
    readings: Dict[str, DataReading],
    cal: CalibrationState,
    credit_signal: Optional[CreditSignal] = None,
    *,
    prior_curve_was_inverted: bool = False,
    sovereign_cds_widening: bool = False,
) -> YieldCurveSignal:
    """
    M17 §3 computeYieldCurveSignal.

    Parameters
    ----------
    readings:
        Expected keys: YIELD_CURVE (dict with year2, year10, month3, year30),
        THREEFYTP10, DXY.
    cal:
        CalibrationState with §12.5 cascade thresholds.
    credit_signal:
        Optional — used for IG_TransmissionReached flag in e_pathway_type determination.
    prior_curve_was_inverted:
        True if the prior session yield curve state was INVERTED. Needed for
        RECESSION_ONSET_PATTERN detection (re-steepening after inversion).
    sovereign_cds_widening:
        Qualitative AI input — True if sovereign CDS spreads are widening significantly.
        Required for SYSTEMIC_LIQUIDITY pathway classification.

    Returns
    -------
    YieldCurveSignal. NEVER routes into M03 or feeds DeriveScenarioProbabilities().
    """
    flags: List[str] = []
    c = cal.cascade

    # ── Extract yield curve data ───────────────────────────────────────────────
    yc_r = readings.get("YIELD_CURVE")
    year2 = year10 = month3 = year30 = None

    if yc_r and yc_r.is_valid:
        v = yc_r.value
        if isinstance(v, dict):
            year2  = v.get("year2")
            year10 = v.get("year10")
            month3 = v.get("month3")
            year30 = v.get("year30")
            if year10 is None:
                flags.append("YIELD_CURVE: year10 missing — spread computations unavailable")
        else:
            flags.append("YIELD_CURVE: expected dict (year2/year10/month3/year30), got scalar")
    else:
        flags.append("YIELD_CURVE: reading unavailable — yield curve signal cannot be computed")

    # Spreads in bps (convert from percentage points if needed)
    def _bps(a: Optional[float], b: Optional[float]) -> Optional[float]:
        if a is not None and b is not None:
            diff = a - b
            # Values are in % (e.g. 4.5 = 4.5%); convert to bps
            return diff * 100.0
        return None

    spread_10y_2y = _bps(year10, year2)    # bps
    spread_10y_3m = _bps(year10, month3)   # bps

    # ── Curve shape ───────────────────────────────────────────────────────────
    curve_state: Optional[CurveState] = None
    if spread_10y_2y is not None and spread_10y_3m is not None:
        if spread_10y_2y < 0 and spread_10y_3m < 0:
            curve_state = CurveState.INVERTED
        elif spread_10y_2y < 0 or spread_10y_3m < 0:
            curve_state = CurveState.PARTIAL_INVERSION
        else:
            curve_state = CurveState.NORMAL_OR_STEEP
    elif spread_10y_2y is None:
        # yfinance fallback: only 10Y and 3M available
        if spread_10y_3m is not None:
            curve_state = (
                CurveState.INVERTED if spread_10y_3m < 0
                else CurveState.NORMAL_OR_STEEP
            )
            flags.append("YIELD_CURVE: year2 unavailable (yfinance fallback) — curve_state derived from 10Y-3M only")
    else:
        flags.append("YIELD_CURVE: insufficient data for curve_state determination")

    # ── D timing signal ───────────────────────────────────────────────────────
    d_timing = DTimingSignal.MONITORING
    d_timing_estimate: Optional[str] = None

    if curve_state == CurveState.INVERTED:
        d_timing = DTimingSignal.CURVE_INVERTED
    elif curve_state == CurveState.NORMAL_OR_STEEP and prior_curve_was_inverted:
        d_timing = DTimingSignal.RECESSION_ONSET_PATTERN
        d_timing_estimate = "0–12 months from re-steepening onset (5/6 post-inversion re-steepenings preceded recession)"
    # else MONITORING

    # ── Long-end elevation / E watch ─────────────────────────────────────────
    tp_r = readings.get("THREEFYTP10")
    term_premium = get_scalar(tp_r, flags, "THREEFYTP10")

    if term_premium is not None:
        # term_premium is in percent (e.g. 0.81 = 0.81%)
        # thresholds: c.e_term_premium_alert = bps (e.g. 150) → convert to %
        alert_pct   = c.e_term_premium_alert_bps   / 100.0
        warning_pct = c.e_term_premium_warning_bps / 100.0
        yr30_warn   = c.e_30y_warning_pct

        if term_premium >= alert_pct:
            e_watch = EWatchFlag.E_PATHWAY_WATCH
        elif (
            term_premium >= warning_pct
            and year30 is not None
            and year30 >= yr30_warn
        ):
            e_watch = EWatchFlag.FISCAL_STRESS_BUILDING
        else:
            e_watch = EWatchFlag.CLEAR
    else:
        e_watch = EWatchFlag.CLEAR
        flags.append("THREEFYTP10: unavailable — E_watch_flag cannot be computed; defaulted to CLEAR")

    # ── e_pathway_type determination (M17 v1.4) ───────────────────────────────
    dxy_r   = readings.get("DXY")
    dxy_hist = get_history(dxy_r)
    dxy_30d_change: Optional[float] = None
    if len(dxy_hist) >= 31:
        base = dxy_hist[-31]
        if base != 0:
            dxy_30d_change = (dxy_hist[-1] - base) / abs(base)
    elif dxy_r and dxy_r.is_valid:
        v = dxy_r.value
        if isinstance(v, dict):
            for key in ("change_30d", "pct_30d", "pct_change_30d"):
                if key in v and v[key] is not None:
                    dxy_30d_change = float(v[key])
                    break

    ig_transmission = (
        credit_signal is not None and credit_signal.ig_transmission_reached
    )

    e_pathway = _determine_pathway_type(
        dxy_30d_change=dxy_30d_change,
        ig_transmission=ig_transmission,
        sovereign_cds_widening=sovereign_cds_widening,
        flags=flags,
    )

    return YieldCurveSignal(
        spread_10y_2y=spread_10y_2y,
        spread_10y_3m=spread_10y_3m,
        curve_state=curve_state,
        d_timing_signal=d_timing,
        d_timing_estimate=d_timing_estimate,
        term_premium=term_premium,
        e_watch_flag=e_watch,
        yield_30y=year30,
        e_pathway_type=e_pathway,
        quality_flags=flags,
    )


def _determine_pathway_type(
    dxy_30d_change: Optional[float],
    ig_transmission: bool,
    sovereign_cds_widening: bool,
    flags: List[str],
) -> EPathwayType:
    """
    M17 v1.4 DeterminePathwayType rule.
    SYSTEMIC_LIQUIDITY: classic credit crisis (2008/LTCM — dollar strengthens, Treasuries rally).
    RESERVE_EROSION: de-dollarization analog (dollar weakens, Treasuries under pressure).
    """
    dxy_strengthening = (
        ig_transmission
        and sovereign_cds_widening
        and dxy_30d_change is not None
        and dxy_30d_change > 0
    )
    if dxy_strengthening:
        return EPathwayType.SYSTEMIC_LIQUIDITY

    if dxy_30d_change is not None:
        if dxy_30d_change < -0.03:                     # dollar weakening >3% / 30 days
            return EPathwayType.RESERVE_EROSION
        if dxy_30d_change > +0.03:                     # dollar strengthening >3% without IG convergence
            return EPathwayType.SYSTEMIC_LIQUIDITY

    # DXY flat (±3%) or unavailable → default RESERVE_EROSION (more protective directive set)
    flags.append(
        "e_pathway_type defaulted to RESERVE_EROSION "
        f"(DXY 30d change: {'unavailable' if dxy_30d_change is None else f'{dxy_30d_change:.1%}'} — "
        "insufficient signal to distinguish; revisit if DXY moves materially)"
    )
    return EPathwayType.RESERVE_EROSION


# ── §5 Cascade Level Assessment ───────────────────────────────────────────────

def assess_cascade_level(
    readings: Dict[str, DataReading],
    cal: CalibrationState,
    credit_signal: Optional[CreditSignal] = None,
    *,
    prior_curve_was_inverted: bool = False,
    sovereign_cds_widening: bool = False,
    chain_4_t1_confirmed: bool = False,
) -> CascadeSignal:
    """
    M17 §5 assessCascadeLevel — full cascade assessment in one call.

    Computes:
      - sector_stress_score() from chain analysis
      - compute_yield_curve_signal() for yield curve data
      - assessCascadeLevel() mapping: score + active_chains → CascadeLevel

    M17.assessCascadeLevel() logic:
      IF active_chains >= 3 OR M11_approaching → PRE_POSITION
      IF active_chains >= 2 OR formal_score >= 2 → ALERT
      ELSE MONITORING

    M11_approaching = HY_OAS > (trailing_180d_median + HY_STRESS_DELTA × 0.70)
    This requires credit_signal to be provided.
    """
    score, fires, watch, score_flags = sector_stress_score(
        readings, cal, chain_4_t1_confirmed=chain_4_t1_confirmed
    )

    yc_signal = compute_yield_curve_signal(
        readings, cal, credit_signal,
        prior_curve_was_inverted=prior_curve_was_inverted,
        sovereign_cds_widening=sovereign_cds_widening,
    )

    active_chains = sum(1 for v in fires.values() if v)

    # M11_approaching check
    m11_approaching = False
    if (
        credit_signal is not None
        and credit_signal.hy_oas is not None
        and credit_signal.hy_median_180d is not None
    ):
        t = cal.thresholds
        m11_threshold_70pct = credit_signal.hy_median_180d + t.hy_stress_delta * 0.70
        m11_approaching = credit_signal.hy_oas > m11_threshold_70pct

    # CascadeLevel mapping
    if active_chains >= 3 or m11_approaching:
        level = CascadeLevel.PRE_POSITION
    elif active_chains >= 2 or score >= 2:
        level = CascadeLevel.ALERT
    else:
        level = CascadeLevel.MONITORING

    all_flags = score_flags + yc_signal.quality_flags
    # Deduplicate flags preserving order
    seen: set = set()
    deduped = []
    for f in all_flags:
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    return CascadeSignal(
        level=level,
        sector_stress_score=score,
        chain_fires=fires,
        chain_watch=watch,
        active_chains_count=active_chains,
        yield_curve=yc_signal,
        quality_flags=deduped,
    )
