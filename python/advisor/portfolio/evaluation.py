"""
portfolio/evaluation.py — M07 auto-disqualification and M08 dual-role conflict detection.

Public functions:
  auto_disqualify()    — M07.AutoDisqualify(): four hard GUARD conditions
  dual_role_conflict() — M08.DualRoleConflict(): conflicting directives in composite instruments

Design:
  - auto_disqualify() is pure on InstrumentSpec — no CalibrationState dependency.
  - dual_role_conflict() detects ADD-vs-REDUCE direction conflicts in composites.
  - Neither raises HardStopException; they return result types for the operator to act on.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..types import (
    AutoDisqualifyResult,
    CalibrationState,
    DirectiveCode,
    InstrumentSpec,
)
from .directives import get_directive

# ── M07 threshold constants (fixed structural per M07) ────────────────────────

_AUM_DISQUALIFY_M           = 100.0   # $100M — minimum AUM for 10yr hold
_TRACK_RECORD_MIN_YEARS     = 3.0     # 3 years minimum track record
_FOREIGN_CONCENTRATION_MAX  = 40.0    # 40% single-country/region cap

# Instrument types subject to foreign concentration rule (M07.ForeignExposureRule)
_CONCENTRATION_RULE_TYPES = frozenset({"active_fund", "sector_ETF"})


# ── M07.AutoDisqualify ────────────────────────────────────────────────────────

def auto_disqualify(spec: InstrumentSpec) -> AutoDisqualifyResult:
    """
    M07.AutoDisqualify(instrument) → AutoDisqualifyResult.

    Four hard GUARD conditions (M07 §AutoDisqualify):
      1. AUM < $100M AND hold_horizon >= 10 years → DISQUALIFY
      2. foreign_concentration > 40% AND type in {active_fund, sector_ETF} → DISQUALIFY
      3. revenue = commodity_dependent AND no contract_backstop → DISQUALIFY
      4. track_record < 3 years → DISQUALIFY

    Guards 1, 2, 4 surface quality_flags when metrics are unknown (None) and
    skip that guard rather than falsely disqualifying.

    Parameters
    ----------
    spec : InstrumentSpec
        Required M07 metrics for this instrument.

    Returns
    -------
    AutoDisqualifyResult — .disqualified=True terminates M07 evaluation.
    """
    flags: List[str] = []

    # Guard 1: AUM / hold horizon liquidity
    if spec.aum_millions is not None:
        if spec.aum_millions < _AUM_DISQUALIFY_M and spec.hold_horizon_years >= 10:
            return AutoDisqualifyResult(
                ticker=spec.ticker,
                disqualified=True,
                reason=(
                    f"AUM ${spec.aum_millions:.0f}M < ${_AUM_DISQUALIFY_M:.0f}M "
                    f"with {spec.hold_horizon_years}-year hold horizon. "
                    "Liquidity risk disqualification (M07 Guard 1)."
                ),
            )
    else:
        flags.append(
            f"⚠ {spec.ticker}: AUM unknown — Guard 1 (liquidity) not evaluated. "
            "Obtain AUM data before proceeding."
        )

    # Guard 2: Foreign concentration
    if spec.foreign_concentration_pct is not None:
        if (
            spec.foreign_concentration_pct > _FOREIGN_CONCENTRATION_MAX
            and spec.instrument_type in _CONCENTRATION_RULE_TYPES
        ):
            return AutoDisqualifyResult(
                ticker=spec.ticker,
                disqualified=True,
                reason=(
                    f"Single-country/region concentration "
                    f"{spec.foreign_concentration_pct:.1f}% > "
                    f"{_FOREIGN_CONCENTRATION_MAX:.0f}% for {spec.instrument_type}. "
                    "Monitoring burden disqualification (M07 Guard 2 / ForeignExposureRule)."
                ),
            )
    else:
        if spec.instrument_type in _CONCENTRATION_RULE_TYPES:
            flags.append(
                f"⚠ {spec.ticker}: foreign_concentration_pct unknown for "
                f"{spec.instrument_type} — Guard 2 not evaluated. Obtain holdings data."
            )

    # Guard 3: Revenue / contract backstop (no data-unknown branch — both fields required)
    if spec.revenue_type == "commodity_dependent" and not spec.has_contract_backstop:
        return AutoDisqualifyResult(
            ticker=spec.ticker,
            disqualified=True,
            reason=(
                "Pure commodity-dependent revenue with no contract backstop. "
                "Price-direct exposure without contractual protection "
                "disqualified (M07 Guard 3)."
            ),
        )

    # Guard 4: Track record
    if spec.track_record_years is not None:
        if spec.track_record_years < _TRACK_RECORD_MIN_YEARS:
            return AutoDisqualifyResult(
                ticker=spec.ticker,
                disqualified=True,
                reason=(
                    f"Track record {spec.track_record_years:.1f} years < "
                    f"{_TRACK_RECORD_MIN_YEARS:.0f}-year minimum. "
                    "Insufficient drawdown history (M07 Guard 4)."
                ),
            )
    else:
        flags.append(
            f"⚠ {spec.ticker}: track_record_years unknown — Guard 4 not evaluated. "
            "Obtain inception date before proceeding."
        )

    return AutoDisqualifyResult(ticker=spec.ticker, disqualified=False, quality_flags=flags)


# ── M08.DualRoleConflict ───────────────────────────────────────────────────────

def dual_role_conflict(
    ticker: str,
    scenario: str,
    cal: CalibrationState,
) -> Optional[str]:
    """
    M08.DualRoleConflict(holding, roleA, roleB) for composite instruments.

    For instruments with two or more components, detects when role-level
    M09/M10 directives point in conflicting directions (ADD vs REDUCE/EXIT).

    M08 rule: when conflicting, identify the dominant role by weight and apply
    that role's directive. Flag for manual review if dominant role is unclear.

    Parameters
    ----------
    ticker : str
        Composite instrument ticker — must be in cal.instruments.
    scenario : str
        One of "A"–"F".
    cal : CalibrationState
        §11 instrument entries with component weights.

    Returns
    -------
    Conflict description string if ADD-vs-REDUCE conflict exists, else None.
    Single-role instruments always return None.
    """
    entry = cal.instruments.get(ticker)
    if entry is None or len(entry.components) <= 1:
        return None

    def _direction(code: DirectiveCode) -> str:
        if code in (DirectiveCode.ADD, DirectiveCode.ADD_AGGRESSIVE):
            return "ADD"
        if code in (
            DirectiveCode.REDUCE,
            DirectiveCode.REDUCE_TO_MIN,
            DirectiveCode.REDUCE_50PCT,
            DirectiveCode.EXIT,
        ):
            return "REDUCE"
        return "HOLD"

    comp_directives: List[Tuple[str, float, DirectiveCode]] = [
        (c.role_id, c.weight, get_directive(c.role_id, scenario).code)
        for c in entry.components
    ]

    directions = {_direction(code) for _, _, code in comp_directives}

    if "ADD" not in directions or "REDUCE" not in directions:
        return None  # no conflict

    sorted_comps = sorted(comp_directives, key=lambda x: x[1], reverse=True)
    primary_role, primary_weight, primary_code = sorted_comps[0]

    parts = [
        f"{role}({weight:.0%}): {code.value}"
        for role, weight, code in sorted_comps
    ]

    return (
        f"DualRoleConflict [{ticker} scenario {scenario}]: "
        f"conflicting directions — {'; '.join(parts)}. "
        f"Dominant role '{primary_role}' ({primary_weight:.0%}) → apply {primary_code.value}. "
        f"M08 rule: if dominant role is unclear this session, flag for manual review "
        f"and take no action."
    )
