"""
portfolio/allocation.py — M13 growth objectives and allocation math.

Public functions:
  compute_floor()                — M13.ComputeFloor()
  compute_target_multiplier()    — M13.ComputeTargetMultiplier()
  required_real_return()         — M13.RequiredRealReturn()
  ideal_allocation()             — M13.idealAllocation() per scenario
  scenario_weighted_allocation() — M03/M13 integration: probability-weighted target
  feasibility_check()            — M13.FeasibilityCheck()
  recalibration_sequence()       — M13.RecalibrationSequence() (ENG-24)

Design:
  - Uses blended_scenario_return() for ALL return computations — no direct §4.1 lookups.
  - account parameter required on every call per framework GUARD.
  - REDUCE_TO_MIN resolves to floor (non-circular: ComputeFloor is independent).
  - Returns are in percent units throughout (e.g. 4.6 = 4.6%) — consistent with
    blended_scenario_return() output convention.
  - recalibration_sequence() is a pure advisory function — fires when feasibility_check
    returns feasible=False. Caller (mcp_server) invokes it; feasibility_check does not
    call it internally to avoid circular logic.
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
    RecalibrationResult,
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


# ── recalibration_sequence ──────────────────────────────────────────────────────────────────────────────

def recalibration_sequence(
    account: AccountProfile,
    proposed_allocations: Dict[str, float],
    probs: ScenarioProbabilities,
    cal: CalibrationState,
    shortfall_pp: float,
    priority: str,
    high_conviction_tickers: Optional[List[str]] = None,
) -> RecalibrationResult:
    """
    M13.RecalibrationSequence() — advisory gap-closing analysis.

    Fires when feasibility_check() returns feasible=False.
    Caller (mcp_server._tool_evaluate_allocation) invokes this; feasibility_check
    does not call it internally (avoids circular logic).

    Step 1: identify anchor positions + compute gap arithmetic.
    Step 2a: reallocate non-anchors toward higher-return roles (dominant scenario).
    Step 2b: if gap persists, identify the best unheld role from §4.1 return table.

    Both steps always run; step 2b runs regardless of step 2a outcome.

    Parameters
    ----------
    high_conviction_tickers : optional list supplied by Claude after running
        M06.SimplicityTest(). If None, Python defaults to tickers with
        proposed_weight > compute_floor() as a computable proxy.
    shortfall_pp : pp gap that triggered the sequence (from FeasibilityResult).
    priority : "TARGET" for TARGET_THEN_RETURN accounts,
               "FLOOR_PROTECTION" for FLOOR_THEN_RETURN / PRESERVATION.
    """
    quality_flags: List[str] = []
    dominant_scenario = max(_SCENARIOS, key=lambda s: getattr(probs, s))

    # ── Step 1: Anchor identification and gap analysis ─────────────────────────────────────
    if high_conviction_tickers is not None:
        anchors = [t for t in high_conviction_tickers if t in proposed_allocations]
    else:
        anchors = [
            t for t, w in proposed_allocations.items()
            if w > compute_floor(t, account, w, cal) + 1e-6
        ]
        if not anchors:
            quality_flags.append(
                "⚠ No high-conviction anchors found (all tickers at or near floor). "
                "SimplicityTest result not available — defaulted to above-floor proxy."
            )

    def _weighted_return(ticker: str) -> float:
        total = 0.0
        for s in _SCENARIOS:
            try:
                total += (getattr(probs, s) / 100.0) * blended_scenario_return(
                    ticker, s, "conservative", cal
                )
            except (HardStopException, ValueError, KeyError):
                pass
        return total

    anchor_weight = sum(proposed_allocations.get(t, 0.0) for t in anchors)
    anchor_return = sum(
        proposed_allocations.get(t, 0.0) * _weighted_return(t) for t in anchors
    )
    residual_weight = max(0.0, 1.0 - anchor_weight)

    # required return: TARGET_THEN_RETURN uses multiplier; others target 0%
    required = required_real_return(account, probs, cal) or 0.0

    residual_required: Optional[float] = None
    if residual_weight > 1e-6:
        residual_required = (required - anchor_return) / residual_weight

    # ── Step 2a: Reallocate non-anchor positions (dominant scenario) ──────────────────
    non_anchors = [t for t in proposed_allocations if t not in anchors]
    all_tickers = list(proposed_allocations.keys())

    def _dominant_return(ticker: str) -> float:
        try:
            return blended_scenario_return(ticker, dominant_scenario, "conservative", cal)
        except (HardStopException, ValueError, KeyError):
            return -999.0

    ranked_non_anchors = sorted(non_anchors, key=_dominant_return, reverse=True)

    revised: Dict[str, float] = {t: proposed_allocations[t] for t in anchors}
    for t in ranked_non_anchors:
        try:
            w, flags = ideal_allocation(
                ticker=t,
                scenario=dominant_scenario,
                account=account,
                current_weight=proposed_allocations.get(t, 0.0),
                all_tickers=all_tickers,
                all_current_weights=proposed_allocations,
                cal=cal,
            )
            revised[t] = w
            quality_flags.extend(flags)
        except (HardStopException, ValueError) as e:
            revised[t] = proposed_allocations.get(t, 0.0)
            quality_flags.append(
                f"⚠ idealAllocation for {t} in {dominant_scenario} failed: {e} — kept original weight."
            )

    # Compute revised portfolio return directly (no recursive feasibility_check)
    revised_return = 0.0
    for s in _SCENARIOS:
        s_ret = 0.0
        for t, w in revised.items():
            try:
                s_ret += w * blended_scenario_return(t, s, "conservative", cal)
            except (HardStopException, ValueError, KeyError):
                pass
        revised_return += (getattr(probs, s) / 100.0) * s_ret

    revised_gap = required - revised_return
    gap_closed = revised_gap <= 1e-4  # within rounding tolerance

    # ── Step 2b: Identify candidate unheld role if gap persists ───────────────────────
    candidate_role: Optional[str] = None
    candidate_return: Optional[float] = None
    candidate_gap_est: Optional[float] = None
    no_candidate_msg: Optional[str] = None

    if not gap_closed:
        held_roles: set = set()
        for t in proposed_allocations:
            entry = cal.instruments.get(t)
            if entry:
                for comp in entry.components:
                    held_roles.add(comp.role_id)

        best_role: Optional[str] = None
        best_return_val: float = -999.0
        for role_id, scenario_map in cal.return_table.items():
            if role_id in held_roles:
                continue
            try:
                r = scenario_map[dominant_scenario].conservative
                if r > best_return_val:
                    best_return_val = r
                    best_role = role_id
            except (KeyError, AttributeError):
                pass

        if best_role is not None and best_return_val > 0.0:
            candidate_role = best_role
            candidate_return = best_return_val
            cap = account.concentration_cap
            candidate_weight_est = min(cap, residual_weight) if residual_weight > 0 else 0.0
            candidate_gap_est = round(candidate_weight_est * best_return_val, 2)
        elif best_role is not None:
            no_candidate_msg = (
                f"No unheld role with positive conservative return in scenario {dominant_scenario}. "
                "Target may not be achievable under current macro regime. "
                "Consider: (1) extend planning horizon, "
                "(2) revise target multiplier in CALIBRATION_STATE §4.2 or §4.3, "
                "(3) accept reduced target for this regime."
            )
        else:
            no_candidate_msg = (
                "No unheld roles found in §4.1 return table — "
                "all registered roles appear to be held."
            )

    return RecalibrationResult(
        shortfall_pp=round(shortfall_pp, 2),
        priority=priority,
        anchor_tickers=anchors,
        anchor_weight=round(anchor_weight, 4),
        anchor_return_pct=round(anchor_return, 2),
        residual_weight=round(residual_weight, 4),
        residual_required_return_pct=(
            round(residual_required, 2) if residual_required is not None else None
        ),
        gap_closed_by_reallocation=gap_closed,
        revised_portfolio_return_pct=round(revised_return, 2),
        revised_gap_pp=round(max(0.0, revised_gap), 2),
        revised_allocations={t: round(w, 4) for t, w in revised.items()} if gap_closed else None,
        candidate_role=candidate_role,
        candidate_role_return_pct=(
            round(candidate_return, 2) if candidate_return is not None else None
        ),
        candidate_gap_closure_est_pp=candidate_gap_est,
        no_candidate_message=no_candidate_msg,
        quality_flags=quality_flags,
    )

