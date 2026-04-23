# M05 — Session Initialization
<!-- Supersedes: any prior hardcoded file ID references (Amendment 1) -->
<!-- Cross-references: @see M12_DriveProtocol, @see M04_BriefingFormat, @see M03_ScenarioFramework -->

```
MODULE SessionInit {

  // ─── REQUIRED INPUTS ─────────────────────────────────────────────────────
  // Do NOT proceed to analysis without ALL inputs confirmed.

  INPUT_1: AllocationFile {
    fetch_via:  @see M12_DriveProtocol.fetchFile("Allocation")
    format:     Google_Sheets
    sheets:     ["Schwab Accounts", "Relative's Schwab Accounts"]
    REQUIRE:    loaded_before_briefing
    // Prices are live via GOOGLEFINANCE formula — updated every ~20 minutes.
    // Treat prices in the Allocation sheet as current market prices at time of fetch.
    // No separate price lookup needed for holdings.
  }

  INPUT_2: PendingDecisions {
    ASK_CLIENT: "Are there any pending decisions, conditional triggers, or time-sensitive items from our last session?"
    ALSO_CHECK: §6_Session_State_Log  // loaded in INPUT_3 — open_decisions and open_triggers fields
  }

  INPUT_3: FrameworkFiles {
    // M11_CreditAndCalibration is Project Knowledge — always in context, no fetch needed.
    // CALIBRATION_STATE lives in Drive — fetch at session start, write back at session end.
    // §6 Session State Log lives inside CALIBRATION_STATE — loaded here.

    fetch_via:  @see M12_DriveProtocol.fetchFile("Calibration_State.md")

    APPLY M11_CreditAndCalibration as_binding_extension_of_main_framework
    APPLY current_threshold_values_from CALIBRATION_STATE §1, §2  // NOT remembered values

    LOAD §6_Session_State_Log {
      // §6 contains the prior session's scenario probabilities, primary driver,
      // open triggers, and open decisions — written at prior session end.
      IF §6 EXISTS AND §6.latest_entry.date >= current_date - 7_calendar_days {
        prior_scenario_probabilities = §6.latest_entry.scenario_probabilities
        prior_primary_driver         = §6.latest_entry.primary_driver
        prior_open_triggers          = §6.latest_entry.open_triggers
        prior_open_decisions         = §6.latest_entry.open_decisions
        prior_next_session_flags     = §6.latest_entry.next_session_flags
        // Feed into:
        //   Step 2 (pending decisions — cross-check against prior_open_decisions)
        //   Step 6 (DeriveScenarioProbabilities — 25pp cap enforcement)
        //   Step 8 (briefing — CHANGES block, prior anchor)
      }
      IF §6 DOES_NOT_EXIST OR §6.latest_entry.date < current_date - 7_calendar_days {
        FLAG: "No recent session state found in §6 (missing or > 7 days old).
               Scenario probabilities will be derived without 25pp cap this session.
               Logged as initial derivation."
        prior_scenario_probabilities = null
      }
    }

    WHEN M11 contradicts_main_framework → M11 takes_precedence

    // Audit trail — include in briefing for traceability
    NOTE_IN_BRIEFING: "Calibration State: last update [date from CALIBRATION_STATE.md]"
  }

  // ─── EXECUTION ORDER ─────────────────────────────────────────────────────

  SEQUENCE SessionStartSequence {
    // Steps execute in strict order.
    // Steps 2 and 3 may run concurrently ONLY after Step 1 is confirmed successful.
    // No subsequent step begins until its predecessor is confirmed complete.

    1: confirm_allocation_file_loaded
       // INPUT_1 — hard gate; STOP if fails
       // Prices are live via GOOGLEFINANCE; treat as current at time of fetch.

    2: confirm_pending_decisions
       // INPUT_2
       // Cross-check against prior_open_decisions loaded from §6 in Step 3
       // Steps 2 and 3 may run concurrently — only after Step 1 confirmed successful

    3: fetch_calibration_state_from_drive
       // INPUT_3 — Drive fetch
       // Apply threshold values from §1 and §2
       // Load §6 Session State Log — prior scenario probabilities, open items
       // Steps 2 and 3 may run concurrently — only after Step 1 confirmed successful

    4: fetch_current_market_data
       // @see M02_IntelGathering.FETCH_LIST
       // Includes credit spreads from M11

    5: identify_primary_driver
       // @see M02_IntelGathering.identifyPrimaryDriver()

    6: derive_scenario_probabilities
       // @see M03_ScenarioFramework.DeriveScenarioProbabilities()
       // Uses: intel from Steps 4–5; prior probabilities from §6 (Step 3)
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

    10: write_session_state_and_credit_readings_to_drive
        // @see M12_DriveProtocol.WriteBack
        // Writes both §5 (credit readings) and §6 (scenario state) in one operation
        // ALWAYS execute at session end — do not wait for client instruction
        // If conversation winds down without explicit session-end — execute anyway
  }

}
```
