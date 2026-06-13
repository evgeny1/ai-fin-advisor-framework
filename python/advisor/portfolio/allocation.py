"""
portfolio/allocation.py — M13 growth objectives and allocation math.

Public functions:
  compute_floor()                — M13.ComputeFloor()
  compute_target_multiplier()    — M13.ComputeTargetMultiplier()
  required_real_return()         — M13.RequiredRealReturn()
  ideal_allocation()             — M13.idealAllocation() per scenario
  scenario_weighted_allocation() — M03/M13 integration: probability-weighted target
  feasibility_check()            — M13.FeasibilityCheck()

Design:
  - Uses blended_scenario_return() for ALL return computations — no direct §4.1 lookups.
  - account parameter required on every call per framework GUARD.
  - REDUCE_TO_MIN resolves to floor (non-circular: ComputeFloor is independent).
  - Returns are in percent units throughout (e.g. 4.6 = 4.6%) — consistent with
    blended_scenario_return() output convention.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..exceptions import HardStopException
from ..types import (
    AccountProfile,
    AllocationTarget,
    CalibrationState,
    DirectiveCode,
    FeasibilityResult,
    ObjectiveType,
    ScenarioProbabilities,
)
from ..analysis.instruments import blended_scenario_return
from .directives import DIRECTIVES, get_directive

_SCENARIOS: Tuple[str, ...] = ("A", "B", "C", "D", "E", "F")
_CLAMP_TOL = 1e-9  # floating-point tolerance


# ── Floor computation ──────────────────────────────────────────────────────────

def compute_floor(
    ticker: str,           # noqa: ARG001  (kept for symmetry with framework signature)
    account: AccountProfile,
    current_weight: float,
    cal: CalibrationState,
) -> float:
    """
    M13.ComputeFloor(asset, account) → float (fraction).

    base_floor = §4.4.base_floor × current_weight
    min_floor  = §4.4.min_floor_pct  (fraction of account)
    floor      = MAX(base_floor, min_floor)
    """
    fp = cal.floor_params
    base_floor = fp.base_floor * current_weight
    return max(base_floor, fp.min_floor_pct)


# ── Target multiplier ──────────────────────────────────────────────────────────

def compute_target_multiplier(
    account: AccountProfile,
    probs: ScenarioProbabilities,
    cal: CalibrationState,
) -> Optional[float]:
    """
    M13.ComputeTargetMultiplier(account) → float or None.

    Only applies to TARGET_THEN_RETURN accounts (IRA, Roth IRA).
    Returns None for RETURN_THEN_TARGET, FLOOR_THEN_RETURN, PRESERVATION.

    Routes to §4.2 (IRA) or §4.3 (Roth) based on account_id substring.
    Enforces the floor from the multiplier block.
    """
    if account.objective_type != ObjectiveType.TARGET_THEN_RETURN:
        return None

    acc_id = account.account_id.lower()
    if "roth" in acc_id:
        mults = cal.multipliers.roth
        floor = cal.multipliers.roth_floor
    elif "ira" in acc_id:
        mults = cal.multipliers.ira
        floor = cal.multipliers.ira_floor
    else:
        return None  # no multiplier table for non-IRA accounts

    raw = sum(
        (getattr(probs, s) / 100.0) * mults.get(s, 1.0)
        for s in _SCENARIOS
    )
    return max(raw, floor)


def required_real_return(
    account: AccountProfile,
    probs: ScenarioProbabilities,
    cal: CalibrationState,
) -> Optional[float]:
    """
    M13.RequiredRealReturn(account) → float (percent, e.g. 4.6 = 4.6%) or None.

    Formula: (multiplier ^ (1/horizon)) - 1  converted to percent.
    Returns None for non-TARGET accounts or invalid horizon.
    """
    mult = compute_target_multiplier(account, probs, cal)
    if mult is None:
        return None
    h = account.planning_horizon_years
    if h <= 0:
        return None
    return ((mult ** (1.0 / h)) - 1.0) * 100.0


# ── Direction bounds ───────────────────────────────────────────────────────────

def _direction_bounds(
    directive: DirectiveCode,
    floor: float,
    current_weight: float,
    cap: float,
) -> Tuple[float, float]:
    """
    Map DirectiveCode → (min_weight, max_weight) per M13.DIRECTION_BOUNDS.
    All values are fractions of account value.
    """
    if directive == DirectiveCode.EXIT:
        return (0.0, 0.0)
    if directive == DirectiveCode.REDUCE_TO_MIN:
        # Non-circular resolution: REDUCE_TO_MIN → floor point
        return (floor, floor)
    if directive == DirectiveCode.REDUCE:
        return (floor, current_weight)
    if directive == DirectiveCode.REDUCE_50PCT:
        mid = 0.5 * current_weight
        return (mid, mid)
    if directive in (
        DirectiveCode.HOLD,
        DirectiveCode.HOLD_WATCH,
        DirectiveCode.HOLD_EVALUATE,
        DirectiveCode.EVALUATE,
        DirectiveCode.PATHWAY_CONDITIONAL,
    ):
        return (current_weight, current_weight)
    if directive in (DirectiveCode.ADD, DirectiveCode.ADD_AGGRESSIVE):
        return (current_weight, cap)
    # Unknown code — conservative default: hold
    return (current_weight, current_weight)


# ── idealAllocation ────────────────────────────────────────────────────────────

def ideal_allocation(
    ticker: str,
    scenario: str,
    account: AccountProfile,
    current_weight: float,
    all_tickers: List[str],
    all_current_weights: Dict[str, float],
    cal: CalibrationState,
) -> Tuple[float, List[str]]:
    """
    M13.idealAllocation(asset, scenario, account) → (weight, quality_flags).

    Steps:
      1. Resolve primary-role directive from M09/M10 DIRECTIVES table.
      2. Compute permitted [min_w, max_w] from M13.DIRECTION_BOUNDS.
      3. Rank all holdings by blended conservative return in scenario; scale within bounds.
      4. Apply floor nominal loss guard (FLOOR_THEN_RETURN / PRESERVATION accounts).
      5. Clamp and return.

    Parameters
    ----------
    ticker : str
        Target instrument — must be in cal.instruments (§11).
    scenario : str
        One of "A"–"F".
    account : AccountProfile
        Account context — objective type, floor_nominal_loss, concentration_cap.
    current_weight : float
        Current allocation fraction for this ticker in this account.
    all_tickers : List[str]
        All tickers allocated in this account (for ranking).
    all_current_weights : Dict[str, float]
        Current allocation fractions for all tickers.
    cal : CalibrationState
        §4.1 return table + §11 instrument entries.

    Returns
    -------
    (ideal_weight, quality_flags) — weight is a fraction in [0, concentration_cap].
    """
    quality_flags: List[str] = []

    # ── Step 1: Resolve directive ──────────────────────────────────────────────
    entry = cal.instruments.get(ticker)
    if entry is None:
        raise HardStopException(
            f"idealAllocation: '{ticker}' not in §11. "
            "ValidateClassifications() should have caught this at session start."
        )
    primary_role = max(entry.components, key=lambda c: c.weight).role_id
    d_result = get_directive(primary_role, scenario)
    quality_flags.extend(d_result.quality_flags)
    directive = d_result.code

    # ── Step 2: Floor and direction bounds ────────────────────────────────────
    floor = compute_floor(ticker, account, current_weight, cal)
    cap   = account.concentration_cap
    min_w, max_w = _direction_bounds(directive, floor, current_weight, cap)

    # Short-circuit: fixed-point directives (EXIT, HOLD, REDUCE_TO_MIN, etc.)
    if abs(max_w - min_w) < _CLAMP_TOL:
        return (max(0.0, min(cap, min_w)), quality_flags)

    # ── Step 3: Rank by blended conservative return ───────────────────────────
    ticker_returns: List[Tuple[str, float]] = []
    for t in all_tickers:
        try:
            r = blended_scenario_return(t, scenario, "conservative", cal)
            ticker_returns.append((t, r))
        except (HardStopException, ValueError, KeyError):
            quality_flags.append(
                f"⚠ Ranking: could not compute return for {t} in scenario {scenario} — "
                "excluded from ranking."
            )

    ticker_returns.sort(key=lambda x: x[1], reverse=True)  # descending (best = rank 0)
    ranked = [t for t, _ in ticker_returns]
    rank_count = len(ranked)

    try:
        rank_position = ranked.index(ticker)
    except ValueError:
        rank_position = rank_count // 2  # midpoint fallback
        quality_flags.append(
            f"⚠ {ticker} not in return ranking for scenario {scenario} — "
            "used midpoint rank."
        )

    rank_fraction = (1.0 - rank_position / rank_count) if rank_count > 0 else 0.5
    raw_weight = min_w + rank_fraction * (max_w - min_w)

    # ── Step 4: Floor nominal loss guard ──────────────────────────────────────
    if account.floor_nominal_loss:
        try:
            cons_return = blended_scenario_return(ticker, scenario, "conservative", cal)
            if cons_return < 0.0 and directive in (
                DirectiveCode.ADD,
                DirectiveCode.ADD_AGGRESSIVE,
                DirectiveCode.HOLD,
                DirectiveCode.HOLD_EVALUATE,
                DirectiveCode.HOLD_WATCH,
            ):
                raw_weight = min(raw_weight, floor)
                quality_flags.append(
                    f"⚠ {ticker} scenario {scenario}: negative conservative return "
                    f"({cons_return:.1f}%) with {directive.value} — "
                    "weight capped at floor per §4.4 nominal loss guard."
                )
        except (HardStopException, ValueError):
            pass

    # ── Step 5: Clamp ─────────────────────────────────────────────────────────
    ideal = max(min_w, min(max_w, raw_weight))
    ideal = min(ideal, cap)
    ideal = max(ideal, 0.0)
    return (ideal, quality_flags)


# ── scenario_weighted_allocation ───────────────────────────────────────────────

def scenario_weighted_allocation(
    ticker: str,
    account: AccountProfile,
    probs: ScenarioProbabilities,
    all_current_weights: Dict[str, float],
    cal: CalibrationState,
) -> AllocationTarget:
    """
    M03.scenarioWeightedAllocation(asset, account) → AllocationTarget.

    Calls idealAllocation() for each of the six scenarios, produces the
    probability-weighted target, and reports the dominant directive and floor.

    Parameters
    ----------
    ticker : str
        Target instrument.
    account : AccountProfile
        Account context — required per framework GUARD.
    probs : ScenarioProbabilities
        Current §8 probabilities (AUTHORITATIVE — from Session_Log).
    all_current_weights : Dict[str, float]
        All tickers and their current weights in this account.
    cal : CalibrationState
        §4.1 return table + §11 instrument entries.

    Returns
    -------
    AllocationTarget with per-scenario ideal weights, probability-weighted
    target, blended conservative return, dominant directive, and floor.
    """
    current_weight = all_current_weights.get(ticker, 0.0)
    all_tickers = list(all_current_weights.keys())
    all_flags: List[str] = []

    per_scenario: Dict[str, float] = {}
    for s in _SCENARIOS:
        w, flags = ideal_allocation(
            ticker=ticker,
            scenario=s,
            account=account,
            current_weight=current_weight,
            all_tickers=all_tickers,
            all_current_weights=all_current_weights,
            cal=cal,
        )
        per_scenario[s] = w
        all_flags.extend(flags)

    # Probability-weighted target weight
    weighted = sum(
        (getattr(probs, s) / 100.0) * per_scenario[s]
        for s in _SCENARIOS
    )

    # Scenario-weighted conservative blended return (%)
    blended_ret = 0.0
    for s in _SCENARIOS:
        try:
            r = blended_scenario_return(ticker, s, "conservative", cal)
            blended_ret += (getattr(probs, s) / 100.0) * r
        except (HardStopException, ValueError):
            all_flags.append(
                f"⚠ Could not compute blended return for {ticker} scenario {s}."
            )

    # Dominant directive: highest-probability scenario
    dominant_s = max(_SCENARIOS, key=lambda s: getattr(probs, s))
    entry = cal.instruments.get(ticker)
    primary_role = (
        max(entry.components, key=lambda c: c.weight).role_id
        if entry else "unknown"
    )
    dom_code = DIRECTIVES.get((primary_role, dominant_s), DirectiveCode.HOLD)
    floor = compute_floor(ticker, account, current_weight, cal)

    return AllocationTarget(
        ticker=ticker,
        account_id=account.account_id,
        scenario_weighted_weight=weighted,
        per_scenario=per_scenario,
        blended_conservative_return=blended_ret,
        directive=dom_code,
        floor=floor,
        quality_flags=all_flags,
    )


# ── feasibility_check ─────────────────────────────────────────────────────────

def feasibility_check(
    account: AccountProfile,
    proposed_allocations: Dict[str, float],
    probs: ScenarioProbabilities,
    cal: CalibrationState,
) -> FeasibilityResult:
    """
    M13.FeasibilityCheck(account, proposed_allocations) → FeasibilityResult.

    Runs after scenarioWeightedAllocation() produces proposed allocations.
    Must run before any allocation recommendation is presented.
    Uses conservative blended return throughout (never upside).

    Branches by objective_type:
      TARGET_THEN_RETURN  — portfolio_return >= required_real_return?
      RETURN_THEN_TARGET  — always feasible; reports drawdown-adjusted return
      FLOOR_THEN_RETURN   — no nominal loss in scenarios with prob >= threshold
      PRESERVATION        — portfolio_return >= 0?

    Parameters
    ----------
    account : AccountProfile
        Account objective and constraints.
    proposed_allocations : Dict[str, float]
        Ticker → weight fraction for all holdings. Values should sum to ~1.0.
    probs : ScenarioProbabilities
        Current probability vector.
    cal : CalibrationState
        §4.1 return table + §4.4 floor params + multipliers.

    Returns
    -------
    FeasibilityResult — check .feasible before presenting recommendations.
    """
    quality_flags: List[str] = []

    def _scenario_portfolio_return(s: str) -> float:
        """Conservative portfolio return for scenario s (%)."""
        total = 0.0
        for ticker, weight in proposed_allocations.items():
            try:
                total += weight * blended_scenario_return(ticker, s, "conservative", cal)
            except (HardStopException, ValueError):
                quality_flags.append(
                    f"⚠ FeasibilityCheck: could not compute return for {ticker} "
                    f"in scenario {s} — treated as 0%."
                )
        return total

    # Scenario-weighted conservative portfolio return (%)
    portfolio_return = sum(
        (getattr(probs, s) / 100.0) * _scenario_portfolio_return(s)
        for s in _SCENARIOS
    )

    obj = account.objective_type

    # ── TARGET_THEN_RETURN ────────────────────────────────────────────────────
    if obj == ObjectiveType.TARGET_THEN_RETURN:
        mult = compute_target_multiplier(account, probs, cal)
        req  = required_real_return(account, probs, cal)
        if req is None:
            quality_flags.append(
                "⚠ required_real_return unavailable — multiplier table not found "
                "for this account type."
            )
            return FeasibilityResult(
                feasible=False,
                portfolio_return=portfolio_return,
                objective_type=obj.value,
                quality_flags=quality_flags,
            )
        feasible = portfolio_return >= req
        return FeasibilityResult(
            feasible=feasible,
            portfolio_return=portfolio_return,
            objective_type=obj.value,
            required_return=req,
            target_multiplier=mult,
            shortfall_pp=(req - portfolio_return) if not feasible else None,
            quality_flags=quality_flags,
        )

    # ── RETURN_THEN_TARGET ────────────────────────────────────────────────────
    if obj == ObjectiveType.RETURN_THEN_TARGET:
        dt = account.drawdown_tolerance
        dta = portfolio_return / dt if dt else 0.0
        req = required_real_return(account, probs, cal)
        return FeasibilityResult(
            feasible=True,   # optimization objective — not a gate
            portfolio_return=portfolio_return,
            objective_type=obj.value,
            drawdown_adjusted_return=dta,
            required_return=req,
            target_met=(portfolio_return >= req) if req is not None else None,
            quality_flags=quality_flags,
        )

    # ── FLOOR_THEN_RETURN ─────────────────────────────────────────────────────
    if obj == ObjectiveType.FLOOR_THEN_RETURN:
        threshold_pct = cal.floor_params.floor_loss_prob_threshold * 100.0
        floor_breached = False
        worst_scenario: Optional[str] = None
        worst_return: Optional[float] = None

        for s in _SCENARIOS:
            if getattr(probs, s) < threshold_pct:
                continue
            s_ret = _scenario_portfolio_return(s)
            if s_ret < 0.0:
                floor_breached = True
                if worst_return is None or s_ret < worst_return:
                    worst_return  = s_ret
                    worst_scenario = s

        req = required_real_return(account, probs, cal)
        return FeasibilityResult(
            feasible=not floor_breached,
            portfolio_return=portfolio_return,
            objective_type=obj.value,
            floor_breached=floor_breached,
            worst_scenario=worst_scenario,
            worst_return=worst_return,
            required_return=req,
            target_met=(portfolio_return >= req) if req is not None else None,
            quality_flags=quality_flags,
        )

    # ── PRESERVATION ──────────────────────────────────────────────────────────
    if obj == ObjectiveType.PRESERVATION:
        feasible = portfolio_return >= 0.0
        if not feasible:
            quality_flags.append(
                "⚠ Preservation account: negative conservative real return expected. "
                "Requires immediate review."
            )
        return FeasibilityResult(
            feasible=feasible,
            portfolio_return=portfolio_return,
            objective_type=obj.value,
            quality_flags=quality_flags,
        )

    # Unknown objective type
    quality_flags.append(f"⚠ Unknown objective_type '{obj}' — FeasibilityCheck skipped.")
    return FeasibilityResult(
        feasible=True,
        portfolio_return=portfolio_return,
        objective_type=str(obj),
        quality_flags=quality_flags,
    )
