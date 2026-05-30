# 00 — Index & Module Map
<!-- Personal Financial Advisor Framework — Pseudo-Code Edition -->
<!-- Source documents: Framework_Main_v1, Framework_Extension_v1, Calibration_State, Amendment 1, Amendment 2 -->
<!-- Last updated: May 29, 2026 (v1.23 portfolio-state-writeback: Portfolio_State.md added to SOURCE_MAP, -->
<!--   WriteBack upgraded to three-file atomic push, PERMANENT_RULES and NEVER list updated) -->

```
FRAMEWORK PersonalFinancialAdvisor {

  // ─── MODULE REGISTRY ─────────────────────────────────────────────────────────────────

  MODULES {
    M01_SourceIntegrity           // Source tiers, propaganda checklist, symmetric skepticism
    M02_IntelGathering            // FetchRegistry orchestrator, price integrity, gather procedure, primary driver
    M03_ScenarioFramework         // Six scenarios, probability rules, B vs C rule, scenario-weighted math
    M04_BriefingFormat            // BriefingRegistry orchestrator, render functions, briefing template
    M05_SessionInit               // Session initialization sequence — entry point
    M06_ClientAndAdvisory         // Client profile, advisory principles
    M07_InstrumentEval            // Instrument evaluation framework
    M08_FunctionalRoles           // Dynamic position classification, dual-role conflicts, execution guards
    M09_ScenariosABC              // Execution protocols: Scenario A, B, C
    M10_ScenariosDEF              // Execution protocols: Scenario D, E, F
    M11_CreditAndCalibration      // Extension v1: credit signal protocol, calibration discipline
    M12_DriveProtocol             // Amendment 2: hybrid GitHub+Drive file access; canonical write workflow
    M13_GrowthObjectives          // Growth objectives, ideal allocation, feasibility check
    M14_MarketRegime              // Market desensitization signal, underweight review, entry extension guard
    M15_InstrumentClassification  // Extensible role registry, composite decomposition, blended returns
    M16_ReturnTableCalibration    // §4.1 return table revision methodology
    M17_SystemicCascadeWarning    // Cascade chain registry, sector stress scoring (v1.4 e_pathway_type),
                                  //   yield curve protocol, supply chain indicators,
                                  //   pre-positioning ladder (role-based), data integrity rules
    M18_MarketDataFetch           // Centralized financial data registry (v1.1, added v1.20):
                                  //   all DATA_REGISTRY_ENTRIES for the framework in one place;
                                  //   PriceDataIntegrity guard. M02/M11/M14/M17 entries superseded.
    // Cross-cutting framework files (@see SUB_PROJECTS below)
    FW_Types                      // Shared type contracts (v1.1) — ALL modules consume/produce these types
    CALIBRATION_STATE             // Live threshold values (GitHub: Calibration_State.md)
    SESSION_LOG                   // Session credit readings (§7) + scenario state (§8) (GitHub)
    PORTFOLIO_STATE               // Companion project context snapshot (GitHub: Portfolio_State.md) — written every session
    CALIBRATION_LOG               // §3 calibration history archive (GitHub, read-only)
  }


  // ─── SUB-PROJECTS ────────────────────────────────────────────────────────────────────
  // Each sub-project has exactly ONE reason to change. @see FW_Types.md for contracts.
  // Phase 2 complete: M02 integrates FetchRegistry.fetchAll(); M04 integrates BriefingRegistry.assemble().
  //   Adding new data → register DATA_REGISTRY_ENTRIES in M18_MarketDataFetch only; M02 does not change.
  //   Adding new briefing section → register BRIEFING_REGISTRY_ENTRY in the owning module; M04 does not change.
  // Phase 3 target: M11 splits into M11_CreditData (DATA_INTELLIGENCE) + M11_CreditAnalysis (ANALYSIS_ENGINE).

  SUB_PROJECTS {

    DATA_INTELLIGENCE {
      reason_to_change: "data sources or source quality rules change"
      modules:          [M01_SourceIntegrity, M02_IntelGathering, M12_DriveProtocol,
                         M18_MarketDataFetch]
      extension_point:  M18_MarketDataFetch
                        // New series: add ENTRY to M18.DATA_REGISTRY_ENTRIES only.
                        // No other module changes when adding a data series.
      produces:         List<DataReading>   // @see FW_Types.md
    }

    ANALYSIS_ENGINE {
      reason_to_change: "analytical methodology changes"
      modules:          [M03_ScenarioFramework, M11_CreditAndCalibration, M14_MarketRegime,
                         M15_InstrumentClassification, M16_ReturnTableCalibration,
                         M17_SystemicCascadeWarning §1–4]
      consumes:         List<DataReading>   // from DATA_INTELLIGENCE
      produces:         [CreditSignal, RegimeSignal, CascadeSignal, YieldCurveSignal,
                         ScenarioProbabilities, BlendedReturn]   // @see FW_Types.md
    }

    PORTFOLIO_ADVISOR {
      reason_to_change: "investment strategy or client objectives change"
      modules:          [M06_ClientAndAdvisory, M07_InstrumentEval, M08_FunctionalRoles,
                         M09_ScenariosABC, M10_ScenariosDEF, M13_GrowthObjectives,
                         M17_SystemicCascadeWarning §5]
      consumes:         [ScenarioProbabilities, BlendedReturn, ClientContext]
      produces:         [AllocationTarget, AdvisoryAction, ExecutionDirective]  // @see FW_Types.md
    }

    FRAMEWORK_CORE {
      reason_to_change: "fundamental shared contracts change (rare)"
      files:            [FW_Types.md, CALIBRATION_STATE, SESSION_LOG, PORTFOLIO_STATE, 00_INDEX]
      note:             "All other sub-projects depend on FRAMEWORK_CORE. It depends on nothing."
    }

    ORCHESTRATION {
      reason_to_change: "session flow or output format changes (rare)"
      modules:          [M05_SessionInit, M04_BriefingFormat]
      extension_points: [FetchRegistry, BriefingRegistry]   // @see FW_Types.md
      note:             "Thin wiring layer. Contains NO business logic.
                         Phase 2 complete: iterates registries only — does not enumerate modules."
    }

  }  // end SUB_PROJECTS


  // ─── FILE MAP ────────────────────────────────────────────────────────────────────────

  FILE_MAP {
    // Framework core (Project Knowledge — no fetch needed)
    "FW_Types.md"                      // FRAMEWORK_CORE: shared type contracts (v1.1, added v1.20)

    // Framework modules (Project Knowledge — no fetch needed)
    "M01_SourceIntegrity.md"
    "M02_IntelGathering.md"            // v2.1: FetchRegistry orchestrator; M18 integration
    "M03_ScenarioFramework.md"
    "M04_BriefingFormat.md"            // v2.0: BriefingRegistry orchestrator
    "M05_SessionInit.md"
    "M06_ClientAndAdvisory.md"
    "M07_InstrumentEval.md"
    "M08_FunctionalRoles.md"
    "M09_ScenariosABC.md"
    "M10_ScenariosDEF.md"
    "M11_CreditAndCalibration.md"      // v1.2: DATA_REGISTRY_ENTRIES → _LEGACY; M18 integration
    "M12_DriveProtocol.md"
    "M13_GrowthObjectives.md"
    "M14_MarketRegime.md"              // v1.2: DATA_REGISTRY_ENTRIES → _LEGACY; M18 integration
    "M15_InstrumentClassification.md"
    "M16_ReturnTableCalibration.md"
    "M17_SystemicCascadeWarning.md"    // v1.4: e_pathway_type derivation; CHAIN_5 calibration gap
    "M18_MarketDataFetch.md"           // v1.1: all framework DATA_REGISTRY_ENTRIES centralized here

    // GitHub-resident operational files (fetched every session)
    "Calibration_State.md"  // LIVE CONFIG: §1–§6, §9–§12 thresholds, return table, classifications
    "Session_Log.md"        // SESSION DATA: §7 credit readings, §8 scenario state (AUTHORITATIVE for prior probs)
    "Portfolio_State.md"    // COMPANION CONTEXT: living snapshot written every session — companion project only
    "Calibration_Log.md"    // ARCHIVE: §3 history; read-only
    "Archive_[Year]Q[N].md" // Q-end compaction archives
  }


  // ─── LOAD ORDER (every session) ──────────────────────────────────────────────────────

  SESSION_START_SEQUENCE {
    // @see M05_SessionInit.SessionStartSequence for full detail
    1:  M12_FileProtocol.fetchAllocation()        // Google Drive — hard gate
    2:  confirm_pending_decisions                 // cross-check against Session_Log §8
    3:  M12_FileProtocol.fetchCalibrationState()  // GitHub — Calibration_State.md
        M12_FileProtocol.fetchSessionLog()        // GitHub — Session_Log.md (CONCURRENT)
        // Apply: §1, §2 thresholds; §4 return table (M13); §9 M14 thresholds;
        //        §11 classifications (M15); §12 M17 cascade thresholds
        // Load: §8 prior probabilities (AUTHORITATIVE)
        // Run M15.ValidateClassifications() — HARD_STOP if any instrument absent from §11
    4:  FetchRegistry.fetchAll()                  // Phase 2 complete — parallel fetch of all registered FetchSpecs
        // M02 (core market data), M11 (credit spreads), M14 (VIX trailing, equity trailing),
        // M17 (yield curve, cascade chain inputs)
        // + M02.QualitativeGatherList (geopolitical, Fed guidance — web search)
        // @see M02_IntelGathering.GatherIntel STEP 1
    5:  M02_IntelGathering.identifyPrimaryDriver()
    6:  M03_ScenarioFramework.RecalibrationRule  +  M11.CalibrationDiscipline.SessionLoad
    7:  M02_IntelGathering.GatherIntel STEPS 2–5
        + M14.ComputeDivergenceSignal()           // → RegimeSignal
        + M17.sectorStressScore()                 // → CascadeSignal.D_precursor_binding
        + M17.computeYieldCurveSignal()           // → YieldCurveSignal (incl. e_pathway_type)
        + M17.assessCascadeLevel()               // → [MONITORING | ALERT | PRE_POSITION]
        → IF M14.composite IN [HIGH, MODERATE]: M14.UnderweightReviewTrigger(account)
        → IF M17.cascadeLevel IN [ALERT, PRE_POSITION]: surface in briefing; prepare §5 review
    8:  BriefingRegistry.assemble(readings)       // Phase 2 complete — ordered section list
        // M04-owned + M11, M14, M17 registered sections assembled in declared order
        // @see M04_BriefingFormat.IntelligenceBriefing
    9:  portfolio discussion
        → before any ADD executes: M14.EntryExtensionGuard(asset, account)
        → if Scenario E active: read YieldCurveSignal.e_pathway_type before rate directives
    10: M12_FileProtocol.WriteBack
        // push_files([Calibration_State.md, Session_Log.md, Portfolio_State.md]) — atomic to master
        // Portfolio_State.md rendered by M12.constructPortfolioState() — companion project context snapshot
  }


  // ─── PRECEDENCE RULES ────────────────────────────────────────────────────────────────

  PRECEDENCE [highest → lowest] {
    1:   M11_CreditAndCalibration
    2:   M12_DriveProtocol
    2.5: M16_ReturnTableCalibration
    3:   M13_GrowthObjectives
    4:   CALIBRATION_STATE
         SESSION_LOG                   // §8 is AUTHORITATIVE for prior scenario probabilities
    4.5: M14_MarketRegime
    4.7: M15_InstrumentClassification
    4.8: M17_SystemicCascadeWarning    // sectorStressScore() = one D-binding variable;
                                       // yield curve signals = timing only, NEVER into M03;
                                       // e_pathway_type = M10 directive routing only, NEVER into M03;
                                       // AdvisoryAction.role_id = RoleID always (v1.2)
    5:   M09_ScenariosABC, M10_ScenariosDEF
    6:   M01–M08
  }


  // ─── KEY CROSS-REFERENCE MAP ─────────────────────────────────────────────────────────

  CROSS_REFERENCES {

    any_claim
      → M01_SourceIntegrity.classify()
      → M01_SourceIntegrity.PropagandaChecklist
      → M01_SourceIntegrity.SymmetricSkepticism

    market_data
      → FetchRegistry.fetchAll()  // Phase 2 complete (M02_IntelGathering.GatherIntel STEP 1)
      → M02_IntelGathering.QualitativeGatherList  // geopolitical, Fed guidance — web search
      → M02_IntelGathering.PriceDataIntegrity
      → M02_IntelGathering.GatherIntel (Steps 2–5)
      → M02_IntelGathering.identifyPrimaryDriver()
      → M03_ScenarioFramework.RecalibrationRule?
      → BriefingRegistry.assemble(readings)  // Phase 2 complete (M04_BriefingFormat.IntelligenceBriefing)

    credit_spreads
      → M11_CreditAndCalibration.SignalConvergenceTest()
      → M11_CreditAndCalibration.AsymmetricWeighting
      → M11_CreditAndCalibration.ScenarioRouting()
      → [HY_StressBeginning | HY_RecessionPricing | IG_TransmissionReached | CCC_TailFirstWidening]
      → CALIBRATION_STATE §1 (threshold deltas)
      → RETURNS CreditSignal (@see FW_Types.md)

    market_regime_signal
      → M14_MarketRegime.ComputeDivergenceSignal()       // → RegimeSignal
      → M14_MarketRegime.UnderweightReviewTrigger()
      → M14_MarketRegime.EntryExtensionGuard()
      // NEVER routes into M03.DeriveScenarioProbabilities

    cascade_early_warning
      → M17.sectorStressScore()                         // → CascadeSignal.D_precursor_binding
      → M17.computeYieldCurveSignal()                   // → YieldCurveSignal (timing + e_pathway_type)
      → M17.assessCascadeLevel()
      → IF ALERT or PRE_POSITION: §5 AdvisoryAction[] (role-based; client confirmation required)
      // NEVER routes yield_curve signals into M03
      // NEVER routes e_pathway_type into M03
      // NEVER auto-executes AdvisoryAction

    instrument_classification
      → M15.ValidateClassifications()    // session start — HARD_STOP if unclassified
      → M15.classifyInstrument()         // §11 lookup → ComponentVector
      → M15.blendedScenarioReturn()      // weighted blend → BlendedReturn
      → M15.dominantDirective()

    return_table_revision
      → M16.CalibrationMethodology() [4 layers]
      → M16.RevisionAdoption
      → M16.LivingUpdateTriggers
      → write to CALIBRATION_STATE §4.1 via M12 write-back

    allocation_recommendation
      → M13.RecommendationFlow [steps 1–10]
      → PRODUCES AllocationTarget[] (@see FW_Types.md)

    execution_trigger
      → M15.classifyInstrument() + M15.dominantDirective()
      → M08.DualRoleConflict?
      → M14.EntryExtensionGuard() (if ADD)
      → M08.ExecutionGuards (graduated response)
      → [M09 | M10].RESPONSES[role]
      → IF M10.ScenarioE: read YieldCurveSignal.e_pathway_type for rate directives
      → M08.ExecutionTaxPlacement
      → PRODUCES ExecutionDirective (@see FW_Types.md)

    advisory_action
      → PRODUCES AdvisoryAction { role_id: RoleID, ... } (@see FW_Types.md)
      // Instrument resolution: M15.classifyInstrument() + CALIBRATION_STATE §11
      // Tax placement: M06.TaxPlacement(role_id, account)

    recommendation
      → M06.SimplicityTest()
      → M06.StructuralThesis
      → M06.ClientBias (GUARD)
      → M06.HoldJustification? (if hold)
      → M13.FeasibilityCheck()
      → M03.scenarioWeightedAllocation()
      → M07.AutoDisqualify?
      → M06.TaxPlacement()

    threshold_check
      → CALIBRATION_STATE (current values)
      → M11.CalibrationDiscipline.ReviewRelativeThreshold?
      → M11.CalibrationDiscipline.ReviewAbsoluteThreshold?
      → CALIBRATION_STATE §3 (log entry)

    session_writeback
      → M12.WriteBack
      → M12.constructPortfolioState()   // renders Portfolio_State.md from session data
      → push_files([Calibration_State.md, Session_Log.md, Portfolio_State.md])
  }


  // ─── CALIBRATION-DATED THRESHOLDS AT A GLANCE ────────────────────────────────────────

  CALIBRATION_DATED_THRESHOLDS {
    HY_STRESS_DELTA:             +150 bps   // §1.1
    HY_RECESSION_DELTA:          +300 bps   // §1.1
    IG_TRANSMISSION_DELTA:       +60 bps    // §1.2
    CCC_absolute_divergence:     +200 bps   // §1.3
    WTI_floor_SGOL:              $55 | 30%-below-90d-avg
    Brent_trigger_C:             $110 | 40%-above-90d-avg
    Brent_invalidation_C:        $80 | 20%-below-90d-avg
    DXY_SGOL_invalidation:       105
    CPI_trigger_B:               4% YoY x3
    CPI_invalidation_B:          3% YoY x2
    GDP_trigger_F:               3% annualized x2
    GDP_invalidation_F:          2% BEA advance
    unemployment_trigger_D:      +0.5% over 3m
    return_table:                roles × 6 scenarios [conservative, upside]  // §4.1
    IRA_multipliers:             A:2.0 B:1.3 C:1.3 D:1.3 E:1.2 F:2.0
    Roth_multipliers:            A:3.1 B:1.3 C:1.3 D:1.6 E:1.4 F:3.1
    floor_fraction:              0.25× current allocation
    floor_minimum_pct:           2% of account value
    concentration_cap:           40%
    floor_loss_probability:      15%
    entry_extension_broad_equity:        15% above 90d trailing avg
    entry_extension_thematic_sector:     20% above 90d trailing avg
    entry_extension_commodity_linked:    20% above 90d trailing avg
    entry_extension_precious_metals:     20% above 90d trailing avg
    entry_extension_real_asset:          15% above 90d trailing avg
    underweight_gap_trigger:             5 pp
    underweight_appreciation_trigger:    5% over 30d
    role_registry:               extensible list of roles + binding drivers  // §11.1
    instrument_classification:   per-instrument component weights            // §11.3
    classification_staleness:    90 calendar days
    next_full_audit:             September 30, 2026
    // MOVE index thresholds (M11/M14 — §9.4, added v1.22)
    MOVE_NORMAL:                 < 80
    MOVE_ELEVATED:               80–100
    MOVE_STRESS:                 100–130
    MOVE_CRISIS:                 > 130
    MOVE_SYSTEMIC:               > 160
    // Cascade thresholds (M17) — §12
    farm_filings_D_alert_YoY:    +50% YoY
    natgas_D_alert:              $6.00/mmBtu sustained 30 days
    fertilizer_D_alert:          +50% above 12-month average
    KRE_underperformance_alert:  −15% vs SPX over 90 days
    SOFR_DFF_D_alert:            SOFR > DFF by +10bp sustained 5 trading days
    margin_monthly_decline_alert: −5% single month after record high
    private_credit_gate_alert:   3 distinct named fund gate events in 90 days
    E_term_premium_alert:        150 bp (THREEFYTP10)
    E_term_premium_warning:      100 bp
    E_yield_30Y_warning:         5.50%
    resteepening_min_inversion:  3 months sustained inversion before RECESSION_ONSET_PATTERN fires
  }


  // ─── FIXED STRUCTURAL RULES ──────────────────────────────────────────────────────────

  PERMANENT_RULES {
    source_tier_definitions:          M01_SourceIntegrity
    propaganda_scoring_method:        M01_SourceIntegrity.PropagandaChecklist
    symmetric_skepticism_mandate:     M01_SourceIntegrity.SymmetricSkepticism
    velocity_overlays:                M11 (100bps/60d HY; 40bps/60d IG)
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
    calibration_prospective_only:     M11.ProspectiveOnly
    market_regime_boundary:           M14 signals NEVER feed M03.DeriveScenarioProbabilities
    cascade_timing_boundary:          M17 yield curve signals inform D timing only —
                                        NEVER feed into M03.DeriveScenarioProbabilities
    e_pathway_type_boundary:          M17 e_pathway_type routes M10 directives only —
                                        NEVER feed into M03.DeriveScenarioProbabilities
    no_hardcoded_tickers_in_modules:  instrument tickers never appear in M01–M17 module files
    no_hardcoded_roles_in_modules:    roles defined in CALIBRATION_STATE §11 only
    blended_return_mandatory:         ALL scenario return computations use M15.blendedScenarioReturn()
    new_instrument_hard_stop:         any ticker in allocation file absent from §11 → HARD_STOP
    return_table_revision_M16:        NEVER revise §4.1 without M16.CalibrationMethodology() 4 layers
    MEDIUM_LOW_revision_deferred:     NEVER adopt MEDIUM/LOW confidence revisions intra-session
    session_log_authoritative:        prior probs ALWAYS from Session_Log §8; never from memory
    layer_4_neutral_distribution:     ALWAYS use A=35/B=15/C=15/D=10/E=5/F=20 for M16 Layer 4
    M17_sector_PE_source:             FMP sector-PE-snapshot REJECTED; use ETF-based PE
    M17_preposition_requires_client:  AdvisoryAction executions always require explicit client confirmation
    M17_implausibility_check:         metrics deviating >2× from historical norm → cross-reference first
    M17_chain4_T1_requirement:        CHAIN_4 score = 0 until AACER/PACER T1 source available
    // Phase 0+1 architecture rules (added v1.20)
    AdvisoryAction_RoleID_only:       AdvisoryAction.role_id is always a RoleID (FW_Types.md) —
                                        NEVER a ticker; tickers resolved from §11 at execution
    module_manifest_required:         every new module file must include a MODULE_MANIFEST block
                                        declaring: sub_project, reason_to_change, inputs_consumed,
                                        outputs_produced, calibration_deps, types consumed
    type_compliance:                  modules consume and produce types defined in FW_Types.md;
                                        cross-sub-project data flows through these types only
    RoleID_enum_is_shadow:            FW_Types.md RoleID enum shadows CALIBRATION_STATE §11;
                                        §11 is AUTHORITATIVE; update both atomically on AddRole()
    sub_project_boundary:             PORTFOLIO_ADVISOR never reads DataReading directly;
                                        ANALYSIS_ENGINE never reads AllocationTarget or AdvisoryAction;
                                        cross-boundary data flows through FW_Types.md contracts only
    // Phase 2 architecture rules (added v1.21; FetchRegistry rule updated v1.22)
    FetchRegistry_is_extension_point:    add new data series → DATA_REGISTRY_ENTRIES in M18_MarketDataFetch only;
                                           FetchRegistry.fetchAll() picks it up; M02 does not change;
                                           owning-module registration is superseded by M18 (v1.21)
    BriefingRegistry_is_extension_point: add new briefing section → BRIEFING_REGISTRY_ENTRY in owning module;
                                           BriefingRegistry.assemble() picks it up; M04 does not change
    canonical_briefing_section_ids:      PRIMARY_DRIVER | SCENARIO_PROBABILITIES | ENERGY_AND_COMMODITIES
                                           | EQUITY_MARKETS | MARKET_REGIME_SIGNAL | FIXED_INCOME_AND_RATES
                                           | CREDIT_SIGNALS | CASCADE_EARLY_WARNING
                                           | CURRENCY | CURRENT_HOLDINGS | GEOPOLITICAL_SIGNAL
                                           | PENDING_TRIGGERS | NET_ASSESSMENT
    qualitative_gather_not_DataReading:  M02.QualitativeGatherList outputs are working inputs only —
                                           NEVER registered as DataReading or FetchSpec
    portfolio_state_writeback:           Portfolio_State.md written atomically with Session_Log.md
                                           and Calibration_State.md at every session end —
                                           NEVER write Session_Log.md without also writing Portfolio_State.md
  }


  // ─── WHAT NEVER TO DO ────────────────────────────────────────────────────────────────

  NEVER [
    // M12
    hardcode_Google_Drive_file_ID,
    use_web_fetch_to_read_Google_Drive_file,
    hardcode_GitHub_SHA,
    write_to_GitHub_without_confirming_session_start_fetch_succeeded,
    // M01
    treat_T2_or_T3_source_claim_as_fact_without_T1_corroboration,
    // M02
    accept_price_from_sidebar_widget_or_aggregator_page,
    // M03
    move_scenario_probabilities_on_single_unverified_report,
    let_scenario_probabilities_sum_to_anything_other_than_100,
    // M06
    recommend_based_on_momentum_or_single_scenario_thinking,
    justify_hold_with_qualitative_reasoning_alone__show_EV_math,
    // M08
    act_on_scenario_trigger_without_T1_evidence_documented,
    // M11
    apply_recalibration_retroactively,
    // M01
    apply_asymmetric_skepticism__all_actors_get_same_scrutiny,
    // M13
    call_scenarioWeightedAllocation_without_account_context,
    // M14
    feed_M14_market_regime_signals_into_M03_DeriveScenarioProbabilities,
    // M15
    use_direct_section_4_1_lookups__route_through_blendedScenarioReturn,
    use_M08_classifyRole_for_allocation__use_M15_classifyInstrument,
    proceed_with_allocation_if_instrument_absent_from_section_11__HARD_STOP,
    hardcode_instrument_tickers_or_role_names_in_module_files,
    // M16
    revise_section_4_1_without_M16_4_layer_methodology,
    adopt_MEDIUM_or_LOW_confidence_revision_intra_session,
    run_M16_Layer_4_with_current_operating_distribution__use_neutral_A35_B15_C15_D10_E5_F20,
    load_prior_probs_from_memory_or_Calibration_State__always_Session_Log_section_8,
    // M17
    feed_M17_yield_curve_signals_into_M03_DeriveScenarioProbabilities,
    feed_e_pathway_type_into_M03_DeriveScenarioProbabilities,
    use_FMP_sector_PE_snapshot_for_sector_valuation,
    treat_sectorStressScore_3_as_standalone_D_probability_override,
    execute_PrePositioningLadder_without_explicit_client_confirmation,
    score_CHAIN_4_without_T1_AACER_PACER_source,
    include_metric_deviating_2x_from_norm_without_cross_referencing,
    // Phase 0+1 architecture rules (added v1.20)
    use_ticker_symbol_in_AdvisoryAction__role_id_must_be_RoleID_resolved_via_section_11,
    cross_sub_project_boundary_with_raw_DataReading_or_AllocationTarget__use_FW_Types_contracts,
    add_new_module_without_MODULE_MANIFEST_block,
    // Phase 2 architecture rules (added v1.21; updated v1.22)
    edit_M02_to_add_new_module_data__register_DATA_REGISTRY_ENTRIES_in_owning_module,
    edit_M04_to_add_new_briefing_section__register_BRIEFING_REGISTRY_ENTRY_in_owning_module,
    add_DATA_REGISTRY_ENTRIES_to_any_module_other_than_M18,  // all structured data series registered in M18 only; no other module defines FetchSpecs
    treat_QualitativeGatherList_output_as_DataReading,
    // Portfolio_State rules (added v1.23)
    write_Session_Log_without_also_writing_Portfolio_State,  // all three operational files must be consistent as of the same session
    write_Portfolio_State_with_stale_probabilities__use_session_end_confirmed_vector_only,
    use_Portfolio_State_for_execution_decisions__advisory_project_only
  ]

}
```
