# M13 — Growth Objectives
<!-- Version: 1.0 | Adopted: April 23, 2026 -->
<!-- Resolves: idealAllocation() gap in M03_ScenarioFramework.scenarioWeightedAllocation() -->
<!-- Replaces: M03_ScenarioFramework.minimumConvictionWeight() -->
<!-- Provides: per-account objective profiles, expected return table, feasibility check, recalibration sequence -->
<!-- Consumes: M03 (probabilities), M08 (role classification), M09/M10 (directives), Allocation sheet (profiles) -->
<!-- Companion: @see CALIBRATION_STATE §4 (return table + multipliers — load every session) -->

```
MODULE GrowthObjectives {

  // ─── ACCOUNT OBJECTIVE PROFILES ─────────────────────────────────────────
  // Lives in: Allocation sheet — dedicated "Objectives" tab
  // Fetch via: M12_FileProtocol.fetchFile("Allocation") — profiles loaded as part of sheet
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
  // For TARGET_THEN_RETURN accounts: regime-dependent, probability-weighted.
  // Prevents cliff effects from dominant-scenario shifts.
  // Floor enforced regardless of probability vector.
  // ⚑ Per-scenario multipliers CALIBRATION_DATED → CALIBRATION_STATE §4.2 (IRA) / §4.3 (Roth)

  FUNCTION ComputeTargetMultiplier(account) -> Float {
    IF account.objective_type NOT IN [TARGET_THEN_RETURN] {
      RETURN null  // no target multiplier for non-TARGET accounts
    }

    // Load multipliers from CALIBRATION_STATE based on account type
    IF account.account_id IN ["IRA_primary", "IRA_relative"] {
      multipliers = CALIBRATION_STATE §4.2
    }
    IF account.account_id IN ["Roth_IRA_primary", "Roth_IRA_relative"] {
      multipliers = CALIBRATION_STATE §4.3
    }

    result = 0
    FOR each scenario s IN [A, B, C, D, E, F] {
      result += s.probability × multipliers[s]
    }
    RETURN MAX(result, multipliers.floor)
  }

  FUNCTION RequiredRealReturn(account) -> Float {
    // Real annualized return needed to reach target over planning horizon
    multiplier = ComputeTargetMultiplier(account)
    horizon    = account.planning_horizon_years
    RETURN (multiplier ^ (1.0 / horizon)) - 1
    // Example: IRA current B/C regime (~1.57× over 10yr) → ~4.6% real annualized
    // Example: Roth current B/C regime (~2.0× over 15yr) → ~4.7% real annualized
  }

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
  // Independently defined — does NOT reference scenarioWeightedAllocation().
  // Breaks the circularity in the prior M03 definition.

  FUNCTION ComputeFloor(asset, account) -> Float {
    base_floor    = [FLOOR_FRACTION] × AllocationSheet.currentAllocation(asset, account)
    minimum_floor = [FLOOR_MINIMUM_PCT] × account.total_value
    // ⚑ CALIBRATION_DATED values → CALIBRATION_STATE §4.4
    RETURN MAX(base_floor, minimum_floor)
    // NEVER zero unless both inputs are zero
  }

  // ─── IDEAL ALLOCATION ────────────────────────────────────────────────────
  // Resolves the gap in M03_ScenarioFramework.scenarioWeightedAllocation()
  // @see M03_ScenarioFramework.scenarioWeightedAllocation()

  FUNCTION idealAllocation(asset, scenario, account) -> Float {

    // STEP 1: Resolve role and directive
    role      = M08_FunctionalRoles.classifyRole(asset)
    directive = lookup_directive(role, scenario)  // from M09 or M10 RESPONSES

    // STEP 2: Establish permitted weight range for this directive
    floor   = ComputeFloor(asset, account)
    cap     = account.concentration_cap  // ⚑ CALIBRATION_STATE §4.4
    current = AllocationSheet.currentAllocation(asset, account)

    DIRECTION_BOUNDS {
      "Exit"             → [  0%,    0%   ]
      "reduce_to_floor"  → [floor,  floor ]
      "Reduce"           → [floor,  current]
      "Hold"             → [current, current]
      "Evaluate"         → [current, current]  // no move without EV calc per M06
      "Add"              → [current,   cap ]
      "Add_aggressive"   → [current,   cap ]   // same bounds; ranking drives toward cap
    }
    [min_w, max_w] = DIRECTION_BOUNDS[directive]

    IF min_w == max_w {
      RETURN min_w  // direction fully determines weight; no optimization needed
    }

    // STEP 3: Rank by conservative expected return in this scenario.
    //         Scale within permitted range proportionally.
    r_conservative = CALIBRATION_STATE §4.1[role][scenario].conservative

    all_roles     = [M08.classifyRole(h) for h in account.holdings]
    all_returns   = sorted_descending(
      [(role_r, CALIBRATION_STATE §4.1[role_r][scenario].conservative) for role_r in all_roles]
    )
    rank_position  = all_returns.index_of(role)          // 0 = highest return
    rank_count     = all_returns.length
    rank_fraction  = 1.0 - (rank_position / rank_count)  // 1.0 = best; ~0 = worst

    raw_weight = min_w + (rank_fraction × (max_w - min_w))

    // STEP 4: Apply floor nominal loss guard (FLOOR_THEN_RETURN and PRESERVATION accounts)
    IF account.floor_nominal_loss {
      IF r_conservative < 0 AND directive IN ["Add", "Add_aggressive", "Hold"] {
        raw_weight = MIN(raw_weight, floor)
        FLAG: "[asset.ticker] expected negative conservative real return in [scenario]
               under directive [directive]. Weight capped at floor. Surface in briefing."
      }
    }

    // STEP 5: Clamp and return
    ideal = CLAMP(raw_weight, min_w, max_w)
    ideal = MIN(ideal, cap)
    ideal = MAX(ideal, 0.0)
    RETURN ideal
  }

  // ─── UPDATED minimumConvictionWeight() ───────────────────────────────────
  // Replaces M03_ScenarioFramework.minimumConvictionWeight().
  // Non-circular: floor independently defined above.

  FUNCTION minimumConvictionWeight(asset, account) -> Float {
    floor_value = ComputeFloor(asset, account)
    weighted    = M03_ScenarioFramework.scenarioWeightedAllocation(asset, account)
    RETURN MAX(floor_value, weighted)
    // Run explicitly — never estimate.
    // Never zero unless both inputs are zero.
  }

  // ─── FEASIBILITY CHECK ───────────────────────────────────────────────────
  // Runs after scenarioWeightedAllocation() produces proposed allocations.
  // Runs before any allocation recommendation is presented.
  // Uses conservative expected return throughout.

  FUNCTION FeasibilityCheck(account, proposed_allocations) -> FeasibilityResult {

    // STEP 1: Compute scenario-weighted conservative portfolio return
    portfolio_return = 0
    FOR each scenario s IN [A, B, C, D, E, F] {
      scenario_return_s = 0
      FOR each asset a IN account.holdings {
        role              = M08.classifyRole(a)
        weight            = proposed_allocations[a]
        r                 = CALIBRATION_STATE §4.1[role][s].conservative
        scenario_return_s += weight × r
      }
      portfolio_return += s.probability × scenario_return_s
    }

    // STEP 2: Branch by objective type

    CASE account.objective_type {

      TARGET_THEN_RETURN: {
        required = RequiredRealReturn(account)
        IF portfolio_return >= required {
          RETURN FeasibilityResult {
            feasible:          true
            portfolio_return:  portfolio_return
            required_return:   required
            target_multiplier: ComputeTargetMultiplier(account)
          }
        } ELSE {
          RETURN FeasibilityResult {
            feasible:         false
            portfolio_return: portfolio_return
            required_return:  required
            shortfall_pp:     required - portfolio_return
            → fire: RecalibrationSequence(account, proposed_allocations,
                                          shortfall: required - portfolio_return,
                                          priority: TARGET)
          }
        }
      }

      RETURN_THEN_TARGET: {
        // Primary: maximize return per unit of drawdown risk. Target is advisory.
        drawdown_adjusted_return = portfolio_return / account.drawdown_tolerance
        required                 = RequiredRealReturn(account)
        RETURN FeasibilityResult {
          feasible:                 true   // always — optimization, not a gate
          portfolio_return:         portfolio_return
          drawdown_adjusted_return: drawdown_adjusted_return
          target_met:               portfolio_return >= required  // advisory note only
        }
      }

      FLOOR_THEN_RETURN: {
        // Hard floor: no nominal loss in any scenario above probability threshold.
        // ⚑ floor_nominal_loss_probability_threshold → CALIBRATION_STATE §4.4
        floor_threshold = CALIBRATION_STATE §4.4.floor_nominal_loss_probability_threshold
        floor_breach    = false
        worst_return    = null
        worst_scenario  = null

        FOR each scenario s WHERE s.probability >= floor_threshold {
          scenario_return_s = Σ [
            proposed_allocations[a]
            × CALIBRATION_STATE §4.1[M08.classifyRole(a)][s].conservative
            for a in account.holdings
          ]
          IF scenario_return_s < 0 {
            floor_breach   = true
            worst_return   = MIN(worst_return ?? scenario_return_s, scenario_return_s)
            worst_scenario = s
          }
        }

        IF floor_breach {
          RETURN FeasibilityResult {
            feasible:       false
            floor_breached: true
            worst_scenario: worst_scenario
            worst_return:   worst_return
            → fire: RecalibrationSequence(account, proposed_allocations,
                                          shortfall: abs(worst_return),
                                          priority: FLOOR_PROTECTION)
          }
        } ELSE {
          required = RequiredRealReturn(account)
          RETURN FeasibilityResult {
            feasible:         true
            portfolio_return: portfolio_return
            floor_breached:   false
            target_met:       portfolio_return >= required  // advisory
          }
        }
      }

      PRESERVATION: {
        IF portfolio_return < 0 {
          FLAG: "Preservation account: negative conservative real return expected.
                 Requires immediate review."
          RETURN FeasibilityResult {
            feasible: false
            → fire: RecalibrationSequence(account, proposed_allocations,
                                          shortfall: abs(portfolio_return),
                                          priority: FLOOR_PROTECTION)
          }
        } ELSE {
          RETURN FeasibilityResult { feasible: true, portfolio_return: portfolio_return }
        }
      }

    }
  }

  // ─── RECALIBRATION SEQUENCE ──────────────────────────────────────────────
  // Fires when FeasibilityCheck returns feasible: false.
  // Both steps always run in sequence — step 2 runs regardless of step 1 outcome.

  PROCEDURE RecalibrationSequence(account, proposed_allocations, shortfall, priority) {

    // STEP 1: Anchor identification and gap analysis
    high_conviction = []
    FOR each asset a IN account.holdings {
      IF M06.SimplicityTest(a) == true
         AND M03.scenarioWeightedAllocation(a, account) > ComputeFloor(a, account) {
        high_conviction.APPEND(a)
      }
    }
    // Anchors not touched in recalibration — held on structural thesis.

    anchor_return = Σ [
      proposed_allocations[a]
      × Σ [s.probability × CALIBRATION_STATE §4.1[M08.classifyRole(a)][s].conservative
           for s in [A,B,C,D,E,F]]
      for a in high_conviction
    ]
    anchor_weight     = Σ [proposed_allocations[a] for a in high_conviction]
    residual_weight   = 1.0 - anchor_weight
    required          = RequiredRealReturn(account)
    residual_required = IF residual_weight > 0
                        THEN (required - anchor_return) / residual_weight
                        ELSE null  // all weight anchored — gap cannot be closed by reallocation

    OUTPUT {
      "Anchor positions: [list with return contributions]"
      "Anchor weight: [%] | Anchor return contribution: [%]"
      "Residual weight available for reallocation: [%]"
      "Return required from residual positions to close gap: [residual_required%]"
      "Gap: [shortfall pp]"
    }

    // STEP 2a: Shift non-anchor positions toward higher-return roles
    dominant_scenario = M02_IntelGathering.identifyPrimaryDriver().current_dominant_driver
    non_anchor        = account.holdings EXCLUDING high_conviction
    ranked_non_anchor = sort_descending(
      [(a, Σ [s.probability × CALIBRATION_STATE §4.1[M08.classifyRole(a)][s].conservative
              for s in [A,B,C,D,E,F]])
       for a in non_anchor]
    )

    revised_allocations = copy(proposed_allocations)
    FOR each asset a IN ranked_non_anchor (descending by scenario-weighted conservative return) {
      revised_allocations[a] = idealAllocation(a, dominant_scenario, account)
    }

    revised_return = FeasibilityCheck(account, revised_allocations).portfolio_return
    revised_gap    = required - revised_return

    IF revised_gap <= 0 {
      OUTPUT: "Gap closed by reallocation alone."
              "Revised recommended allocations: [list with return projections per scenario]"
      RETURN
    }

    // STEP 2b: Evaluate new instrument if gap persists after reallocation
    OUTPUT {
      "Reallocation reduced gap. Residual gap of [revised_gap pp] remains."
      "Evaluating unheld functional roles."
    }

    all_roles_held = [M08.classifyRole(a) for a in account.holdings]
    candidate_role = highest_conservative_return_role(
                       scenario:       dominant_scenario,
                       excluding:      all_roles_held,
                       objective_type: account.objective_type
                     )

    IF candidate_role EXISTS {
      FLAG {
        "Consider adding instrument in role: [candidate_role]"
        "Conservative real return in [dominant_scenario]: [X%]"
        "Estimated gap closure if added at concentration_cap × residual_weight: [Y pp]"
        "Next step: run M07_InstrumentEval before recommending any specific instrument."
        "NEVER recommend a specific instrument without completing M07 evaluation."
      }
    } ELSE {
      FLAG {
        "No unheld role with positive conservative return in current dominant scenario."
        "Target may not be achievable under current macro regime."
        "Consider in order:"
        "  1. Extend planning horizon — if account structure permits"
        "  2. Revise target multiplier — document in CALIBRATION_STATE §4.2 or §4.3"
        "  3. Accept reduced target for this regime — flag for reassessment when"
        "     scenario probabilities shift materially"
      }
    }
  }

  // ─── INTEGRATION WITH M03 ────────────────────────────────────────────────

  // M03.scenarioWeightedAllocation(asset, account) now calls:
  //   M13.idealAllocation(asset, scenario, account) for each scenario s
  //   account parameter required — load from Allocation sheet "Objectives" tab
  //
  // M03.minimumConvictionWeight() superseded by:
  //   M13.minimumConvictionWeight(asset, account)
  //   All references in M09/M10 execution protocols resolve to M13 version

  // Full per-asset per-account recommendation flow:
  SEQUENCE RecommendationFlow {
    1: load_profiles    → Allocation sheet "Objectives" tab
    2: load_return_tbl  → CALIBRATION_STATE §4.1 (loaded at session start with §4.2–4.4)
    3: classify_role    → M08_FunctionalRoles.classifyRole(asset)
    4: derive_probs     → M03_ScenarioFramework.DeriveScenarioProbabilities()
    5: compute_ideals   → M13.idealAllocation(asset, s, account) for each s
    6: compute_weighted → M03.scenarioWeightedAllocation(asset, account)
    7: feasibility      → M13.FeasibilityCheck(account, proposed_allocations)
    8: IF feasible      → present with full math shown
       IF not_feasible  → M13.RecalibrationSequence() — complete before presenting
    9: validate         → M06.SimplicityTest, M07.AutoDisqualify, M06.TaxPlacement
    10: hold_ev         → M06.HoldJustification (EV math required if hold recommended)
  }

  // ─── SESSION LOAD REQUIREMENT ─────────────────────────────────────────────
  // M13 is Project Knowledge — always in context.
  // The following CALIBRATION_STATE sections must be loaded at session start
  // (fetched as part of Calibration_State.md from GitHub — @see M12_FileProtocol).

  REQUIRE at_session_start {
    CALIBRATION_STATE §4.1  // return table — required for idealAllocation()
    CALIBRATION_STATE §4.2  // IRA target multipliers
    CALIBRATION_STATE §4.3  // Roth IRA target multipliers
    CALIBRATION_STATE §4.4  // floor and concentration parameters
    account_objective_profiles  // from Allocation sheet "Objectives" tab
    // Absence of any of the above = session invalid for growth objective computations
  }

}
```
