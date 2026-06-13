"""
portfolio/directives.py — M09/M10 RESPONSES table as Python data.

Maps (role_id, scenario) → DirectiveCode for the nine roles explicitly
defined in M09_ScenariosABC.md and M10_ScenariosDEF.md.

Design:
  - Covers the original nine M08.Role roles. Newer §11 roles not in M09/M10
    return HOLD with a quality_flag via get_directive().
  - Scenario E rate directives are PATHWAY_CONDITIONAL; resolve via
    resolve_e_pathway_directive() after reading YieldCurveSignal.e_pathway_type.
  - OCP: adding a role → add rows to this table + §11. No other edits needed.
  - Role names sourced from §11.ROLE_REGISTRY (not hardcoded against M08 enum).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..types import DirectiveCode, DirectiveResult, EPathwayType

# ── Core 9-role × 6-scenario directives (M09 / M10 RESPONSES) ─────────────────
#
# Keys:   (role_id, scenario_str)
# Values: DirectiveCode — one RESPONSES entry per M09/M10 role × scenario
#
# Encoding conventions:
#   REDUCE_50PCT   → M09.ScenarioA geopolitical_premium "reduce to 50% of current weight"
#   REDUCE_TO_MIN  → any "reduce_to minimumConvictionWeight()" directive
#   HOLD_WATCH     → M10.ScenarioD real_asset "Hold WITH monitoring / downgrade to watch"
#   HOLD_EVALUATE  → M10.ScenarioD rate_long "Hold OR Add IF EV_calculation_supports"
#   EVALUATE       → directive says "evaluate" or "assess" before acting (EV calc required)
#   PATHWAY_CONDITIONAL → M10.ScenarioE rate roles — branch on e_pathway_type

DIRECTIVES: Dict[Tuple[str, str], DirectiveCode] = {

    # ── Scenario A: Soft Landing (M09.ScenarioA.RESPONSES) ───────────────────
    ("geopolitical_premium",                "A"): DirectiveCode.REDUCE_50PCT,
    ("inflation_hedge_precious_metals",     "A"): DirectiveCode.HOLD,
    ("inflation_hedge_commodity_linked",    "A"): DirectiveCode.HOLD,
    ("real_asset_contracted_revenue",       "A"): DirectiveCode.HOLD,
    ("policy_driven_thematic_equity",       "A"): DirectiveCode.HOLD,
    ("rate_sensitive_income_short_duration","A"): DirectiveCode.REDUCE,
    ("rate_sensitive_income_long_duration", "A"): DirectiveCode.HOLD,
    ("broad_market_equity_domestic",        "A"): DirectiveCode.ADD,
    ("broad_market_equity_international",   "A"): DirectiveCode.EVALUATE,

    # ── Scenario B: Stagflation Lock (M09.ScenarioB.RESPONSES) ───────────────
    ("geopolitical_premium",                "B"): DirectiveCode.HOLD,
    ("inflation_hedge_precious_metals",     "B"): DirectiveCode.ADD,
    ("inflation_hedge_commodity_linked",    "B"): DirectiveCode.ADD,
    ("real_asset_contracted_revenue",       "B"): DirectiveCode.HOLD,
    ("policy_driven_thematic_equity",       "B"): DirectiveCode.REDUCE_TO_MIN,
    ("rate_sensitive_income_short_duration","B"): DirectiveCode.HOLD,
    ("rate_sensitive_income_long_duration", "B"): DirectiveCode.REDUCE,
    ("broad_market_equity_domestic",        "B"): DirectiveCode.REDUCE_TO_MIN,
    ("broad_market_equity_international",   "B"): DirectiveCode.REDUCE,

    # ── Scenario C: Inflationary Shock (M09.ScenarioC.RESPONSES) ─────────────
    ("geopolitical_premium",                "C"): DirectiveCode.ADD,
    ("inflation_hedge_precious_metals",     "C"): DirectiveCode.HOLD,
    ("inflation_hedge_commodity_linked",    "C"): DirectiveCode.HOLD,
    ("real_asset_contracted_revenue",       "C"): DirectiveCode.HOLD,
    ("policy_driven_thematic_equity",       "C"): DirectiveCode.HOLD,
    ("rate_sensitive_income_short_duration","C"): DirectiveCode.HOLD,
    ("rate_sensitive_income_long_duration", "C"): DirectiveCode.REDUCE,
    ("broad_market_equity_domestic",        "C"): DirectiveCode.REDUCE_TO_MIN,
    ("broad_market_equity_international",   "C"): DirectiveCode.REDUCE,

    # ── Scenario D: Deflationary Recession (M10.ScenarioD.RESPONSES) ─────────
    ("geopolitical_premium",                "D"): DirectiveCode.REDUCE,
    ("inflation_hedge_precious_metals",     "D"): DirectiveCode.EVALUATE,
    ("inflation_hedge_commodity_linked",    "D"): DirectiveCode.REDUCE,
    ("real_asset_contracted_revenue",       "D"): DirectiveCode.HOLD_WATCH,
    ("policy_driven_thematic_equity",       "D"): DirectiveCode.REDUCE,
    ("rate_sensitive_income_short_duration","D"): DirectiveCode.EVALUATE,
    ("rate_sensitive_income_long_duration", "D"): DirectiveCode.HOLD_EVALUATE,
    ("broad_market_equity_domestic",        "D"): DirectiveCode.REDUCE_TO_MIN,
    ("broad_market_equity_international",   "D"): DirectiveCode.EXIT,

    # ── Scenario E: Structural Rupture (M10.ScenarioE.RESPONSES) ─────────────
    # Rate directives are pathway-conditional — resolve via resolve_e_pathway_directive().
    ("geopolitical_premium",                "E"): DirectiveCode.HOLD,
    ("inflation_hedge_precious_metals",     "E"): DirectiveCode.ADD_AGGRESSIVE,
    ("inflation_hedge_commodity_linked",    "E"): DirectiveCode.HOLD,
    ("real_asset_contracted_revenue",       "E"): DirectiveCode.HOLD,
    ("policy_driven_thematic_equity",       "E"): DirectiveCode.REDUCE_TO_MIN,
    ("rate_sensitive_income_short_duration","E"): DirectiveCode.PATHWAY_CONDITIONAL,
    ("rate_sensitive_income_long_duration", "E"): DirectiveCode.PATHWAY_CONDITIONAL,
    ("broad_market_equity_domestic",        "E"): DirectiveCode.REDUCE_TO_MIN,
    ("broad_market_equity_international",   "E"): DirectiveCode.EXIT,

    # ── Scenario F: Growth Overheat (M10.ScenarioF.RESPONSES) ────────────────
    ("geopolitical_premium",                "F"): DirectiveCode.HOLD,
    ("inflation_hedge_precious_metals",     "F"): DirectiveCode.REDUCE_TO_MIN,
    ("inflation_hedge_commodity_linked",    "F"): DirectiveCode.HOLD,
    ("real_asset_contracted_revenue",       "F"): DirectiveCode.HOLD,
    ("policy_driven_thematic_equity",       "F"): DirectiveCode.HOLD,
    ("rate_sensitive_income_short_duration","F"): DirectiveCode.HOLD,
    ("rate_sensitive_income_long_duration", "F"): DirectiveCode.REDUCE,
    ("broad_market_equity_domestic",        "F"): DirectiveCode.ADD,
    ("broad_market_equity_international",   "F"): DirectiveCode.EVALUATE,
}

# Roles explicitly covered by M09/M10 RESPONSES tables
_M09_M10_ROLES: frozenset = frozenset({
    "geopolitical_premium",
    "inflation_hedge_precious_metals",
    "inflation_hedge_commodity_linked",
    "real_asset_contracted_revenue",
    "policy_driven_thematic_equity",
    "rate_sensitive_income_short_duration",
    "rate_sensitive_income_long_duration",
    "broad_market_equity_domestic",
    "broad_market_equity_international",
})

# Roles that are pathway-conditional in Scenario E
_E_PATHWAY_ROLES: frozenset = frozenset({
    "rate_sensitive_income_short_duration",
    "rate_sensitive_income_long_duration",
})

_VALID_SCENARIOS: frozenset = frozenset("ABCDEF")


# ── Public API ─────────────────────────────────────────────────────────────────

def get_directive(role_id: str, scenario: str) -> DirectiveResult:
    """
    Resolve M09/M10 RESPONSES directive for (role_id, scenario).

    For Scenario E rate roles, returns PATHWAY_CONDITIONAL with a pathway_note.
    For newer §11 roles not in M09/M10, returns HOLD with a quality_flag.

    Parameters
    ----------
    role_id : str
        Role identifier from §11.ROLE_REGISTRY.
    scenario : str
        One of "A", "B", "C", "D", "E", "F".

    Returns
    -------
    DirectiveResult with resolved code, optional conflict_flag, pathway_note,
    and quality_flags.
    """
    if scenario not in _VALID_SCENARIOS:
        return DirectiveResult(
            code=DirectiveCode.HOLD,
            role_id=role_id,
            quality_flags=[f"INVALID_SCENARIO:'{scenario}' — must be A–F. Defaulted to HOLD."],
        )

    code = DIRECTIVES.get((role_id, scenario))
    if code is not None:
        result = DirectiveResult(code=code, role_id=role_id)
        if code == DirectiveCode.PATHWAY_CONDITIONAL:
            result.pathway_note = (
                f"Scenario E pathway-conditional: read YieldCurveSignal.e_pathway_type "
                f"before acting on '{role_id}'. "
                f"Call resolve_e_pathway_directive(role_id, pathway_type) to resolve."
            )
        return result

    # Role not in M09/M10 — newer §11 role, no defined directive yet
    return DirectiveResult(
        code=DirectiveCode.HOLD,
        role_id=role_id,
        quality_flags=[
            f"UNREGISTERED_DIRECTIVE: '{role_id}' has no M09/M10 RESPONSES entry for "
            f"scenario {scenario}. Defaulting to HOLD. Add rows to "
            f"portfolio/directives.py + §11 to define behaviour for this role."
        ],
    )


def resolve_e_pathway_directive(
    role_id: str,
    pathway_type: EPathwayType,
) -> DirectiveResult:
    """
    Resolve M10.ScenarioE pathway-conditional directive for rate-sensitive roles.

    Called after get_directive() returns PATHWAY_CONDITIONAL. Branches on
    YieldCurveSignal.e_pathway_type per M10.ScenarioE pathway-conditional logic:

      SYSTEMIC_LIQUIDITY — 2008-analog: dollar strengthens, Treasuries rally.
      RESERVE_EROSION    — de-dollarization analog: dollar weakens, UST demand falls.

    Parameters
    ----------
    role_id : str
        Must be "rate_sensitive_income_short_duration" or "rate_sensitive_income_long_duration".
    pathway_type : EPathwayType
        From YieldCurveSignal.e_pathway_type.

    Returns
    -------
    DirectiveResult with concrete DirectiveCode (no longer PATHWAY_CONDITIONAL).
    """
    if role_id == "rate_sensitive_income_short_duration":
        if pathway_type == EPathwayType.SYSTEMIC_LIQUIDITY:
            return DirectiveResult(
                code=DirectiveCode.HOLD,
                role_id=role_id,
                pathway_note=(
                    "SYSTEMIC_LIQUIDITY: short-duration Treasuries are flight-to-safety. "
                    "Hold — roll at elevated yields while crisis resolves."
                ),
            )
        # RESERVE_EROSION
        return DirectiveResult(
            code=DirectiveCode.EVALUATE,
            role_id=role_id,
            pathway_note=(
                "RESERVE_EROSION: assess sovereign counterparty risk. "
                "Evaluate whether reserve erosion impairs demand for short-duration UST "
                "before acting."
            ),
        )

    if role_id == "rate_sensitive_income_long_duration":
        if pathway_type == EPathwayType.SYSTEMIC_LIQUIDITY:
            return DirectiveResult(
                code=DirectiveCode.HOLD_EVALUATE,
                role_id=role_id,
                pathway_note=(
                    "SYSTEMIC_LIQUIDITY: long-duration Treasuries rally as Fed cuts aggressively. "
                    "2008 empirical: TLT +26%, 10Y 4.0%→2.1%. Hold or Add if EV confirms. "
                    "⚠ §4.1 return table anchored to RESERVE_EROSION — EV may overstate "
                    "conservative return in SYSTEMIC_LIQUIDITY. Surface caveat in briefing."
                ),
            )
        # RESERVE_EROSION
        return DirectiveResult(
            code=DirectiveCode.REDUCE,
            role_id=role_id,
            pathway_note=(
                "RESERVE_EROSION: foreign demand for UST falls as reserve status erodes. "
                "Long-duration bonds face mark-to-market losses. Reduce or exit per "
                "M08.ExecutionTaxPlacement."
            ),
        )

    # Non-pathway-conditional role — shouldn't reach here in normal flow
    return DirectiveResult(
        code=DirectiveCode.EVALUATE,
        role_id=role_id,
        quality_flags=[
            f"resolve_e_pathway_directive() called for non-pathway-conditional role "
            f"'{role_id}'. Expected rate_sensitive_income_short_duration or "
            f"rate_sensitive_income_long_duration."
        ],
    )


def is_covered_role(role_id: str) -> bool:
    """Return True if role_id has explicit M09/M10 entries in DIRECTIVES."""
    return role_id in _M09_M10_ROLES


def directive_count() -> int:
    """Return number of (role, scenario) entries in DIRECTIVES table.
    Regression anchor: 9 roles × 6 scenarios = 54 entries."""
    return len(DIRECTIVES)
