"""
tests/test_stage4/test_directives.py — Unit tests for portfolio/directives.py

Coverage:
  - All 54 (role, scenario) entries exist and return valid DirectiveCode
  - directive_count() regression anchor = 54
  - is_covered_role() distinguishes M09/M10 roles from newer §11 roles
  - Unregistered roles return HOLD + quality_flag
  - Invalid scenario returns HOLD + quality_flag
  - Scenario E pathway-conditional roles are flagged as PATHWAY_CONDITIONAL
  - resolve_e_pathway_directive() branches correctly for both pathway types
  - All six scenarios represented in DIRECTIVES for each of the nine roles
"""
from __future__ import annotations

import pytest

from advisor.types import DirectiveCode, EPathwayType
from advisor.portfolio.directives import (
    DIRECTIVES,
    directive_count,
    get_directive,
    is_covered_role,
    resolve_e_pathway_directive,
)

_M09_M10_ROLES = [
    "geopolitical_premium",
    "inflation_hedge_precious_metals",
    "inflation_hedge_commodity_linked",
    "real_asset_contracted_revenue",
    "policy_driven_thematic_equity",
    "rate_sensitive_income_short_duration",
    "rate_sensitive_income_long_duration",
    "broad_market_equity_domestic",
    "broad_market_equity_international",
]
_SCENARIOS = list("ABCDEF")

# ── Regression anchors ─────────────────────────────────────────────────────────

def test_directive_count_regression():
    """9 roles × 6 scenarios = 54 entries (OCP regression anchor)."""
    assert directive_count() == 54


def test_all_role_scenario_combinations_present():
    """Every M09/M10 role must have an entry for every scenario."""
    for role in _M09_M10_ROLES:
        for s in _SCENARIOS:
            assert (role, s) in DIRECTIVES, (
                f"Missing DIRECTIVES entry for ({role!r}, {s!r})"
            )


# ── Return type and validity ───────────────────────────────────────────────────

@pytest.mark.parametrize("role,scenario", [
    (r, s) for r in _M09_M10_ROLES for s in _SCENARIOS
])
def test_get_directive_returns_valid_code(role, scenario):
    result = get_directive(role, scenario)
    assert isinstance(result.code, DirectiveCode)
    assert result.role_id == role
    assert isinstance(result.quality_flags, list)


def test_get_directive_no_flags_for_known_roles():
    """Known M09/M10 roles must produce no quality_flags."""
    for role in _M09_M10_ROLES:
        for s in _SCENARIOS:
            r = get_directive(role, s)
            if r.code != DirectiveCode.PATHWAY_CONDITIONAL:
                assert r.quality_flags == [], (
                    f"{role}/{s} unexpectedly has flags: {r.quality_flags}"
                )


# ── Specific directive values (spot-check key M09/M10 cells) ──────────────────

@pytest.mark.parametrize("role,scenario,expected_code", [
    # Scenario A
    ("broad_market_equity_domestic",        "A", DirectiveCode.ADD),
    ("geopolitical_premium",                "A", DirectiveCode.REDUCE_50PCT),
    ("rate_sensitive_income_short_duration","A", DirectiveCode.REDUCE),
    ("broad_market_equity_international",   "A", DirectiveCode.EVALUATE),
    ("rate_sensitive_income_long_duration", "A", DirectiveCode.HOLD),
    # Scenario B
    ("inflation_hedge_precious_metals",     "B", DirectiveCode.ADD),
    ("policy_driven_thematic_equity",       "B", DirectiveCode.REDUCE_TO_MIN),
    ("broad_market_equity_domestic",        "B", DirectiveCode.REDUCE_TO_MIN),
    ("rate_sensitive_income_long_duration", "B", DirectiveCode.REDUCE),
    # Scenario C
    ("geopolitical_premium",                "C", DirectiveCode.ADD),
    ("rate_sensitive_income_long_duration", "C", DirectiveCode.REDUCE),
    ("broad_market_equity_domestic",        "C", DirectiveCode.REDUCE_TO_MIN),
    # Scenario D
    ("broad_market_equity_international",   "D", DirectiveCode.EXIT),
    ("real_asset_contracted_revenue",       "D", DirectiveCode.HOLD_WATCH),
    ("rate_sensitive_income_long_duration", "D", DirectiveCode.HOLD_EVALUATE),
    ("inflation_hedge_precious_metals",     "D", DirectiveCode.EVALUATE),
    # Scenario E
    ("inflation_hedge_precious_metals",     "E", DirectiveCode.ADD_AGGRESSIVE),
    ("broad_market_equity_international",   "E", DirectiveCode.EXIT),
    ("policy_driven_thematic_equity",       "E", DirectiveCode.REDUCE_TO_MIN),
    # Scenario F
    ("broad_market_equity_domestic",        "F", DirectiveCode.ADD),
    ("inflation_hedge_precious_metals",     "F", DirectiveCode.REDUCE_TO_MIN),
    ("rate_sensitive_income_long_duration", "F", DirectiveCode.REDUCE),
])
def test_specific_directive_values(role, scenario, expected_code):
    assert get_directive(role, scenario).code == expected_code


# ── Scenario E pathway-conditional ────────────────────────────────────────────

def test_rate_short_e_is_pathway_conditional():
    r = get_directive("rate_sensitive_income_short_duration", "E")
    assert r.code == DirectiveCode.PATHWAY_CONDITIONAL
    assert r.pathway_note is not None
    assert len(r.quality_flags) == 0


def test_rate_long_e_is_pathway_conditional():
    r = get_directive("rate_sensitive_income_long_duration", "E")
    assert r.code == DirectiveCode.PATHWAY_CONDITIONAL
    assert r.pathway_note is not None


@pytest.mark.parametrize("role,pathway,expected_code", [
    ("rate_sensitive_income_short_duration", EPathwayType.SYSTEMIC_LIQUIDITY, DirectiveCode.HOLD),
    ("rate_sensitive_income_short_duration", EPathwayType.RESERVE_EROSION,    DirectiveCode.EVALUATE),
    ("rate_sensitive_income_long_duration",  EPathwayType.SYSTEMIC_LIQUIDITY, DirectiveCode.HOLD_EVALUATE),
    ("rate_sensitive_income_long_duration",  EPathwayType.RESERVE_EROSION,    DirectiveCode.REDUCE),
])
def test_resolve_e_pathway(role, pathway, expected_code):
    r = resolve_e_pathway_directive(role, pathway)
    assert r.code == expected_code
    assert r.pathway_note is not None
    assert len(r.quality_flags) == 0


def test_resolve_e_pathway_non_rate_role_returns_evaluate_with_flag():
    r = resolve_e_pathway_directive("geopolitical_premium", EPathwayType.SYSTEMIC_LIQUIDITY)
    assert r.code == DirectiveCode.EVALUATE
    assert len(r.quality_flags) == 1
    assert "non-pathway-conditional" in r.quality_flags[0]


# ── Unregistered roles ────────────────────────────────────────────────────────

def test_unregistered_role_returns_hold():
    r = get_directive("secular_technology_growth", "B")
    assert r.code == DirectiveCode.HOLD


def test_unregistered_role_has_quality_flag():
    r = get_directive("systematic_trend_following", "C")
    assert len(r.quality_flags) == 1
    assert "UNREGISTERED_DIRECTIVE" in r.quality_flags[0]


def test_unregistered_role_flag_mentions_role():
    r = get_directive("consumer_defensive_equity", "A")
    assert "consumer_defensive_equity" in r.quality_flags[0]


# ── Invalid scenario ──────────────────────────────────────────────────────────

def test_invalid_scenario_returns_hold():
    r = get_directive("geopolitical_premium", "Z")
    assert r.code == DirectiveCode.HOLD
    assert len(r.quality_flags) == 1
    assert "INVALID_SCENARIO" in r.quality_flags[0]


# ── is_covered_role ───────────────────────────────────────────────────────────

def test_is_covered_role_true_for_all_m09_m10():
    for role in _M09_M10_ROLES:
        assert is_covered_role(role), f"{role} should be covered"


def test_is_covered_role_false_for_newer_roles():
    assert not is_covered_role("secular_technology_growth")
    assert not is_covered_role("systematic_trend_following")
    assert not is_covered_role("consumer_defensive_equity")
    assert not is_covered_role("floating_rate_credit_income")
