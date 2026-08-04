# M13 — Growth Objectives
<!-- Version: 1.5 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M13_GrowthObjectives
  Version:         1.5
  Sub-project:     PORTFOLIO_ADVISOR
  Reason to change: account objective logic, feasibility methodology, or recalibration sequence changes.
                    Return table values: go to CALIBRATION_STATE §4 only — not here.
  Inputs consumed:  ScenarioProbabilities (from M03); BlendedReturn (from M15)
                    account objective profiles (from the "Allocation - Objectives" file)
  Outputs produced: AllocationTarget, FeasibilityResult, FloorBreachAlert
  Calibration deps: CALIBRATION_STATE §4.1 (return table), §4.2–4.3 (multipliers), §4.4 (floor/cap params)
  Types consumed:   @see FW_Types.md — ScenarioProbabilities, BlendedReturn, AllocationTarget, FeasibilityResult, FloorBreachAlert
-->

```
MODULE GrowthObjectives {

  // ─── ACCOUNT OBJECTIVE PROFILES ─────────────────────────────────────────
  // Lives in: dedicated "Allocation - Objectives" file (own single-tab spreadsheet
  //           as of 2026-07-12 — split out of the combined "Allocation" file)
  // Fetch via: M12_FileProtocol.fetchAllocationFile("Allocation - Objectives")
  // Updatable: any session — no quarter-end gate required
  // REQUIRE: loaded before any idealAllocation() or FeasibilityCheck() call

  STRUCT AccountObjectiveProfile {
    account_id:             String   // e.g., "IRA_primary", "Roth_IRA", "Taxable_primary"
    owner:                  String   // "primary" | "relative"
    planning_horizon_years: Int
    objective_type:         Enum [
      TARGET_THEN_RETURN,   // Target feasibility is primary. Maximize return within it.
                            // Used for: IRA (primary), Roth IRA (primary + relative)
      RETURN_THEN_TARGET,   // Maximize return per unit drawdown risk. Target is secondary check.
                            // Used for: Taxable primary
      FLOOR_THEN_RETURN,    // Hard nominal floor is primary, non-negotiable. Maximize return within it.
                            // Used for: Relative's IRAs (owner is 75yo — floor takes lexicographic priority)
      PRESERVATION          // No nominal loss on rolling 12-month basis. Return is secondary.
                            // Used for: Taxable preservation
    ]
    floor_nominal_loss:     Bool     // true = no nominal loss constraint active
    concentration_cap:      Float    // max single position as % of account value
                                     // ⚑ CALIBRATION_DATED → CALIBRATION_STATE §4.4
    drawdown_tolerance:     Float    // per M06_ClientAndAdvisory — 0.30 to 0.40
  }

  // ─── TARGET MULTIPLIER ───────────────────────────────────────────────────
  // SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-17; wiring
  // closed via ENG-16). For TARGET_THEN_RETURN accounts (IRA, Roth IRA): a regime-
  // dependent, probability-weighted multiplier, floor-enforced regardless of
  // probability vector, that prevents cliff effects from dominant-scenario shifts.
  // Routes to §4.2 (IRA) or §4.3 (Roth) multiplier tables. Not separately exposed
  // as its own MCP field — its result surfaces inside `advisor_evaluate_allocation()`'s
  // `feasibility.target_multiplier` field whenever proposed_allocations is supplied.
  // Formula: multiplier = MAX(Σ probability[s] × table_multiplier[s], table_floor)
  // RequiredRealReturn: real annualized return needed to reach target over the
  // planning horizon — surfaces as `feasibility.required_return`.
  // Formula: required_return = (multiplier ^ (1/horizon_years)) − 1
  // @see python/advisor/portfolio/allocation.py compute_target_multiplier(), required_real_return()

  // ─── EXPECTED REAL ANNUALIZED RETURN TABLE ───────────────────────────────
  // Empirically grounded structural estimates per functional role per scenario.
  // NOT forecasts. NEVER present as precise predictions.
  // Conservative end: used for ALL feasibility checks and ideal allocation ranking.
  // Upside end: disclosed in briefing only — never used in computation.
  // ⚑ ALL VALUES CALIBRATION_DATED → CALIBRATION_STATE §4.1
  // Empirical basis documented in CALIBRATION_STATE §4.1 and Calibration Log (2026-04-23 entry)
  // Review at quarter-end alongside §1 and §2 thresholds.

  TABLE ExpectedRealReturn[role][scenario] {
    // ALWAYS load from CALIBRATION_STATE §4.1 at session start.
    // Do NOT use values from memory or prior sessions.
    // @see CALIBRATION_STATE §4.1 for current values and revision history.
  }

  // ─── FLOOR COMPUTATION ──────────────────────────────────────────────────
  // SUPERSEDED — wired, surfaces as the `floor` field in
  // `advisor_evaluate_allocation()`'s AllocationTarget output. Independently
  // defined — does NOT reference scenarioWeightedAllocation(); breaks the
  // circularity in the prior M03 definition. REDUCE_TO_MIN directives (the
  // old "minimumConvictionWeight()") resolve to this same floor point — there
  // is no separate minimum-conviction computation anymore, by design.
  // Formula: floor = MAX([FLOOR_FRACTION] × current_weight, [FLOOR_MINIMUM_PCT] × account_total)
  // (⚑ FLOOR_FRACTION / FLOOR_MINIMUM_PCT → CALIBRATION_STATE §4.4. Never zero
  // unless both inputs are zero.)
  // @see python/advisor/portfolio/allocation.py compute_floor()

  // ─── IDEAL ALLOCATION ────────────────────────────────────────────────────
  // SUPERSEDED — wired, surfaces as the `per_scenario` field in
  // `advisor_evaluate_allocation()`'s AllocationTarget output (one ideal weight
  // per scenario A–F). Resolves the gap in M03_ScenarioFramework.scenarioWeightedAllocation().
  // Spec the Python implements:
  //   1. Resolve primary-role directive from M09/M10 DIRECTIVES (via M15.classifyInstrument()
  //      — NOT M08.classifyRole(), superseded per M15's INTEGRATION note).
  //   2. Map directive → permitted [min_w, max_w] weight range:
  //        Exit → [0, 0] | REDUCE_TO_MIN → [floor, floor] | Reduce → [floor, current]
  //        Hold | Evaluate → [current, current] | Add | Add_aggressive → [current, cap]
  //      If min_w == max_w, the directive fully determines weight — no ranking needed.
  //   3. Otherwise: rank all holdings by blended conservative return in this scenario;
  //      scale linearly within [min_w, max_w] by rank (best return → max_w).
  //   4. FLOOR_THEN_RETURN / PRESERVATION accounts: if blended conservative return is
  //      negative under an Add/Add_aggressive/Hold directive, cap weight at floor.
  //   5. Clamp to [min_w, max_w] ∩ [0, cap] and return.
  // @see python/advisor/portfolio/allocation.py ideal_allocation()

  // ─── MINIMUM CONVICTION WEIGHT (REDUCE_TO_MIN) ───────────────────────────
  // SUPERSEDED — folded into ComputeFloor() above and the REDUCE_TO_MIN row of
  // DIRECTION_BOUNDS. No longer a separate function: REDUCE_TO_MIN directives
  // resolve directly to the floor point, non-circularly. `M03_ScenarioFramework.
  // minimumConvictionWeight()` is fully retired by this.

  // ─── FEASIBILITY CHECK ───────────────────────────────────────────────────
  // SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-17; wiring
  // closed via ENG-16). Wired into `advisor_evaluate_allocation()`'s `feasibility`
  // field — only computed when `proposed_allocations` is passed; never present
  // allocation numbers without it having run. Runs after scenario-weighted
  // allocations are produced, before any recommendation is presented. Uses
  // conservative blended return throughout — never upside.
  //
  // Always computes the scenario-weighted conservative portfolio return first,
  // then branches by account.objective_type:
  //   TARGET_THEN_RETURN  — feasible iff portfolio_return >= RequiredRealReturn();
  //                         on failure, reports shortfall_pp and fires RecalibrationSequence
  //                         (below — NOT yet wired, still Claude's job to run by hand)
  //   RETURN_THEN_TARGET  — always feasible (optimization, not a gate); reports
  //                         drawdown_adjusted_return = portfolio_return / drawdown_tolerance,
  //                         and target_met as an advisory note only
  //   FLOOR_THEN_RETURN   — hard floor: no nominal loss allowed in any scenario whose
  //                         probability >= §4.4.floor_nominal_loss_probability_threshold;
  //                         a breach sets floor_breached=true and fires RecalibrationSequence
  //                         at FLOOR_PROTECTION priority
  //   PRESERVATION        — feasible iff portfolio_return >= 0; failure fires
  //                         RecalibrationSequence at FLOOR_PROTECTION priority
  // @see python/advisor/portfolio/allocation.py feasibility_check()

  // ─── RECALIBRATION SEQUENCE ──────────────────────────────────────────────
  // SPEC ONLY, added 2026-08-03 (re-evaluation/ad-hoc session, client-drafted
  // via chat) -- NO PYTHON IMPLEMENTATION. FeasibilityCheck has referenced
  // "fires RecalibrationSequence" by name since this file's earliest version
  // without this function ever being defined; ENG-24 (CLOSED) noted "no
  // Python implementation -- still 100% manual" but never wrote down what
  // "manual" means step by step either. This block is that missing
  // definition. ("Floor Defense Guard" in Session_Log.md/Portfolio_State.md
  // open items 2026-07-31 onward was informal session shorthand for this
  // same gap -- not a separate thing, and not itself ever specified anywhere
  // before this entry.)
  //
  // Distinguish carefully from the per-instrument "floor" already computed
  // by ComputeFloor() (§4.4 Base floor / Minimum floor -- a REDUCE_TO_MIN
  // resting point for ONE instrument). RecalibrationSequence operates on the
  // OTHER floor concept: the account-level §4.4 floor_nominal_loss_probability_
  // threshold (currently 15%, CALIBRATION_DATED) -- no nominal portfolio loss
  // allowed in any scenario at or above that probability.

  FUNCTION RecalibrationSequence(account, current_weights, breach) {

    REQUIRE: breach.floor_breached == true
    REQUIRE: account.objective_type IN [FLOOR_THEN_RETURN, PRESERVATION]

    // STEP 1 -- qualifying constraint set
    // breach.worst_scenario is a DIAGNOSTIC (the single worst-return
    // qualifying scenario) -- it is NOT the full constraint set. Every
    // scenario at or above the threshold must independently clear zero.
    // Confirmed live 2026-08-03: at that session's operating probabilities
    // (A=27.3/B=36.4/C=27.3/D=E=F=3), THREE scenarios (A, B, C) cleared the
    // 15% bar simultaneously on both Relative accounts, but
    // advisor_evaluate_allocation() only ever surfaced worst_scenario "A" --
    // B and C's individual portfolio returns were never actually checked
    // against zero in that session. This is exactly the gap this step
    // closes.
    Q = { s IN SCENARIOS : prob(s) >= CALIBRATION_STATE.§4.4.
          floor_nominal_loss_probability_threshold }

    // STEP 2 -- eligible universe
    // U = current holdings, plus any instrument already ADOPTED in §11 for
    // a role this account is permitted to hold (do not introduce a
    // candidate ticker here that hasn't cleared M07.AutoDisqualify() --
    // re-check existing holdings too, not just new candidates, since
    // eligibility metrics can change session to session; @see "How to make
    // a recommendation" in Project_Instructions_MCP.md).
    U = tickers(current_weights) UNION AdoptedCandidatesForAccount(account)

    // STEP 3 -- greedy iterative reallocation (primary method)
    // Full LP (scipy.optimize.linprog over the same constraints) was
    // considered and set aside for v1: this framework's own bias throughout
    // (M06.SimplicityTest, transparent step-by-step procedures everywhere
    // else) favors an auditable, one-move-at-a-time search whose
    // intermediate states can be logged and reviewed, over an opaque
    // solver call. Revisit LP as a v2 upgrade path if greedy search proves
    // too slow or gets stuck short of a solution the LP relaxation would
    // find (a real risk -- greedy is not guaranteed optimal or even
    // complete). Track that comparison as its own coding-session item, not
    // decided finally here.
    //
    // reference = current_weights (deviation-minimization anchor -- prefer
    // the smallest total turnover that clears the floor, not the
    // highest-return solution; turnover has tax/transaction-cost
    // consequences this function does not otherwise price in)
    //
    // bounded_step = 2pp per iteration (CALIBRATION_DATED -- placeholder,
    // needs a real value set at implementation time)
    //
    // WHILE NOT (ALL s IN Q: PortfolioReturn(w, s) >= 0) AND U has untried
    // moves:
    //   worst = ARGMIN_{s IN Q} PortfolioReturn(w, s)
    //   donor = ARGMIN_{i IN U : w[i] > ComputeFloor(i)} r[i][worst]
    //           // worst performer under the currently-binding scenario,
    //           // above its OWN per-instrument floor -- never trim an
    //           // instrument below its own ComputeFloor() point inside
    //           // this search; if every instrument is already at its
    //           // floor, that instrument drops out of the donor pool
    //   receiver = ARGMAX_{i IN U : w[i] < concentration_cap} r[i][worst]
    //           // best performer under the binding scenario, below its cap
    //   step = MIN(donor.available_weight, receiver.headroom_to_cap,
    //              bounded_step)
    //   move `step` from donor to receiver
    //   recompute PortfolioReturn(w, s) for ALL s IN Q via
    //   M15.blendedScenarioReturn() -- not just the previously-worst one;
    //   a move that fixes one scenario can push a different qualifying
    //   scenario negative

    // STEP 4 -- outcome
    // IF ALL s IN Q: PortfolioReturn(w, s) >= 0:
    //   RETURN { status: RESOLVED, proposed_allocations: w,
    //            per_scenario_returns: {s: PortfolioReturn(w,s) for s in Q},
    //            iterations, tickers_touched }
    // ELSE:
    //   RETURN { status: NO_SOLUTION_IN_UNIVERSE,
    //            best_attempt: w, remaining_shortfall_pp,
    //            per_scenario_returns: {s: PortfolioReturn(w,s) for s in Q},
    //            message: "No reallocation within the current §11-eligible
    //                      universe clears the floor across all qualifying
    //                      scenarios. Options: (a) external cash
    //                      contribution; (b) revisit
    //                      floor_nominal_loss_probability_threshold or
    //                      objective_type itself with the client -- a
    //                      calibration/objective question, not something
    //                      this function should silently work around; (c)
    //                      source a new instrument/role candidate via
    //                      M07.AutoDisqualify() + M16 calibration." }

    GUARD RecalibrationOutputHandling {
      NEVER: treat a RESOLVED result as authorization to execute -- output
             is a CANDIDATE proposed_allocations only. Still routes through
             the full "How to make a recommendation" chain (M06.SimplicityTest,
             M07.AutoDisqualify on any newly-introduced ticker,
             M06.TaxPlacement, M06.HoldJustification if applicable) and
             REQUIRES explicit client confirmation before any trade.
      NEVER: report a partial improvement (worst_return_pct less negative
             but still < 0 for any s IN Q) as RESOLVED, or elide the
             RESOLVED/NO_SOLUTION_IN_UNIVERSE distinction in a briefing or
             chat response. This is not a hypothetical failure mode -- it is
             exactly what happened in the 2026-08-03 session, where a
             directionally-helpful hand-tested reallocation (floor breach
             -0.75%->-0.48% IRA, -2.02%->-1.58% Roth) was presented without
             a status flag distinguishing "improved" from "cleared," and
             both accounts in fact stayed floor_breached=true throughout.
      ALWAYS: report the FULL per_scenario_returns set for Q, not just
              whichever scenario was worst before the search started.
    }

    RETURN
  }
  // @see python/advisor/portfolio/allocation.py -- NOT YET IMPLEMENTED;
  // wiring this in (plus the Step 3 greedy-vs-LP decision) is a dedicated
  // coding-session item, not something to build inside an advisory session.
  // Suggest opening as a new FRAMEWORK_BACKLOG.md ENG item at next coding
  // session (ENG-24 should be reopened or superseded -- it was closed
  // without this definition existing, which is the actual gap).


  // ─── PASSIVE MANDATE ABSENT WARNING ─────────────────────────────────────
  // SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-17; wiring
  // closed pre-existing). Update 3 — added v1.1. Advisory only — does not block
  // execution or FeasibilityCheck. Runs automatically inside `advisor_run_computation()`
  // for FLOOR_THEN_RETURN accounts when `floor_account_weights_json` is supplied;
  // surfaces as `passive_mandate_warnings` in the tool output.
  //
  // Rationale: VTI/VOO hold a structural price floor from mandated passive inflows
  // (401K contributions, target-date fund rebalancing, index inclusion). Sector/thematic
  // ETFs with passive_mandate_eligible=false have no such floor. When actively repricing
  // downward with concentrated weight in a FLOOR_THEN_RETURN account, the asymmetry
  // warrants explicit surfacing — market participants may continue selling without a
  // natural passive bid to slow the descent.
  //
  // Fires when ALL THREE conditions hold for an instrument in a FLOOR_THEN_RETURN account:
  //   1. §11 passive_mandate_eligible == false
  //   2. current_market_weight >= 15% of account
  //   3. instrument_30d < 0 (actively repricing down)
  //      OR instrument_30d unavailable AND account within 5pp of floor breach
  // @see python/advisor/analysis/floor_monitor.py passive_mandate_absent_warnings()

  // ─── CURRENT HOLDINGS FLOOR CHECK ───────────────────────────────────────
  // SUPERSEDED — wired, runs automatically inside `advisor_run_computation()`
  // (Step 3b, prior probs) and `advisor_apply_scoring()` (Step 6b, newly derived
  // probs, auto-fires if any scenario shifted >= 5pp) — surfaces as
  // `floor_breach_alerts` / `floor_breach_alerts_6b`. `status == "FLOOR_BREACH"`
  // must be surfaced before any other session content, per Project_Instructions_MCP.md.
  //
  // Distinct from FeasibilityCheck(): FeasibilityCheck checks PROPOSED allocations
  // (pre-trade); this checks ACTUAL current holdings at current market prices —
  // detecting between-session price drift that has moved a FLOOR_THEN_RETURN
  // account toward or into floor breach without waiting for a formal trade proposal.
  // Data source: the "Allocation" / "Allocation - Relative's Schwab Accounts" files'
  //   GOOGLEFINANCE current values / account_total —
  // NEVER target allocation weights, which reflect intent, not current state.
  // Fires (any scenario s with probability >= §4.4.floor_nominal_loss_probability_threshold):
  //   Σ current_market_weight[t] × blendedScenarioReturn(t, s, "conservative") < 0
  // @see python/advisor/analysis/floor_monitor.py current_holdings_floor_check()

  // ─── RECALIBRATION SEQUENCE ──────────────────────────────────────────────
  // SUPERSEDED (ENG-24, 2026-06-18). Wired into `advisor_evaluate_allocation()`
  // — when `proposed_allocations` is passed and `feasibility.feasible == False`,
  // the tool automatically calls `recalibration_sequence()` and adds a
  // `recalibration` block to the JSON output. No separate Claude call needed.
  //
  // Spec summary (Python implements all of this):
  //   Fires when FeasibilityCheck returns feasible=False. Both steps always run.
  //   Step 1 — anchor identification: tickers with proposed_weight > floor are
  //     anchors (proxy for M06.SimplicityTest; Claude can pass
  //     `high_conviction_tickers` to the function to override with the true set).
  //     Computes: anchor_weight, anchor_return_contribution, residual_weight,
  //     residual_required_return = (required − anchor_return) / residual_weight.
  //   Step 2a — reallocation: rank non-anchor tickers by conservative return in
  //     dominant scenario; re-set each to idealAllocation(t, dominant_scenario).
  //     If revised portfolio_return >= required: gap_closed_by_reallocation=true,
  //     revised_allocations populated. Both steps still run.
  //   Step 2b — new instrument: if gap still persists, find the highest-return
  //     unheld role from §4.1 return table in dominant scenario.
  //     If positive return found: candidate_role + estimated gap closure pp.
  //     If none: no_candidate_message with "consider: extend horizon / revise
  //     multiplier / accept reduced target."
  // @see python/advisor/portfolio/allocation.py recalibration_sequence()
  // @see python/advisor/mcp_server.py _tool_evaluate_allocation() (wiring)

  // ─── INTEGRATION WITH M03 ────────────────────────────────────────────────

  // M03.scenarioWeightedAllocation(asset, account) now calls:
  //   M13.idealAllocation(asset, scenario, account) for each scenario s
  //   account parameter required — load from the "Allocation - Objectives" file
  //
  // M03.minimumConvictionWeight() is fully retired (see MINIMUM CONVICTION WEIGHT
  // above) — REDUCE_TO_MIN directives resolve directly to ComputeFloor()'s floor
  // point. There is no M13.minimumConvictionWeight() function to call instead.

  // Full per-asset per-account recommendation flow:
  SEQUENCE RecommendationFlow {
    1: load_profiles    → "Allocation - Objectives" file
    2: load_return_tbl  → CALIBRATION_STATE §4.1 (loaded at session start with §4.2–4.4)
    3: classify         → M15_InstrumentClassification.classifyInstrument(asset)
                          // NOT M08_FunctionalRoles.classifyRole() — superseded, see M15
    4: derive_probs     → M03_ScenarioFramework.DeriveScenarioProbabilities()
    5: compute_ideals   → M13.idealAllocation(asset, s, account) for each s
    6: compute_weighted → M03.scenarioWeightedAllocation(asset, account)
    7: feasibility      → M13.FeasibilityCheck(account, proposed_allocations)
    8: IF feasible      → present with full math shown
       IF not_feasible  → M13.RecalibrationSequence() — complete before presenting
    9: validate         → M06.SimplicityTest, M07.AutoDisqualify, M06.TaxPlacement
    10: hold_ev         → M06.HoldJustification (EV math required if hold recommended)
  }
  // In practice (Pattern B / MCP mode): steps 1–8 collapse into one
  // `advisor_evaluate_allocation()` call — @see Project_Instructions_MCP.md
  // "How to make a recommendation". This SEQUENCE is the conceptual map it implements.

  // ─── SESSION LOAD REQUIREMENT ─────────────────────────────────────────────
  // M13 is Project Knowledge — always in context.
  // The following CALIBRATION_STATE sections must be loaded at session start
  // (read from the local filesystem via `advisor_run_computation()` —
  // @see Project_Instructions_MCP.md, M12_DriveProtocol; NEVER GitHub for this read).

  REQUIRE at_session_start {
    CALIBRATION_STATE §4.1  // return table — required for idealAllocation()
    CALIBRATION_STATE §4.2  // IRA target multipliers
    CALIBRATION_STATE §4.3  // Roth IRA target multipliers
    CALIBRATION_STATE §4.4  // floor and concentration parameters
    account_objective_profiles  // from the "Allocation - Objectives" file
    // Absence of any of the above = session invalid for growth objective computations
  }

}
```
