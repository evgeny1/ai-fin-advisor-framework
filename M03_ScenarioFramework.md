# M03 — Scenario Framework
<!-- Version: 1.3 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M03_ScenarioFramework
  Version:         1.3
  Sub-project:     ANALYSIS_ENGINE
  Reason to change: scenario definitions, probability derivation rules, B vs C separation, or scoring methodology changes.
                    scenarioWeightedAllocation() and minimumConvictionWeight() delegate to M13 — changes to those go to M13.
  Inputs consumed:  List<DataReading>       // from FetchRegistry.fetchAll()
                    PriorProbabilities      // from Session_Log §8
  Outputs produced: ScenarioProbabilities, ProbabilityVector
  Calibration deps: CALIBRATION_STATE §2 (Brent/GDP/CPI trigger thresholds used in scoring)
                    SESSION_LOG §8 (prior probabilities — 25pp cap enforcement)
  Types consumed:   @see FW_Types.md — DataReading, ScenarioProbabilities
-->

```
MODULE ScenarioFramework {

  // ─── CORE PRINCIPLE ───────────────────────────────────────────────────
  // Scenarios describe STRUCTURAL MACRO ENVIRONMENTS — not individual events.
  // They are durable across driver shifts.
  // Only probability weights change when the primary driver changes.
  // Scenario LABELS never change.

  // ─── SIX UNIVERSAL SCENARIOS ──────────────────────────────────────────────

  ENUM Scenario {
    A: {
      label:            "Soft Landing"
      core_condition:   "Inflation normalizes; Fed cuts gradually; growth holds; no major supply shock"
      binding_variable: fed_normalization
      portfolio_impl:   "Risk assets rally broadly; defensives and inflation hedges underperform"
      protocol:         @see M09_ScenariosABC.ScenarioA
    }
    B: {
      label:            "Stagflation Lock"
      core_condition:   "Inflation elevated and persistent; Fed constrained; growth stagnant/contracting; no new discrete supply event required"
      binding_variable: fed_constraint
      portfolio_impl:   "Inflation assets, commodities, infrastructure outperform; equities grind lower"
      protocol:         @see M09_ScenariosABC.ScenarioB
      // B is a STATE (persistent equilibrium) — not an event
    }
    C: {
      label:            "Inflationary Shock"
      core_condition:   "Discrete, dateable supply-side disruption deepens; energy spikes; new chokepoints verified"
      binding_variable: supply_shock_severity
      portfolio_impl:   "Energy surges; inflation hedges spike; equities sell off; geopolitical premium outperforms"
      protocol:         @see M09_ScenariosABC.ScenarioC
      // C is an EVENT (discrete, dateable) — not a persistent state
    }
    D: {
      label:            "Deflationary Recession"
      core_condition:   "Demand collapse; credit stress; Fed easing aggressively; commodities fall"
      binding_variable: demand_destruction
      portfolio_impl:   "Long Treasuries rally; commodities fall; inflation hedges mixed; equities impaired"
      protocol:         @see M10_ScenariosDEF.ScenarioD
    }
    E: {
      label:            "Structural Rupture"
      core_condition:   "Dollar reserve status challenged; systemic financial stress; sovereign debt stress"
      binding_variable: reserve_system_integrity
      portfolio_impl:   "Real assets critical; equities severely impaired; sovereign debt stress"
      protocol:         @see M10_ScenariosDEF.ScenarioE
    }
    F: {
      label:            "Growth Overheat"
      core_condition:   "Strong nominal GDP growth; inflation rising but below stagflationary threshold; Fed tightening but not yet constraining demand; no supply shock"
      binding_variable: growth_momentum
      portfolio_impl:   "Cyclicals and financials outperform; long-duration bonds sell off; growth stocks underperform value; inflation hedges underperform"
      protocol:         @see M10_ScenariosDEF.ScenarioF
    }
  }

  INVARIANT {
    REQUIRE: sum(all_scenario_probabilities) == 100%  // at all times
  }

  // ─── B vs C SEPARATION RULE ───────────────────────────────────────────────
  // These two are separable by different T1 indicators and must never
  // simultaneously exceed 30% without explicit documented justification.

  RULE BvsCRule(current_inflation_elevated: Bool) {
    IF current_inflation_elevated {
      ASK: is_there_verifiable_dateable_supply_side_event?
      IF yes → Scenario_C_applies
      IF no  → Scenario_B_applies  // persistent, self-sustaining, no new trigger

      CONSTRAINT simultaneous_high_probability {
        IF B.probability > 30% AND C.probability > 30% {
          REQUIRE: explicit_documented_justification_in_session
        }
      }
    }
  }

  // ─── PROBABILITY UPDATE DISCIPLINE ──────────────────────────────────────────────

  GUARD ProbabilityDiscipline {
    NEVER:  move_probabilities on single_unverified_report
    ALWAYS: move_when T1_evidence_confirms_directional_shift
    ALWAYS: state_explicitly what_evidence_caused_each_update
  }

  // ─── RECALIBRATION TRIGGER ───────────────────────────────────────────────────

  RULE RecalibrationRule {
    WHEN primary_driver_shifts_materially {
      recalibrate: all_six_scenario_probability_weights  // in this session
      NEVER:       change_scenario_labels
      ALWAYS:      document_evidence_that_caused_probability_shift
    }
  }

  // ─── SIGNAL CONVERGENCE RULE ──────────────────────────────────────────────────

  RULE SignalConvergence {
    IF independent_T1_signals_pointing_same_direction >= 3
    WITHIN 72h_window {
      ALLOW: larger_magnitude_probability_shift_in_single_step
      CONSTRAINT max_single_session_shift: 25_percentage_points
                 // regardless of convergence signal count
      REQUIRE: document_each_signal_and_source
    }
  }

  // ─── SCENARIO-WEIGHTED ALLOCATION MATH ───────────────────────────────────────────
  // Used by M06_ClientAndAdvisory and all execution protocols.
  // idealAllocation() is defined in M13_GrowthObjectives — delegates there.

  FUNCTION scenarioWeightedAllocation(asset, account) -> Float {
    // account parameter required — load from the "Allocation - Objectives" file
    // @see M13_GrowthObjectives.idealAllocation()
    result = 0
    FOR each s IN Scenario {
      result += s.probability × M13_GrowthObjectives.idealAllocation(asset, s, account)
    }
    RETURN result
    // NEVER present allocation numbers without showing the full per-scenario breakdown
    // NEVER present without showing M13.idealAllocation() inputs per scenario
  }

  // ─── MINIMUM CONVICTION WEIGHT ───────────────────────────────────────────────
  // Defined in M13_GrowthObjectives.minimumConvictionWeight().
  // All references in M09/M10 execution protocols resolve to M13 version.
  // account parameter required.

  FUNCTION minimumConvictionWeight(asset, account) -> Float {
    RETURN M13_GrowthObjectives.minimumConvictionWeight(asset, account)
    // Do NOT call this without an account context.
    // Do NOT estimate — always compute explicitly.
  }

  // ─── SCENARIO PROBABILITY DERIVATION ─────────────────────────────────────────────
  // Run at every session start, after intel gathering and primary driver
  // identification, before producing the Intelligence Briefing.
  // Produces a reproducible probability vector from binding variable scores.
  // Any session running the same data produces the same output within a
  // narrow, auditable band — eliminating unconstrained fresh-session judgment.
  // @see Project_Instructions_MCP.md "Session start sequence" Step 6 (advisor_apply_scoring)
  // @see M12_FileProtocol.WriteBack §8 (output persisted at session end)
  // @see M04_BriefingFormat.ScenarioProbabilities (output display format)

  FUNCTION DeriveScenarioProbabilities() -> ProbabilityVector {

    // ─── SCORE SCALE ─────────────────────────────────────────────────────────────────────
    // Applied to every check below:
    // 0 = conditions actively diverging from this scenario
    // 1 = conditions neutral or not yet informative
    // 2 = conditions consistent with but not yet at formal trigger level
    // 3 = trigger condition MET (T1 confirmed, sustain period satisfied)

    // ─── PER-SCENARIO CHECKS ──────────────────────────────────────────────────────────────
    // Confirmed during ENG-2 review (2026-06-17): the full check-by-check scoring rubric
    // (score thresholds, evidence requirements, per-check wording) is generated verbatim
    // into ScoringQuestion.question text by scoring_questions.py.generate_questions() —
    // the exact text Claude receives from advisor_run_computation() already contains this
    // rubric, word for word at review time. Maintaining a second copy here only risks the
    // two drifting apart; this file is no longer consulted to score a live session.
    // @see python/advisor/orchestrator/scoring_questions.py — generate_questions()
    //
    // Check membership per scenario (which raw scores sum into which scenario):
    //   raw_A = check_fed + check_energy + check_credit                    (max 5)
    //   raw_B = check_cpi + check_gdp + check_fed                          (max 8)
    //   raw_C = check_brent + check_cpi + check_chokepoint                 (max 7)
    //   raw_D = check_unemployment + check_fed + credit_check + check_gdp  (max 11)
    //   raw_E = dedollar_check + stress_check + check_ig                   (max 7)
    //   raw_F = MAX(check_gdp + check_cpi + check_fed + check_noshock, 0)  (max 8)
    // Full original criteria (pre-shrink) recoverable from git history of this file.

    // ─── NORMALIZATION ─────────────────────────────────────────────────────────────────────

    PROCEDURE Normalize {
      total_raw = sum(raw_A, raw_B, raw_C, raw_D, raw_E, raw_F)
      IF total_raw == 0 {
        HARD_STOP
        FLAG: "All scenario scores are zero. Data fetch likely incomplete.
               NEVER produce probabilities from zero-total. Re-run intel gathering."
      }
      FOR each scenario s {
        base_probability(s) = (raw_score(s) / total_raw) × 100%
      }
    }

    // ─── APPLY STRUCTURAL FLOORS ────────────────────────────────────────────────────────────────

    PROCEDURE ApplyFloors {
      FLOOR_VALUE: 3%  // no scenario goes to zero — all carry non-trivial tail risk

      FOR each scenario s WHERE base_probability(s) < 3% {
        shortfall(s) = 3% - base_probability(s)
        SET base_probability(s) = 3%
      }
      IF any_floors_applied {
        total_shortfall = sum(shortfall_values)
        FOR each above-floor scenario s (descending by raw_score) {
          reduction(s) = total_shortfall × (raw_score(s) / sum_of_above_floor_raw_scores)
          base_probability(s) -= reduction(s)
        }
      }

      // D structural floor — overrides normalization; cannot be distributed away
      IF HY_RecessionPricing_fired {  // @see M11_CreditAndCalibration.HY_RecessionPricing
        IF base_probability(D) < 25% {
          excess = 25% - base_probability(D)
          SET base_probability(D) = 25%
          FOR each scenario s WHERE s != D {
            base_probability(s) -= excess × (base_probability(s) /
                                   sum_of_non_D_probabilities)
          }
        }
      }

      VERIFY: sum(all_base_probabilities) == 100%
    }

    // ─── APPLY SESSION CAP ───────────────────────────────────────────────────────────────────

    PROCEDURE ApplySessionCap {
      prior = load_from §8_Session_State_Log  // @see M12_FileProtocol.WriteBack

      IF prior EXISTS AND prior.date >= current_session_date - 7_calendar_days {
        FOR each scenario s {
          delta = abs(base_probability(s) - prior.scenario_probabilities(s))
          IF delta > 25pp {
            CHECK: @see M03_ScenarioFramework.SignalConvergence
            IF SignalConvergence_documented {
              ALLOW: full derived shift
              REQUIRE: log_each_signal_and_source in briefing
            } ELSE {
              direction = SIGN(base_probability(s) - prior.scenario_probabilities(s))
              base_probability(s) = prior.scenario_probabilities(s) + (direction × 25pp)
              FLAG: "25pp session cap applied to [s].
                     Derived: [X]%. Prior: [Y]%. Capped at: [Z]%.
                     Full shift requires SignalConvergence: 3+ T1 signals within 72h."
            }
          }
        }
        IF any_caps_applied {
          normalize_remaining_to_sum_100()
        }
        VERIFY: sum(all) == 100%
      }

      IF prior DOES_NOT_EXIST OR prior.date < current_session_date - 7_calendar_days {
        LOG: derivation_method = "initial_derivation"
             reason = "No recent session state found in §8 (or > 7 days old).
                       25pp cap not applicable this session."
      }
    }

    // ─── B vs C CHECK ──────────────────────────────────────────────────────────────────────

    PROCEDURE CheckBvsC {
      IF base_probability(B) > 30% AND base_probability(C) > 30% {
        REQUIRE: explicit_documented_justification in session briefing
      }
    }

    // ─── EXECUTION ORDER ───────────────────────────────────────────────────────────────────

    SEQUENCE {
      1: score_all_six_scenarios  // using data from completed GatherIntel
      2: Normalize()
      3: ApplyFloors()
      4: ApplySessionCap()
      5: CheckBvsC()
      6: output_to_briefing       // @see M04_BriefingFormat.ScenarioProbabilities
      7: write_to_session_state   // at session end @see M12_FileProtocol.WriteBack §8
    }

    GUARD ScoringIntegrity {
      NEVER:  use_market_prices as primary_evidence for scenario probability
      NEVER:  embed trajectory_arguments inside binding_variable_scores
      ALWAYS: score_only_current_T1_confirmed_binding_variable_status
      ALWAYS: surface_trajectory_risk in M02_IntelGathering.identifyPrimaryDriver
              challenger_drivers field — not inside probability scores
    }

    RETURN probability_vector  // all six probabilities summing to 100%
  }

}
```
