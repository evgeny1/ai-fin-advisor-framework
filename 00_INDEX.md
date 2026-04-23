# 00 — Index & Module Map
<!-- Personal Financial Advisor Framework — Pseudo-Code Edition -->
<!-- Source documents: Framework_Main_v1, Framework_Extension_v1, Calibration_State, Amendment 1 -->
<!-- Last converted: April 20, 2026 -->

```
FRAMEWORK PersonalFinancialAdvisor {

  // ─── MODULE REGISTRY ─────────────────────────────────────────────────────

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
    M12_DriveProtocol          // Amendment 1: Google Drive fetch procedure
    CALIBRATION_STATE          // Live threshold values — load every session
  }

  // ─── LOAD ORDER (every session) ──────────────────────────────────────────

  SESSION_START_SEQUENCE {
    // @see M05_SessionInit.SessionStartSequence for full detail
    1:  M12_DriveProtocol.fetchFile("Allocation")
    2:  confirm_pending_decisions
    3:  M12_DriveProtocol.fetchFile("Framework_Extension_v1_Credit_And_Calibration.md")
        M12_DriveProtocol.fetchFile("Calibration_State.md")
        → apply CALIBRATION_STATE thresholds (not remembered values)
    4:  M02_IntelGathering.FETCH_LIST  (includes M11.CreditSignal.FetchList)
    5:  M02_IntelGathering.identifyPrimaryDriver()
    6:  M03_ScenarioFramework.RecalibrationRule  +  M11.CalibrationDiscipline.SessionLoad
    7:  M02_IntelGathering.GatherIntel STEPS 2–5
    8:  M04_BriefingFormat.IntelligenceBriefing
    9:  portfolio discussion
  }

  // ─── PRECEDENCE RULES ────────────────────────────────────────────────────

  PRECEDENCE [highest → lowest] {
    1: M11_CreditAndCalibration   // Extension v1 overrides main framework where they conflict
    2: M12_DriveProtocol          // Amendment 1 supersedes any prior fetch instructions
    3: CALIBRATION_STATE          // live threshold values override any remembered values
    4: M09_ScenariosABC, M10_ScenariosDEF   // execution protocols
    5: M01–M08                    // core framework
  }

  // ─── KEY CROSS-REFERENCE MAP ─────────────────────────────────────────────

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

    // Position action flow
    execution_trigger
      → M08_FunctionalRoles.classifyRole(holding)
      → M08_FunctionalRoles.DualRoleConflict?
      → M08_FunctionalRoles.ExecutionGuards  (graduated response)
      → [M09_ScenariosABC | M10_ScenariosDEF].RESPONSES[role]
      → M08_FunctionalRoles.ExecutionTaxPlacement
      → M03_ScenarioFramework.minimumConvictionWeight()?

    // Recommendation validation chain
    recommendation
      → M06_ClientAndAdvisory.SimplicityTest()
      → M06_ClientAndAdvisory.StructuralThesis
      → M06_ClientAndAdvisory.ClientBias (GUARD)
      → M06_ClientAndAdvisory.HoldJustification?  (if hold recommended)
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

  // ─── CALIBRATION-DATED THRESHOLDS AT A GLANCE ────────────────────────────
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
    next_full_audit:             June 30, 2026
  }

  // ─── FIXED STRUCTURAL RULES (never calibration-dated) ────────────────────

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
    drive_fetch_rule:                 search-first, never hardcode IDs
    calibration_prospective_only:     M11_CreditAndCalibration.ProspectiveOnly
  }

}
```
