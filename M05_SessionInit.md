# M05 — Session Initialization
<!-- Supersedes: any prior hardcoded file ID references (Amendment 1) -->
<!-- Updated April 23, 2026: Calibration_State.md now fetched from GitHub; §7/§8 references updated -->
<!-- Updated May 6, 2026 (v1.12 framework-v2-architecture-split): Step 3 now fetches BOTH -->
<!--   Calibration_State.md AND Session_Log.md concurrently. Session_Log §8 is the authoritative -->
<!--   source for prior scenario probabilities and open items. Step 10 WriteBack updated to -->
<!--   push_files([Calibration_State.md, Session_Log.md]) — single atomic operation. -->
<!-- Updated May 25, 2026 (Phase 2 registry integration): Step 4 now calls FetchRegistry.fetchAll() -->
<!--   (M02.GatherIntel STEP 1); Step 8 now calls BriefingRegistry.assemble(readings) -->
<!--   (M04.IntelligenceBriefing); §12 M17 cascade thresholds added to Step 3 apply list. -->
<!-- Cross-references: @see M12_FileProtocol, @see M04_BriefingFormat, @see M03_ScenarioFramework -->

```
MODULE SessionInit {

  // ─── REQUIRED INPUTS ─────────────────────────────────────────────────────────────────

  INPUT_1: AllocationFile {
    fetch_via:  @see M12_FileProtocol.fetchAllocation()
    format:     Google_Sheets
    sheets:     ["Schwab Accounts", "Relative's Schwab Accounts", "Objectives"]
    REQUIRE:    loaded_before_briefing
    // Prices are live via GOOGLEFINANCE formula — treat as current at time of fetch.
    // "Objectives" tab contains AccountObjectiveProfiles @see M13_GrowthObjectives
  }

  INPUT_2: PendingDecisions {
    ASK_CLIENT: "Are there any pending decisions, conditional triggers, or time-sensitive items from our last session?"
    ALSO_CHECK: §8_Session_State_Log  // loaded from Session_Log.md in INPUT_3
  }

  INPUT_3: FrameworkFiles {
    // Framework modules (M01–M17) are Project Knowledge — always in context, no fetch needed.
    // CALIBRATION_STATE and Session_Log.md live in GitHub — fetch every session.

    fetch_via:        @see M12_FileProtocol.fetchCalibrationState()
                      @see M12_FileProtocol.fetchSessionLog()
    // Both fetches run CONCURRENTLY — only after Step 1 is confirmed successful.

    APPLY current_threshold_values_from CALIBRATION_STATE §1, §2
    APPLY M13_GrowthObjectives session load requirements
    APPLY M15_InstrumentClassification session load requirements
    // @see M15.ValidateClassifications() — HARD_STOP if any allocation instrument absent from §11

    APPLY M17_SystemicCascadeWarning cascade threshold values
    // @see CALIBRATION_STATE §12 — M17 thresholds (farm filings, natgas, CRE/KRE, margin, sovereign, yield curve)

    LOAD §8_Session_State_Log FROM Session_Log.md {
      IF §8 EXISTS AND §8.latest_entry.date >= current_date - 7_calendar_days {
        prior_scenario_probabilities = §8.latest_entry.scenario_probabilities
        prior_primary_driver         = §8.latest_entry.primary_driver
        prior_open_triggers          = §8.latest_entry.open_triggers
        prior_open_decisions         = §8.latest_entry.open_decisions
        prior_next_session_flags     = §8.latest_entry.next_session_flags
      }
      IF §8 DOES_NOT_EXIST OR §8.latest_entry.date < current_date - 7_calendar_days {
        FLAG: "No recent session state found in Session_Log §8 (missing or > 7 days old).
               Scenario probabilities derived without 25pp cap this session."
        prior_scenario_probabilities = null
      }
    }

    WHEN M11 contradicts_main_framework → M11 takes_precedence
    NOTE_IN_BRIEFING: "Calibration State: last update [date from CALIBRATION_STATE.md] | Session Log: loaded"
  }

  // ─── EXECUTION ORDER ────────────────────────────────────────────────────────────────

  SEQUENCE SessionStartSequence {

    1: confirm_allocation_file_loaded
       // INPUT_1 — hard gate; STOP if fails
       // Google Drive — @see M12_FileProtocol.fetchAllocation()
       // Load "Objectives" tab — account profiles required for M13

    2: confirm_pending_decisions
       // INPUT_2
       // Steps 2 and 3 may run concurrently — only after Step 1 confirmed successful

    3: fetch_calibration_state_AND_session_log_from_github
       // INPUT_3 — TWO concurrent GitHub fetches (only after Step 1 confirmed)
       //
       // From Calibration_State.md: apply §1, §2 thresholds; §4 return table + multipliers (M13);
       //   §9 M14 market regime thresholds; §11 role registry + instrument classification (M15);
       //   §12 M17 cascade thresholds (farm filings, natgas, CRE/KRE, margin, sovereign, yield curve).
       // From Session_Log.md: load §8 Session State Log (prior scenario probabilities, open items).
       //   §8 in Session_Log is AUTHORITATIVE for prior probabilities — not Calibration_State.
       //
       // Run M15.ValidateClassifications() — HARD_STOP if any allocation instrument absent from §11.

    4: fetch_current_market_data
       // Phase 2 complete: M18.FetchRegistry.fetchAll() — parallel fetch of all registered FetchSpecs
       // Registered by all modules at load time:
       //   M02 (core market data: energy, equities, rates, FX, inflation, FFR, holdings)
       //   M11 (credit spreads: HY_OAS, CCC_OAS, IG_OAS, BBB_OAS, MOVE)
       //   M14 (VIX trailing averages, broad equity trailing performance)
       //   M17 (yield curve, cascade chain inputs: KRE, THREEFYTP10, SOFR, DFF,
       //         FINRA_MARGIN_DEBT, NATGAS_HENRY_HUB, FARM_FILINGS_YOY)
       // + M02.QualitativeGatherList (geopolitical status, Fed guidance — web search)
       // @see M02_IntelGathering.GatherIntel STEP 1

    5: identify_primary_driver
       // @see M02_IntelGathering.identifyPrimaryDriver()

    6: derive_scenario_probabilities
       // @see M03_ScenarioFramework.DeriveScenarioProbabilities()
       AND check_recalibration_trigger
       // @see M03_ScenarioFramework.RecalibrationRule
       AND check_scheduled_review_status
       // @see M11_CreditAndCalibration.CalibrationDiscipline.SessionLoad

    7: complete_intel_gathering_steps_2_to_5
       // @see M02_IntelGathering.GatherIntel STEPS 2–5

    8: produce_intelligence_briefing
       // Phase 2 complete: BriefingRegistry.assemble(readings) — ordered section list
       // M04-owned sections + M11, M14, M17 registered sections assembled in declared order
       // @see M04_BriefingFormat.IntelligenceBriefing
       // ScenarioProbabilities section must show full scoring output
       // from DeriveScenarioProbabilities() — scores, raw, base, final per scenario

    9: begin_portfolio_discussion

    // SESSION END — after portfolio discussion concludes:

    10: write_session_state_and_credit_readings_to_github
        // @see M12_FileProtocol.WriteBack
        // push_files([Calibration_State.md, Session_Log.md]) — single atomic operation
        // ALWAYS execute at session end — do not wait for client instruction
  }

}
```
