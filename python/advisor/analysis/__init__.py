"""
analysis/ — ANALYSIS_ENGINE: signal computation modules (Stage 3).

Public API — import directly from advisor.analysis:

  from advisor.analysis import (
      # M11 credit
      compute_credit_signal,
      # M14 regime
      compute_divergence_signal,
      entry_extension_guard,
      # M17 cascade
      sector_stress_score,
      compute_yield_curve_signal,
      assess_cascade_level,
      # M15 instruments
      validate_classifications,
      blended_scenario_return,
      classify_instrument,
      dominant_directive,
      # M03 arithmetic
      normalize_scores,
      apply_floors,
      apply_session_cap,
      check_b_vs_c,
      apply_all_rules,
  )
"""
from .credit import compute_credit_signal
from .regime import compute_divergence_signal, entry_extension_guard
from .cascade import (
    sector_stress_score,
    compute_yield_curve_signal,
    assess_cascade_level,
)
from .instruments import (
    validate_classifications,
    blended_scenario_return,
    classify_instrument,
    dominant_directive,
)
from .scenario_math import (
    normalize_scores,
    apply_floors,
    apply_session_cap,
    check_b_vs_c,
    apply_all_rules,
)
from .floor_monitor import (
    current_holdings_floor_check,
    check_all_floor_accounts,
)

__all__ = [
    # M11
    "compute_credit_signal",
    # M14
    "compute_divergence_signal",
    "entry_extension_guard",
    # M17
    "sector_stress_score",
    "compute_yield_curve_signal",
    "assess_cascade_level",
    # M15
    "validate_classifications",
    "blended_scenario_return",
    "classify_instrument",
    "dominant_directive",
    # M03 arithmetic
    "normalize_scores",
    "apply_floors",
    "apply_session_cap",
    "check_b_vs_c",
    "apply_all_rules",
    # M13 floor monitor
    "current_holdings_floor_check",
    "check_all_floor_accounts",
]
