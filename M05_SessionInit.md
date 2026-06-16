# M05 — Session Initialization
<!-- Version: 1.5 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M05_SessionInit
  Version:         1.5
  Sub-project:     ORCHESTRATION
  Reason to change: session start sequence steps, write-back protocol, or session type rules change.
  Inputs consumed:  (entry point — orchestrates all other modules)
  Outputs produced: (side effects only: intelligence briefing rendered; write-back committed)
  Calibration deps: all — session init loads full CALIBRATION_STATE and SESSION_LOG at every session
  Types consumed:   @see FW_Types.md — all types (orchestration module)
-->

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
    // Framework modules (M01–M18) are Project Knowledge — always in context, no fetch needed.
    // CALIBRATION_STATE and Session_Log.md are fetched every session via Desktop Commander.
    // @see M12_FileProtocol.readFrameworkFile() — Desktop Commander local path primary; GitHub MCP backup.

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

    0: declare_session_type {
       // REQUIRED before any other step. Declare one of:
       //   FULL_DESKTOP    — Desktop Commander available + local git accessible
       //   READONLY_MOBILE — no Desktop Commander (Android / web-only)
       // Detection: if Desktop Commander tools are present in the tool list → FULL_DESKTOP
       //            if absent or unreachable → READONLY_MOBILE
       // State explicitly in session header before Step 1 runs.
       // FULL_DESKTOP: all steps including WriteBack (Step 10) execute normally.
       // READONLY_MOBILE: skip Step 10 entirely; advisory only; note this in briefing header.
       // @see M12_FileProtocol.SessionType
    }

    1: confirm_allocation_file_loaded
       // INPUT_1 — hard gate; STOP if fails
       // Google Drive — @see M12_FileProtocol.fetchAllocation()
       // Load "Objectives" tab — account profiles required for M13

    2: confirm_pending_decisions
       // INPUT_2
       // Steps 2 and 3 may run concurrently — only after Step 1 confirmed successful

    3: fetch_calibration_state_AND_session_log
       // INPUT_3 — TWO concurrent fetches (only after Step 1 confirmed)
       // @see M12_FileProtocol.readFrameworkFile() — Desktop Commander primary; GitHub backup
       //
       // From Calibration_State.md: apply §1, §2 thresholds; §4 return table + multipliers (M13);
       //   §9 M14 market regime thresholds; §11 role registry + instrument classification (M15);
       //   §12 M17 cascade thresholds (farm filings, natgas, CRE/KRE, margin, sovereign, yield curve).
       // From Session_Log.md: load §8 Session State Log (prior scenario probabilities, open items).
       //   §8 in Session_Log is AUTHORITATIVE for prior probabilities — not Calibration_State.
       //
       // Run M15.ValidateClassifications() — HARD_STOP if any allocation instrument absent from §11.

    3b: current_holdings_floor_check
       // FLOOR_THEN_RETURN accounts only. Runs immediately after Step 3, before market data fetch.
       // Uses allocation sheet values already loaded in Step 1 (GOOGLEFINANCE prices at fetch time).
       // Computes mark-to-market weights from current holding values / account total.
       // Runs FLOOR_THEN_RETURN branch of M13.FeasibilityCheck against those ACTUAL weights
       //   (not proposed target allocations — those are checked later at Step 9).
       // Uses PRIOR session probabilities from §8 (loaded in Step 3) — not yet-derived current probs.
       //   Rationale: prior probs are the best available at this point in the sequence;
       //   current probs require qualitative gather + scoring (Steps 5–6).
       //   If current probs are later derived and differ materially, re-run this check (see Step 6b).
       // @see M13_GrowthObjectives.CurrentHoldingsFloorCheck()
       //
       IF FloorBreachAlert emitted {
         ESCALATE: Priority 1 — display alert BEFORE any other session content
         FORMAT:   "⚠ FLOOR_BREACH_ALERT — [account_id]: scenario [s] returns [worst_return]%
                    at prior probability vector. Floor constraint breached on current holdings.
                    RecalibrationSequence required before allocation recommendations."
         REQUIRE:  client acknowledgment before proceeding to Step 4
         DO_NOT:   proceed to portfolio recommendations without resolving
       }
       // READONLY_MOBILE: run check using allocation sheet values if available;
       //   if allocation sheet unavailable, skip with FLAG: "FloorCheck skipped — no sheet data"

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

    6b: re_run_floor_check_at_current_probabilities
       // Re-run M13.CurrentHoldingsFloorCheck() using newly derived scenario probabilities.
       // Only required if Step 6 produces probabilities that differ from prior (§8) by >= 5pp
       //   on any single scenario. If probabilities are unchanged or within 5pp: skip.
       // Rationale: a meaningful probability shift (e.g., C −23.7pp as in v1.34) may turn
       //   a passing floor check into a breach. Step 3b used prior probs as best available;
       //   Step 6b resolves that with current probs.
       IF FloorBreachAlert emitted AND NOT emitted at Step 3b {
         ESCALATE: same Priority 1 protocol as Step 3b
         NOTE_IN_BRIEFING: "Floor breach detected on current holdings at updated probabilities.
                            Was CLEAR at prior probabilities. Probability shift is the trigger."
       }

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
        // push_files([Calibration_State.md, Session_Log.md, Portfolio_State.md]) — single atomic operation to master
        // Portfolio_State.md rendered by M12.constructPortfolioState() — companion project context snapshot
        // ALWAYS execute at session end — do not wait for client instruction
  }

}
```
