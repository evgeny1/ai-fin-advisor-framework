# M05 — Session Initialization
<!-- Supersedes: any prior hardcoded file ID references (Amendment 1) -->
<!-- Updated April 23, 2026: Calibration_State.md now fetched from GitHub; §7/§8 references updated -->
<!-- Cross-references: @see M12_FileProtocol, @see M04_BriefingFormat, @see M03_ScenarioFramework -->

```
MODULE SessionInit {

  // ─── REQUIRED INPUTS ──────────────────────────────────────────────────────
  // Do NOT proceed to analysis without ALL inputs confirmed.

  INPUT_1: AllocationFile {
    fetch_via:  @see M12_FileProtocol.fetchAllocation()
    format:     Google_Sheets
    sheets:     ["Schwab Accounts", "Relative's Schwab Accounts", "Objectives"]
    REQUIRE:    loaded_before_briefing
    // Prices are live via GOOGLEFINANCE formula — updated every ~20 minutes.
    // Treat prices in the Allocation sheet as current market prices at time of fetch.
    // No separate price lookup needed for holdings.
    // "Objectives" tab contains AccountObjectiveProfiles @see M13_GrowthObjectives
  }

  INPUT_2: PendingDecisions {
    ASK_CLIENT: "Are there any pending decisions, conditional triggers, or time-sensitive items from our last session?"
    ALSO_CHECK: §8_Session_State_Log  // loaded in INPUT_3 — open_decisions and open_triggers fields
  }

  INPUT_3: FrameworkFiles {
    // Framework modules (M01–M13) are Project Knowledge — always in context, no fetch needed.
    // CALIBRATION_STATE lives in GitHub — fetch at session start, write back at session end.
    // §8 Session State Log lives inside CALIBRATION_STATE — loaded here.

    fetch_via:  @see M12_FileProtocol.fetchCalibrationState()
    // Fetches Calibration_State.md from GitHub repo (evgeny1/ai-fin-advisor-framework, master)

    APPLY current_threshold_values_from CALIBRATION_STATE §1, §2  // NOT remembered values
    APPLY M13_GrowthObjectives session load requirements
    // @see M13_GrowthObjectives.REQUIRE at_session_start (§4.1–4.4)

    LOAD §8_Session_State_Log {
      // §8 contains the prior session's scenario probabilities, primary driver,
      // open triggers, and open decisions — written at prior session end.
      IF §8 EXISTS AND §8.latest_entry.date >= current_date - 7_calendar_days {
        prior_scenario_probabilities = §8.latest_entry.scenario_probabilities
        prior_primary_driver         = §8.latest_entry.primary_driver
        prior_open_triggers          = §8.latest_entry.open_triggers
        prior_open_decisions         = §8.latest_entry.open_decisions
        prior_next_session_flags     = §8.latest_entry.next_session_flags
        // Feed into:
        //   Step 2 (pending decisions — cross-check against prior_open_decisions)
        //   Step 6 (DeriveScenarioProbabilities — 25pp cap enforcement)
        //   Step 8 (briefing — CHANGES block, prior anchor)
      }
      IF §8 DOES_NOT_EXIST OR §8.latest_entry.date < current_date - 7_calendar_days {
        FLAG: "No recent session state found in §8 (missing or > 7 days old).
               Scenario probabilities will be derived without 25pp cap this session.
               Logged as initial derivation."
        prior_scenario_probabilities = null
      }
    }

    WHEN M11 contradicts_main_framework → M11 takes_precedence

    // Audit trail — include in briefing for traceability
    NOTE_IN_BRIEFING: "Calibration State: last update [date from CALIBRATION_STATE.md]"
  }

  // ─── EXECUTION ORDER ──────────────────────────────────────────────────────────

  SEQUENCE SessionStartSequence {
    // Steps execute in strict order.
    // Steps 2 and 3 may run concurrently ONLY after Step 1 is confirmed successful.
    // No subsequent step begins until its predecessor is confirmed complete.

    1: confirm_allocation_file_loaded
       // INPUT_1 — hard gate; STOP if fails
       // Google Drive — @see M12_FileProtocol.fetchAllocation()
       // Prices are live via GOOGLEFINANCE; treat as current at time of fetch.
       // Load "Objectives" tab — account profiles required for M13

    2: confirm_pending_decisions
       // INPUT_2
       // Cross-check against prior_open_decisions loaded from §8 in Step 3
       // Steps 2 and 3 may run concurrently — only after Step 1 confirmed successful

    3: fetch_calibration_state_from_github
       // INPUT_3 — GitHub fetch @see M12_FileProtocol.fetchCalibrationState()
       // Apply threshold values from §1 and §2
       // Apply M13 return table and multipliers from §4.1–4.4
       // Load §8 Session State Log — prior scenario probabilities, open items
       // Steps 2 and 3 may run concurrently — only after Step 1 confirmed successful

    4: fetch_current_market_data
       // @see M02_IntelGathering.FETCH_LIST
       // Includes credit spreads from M11

    5: identify_primary_driver
       // @see M02_IntelGathering.identifyPrimaryDriver()

    6: derive_scenario_probabilities
       // @see M03_ScenarioFramework.DeriveScenarioProbabilities()
       // Uses: intel from Steps 4–5; prior probabilities from §8 (Step 3)
       // Applies: 25pp cap against prior (if prior exists); floors; B/C check
       AND check_recalibration_trigger
       // @see M03_ScenarioFramework.RecalibrationRule
       AND check_scheduled_review_status
       // @see M11_CreditAndCalibration.CalibrationDiscipline.SessionLoad

    7: complete_intel_gathering_steps_2_to_5
       // @see M02_IntelGathering.GatherIntel STEPS 2–5

    8: produce_intelligence_briefing
       // @see M04_BriefingFormat.IntelligenceBriefing
       // ScenarioProbabilities section must show full scoring output
       // from DeriveScenarioProbabilities() — scores, raw, base, final per scenario

    9: begin_portfolio_discussion

    // SESSION END — after portfolio discussion concludes:

    10: write_session_state_and_credit_readings_to_github
        // @see M12_FileProtocol.WriteBack
        // Writes both §7 (credit readings) and §8 (scenario state) in one operation
        // GitHub — clean overwrite using SHA from session-start fetch
        // ALWAYS execute at session end — do not wait for client instruction
        // If conversation winds down without explicit session-end — execute anyway
  }

}
```
