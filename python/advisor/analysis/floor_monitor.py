"""
analysis/floor_monitor.py — M13.CurrentHoldingsFloorCheck()

Called at M05 Steps 3b and 6b for every FLOOR_THEN_RETURN account.
Detects between-session price drift that breaches the nominal loss floor
using ACTUAL current market weights — not proposed target allocations.

Distinct from portfolio/allocation.py::feasibility_check(), which validates
proposed allocations pre-trade. This module answers: "Where are we RIGHT NOW?"

Data contract:
  current_market_weights: Dict[ticker, float]
    Derived by caller from allocation sheet current values / account total.
    Source: GOOGLEFINANCE prices fetched at M05 Step 1.
    NEVER use target allocation percentages — those reflect intent, not state.

  probabilities: ScenarioProbabilities
    Step 3b → prior session probabilities from Session_Log §8
    Step 6b → newly derived probabilities from M03 (run only if any scenario
              shifted >= 5pp vs prior)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..types import (
    CalibrationState,
    FloorBreachAlert,
    ObjectiveType,
    ScenarioProbabilities,
)
from .instruments import blended_scenario_return


_SCENARIOS = ["A", "B", "C", "D", "E", "F"]


def current_holdings_floor_check(
    account_id: str,
    current_market_weights: Dict[str, float],
    probabilities: ScenarioProbabilities,
    cal: CalibrationState,
    check_step: str = "3b",
) -> Optional[FloorBreachAlert]:
    """
    M13.CurrentHoldingsFloorCheck() — Python implementation.

    Parameters
    ----------
    account_id:
        Account identifier string (for alert labelling only).
    current_market_weights:
        Dict mapping ticker → current weight fraction derived from sheet
        market values / account total. Must sum to approximately 1.0.
    probabilities:
        ScenarioProbabilities to use for the floor threshold test.
        Step 3b: prior session probs. Step 6b: current session probs.
    cal:
        CalibrationState — provides §4.1 return table and §11 classifications.
    check_step:
        "3b" or "6b" — recorded in FloorBreachAlert for audit trail.

    Returns
    -------
    FloorBreachAlert if floor breached in any scenario above threshold; else None.
    """
    floor_threshold = cal.floor_params.floor_loss_prob_threshold  # §4.4 — default 0.15

    prob_map: Dict[str, float] = {
        "A": probabilities.A,
        "B": probabilities.B,
        "C": probabilities.C,
        "D": probabilities.D,
        "E": probabilities.E,
        "F": probabilities.F,
    }

    worst_return: Optional[float] = None
    worst_scenario: Optional[str] = None

    for scenario in _SCENARIOS:
        p = prob_map[scenario] / 100.0          # convert percentage to fraction
        if p < floor_threshold:
            continue                             # below threshold — skip

        scenario_return = 0.0
        for ticker, weight in current_market_weights.items():
            if ticker not in cal.instruments:
                continue                         # unclassified — skip conservatively
            r = blended_scenario_return(ticker, scenario, "conservative", cal)
            scenario_return += weight * r

        if scenario_return < 0.0:
            if worst_return is None or scenario_return < worst_return:
                worst_return = scenario_return
                worst_scenario = scenario

    if worst_return is not None and worst_scenario is not None:
        return FloorBreachAlert(
            account_id=account_id,
            worst_scenario=worst_scenario,
            worst_return_pct=worst_return,
            weights_used=dict(current_market_weights),
            probabilities_used=probabilities,
            check_step=check_step,
            priority="IMMEDIATE",
        )

    return None


def check_all_floor_accounts(
    floor_accounts: List[Dict],
    probabilities: ScenarioProbabilities,
    cal: CalibrationState,
    check_step: str = "3b",
) -> List[FloorBreachAlert]:
    """
    Run CurrentHoldingsFloorCheck for every FLOOR_THEN_RETURN account.

    Parameters
    ----------
    floor_accounts:
        List of dicts, each with keys:
          "account_id"  : str
          "weights"     : Dict[ticker, float]  — current market weights
        Caller derives these from the allocation sheet at M05 Step 1.
    probabilities:
        ScenarioProbabilities for this check pass.
    cal:
        CalibrationState.
    check_step:
        "3b" or "6b".

    Returns
    -------
    List of FloorBreachAlert — one per breached account. Empty if all clear.
    """
    alerts: List[FloorBreachAlert] = []
    for acct in floor_accounts:
        alert = current_holdings_floor_check(
            account_id=acct["account_id"],
            current_market_weights=acct["weights"],
            probabilities=probabilities,
            cal=cal,
            check_step=check_step,
        )
        if alert is not None:
            alerts.append(alert)
    return alerts



# ── Update 3: Passive Mandate Absent Warning ──────────────────────────────────
# Emitted for FLOOR_THEN_RETURN accounts when a large non-passive-mandate
# instrument is actively repricing downward and the account is near its floor.

_PASSIVE_CONCENTRATION_THRESHOLD = 0.15   # 15% of account — §13 rule
_FLOOR_PROXIMITY_THRESHOLD_PP    = 5.0    # within 5pp of floor breach — §13 rule


@dataclass
class PassiveMandateAbsentWarning:
    """
    M13.PassiveMandateAbsentWarning — Update 3.

    Advisory warning when a FLOOR_THEN_RETURN account holds a large
    non-passive-mandate instrument that is actively repricing downward.
    No passive mandate = no structural bid floor; active holders may continue selling.
    Does not block execution — advisory note in briefing only.
    """
    account_id:          str
    ticker:              str
    current_weight:      float    # fraction
    instrument_30d:      Optional[float]   # return fraction if available; None if unknown
    passive_eligible:    bool     # always False when warning fires
    floor_proximity_pp:  Optional[float]   # how close to floor breach (pp); None if unknown


def passive_mandate_absent_warnings(
    floor_accounts: List[Dict],
    cal: CalibrationState,
    probs: "ScenarioProbabilities",
    holdings_30d_returns: Optional[Dict[str, Optional[float]]] = None,
) -> List["PassiveMandateAbsentWarning"]:
    """
    M13.PassiveMandateAbsentWarning check for FLOOR_THEN_RETURN accounts.

    Fires when ALL THREE conditions hold for an instrument in such an account:
      1. passive_mandate_eligible == False (§11)
      2. current_weight >= 15% of account
      3. instrument_30d return is negative (actively repricing down) — or unknown
         AND account is within 5pp of floor breach

    Parameters
    ----------
    floor_accounts:
        Same format as check_all_floor_accounts: list of
        {"account_id": str, "weights": Dict[ticker, float]}.
    cal:
        CalibrationState — §11 passive_mandate_eligible + §9.5 + §4.1.
    probs:
        ScenarioProbabilities — used to compute floor proximity.
    holdings_30d_returns:
        Optional dict of ticker → 30d return fraction. None if unavailable.

    Returns
    -------
    List of PassiveMandateAbsentWarning — one per (account, ticker) pair that fires.
    """
    from .instruments import blended_scenario_return as _bsr

    warnings_out: List[PassiveMandateAbsentWarning] = []
    floor_threshold = cal.floor_params.floor_loss_prob_threshold
    prob_map = {"A": probs.A, "B": probs.B, "C": probs.C,
                "D": probs.D, "E": probs.E, "F": probs.F}

    for acct in floor_accounts:
        account_id = acct["account_id"]
        weights    = acct["weights"]

        # Compute current worst-scenario portfolio return (for proximity check)
        worst_return: Optional[float] = None
        for scenario, p in prob_map.items():
            if p / 100.0 < floor_threshold:
                continue
            scenario_ret = sum(
                w * _bsr(t, scenario, "conservative", cal)
                for t, w in weights.items()
                if t in cal.instruments
            )
            if worst_return is None or scenario_ret < worst_return:
                worst_return = scenario_ret

        floor_proximity = (worst_return * 100.0) if worst_return is not None else None
        # floor_proximity > 0 means above floor; <= 0 means breached or very close
        near_breach = (
            floor_proximity is not None
            and floor_proximity < _FLOOR_PROXIMITY_THRESHOLD_PP
        )

        for ticker, weight in weights.items():
            if weight < _PASSIVE_CONCENTRATION_THRESHOLD:
                continue   # below 15% — not a material concentration

            entry = cal.instruments.get(ticker)
            if entry is None or entry.passive_mandate_eligible:
                continue   # has passive floor or unknown — skip

            instrument_30d = (
                holdings_30d_returns.get(ticker)
                if holdings_30d_returns else None
            )
            repricing_down = (instrument_30d is not None and instrument_30d < 0)

            if repricing_down or (instrument_30d is None and near_breach):
                warnings_out.append(PassiveMandateAbsentWarning(
                    account_id=account_id,
                    ticker=ticker,
                    current_weight=weight,
                    instrument_30d=instrument_30d,
                    passive_eligible=False,
                    floor_proximity_pp=floor_proximity,
                ))

    return warnings_out
