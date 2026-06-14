"""
analysis/regime.py — M14 market regime divergence signal and entry extension guard.

Maps to: M14_MarketRegime.md MODULE MarketRegimeDiscipline

ComputeDivergenceSignal():
  - commodity_fear_divergence: Brent 90-calendar-day change vs VIX change from 90d avg
  - equity_scenario_divergence: SPX 30-trading-day change while directive is reductive
  - composite: HIGH if either is HIGH; MODERATE if either is MODERATE

EntryExtensionGuard():
  - Checks whether current price is >= threshold% above 90d trailing average
  - Returns PASS | HALT | EXEMPT per §9.3 thresholds
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
)
from ._utils import get_history, get_scalar, compute_pct_change

# Directives that activate equity_scenario_divergence check (M14 §1)
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
) -> DivergenceSignal:
    """
    M14.ComputeDivergenceSignal.

    Window definitions (from M14 §1):
      energy_90d:       90 CALENDAR DAYS — Brent pct change
      broad_equity_30d: 30 TRADING DAYS  — SPX/VTI pct change

    Parameters
    ----------
    readings:
        Expected keys: BRENT_CRUDE, VIX, VIX_90D_AVG, BROAD_EQUITY_TRAILING.
        BRENT_CRUDE.value may be:
          - float  → current price only (90d change unavailable)
          - dict   → {"current": float, "history": [...]} or {"change_90d": float}
        BROAD_EQUITY_TRAILING.value may be:
          - dict   → {"change_30d": float, "change_90d": float} (as fractions)
          - float  → current price only (change unavailable)
    cal:
        CalibrationState with §9 RegimeBlock thresholds (stored as percentages 0–100).
    equity_directive_for_dominant_scenario:
        The M09/M10 directive string for broad_market_equity_domestic in the current
        dominant scenario. Required to evaluate equity_scenario_divergence.
        None → equity_scenario_divergence = NOT_APPLICABLE.

    Returns
    -------
    DivergenceSignal. NEVER route composite into M03 probability derivation.
    """
    flags: List[str] = []
    r = cal.regime

    # ── Brent 90d change (fraction) ───────────────────────────────────────────
    brent_r  = readings.get("BRENT_CRUDE")
    energy_90d_change: Optional[float] = None

    if brent_r and brent_r.is_valid:
        v = brent_r.value
        if isinstance(v, dict):
            # Preferred: pre-computed change from fetcher
            for key in ("change_90d", "pct_change_90d", "pct_90d"):
                if key in v and v[key] is not None:
                    energy_90d_change = float(v[key])
                    break
            if energy_90d_change is None:
                # Fall back to history list
                hist = get_history(brent_r)
                energy_90d_change = compute_pct_change(hist, 90, "BRENT_CRUDE", flags)
        elif brent_r.is_valid:
            # Scalar current price only — need prior to compute change
            hist = get_history(brent_r)
            energy_90d_change = compute_pct_change(hist, 90, "BRENT_CRUDE", flags)
            if energy_90d_change is None:
                flags.append(
                    "BRENT_CRUDE: point-in-time only — 90d change unavailable; "
                    "commodity_fear_divergence cannot be computed"
                )
    else:
        flags.append("BRENT_CRUDE: reading unavailable — commodity_fear_divergence cannot be computed")

    # ── VIX change from 90d rolling average ───────────────────────────────────
    vix_current = get_scalar(readings.get("VIX"),        flags, "VIX")
    vix_90d_avg = get_scalar(readings.get("VIX_90D_AVG"), flags, "VIX_90D_AVG")
    vix_change_90d: Optional[float] = None
    if vix_current is not None and vix_90d_avg is not None:
        vix_change_90d = vix_current - vix_90d_avg
    elif vix_current is not None:
        flags.append("VIX_90D_AVG: unavailable — commodity_fear_divergence VIX component missing")

    # ── Broad equity 30d change (fraction) ────────────────────────────────────
    equity_r = readings.get("BROAD_EQUITY_TRAILING")
    broad_equity_30d: Optional[float] = None
    if equity_r and equity_r.is_valid:
        v = equity_r.value
        if isinstance(v, dict):
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
    # Thresholds from cal.regime are in percentage (e.g. 15.0); convert to fraction
    commodity_fear = DivergenceLevel.NONE
    if energy_90d_change is not None and vix_change_90d is not None:
        e_high_thresh = r.commodity_fear_HIGH_energy_pct / 100.0  # fraction
        e_mod_thresh  = r.commodity_fear_MOD_energy_pct  / 100.0
        v_high_thresh = r.commodity_fear_HIGH_vix_change          # pts (raw)
        v_mod_thresh  = r.commodity_fear_MOD_vix_change           # pts

        if energy_90d_change >= e_high_thresh and vix_change_90d <= v_high_thresh:
            commodity_fear = DivergenceLevel.HIGH
        elif energy_90d_change >= e_mod_thresh and vix_change_90d <= v_mod_thresh:
            commodity_fear = DivergenceLevel.MODERATE
        # else NONE (default)

    # ── Equity scenario divergence ────────────────────────────────────────────
    equity_div = DivergenceLevel.NOT_APPLICABLE
    if equity_directive_for_dominant_scenario in _REDUCTIVE_DIRECTIVES:
        if broad_equity_30d is not None:
            e_high_pct = r.equity_div_HIGH_pct / 100.0  # fraction
            e_mod_pct  = r.equity_div_MOD_pct  / 100.0
            if broad_equity_30d >= e_high_pct:
                equity_div = DivergenceLevel.HIGH
            elif broad_equity_30d >= e_mod_pct:
                equity_div = DivergenceLevel.MODERATE
            else:
                equity_div = DivergenceLevel.NONE
        else:
            # History unavailable — conservative: NONE (cannot confirm divergence)
            equity_div = DivergenceLevel.NONE
            flags.append(
                "BROAD_EQUITY_TRAILING: history unavailable — "
                "equity_scenario_divergence treated as NONE (conservative)"
            )
    # else: directive not reductive → NOT_APPLICABLE (default)

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
    trailing_90d_avg: Optional[float] = None,   # DEPRECATED alias → use trailing_avg
    window_days: int = 90,
    conflict_duration_days: Optional[int] = None,
) -> GuardStatus:
    """
    M14.EntryExtensionGuard for one ticker.

    Called before any ADD directive executes (M05 Step 9, M09/M10 execution).
    WAR PREMIUM ENTRY GUARD (commodity-linked, geopolitical, precious metals roles)
    is an INDEPENDENT guard — apply separately per M08 execution guard spec.

    §9.3 CONFLICT DURATION OVERRIDE (v1.34):
    When conflict_duration_days > 90 and the instrument's primary role is
    inflation_hedge_commodity_linked or inflation_hedge_precious_metals,
    the caller MUST supply the 180-day trailing average in trailing_avg and
    pass window_days=180. This function logs a flag when the override applies.
    The override is the CALLER's responsibility — this function does not
    fetch price history; it receives the pre-computed average.

    Parameters
    ----------
    ticker:
        Instrument ticker. Must be present in cal.instruments (§11).
    cal:
        CalibrationState with §11 instrument entries and §9.3 thresholds.
    current_price:
        Current market price from AllocationSheet (T1 source).
    trailing_avg:
        Trailing average price. 90-calendar-day by default; 180-calendar-day
        when the §9.3 conflict duration override is active (conflict_duration_days > 90
        for CL and IHP roles). Computed externally (M14 compute_trailing_avg).
        None → conservative treatment: guard is HALT (cannot confirm guard clear).
    trailing_90d_avg:
        Deprecated. Alias for trailing_avg for backward compatibility.
        If trailing_avg is None and trailing_90d_avg is not None, trailing_90d_avg is used.
    window_days:
        Calendar days used to compute trailing_avg. 90 (standard) or 180 (override).
        Used only for flag/logging; does not affect threshold math.
    conflict_duration_days:
        Calendar days since T1-confirmed conflict onset (if any active discrete supply event).
        None or <= 90 → standard 90d window expected.
        > 90 → caller should have used 180d window for CL/IHP roles (flag raised if not).

    Returns
    -------
    GuardStatus with result PASS | HALT | EXEMPT.
    """
    flags: List[str] = []

    # Backward-compat: accept legacy trailing_90d_avg keyword
    effective_avg = trailing_avg if trailing_avg is not None else trailing_90d_avg

    # Conflict duration override check (§9.3 v1.34)
    _OVERRIDE_ROLES = frozenset({
        "inflation_hedge_commodity_linked",
        "inflation_hedge_precious_metals",
    })

    entry = cal.instruments.get(ticker)
    if entry is None:
        raise HardStopException(
            f"EntryExtensionGuard: {ticker} not in §11 instrument table. "
            "ValidateClassifications() should have caught this at session start."
        )

    if not entry.components:
        flags.append(f"{ticker}: no components in §11 — guard cannot be applied")
        return GuardStatus(
            result=GuardResult.EXEMPT, ticker=ticker, role_id=None,
            appreciation=None, threshold=None, adjusted_returns=None, flags=flags,
        )

    # Primary role = highest-weight component
    primary_role = max(entry.components, key=lambda c: c.weight).role_id

    # §9.3 conflict duration override: flag if caller should have used 180d but passed 90d
    is_override_role = primary_role in _OVERRIDE_ROLES
    if conflict_duration_days is not None and conflict_duration_days > 90 and is_override_role:
        expected_window = 180
        if window_days < expected_window:
            flags.append(
                f"{ticker} ({primary_role}): §9.3 conflict duration override ACTIVE "
                f"({conflict_duration_days}d > 90d threshold) — expected 180d trailing avg "
                f"but caller supplied {window_days}d. Guard result may be too permissive. "
                "Re-run with 180d trailing avg."
            )
        else:
            flags.append(
                f"{ticker} ({primary_role}): §9.3 conflict duration override applied "
                f"({conflict_duration_days}d conflict) — using {window_days}d trailing avg."
            )

    # Look up threshold from §9.3
    threshold_pct: Optional[float] = cal.regime.entry_extension_thresholds.get(primary_role)
    if threshold_pct is None:
        # N/A role — exempt from this guard
        return GuardStatus(
            result=GuardResult.EXEMPT, ticker=ticker, role_id=primary_role,
            appreciation=None, threshold=None, adjusted_returns=None, flags=flags,
        )

    threshold = threshold_pct / 100.0  # convert percentage to fraction

    # Trailing average check
    if effective_avg is None:
        flags.append(
            f"{ticker}: trailing average unavailable ({window_days}d window) — "
            "conservative: treat guard as HALT per M14 DataIntegrity rule"
        )
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
        # Compute adjusted conservative returns: published − appreciation (per M14)
        adjusted: Dict[str, float] = {}
        for sc in ("A", "B", "C", "D", "E", "F"):
            row = cal.return_table.get(primary_role, {})
            rr  = row.get(sc)
            if rr is not None:
                # return table values are percentages (e.g. 6.0 = 6%); appreciation is fraction
                adjusted[sc] = rr.conservative - appreciation * 100.0
            else:
                adjusted[sc] = float("nan")  # role has no §4.1 row for this scenario
        flags.append(
            f"══ ENTRY EXTENSION GUARD — {ticker} ({primary_role}) ══ "
            f"Extension: {appreciation:.1%} (threshold: {threshold:.0%}). "
            f"Adjusted conservative returns shown. REQUIRED: recalculate EV. HALT until confirmed."
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
