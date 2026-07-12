"""
analysis/regime.py — M14 market regime divergence signal and entry extension guard.

Maps to: M14_MarketRegime.md MODULE MarketRegimeDiscipline

ComputeDivergenceSignal():
  - commodity_fear_divergence: Brent 90-calendar-day change vs VIX change from rolling avg
  - equity_scenario_divergence: SPX 30-trading-day change while directive is reductive
  - composite: HIGH if either component is HIGH; MODERATE if either is MODERATE
  - conflict_duration_days (ENG-20): when > 90, also computes energy_180d and uses the
    higher of the two readings for classification (M14 EXTENDED CONFLICT CAVEAT)

EntryExtensionGuard():
  - Checks whether current price is >= threshold% above trailing average
  - Returns PASS | HALT | EXEMPT per role thresholds
  - All thresholds loaded from CalibrationState.regime.entry_extension_thresholds
  - Thresholds stored as percentages (15.0 = 15%); appreciation computed as fraction

NEVER feeds output into M03.DeriveScenarioProbabilities().
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..exceptions import HardStopException
from ..types import (
    CalibrationState,
    DataReading,
    DivergenceLevel,
    DivergenceSignal,
    GuardResult,
    GuardStatus,
    InstrumentRepricingWarning,
)
from ._utils import get_history, get_scalar, compute_pct_change

_REDUCTIVE_DIRECTIVES = frozenset({
    "Reduce", "REDUCE",
    "reduce_to_minimumConvictionWeight", "reduce_to minimumConvictionWeight()",
    "TRIM", "Trim",
    "EXIT", "Exit", "EXIT_INITIATED",
})


def compute_divergence_signal(
    readings: Dict[str, DataReading],
    cal: CalibrationState,
    *,
    equity_directive_for_dominant_scenario: Optional[str] = None,
    conflict_duration_days: Optional[int] = None,
) -> DivergenceSignal:
    """
    M14.ComputeDivergenceSignal.

    Window definitions:
      energy_90d:       90 CALENDAR DAYS — Brent pct change
      broad_equity_30d: 30 TRADING DAYS  — SPX/VTI pct change

    Parameters
    ----------
    readings:
        Expected keys: BRENT_CRUDE, VIX, VIX_90D_AVG, BROAD_EQUITY_TRAILING.
        BRENT_CRUDE.value may be float (current only) or dict (with history or pre-computed change).
        BROAD_EQUITY_TRAILING.value may be dict {"change_30d": float} or float (current only).
    cal:
        CalibrationState with regime thresholds (stored as percentages 0–100).
    equity_directive_for_dominant_scenario:
        M09/M10 directive for broad_market_equity_domestic in the current dominant scenario.
        None → equity_scenario_divergence = NOT_APPLICABLE.
    conflict_duration_days:
        Days since T1-confirmed onset of an active discrete supply event (e.g. Hormuz
        closure). Caller is responsible for supplying this — mirrors the same
        caller-responsibility convention as entry_extension_guard()'s parameter of the
        same name. When > 90, both endpoints of the energy_90d window fall inside the
        conflict period and the 90d signal may understate a sustained war premium
        (ENG-20 / M14 EXTENDED CONFLICT CAVEAT). In that case, energy_180d is also
        computed (same formula, 180 calendar days) and the higher of the two readings
        is used for commodity_fear_divergence classification. Both readings are always
        reported on the returned DivergenceSignal. None (default) → 90d-only behavior,
        unchanged from before this parameter existed.

    Returns
    -------
    DivergenceSignal. NEVER route composite into M03 probability derivation.
    """
    flags: List[str] = []
    r = cal.regime

    # ── Brent 90d change ──────────────────────────────────────────────────────
    brent_r  = readings.get("BRENT_CRUDE")
    energy_90d_change: Optional[float] = None

    if brent_r and brent_r.is_valid:
        v = brent_r.value
        if isinstance(v, dict):
            for key in ("change_90d", "pct_change_90d", "pct_90d"):
                if key in v and v[key] is not None:
                    energy_90d_change = float(v[key])
                    break
            if energy_90d_change is None:
                hist = get_history(brent_r)
                energy_90d_change = compute_pct_change(hist, 90, "BRENT_CRUDE", flags)
        else:
            hist = get_history(brent_r)
            energy_90d_change = compute_pct_change(hist, 90, "BRENT_CRUDE", flags)
            if energy_90d_change is None:
                flags.append(
                    "BRENT_CRUDE: point-in-time only — 90d change unavailable; "
                    "commodity_fear_divergence cannot be computed"
                )
    else:
        flags.append("BRENT_CRUDE: reading unavailable — commodity_fear_divergence cannot be computed")

    # ── Extended conflict caveat (ENG-20): energy_180d fallback ────────────────
    # When the active discrete supply event has run > 90 calendar days, both
    # endpoints of the 90d window are war-elevated and the signal may understate
    # the sustained premium. Compute energy_180d as supplemental context and use
    # the higher of the two readings for classification. @see M14_MarketRegime.md
    # EXTENDED CONFLICT CAVEAT.
    energy_180d_change: Optional[float] = None
    energy_change_for_classification = energy_90d_change

    if conflict_duration_days is not None and conflict_duration_days > 90:
        if brent_r and brent_r.is_valid:
            hist_180 = get_history(brent_r)
            energy_180d_change = compute_pct_change(hist_180, 180, "BRENT_CRUDE_180D", flags)
        if energy_180d_change is not None:
            if energy_90d_change is None or energy_180d_change > energy_90d_change:
                energy_change_for_classification = energy_180d_change
            flags.append(
                f"⚠ Conflict > 90d ({conflict_duration_days}d): energy_90d may understate "
                f"war premium — 180d: {energy_180d_change:.1%}"
            )
        else:
            flags.append(
                f"Conflict > 90d ({conflict_duration_days}d) — energy_180d fallback requested "
                "but insufficient BRENT_CRUDE history to compute (need 181+ daily points)."
            )

    # ── VIX change from 90d rolling average ───────────────────────────────────
    vix_current = get_scalar(readings.get("VIX"),        flags, "VIX")
    vix_90d_avg = get_scalar(readings.get("VIX_90D_AVG"), flags, "VIX_90D_AVG")
    vix_change_90d: Optional[float] = None
    if vix_current is not None and vix_90d_avg is not None:
        vix_change_90d = vix_current - vix_90d_avg
    elif vix_current is not None:
        flags.append("VIX_90D_AVG: unavailable — commodity_fear_divergence VIX component missing")

    # ── Broad equity 30d change ────────────────────────────────────────────────
    equity_r = readings.get("BROAD_EQUITY_TRAILING")
    broad_equity_30d: Optional[float] = None
    if equity_r and equity_r.is_valid:
        v = equity_r.value
        if isinstance(v, dict):
            # "return_30d_pct" is the actual key both fetch_broad_equity_trailing()
            # implementations (fmp_fetcher.py, yfinance_fetcher.py) produce, as a
            # percentage number (e.g. 2.56 == 2.56%) -- needs /100 to become the
            # fraction this function's threshold comparisons expect (equity_div_HIGH_pct
            # etc. are likewise divided by 100 before comparison). Root cause of
            # RoleRepricingDivergence silently skipping every session: this key was
            # never checked for, so broad_equity_30d fell through to a history-based
            # fallback that also can't succeed (this reading has no attached series).
            if "return_30d_pct" in v and v["return_30d_pct"] is not None:
                broad_equity_30d = float(v["return_30d_pct"]) / 100.0
            else:
                # Alternate shapes no fetcher has ever actually produced; kept for
                # compatibility. Assumed already a fraction (no "_pct" suffix).
                for key in ("change_30d", "pct_30d", "pct_change_30d"):
                    if key in v and v[key] is not None:
                        broad_equity_30d = float(v[key])
                        break
            if broad_equity_30d is None:
                hist = get_history(equity_r)
                broad_equity_30d = compute_pct_change(hist, 30, "BROAD_EQUITY_TRAILING", flags)
        else:
            hist = get_history(equity_r)
            broad_equity_30d = compute_pct_change(hist, 30, "BROAD_EQUITY_TRAILING", flags)
    else:
        flags.append(
            "BROAD_EQUITY_TRAILING: unavailable — equity_scenario_divergence cannot be computed"
        )

    # ── Commodity fear divergence ──────────────────────────────────────────────
    commodity_fear = DivergenceLevel.NONE
    if energy_change_for_classification is not None and vix_change_90d is not None:
        e_high_thresh = r.commodity_fear_HIGH_energy_pct / 100.0
        e_mod_thresh  = r.commodity_fear_MOD_energy_pct  / 100.0
        v_high_thresh = r.commodity_fear_HIGH_vix_change
        v_mod_thresh  = r.commodity_fear_MOD_vix_change

        if energy_change_for_classification >= e_high_thresh and vix_change_90d <= v_high_thresh:
            commodity_fear = DivergenceLevel.HIGH
        elif energy_change_for_classification >= e_mod_thresh and vix_change_90d <= v_mod_thresh:
            commodity_fear = DivergenceLevel.MODERATE

    # ── Equity scenario divergence ────────────────────────────────────────────
    equity_div = DivergenceLevel.NOT_APPLICABLE
    if equity_directive_for_dominant_scenario in _REDUCTIVE_DIRECTIVES:
        if broad_equity_30d is not None:
            e_high_pct = r.equity_div_HIGH_pct / 100.0
            e_mod_pct  = r.equity_div_MOD_pct  / 100.0
            if broad_equity_30d >= e_high_pct:
                equity_div = DivergenceLevel.HIGH
            elif broad_equity_30d >= e_mod_pct:
                equity_div = DivergenceLevel.MODERATE
            else:
                equity_div = DivergenceLevel.NONE
        else:
            equity_div = DivergenceLevel.NONE
            flags.append(
                "BROAD_EQUITY_TRAILING: history unavailable — "
                "equity_scenario_divergence treated as NONE (conservative)"
            )

    # ── Composite ─────────────────────────────────────────────────────────────
    if commodity_fear == DivergenceLevel.HIGH or equity_div == DivergenceLevel.HIGH:
        composite = DivergenceLevel.HIGH
    elif commodity_fear == DivergenceLevel.MODERATE or equity_div == DivergenceLevel.MODERATE:
        composite = DivergenceLevel.MODERATE
    else:
        composite = DivergenceLevel.NONE

    return DivergenceSignal(
        commodity_fear_divergence=commodity_fear,
        equity_scenario_divergence=equity_div,
        composite=composite,
        energy_90d_change=energy_90d_change,
        energy_180d_change=energy_180d_change,
        vix_change_90d_pts=vix_change_90d,
        broad_equity_30d=broad_equity_30d,
        quality_flags=flags,
    )


def entry_extension_guard(
    ticker: str,
    cal: CalibrationState,
    *,
    current_price: float,
    trailing_avg: Optional[float],
    trailing_90d_avg: Optional[float] = None,  # deprecated alias
    window_days: int = 90,
    conflict_duration_days: Optional[int] = None,
) -> GuardStatus:
    """
    M14.EntryExtensionGuard for one ticker.

    Parameters
    ----------
    ticker : str
    cal : CalibrationState
    current_price : float
        Current market price (T1 source).
    trailing_avg : Optional[float]
        Trailing average price over window_days. None → HALT (cannot confirm clear).
    trailing_90d_avg : Optional[float]
        Deprecated alias for trailing_avg.
    window_days : int
        Calendar days used to compute trailing_avg. Default 90; use 180 when conflict
        duration exceeds 90 days (all instruments; caller is responsible for the switch).
    conflict_duration_days : Optional[int]
        Days since T1-confirmed conflict onset. When > 90 and window_days < 180,
        a flag is emitted noting the baseline may be war-elevated.
    """
    flags: List[str] = []

    effective_avg = trailing_avg if trailing_avg is not None else trailing_90d_avg

    # When conflict > 90d the trailing baseline is war-contaminated; caller should switch to 180d.
    if conflict_duration_days is not None and conflict_duration_days > 90 and window_days < 180:
        flags.append(
            f"{ticker}: conflict {conflict_duration_days}d — expected 180d avg, received {window_days}d"
        )

    entry = cal.instruments.get(ticker)
    if entry is None:
        raise HardStopException(
            f"EntryExtensionGuard: {ticker} not in instrument table. "
            "ValidateClassifications should have caught this."
        )

    if not entry.components:
        flags.append(f"{ticker}: no components — guard cannot be applied")
        return GuardStatus(
            result=GuardResult.EXEMPT, ticker=ticker, role_id=None,
            appreciation=None, threshold=None, adjusted_returns=None, flags=flags,
        )

    primary_role = max(entry.components, key=lambda c: c.weight).role_id

    threshold_pct: Optional[float] = cal.regime.entry_extension_thresholds.get(primary_role)
    if threshold_pct is None:
        return GuardStatus(
            result=GuardResult.EXEMPT, ticker=ticker, role_id=primary_role,
            appreciation=None, threshold=None, adjusted_returns=None, flags=flags,
        )

    threshold = threshold_pct / 100.0

    if effective_avg is None:
        flags.append(f"{ticker}: trailing average unavailable — HALT (conservative)")
        return GuardStatus(
            result=GuardResult.HALT, ticker=ticker, role_id=primary_role,
            appreciation=None, threshold=threshold,
            adjusted_returns=None, flags=flags,
        )

    if effective_avg <= 0:
        raise HardStopException(
            f"EntryExtensionGuard: {ticker} trailing_avg <= 0 ({effective_avg})"
        )

    appreciation = (current_price - effective_avg) / effective_avg

    if appreciation >= threshold:
        adjusted: Dict[str, float] = {}
        for sc in ("A", "B", "C", "D", "E", "F"):
            rr = cal.return_table.get(primary_role, {}).get(sc)
            adjusted[sc] = (rr.conservative - appreciation * 100.0) if rr is not None else float("nan")
        flags.append(
            f"ENTRY EXTENSION GUARD — {ticker} ({primary_role}): "
            f"{appreciation:.1%} above {window_days}d avg (threshold {threshold:.0%}). "
            "EV recalculation required. HALT."
        )
        return GuardStatus(
            result=GuardResult.HALT, ticker=ticker, role_id=primary_role,
            appreciation=appreciation, threshold=threshold,
            adjusted_returns=adjusted, flags=flags,
        )

    return GuardStatus(
        result=GuardResult.PASS, ticker=ticker, role_id=primary_role,
        appreciation=appreciation, threshold=threshold,
        adjusted_returns=None, flags=flags,
    )


def role_repricing_divergence(
    holdings_30d_returns: Dict[str, Optional[float]],
    broad_market_30d: Optional[float],
    cal: CalibrationState,
) -> List[InstrumentRepricingWarning]:
    """
    M14.RoleRepricingDivergence() — Update 1.

    Detects when a portfolio instrument underperforms the broad market by more
    than its role-specific threshold (§9.5) over the 30-day window.

    Advisory signal only — never blocks execution. Results surface in briefing
    and feed M13.PassiveMandateAbsentWarning for FLOOR_THEN_RETURN accounts.

    Parameters
    ----------
    holdings_30d_returns:
        Dict mapping ticker → 30-day return as fraction (e.g. -0.12 = -12%).
        None values are skipped with a quality flag.
        In the Python pipeline, populated from allocation sheet GOOGLEFINANCE
        period returns or yfinance history when available.
    broad_market_30d:
        30-day return of broad market proxy (SPY/VTI) as fraction.
        None → function returns empty list with flag.
    cal:
        CalibrationState — provides §11 classifications and §9.5 thresholds.

    Returns
    -------
    List of InstrumentRepricingWarning — one per breached instrument.
    Empty list if broad_market_30d is None or no thresholds are configured.

    NEVER route output into M03.DeriveScenarioProbabilities().
    """
    if broad_market_30d is None:
        return []

    thresholds = cal.regime.role_repricing_thresholds
    if not thresholds:
        return []

    warnings: List[InstrumentRepricingWarning] = []

    for ticker, instrument_30d in holdings_30d_returns.items():
        if instrument_30d is None:
            continue

        entry = cal.instruments.get(ticker)
        if entry is None or not entry.components:
            continue

        # Primary role = highest-weight component
        primary = max(entry.components, key=lambda c: c.weight)
        threshold_pp = thresholds.get(primary.role_id)
        if threshold_pp is None:
            continue   # role not in §9.5 table — no signal defined

        underperformance_pp = (broad_market_30d - instrument_30d) * 100.0

        if underperformance_pp >= threshold_pp:
            warnings.append(InstrumentRepricingWarning(
                ticker=ticker,
                primary_role_id=primary.role_id,
                instrument_30d=instrument_30d,
                broad_market_30d=broad_market_30d,
                underperformance_pp=underperformance_pp,
                threshold_pp=threshold_pp,
            ))

    return warnings
