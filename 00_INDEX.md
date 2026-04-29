# 00 — Index & Module Map
<!-- Personal Financial Advisor Framework — Pseudo-Code Edition -->
<!-- Source documents: Framework_Main_v1, Framework_Extension_v1, Calibration_State, Amendment 1, Amendment 2 -->
<!-- Last updated: April 28, 2026 (M15 added; extensible role registry; composite instrument decomposition; GitHub write workflow codified in M12) -->

```
FRAMEWORK PersonalFinancialAdvisor {

  // ─── MODULE REGISTRY ───────────────────────────────────────────────────────────

  MODULES {
    M01_SourceIntegrity        // Source tiers, propaganda checklist, symmetric skepticism
    M02_IntelGathering         // Fetch list, price integrity, gathering procedure §1.5, primary driver §1.6
    M03_ScenarioFramework      // Six scenarios, probability rules, B vs C rule, scenario-weighted math
    M04_BriefingFormat         // Intelligence briefing output template §1.8
    M05_SessionInit            // Session initialization sequence §2 (inputs + execution order)
    M06_ClientAndAdvisory      // Client profile §3, advisory principles §4
    M07_InstrumentEval         // Instrument evaluation framework §5
    M08_FunctionalRoles        // Dynamic position classification, dual-role conflicts, execution guards
    M09_ScenariosABC           // Execution protocols: Scenario A, B, C
    M10_ScenariosDEF           // Execution protocols: Scenario D, E, F
    M11_CreditAndCalibration   // Extension v1: credit signal protocol §1.5a, calibration discipline §1.10
    M12_DriveProtocol          // Amendment 2: hybrid GitHub+Drive file access protocol; canonical GitHub write workflow
    M13_GrowthObjectives       // Growth objectives, ideal allocation, feasibility check, recalibration sequence
    M14_MarketRegime           // Market desensitization signal, underweight review, entry extension guard
    M15_InstrumentClassification  // Extensible role registry, composite decomposition, blended scenario returns
    CALIBRATION_STATE          // Live threshold values — load every session (GitHub)
  }

  // ─── LOAD ORDER (every session) ────────────────────────────────────────────────────

  SESSION_START_SEQUENCE {
    // @see M05_SessionInit.SessionStartSequence for full detail
    1:  M12_FileProtocol.fetchAllocation()        // Google Drive — hard gate
    2:  confirm_pending_decisions
    3:  M12_FileProtocol.fetchCalibrationState()  // GitHub — includes §4 return table, §8 session state, §9 M14 thresholds, §11 instrument classification
        → apply CALIBRATION_STATE thresholds (not remembered values)
        → apply M13 return table and multipliers (§4.1–4.4)
        → apply M14 market regime thresholds (§9)
        → load §11 role registry and instrument classification table
        → run M15.ValidateClassifications() — all allocation instruments must be in §11
        → load account objective profiles from Allocation "Objectives" tab
    4:  M02_IntelGathering.FETCH_LIST  (includes M11.CreditSignal.FetchList
                                        and M14.FetchList — VIX trailing, position trailing performance)
    5:  M02_IntelGathering.identifyPrimaryDriver()
    6:  M03_ScenarioFramework.RecalibrationRule  +  M11.CalibrationDiscipline.SessionLoad
    7:  M02_IntelGathering.GatherIntel STEPS 2–5
        + M14.ComputeDivergenceSignal()
        → IF composite IN [HIGH, MODERATE]: M14.UnderweightReviewTrigger(account) for each account
    8:  M04_BriefingFormat.IntelligenceBriefing  (includes M14.MarketRegimeSignal block)
    9:  portfolio discussion
        → before any ADD executes: M14.EntryExtensionGuard(asset, account)
    10: M12_FileProtocol.WriteBack  // GitHub — §7 credit + §8 scenario state
  }

  // ─── PRECEDENCE RULES ──────────────────────────────────────────────────────────────

  PRECEDENCE [highest → lowest] {
    1: M11_CreditAndCalibration   // Extension v1 overrides main framework where they conflict
    2: M12_DriveProtocol          // Amendment 2 supersedes any prior fetch/write instructions
    3: M13_GrowthObjectives       // Growth objective logic supersedes M03 idealAllocation and minimumConvictionWeight
    4: CALIBRATION_STATE          // live threshold values override any remembered values
    4.5: M14_MarketRegime         // EntryExtensionGuard gates M09/M10 ADD directives before execution
                                  // NEVER routes signals into M03 probability derivation
    4.7: M15_InstrumentClassification  // blendedScenarioReturn() supersedes direct §4.1 role lookups
                                       // classifyInstrument() supersedes classifyRole() for allocation computations
    5: M09_ScenariosABC, M10_ScenariosDEF   // execution protocols
    6: M01–M08                    // core framework
  }

  // ─── KEY CROSS-REFERENCE MAP ────────────────────────────────────────────────────────

  CROSS_REFERENCES {

    // Source validation chain
    any_claim
      → M01_SourceIntegrity.classify()
      → M01_SourceIntegrity.PropagandaChecklist
      → M01_SourceIntegrity.SymmetricSkepticism

    // Session data flow
    market_data
      → M02_IntelGathering.FETCH_LIST
      → M02_IntelGathering.PriceDataIntegrity
      → M02_IntelGathering.GatherIntel (Steps 1–5)
      → M02_IntelGathering.identifyPrimaryDriver()
      → M03_ScenarioFramework.RecalibrationRule?
      → M04_BriefingFormat.IntelligenceBriefing

    // Credit signal flow (Extension v1)
    credit_spreads
      → M11_CreditAndCalibration.SignalConvergenceTest()
      → M11_CreditAndCalibration.AsymmetricWeighting
      → M11_CreditAndCalibration.ScenarioRouting()
      → [HY_StressBeginning | HY_RecessionPricing | IG_TransmissionReached | CCC_TailFirstWidening]
      → CALIBRATION_STATE §1 (threshold deltas)

    // Market regime signal flow (M14)
    market_regime_signal
      → M14_MarketRegime.ComputeDivergenceSignal()
      → M14_MarketRegime.UnderweightReviewTrigger()     // if composite HIGH or MODERATE
      → M14_MarketRegime.EntryExtensionGuard()          // at execution time, before any ADD
      // NEVER routes into M03.DeriveScenarioProbabilities — ScoringIntegrity applies absolutely

    // Instrument classification flow (M15)
    instrument_classification
      → M15_InstrumentClassification.ValidateClassifications()   // session start — HARD_STOP if unclassified
      → M15_InstrumentClassification.classifyInstrument()        // §11 lookup — ComponentVector
      → M15_InstrumentClassification.blendedScenarioReturn()     // weighted blend → replaces §4.1 direct lookup
      → M15_InstrumentClassification.dominantDirective()         // for M09/M10 execution directives
      // To add role: M15.AddRole() → §11.ROLE_REGISTRY + §4.1 row + §3 log
      // To add instrument: DetermineComponentWeights() → §11.INSTRUMENT_CLASSIFICATION_TABLE entry

    // Allocation and growth objective flow (M13)
    allocation_recommendation
      → M13_GrowthObjectives.RecommendationFlow
        1: load account profiles (Allocation sheet "Objectives" tab)
        2: load return table (CALIBRATION_STATE §4.1–4.4)
        3: M15_InstrumentClassification.classifyInstrument()  // replaces M08.classifyRole()
           M15_InstrumentClassification.dominantDirective()   // for directive per scenario
        4: M03_ScenarioFramework.DeriveScenarioProbabilities()
        5: M13_GrowthObjectives.idealAllocation() per scenario
           → uses M15.blendedScenarioReturn() for all return lookups
        6: M03_ScenarioFramework.scenarioWeightedAllocation()
        7: M13_GrowthObjectives.FeasibilityCheck()
        8: M13_GrowthObjectives.RecalibrationSequence() if infeasible
        9: M06.SimplicityTest, M07.AutoDisqualify, M06.TaxPlacement
        10: M06.HoldJustification (EV math if hold)

    // Position action flow
    execution_trigger
      → M15_InstrumentClassification.classifyInstrument(holding)  // replaces M08.classifyRole()
      → M15_InstrumentClassification.dominantDirective(holding, scenario)
      → M08_FunctionalRoles.DualRoleConflict?  // if component directives conflict
      → M14_MarketRegime.EntryExtensionGuard()  (if ADD — before executing)
      → M08_FunctionalRoles.ExecutionGuards  (graduated response)
      → [M09_ScenariosABC | M10_ScenariosDEF].RESPONSES[role]
      → M08_FunctionalRoles.ExecutionTaxPlacement
      → M13_GrowthObjectives.minimumConvictionWeight()?  // replaces M03 version

    // Recommendation validation chain
    recommendation
      → M06_ClientAndAdvisory.SimplicityTest()
      → M06_ClientAndAdvisory.StructuralThesis
      → M06_ClientAndAdvisory.ClientBias (GUARD)
      → M06_ClientAndAdvisory.HoldJustification?  (if hold recommended)
      → M13_GrowthObjectives.FeasibilityCheck()
      → M03_ScenarioFramework.scenarioWeightedAllocation()
      → M07_InstrumentEval.AutoDisqualify?
      → M06_ClientAndAdvisory.TaxPlacement()

    // Calibration flow
    threshold_check
      → CALIBRATION_STATE (current values)
      → M11_CreditAndCalibration.CalibrationDiscipline.ReviewRelativeThreshold?
      → M11_CreditAndCalibration.CalibrationDiscipline.ReviewAbsoluteThreshold?
      → CALIBRATION_STATE §3 (log entry)
  }

  // ─── CALIBRATION-DATED THRESHOLDS AT A GLANCE ──────────────────────────────────
  // Full values in CALIBRATION_STATE. Marked ⚑ throughout modules.

  CALIBRATION_DATED_THRESHOLDS {
    HY_STRESS_DELTA:             +150 bps   // §1.1 — provisional
    HY_RECESSION_DELTA:          +300 bps   // §1.1 — provisional
    IG_TRANSMISSION_DELTA:       +60 bps    // §1.2 — provisional
    CCC_absolute_divergence:     +200 bps   // §1.3 — provisional
    WTI_floor_SGOL:              $55 | 30%-below-90d-avg   // §2.1
    Brent_trigger_C:             $110 | 40%-above-90d-avg  // §2.1
    Brent_invalidation_C:        $80 | 20%-below-90d-avg   // §2.1
    DXY_SGOL_invalidation:       105        // §2.2
    CPI_trigger_B:               4% YoY x3  // §2.3
    CPI_invalidation_B:          3% YoY x2  // §2.3
    GDP_trigger_F:               3% annualized x2  // §2.3
    GDP_invalidation_F:          2% BEA advance  // §2.3
    unemployment_trigger_D:      +0.5% over 3m   // §2.3
    // Growth objectives (M13) — all in CALIBRATION_STATE §4
    return_table:                roles × 6 scenarios [conservative, upside]  // §4.1 — roles now extensible via §11
    IRA_scenario_multipliers:    A:2.0 B:1.3 C:1.3 D:1.3 E:1.2 F:2.0  // §4.2
    Roth_scenario_multipliers:   A:3.1 B:1.3 C:1.3 D:1.6 E:1.4 F:3.1  // §4.3
    floor_fraction:              0.25× current allocation  // §4.4
    floor_minimum_pct:           2% of account value       // §4.4
    concentration_cap:           40%                        // §4.4
    floor_loss_probability_threshold: 15%                  // §4.4
    // Market regime thresholds (M14) — all in CALIBRATION_STATE §9
    entry_extension_broad_equity:        15% above 90d trailing avg  // §9.3 — provisional
    entry_extension_thematic_sector:     20% above 90d trailing avg  // §9.3 — provisional
    entry_extension_commodity_linked:    20% above 90d trailing avg  // §9.3 — provisional
    entry_extension_precious_metals:     20% above 90d trailing avg  // §9.3 — provisional
    entry_extension_real_asset:          15% above 90d trailing avg  // §9.3 — provisional
    underweight_gap_trigger:             5 pp                         // §9.2 — provisional
    underweight_appreciation_trigger:    5% over 30d                  // §9.2 — provisional
    // Instrument classification (M15) — all in CALIBRATION_STATE §11
    role_registry:               extensible list of roles + binding drivers  // §11.1
    instrument_classification:   per-instrument component weights            // §11.3
    classification_staleness:    90 calendar days (warning threshold)        // §11
    next_full_audit:             June 30, 2026
  }

  // ─── FIXED STRUCTURAL RULES (never calibration-dated) ─────────────────────────

  PERMANENT_RULES {
    source_tier_definitions:          M01_SourceIntegrity
    propaganda_scoring_method:        M01_SourceIntegrity.PropagandaChecklist
    symmetric_skepticism_mandate:     M01_SourceIntegrity.SymmetricSkepticism
    velocity_overlays(HY, IG):        M11_CreditAndCalibration (100bps/60d, 40bps/60d)
    sustain_periods:                  10 trading_days
    D_probability_floor:              25% when HY_RecessionPricing fires
    E_deescalation_threshold:         20% (all others: 25%)
    tax_placement_principles:         M06_ClientAndAdvisory.TaxPlacement
    EV_requirement_for_hold:          M06_ClientAndAdvisory.HoldJustification
    scenario_probability_sum:         must equal 100% at all times
    max_single_session_prob_shift:    25 percentage_points
    signal_convergence_window:        72 hours, >= 3 independent T1 signals
    extraordinary_price_movement:     >40% over 90d → requires 2x T1 verification
    github_fetch_rule:                owner=evgeny1, repo=ai-fin-advisor-framework, branch=master
    drive_fetch_rule:                 search-first for Allocation, never hardcode ID
    calibration_prospective_only:     M11_CreditAndCalibration.ProspectiveOnly
    anchor_positions_in_recalib:      high-conviction positions not touched in M13.RecalibrationSequence
    market_regime_boundary:           M14 signals NEVER feed M03.DeriveScenarioProbabilities
    no_hardcoded_tickers_in_modules:  instrument tickers never appear in M01–M15 module files
    no_hardcoded_roles_in_modules:    roles defined in CALIBRATION_STATE §11 only; modules reference roles by name
    blended_return_mandatory:         ALL scenario return computations use M15.blendedScenarioReturn() — never direct §4.1 lookup
    new_instrument_hard_stop:         any ticker in allocation file absent from §11 → HARD_STOP before analysis
  }

}
```
