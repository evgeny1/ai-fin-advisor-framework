"""
orchestrator/context.py — SessionContext: complete pipeline state for one session.

Produced by SessionPipeline.run(). Contains all computed artifacts from
M05 Steps 1–10. Passed to AI Call 3 (generate_briefing) and written back
to git at session end.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..types import (
    AllocationTarget,
    CalibrationState,
    CascadeSignal,
    CreditSignal,
    DataReading,
    DivergenceSignal,
    FeasibilityResult,
    FloorBreachAlert,
    RawScores,
    ScenarioProbabilities,
    ScoringAnswers,
    ScoringQuestion,
    SessionLogState,
    SessionType,
    YieldCurveSignal,
)


@dataclass
class SessionContext:
    """
    Complete state for one SessionPipeline run.

    Populated stage-by-stage in SessionPipeline._step_*() methods.
    Optional fields are None until the corresponding step completes.
    """

    # ── Session metadata ───────────────────────────────────────────────────────
    session_type:  SessionType
    session_date:  str           # ISO date string "2026-06-12"
    dry_run:       bool

    # ── Loaded config (Step 1+3) ───────────────────────────────────────────────
    cal:            Optional[CalibrationState]  = None
    log:            Optional[SessionLogState]   = None
    validate_flags: List[str]                   = field(default_factory=list)

    # ── Market data (Step 4 / M18 FetchRegistry) ──────────────────────────────
    readings:       List[DataReading]  = field(default_factory=list)
    fetch_flags:    List[str]          = field(default_factory=list)

    # ── AI Call 1 — qualitative gather (M02 QUALITATIVE_GATHER_LIST) ──────────
    qualitative:    Dict[str, str] = field(default_factory=dict)
    # Keys: "fed_guidance", "cpi_trajectory", "gdp_trajectory",
    #       "labor_market", "supply_chokepoint", "dollar_reserve", "geopolitical_broad"

    # ── Analysis signals (Step 7 / Stage 3) ───────────────────────────────────
    credit_signal:     Optional[CreditSignal]    = None
    divergence_signal: Optional[DivergenceSignal] = None
    cascade_signal:    Optional[CascadeSignal]   = None
    yield_curve_signal: Optional[YieldCurveSignal] = None
    signal_flags:      List[str]                  = field(default_factory=list)

    # ── AI Call 2 — scenario scoring (Step 6–8 / M03) ─────────────────────────
    scoring_questions: List[ScoringQuestion]  = field(default_factory=list)
    scoring_answers:   Optional[ScoringAnswers] = None
    raw_scores:        Optional[RawScores]    = None
    scenario_probs:    Optional[ScenarioProbabilities] = None
    prob_flags:        List[str]              = field(default_factory=list)

    # ── Portfolio math (Step 9 / Stage 4) ─────────────────────────────────────
    # account_id → list of AllocationTarget (one per ticker in that account)
    allocation_targets:  Dict[str, List[AllocationTarget]]  = field(default_factory=dict)
    feasibility_results: Dict[str, FeasibilityResult]       = field(default_factory=dict)
    portfolio_flags:     List[str]                          = field(default_factory=list)

    # ── M05 Step 3b/6b — CurrentHoldingsFloorCheck ────────────────────────────
    # Populated by caller before SessionPipeline.run() when allocation sheet is available.
    # Each entry: {"account_id": str, "weights": Dict[ticker, float]}
    # Only FLOOR_THEN_RETURN accounts need to be included.
    # If empty: floor check steps are skipped with a flag (no hard stop).
    floor_account_weights: List[Dict]          = field(default_factory=list)
    floor_alerts:          List[FloorBreachAlert] = field(default_factory=list)

    # ── AI Call 3 — briefing narrative (Step 8 / M04) ─────────────────────────
    briefing: Optional[str] = None

    # ── Write-back (Step 10) ──────────────────────────────────────────────────
    write_back_commit: Optional[str] = None
    write_back_flags:  List[str]     = field(default_factory=list)

    # ── Aggregate quality flags (all steps) ───────────────────────────────────
    @property
    def all_flags(self) -> List[str]:
        floor_strs = [
            f"FLOOR_BREACH_ALERT [{a.check_step}] {a.account_id}: "
            f"scenario {a.worst_scenario} = {a.worst_return_pct:.2f}%"
            for a in self.floor_alerts
        ]
        return (
            self.validate_flags + self.fetch_flags + self.signal_flags
            + self.prob_flags + self.portfolio_flags + self.write_back_flags
            + floor_strs
        )

    @property
    def has_probs(self) -> bool:
        return self.scenario_probs is not None

    @property
    def has_briefing(self) -> bool:
        return self.briefing is not None and len(self.briefing) > 0
