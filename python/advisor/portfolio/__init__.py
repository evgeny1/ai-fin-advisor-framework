"""
portfolio/ — PORTFOLIO_ADVISOR: EV math, directives, and feasibility (Stage 4).

Public API — import directly from advisor.portfolio:

  from advisor.portfolio import (
      # M09/M10 directives
      get_directive,
      resolve_e_pathway_directive,
      is_covered_role,
      directive_count,
      DIRECTIVES,
      # M13 allocation math
      compute_floor,
      compute_target_multiplier,
      required_real_return,
      ideal_allocation,
      scenario_weighted_allocation,
      feasibility_check,
      # M07/M08 evaluation
      auto_disqualify,
      dual_role_conflict,
  )
"""
from .directives import (
    get_directive,
    resolve_e_pathway_directive,
    is_covered_role,
    directive_count,
    DIRECTIVES,
)
from .allocation import (
    compute_floor,
    compute_target_multiplier,
    required_real_return,
    ideal_allocation,
    scenario_weighted_allocation,
    feasibility_check,
)
from .evaluation import (
    auto_disqualify,
    dual_role_conflict,
)

__all__ = [
    # directives
    "get_directive",
    "resolve_e_pathway_directive",
    "is_covered_role",
    "directive_count",
    "DIRECTIVES",
    # allocation
    "compute_floor",
    "compute_target_multiplier",
    "required_real_return",
    "ideal_allocation",
    "scenario_weighted_allocation",
    "feasibility_check",
    # evaluation
    "auto_disqualify",
    "dual_role_conflict",
]
