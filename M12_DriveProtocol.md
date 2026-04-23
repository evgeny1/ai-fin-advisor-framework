# M12 — Google Drive File Fetch Protocol
<!-- Source: Instructions Amendment 1 — April 20, 2026 -->
<!-- Supersedes: any prior hardcoded Drive file IDs or web_fetch usage for Drive files -->
<!-- Applies to: M05_SessionInit INPUT_1 and INPUT_3 -->
<!-- NOTE: Framework Extension is Project Knowledge — no Drive fetch needed -->

```
MODULE DriveProtocol {

  // ─── THE RULE ─────────────────────────────────────────────────────────────

  GUARD FetchRule {
    ALWAYS: fetch_required_files via Google_Drive_search_tool
    NEVER:  hardcode_file_IDs
    NEVER:  store_file_IDs in memory or reuse across_sessions
    NEVER:  use_web_fetch for any_Google_Drive_file
            // web_fetch of Sheets URL returns stale/incorrect data
    // File names are stable. File IDs are NOT.
    // Name match = correct file, regardless of ID.
  }

  // ─── REQUIRED SESSION FILES ───────────────────────────────────────────────
  // Allocation and Calibration State live in Drive — fetched and written each session.
  // Framework Extension (M11) is Project Knowledge — always in context, no fetch needed.

  FILES {
    allocation_sheet: {
      exact_title:  "Allocation"
      type:         Google_Sheets
      purpose:      live_holdings_and_prices
      read_method:  read_file_content  // NOT download_file_content (returns binary for Sheets)
      write_back:   false              // read-only
      // Prices are live via GOOGLEFINANCE formula — updated every ~20 minutes.
      // Treat prices as current at time of fetch. No separate price lookup needed.
    }
    calibration_state: {
      exact_title:  "Calibration_State.md"
      type:         Google_Doc
      purpose:      persistent_threshold_configuration
                    + session_observations_log (§5 credit readings)
                    + session_state_log (§6 scenario probabilities + open items)
      read_method:  download_file_content
      write_back:   true   // append §5 and §6 at session end — see WriteBack
    }
  }

  // ─── FETCH PROCEDURE (execute for each required file) ────────────────────

  FUNCTION fetchFile(exact_title: String) {
    STEP 1: search {
      tool:      Google_Drive:search_files
      query:     "title = '[exact_title]' and parentId = 'root'"
      pageSize:  5
      scope:     root_only  // NEVER search subfolders unless explicitly instructed
    }

    STEP 2: validate_result {
      IF result_count == 0 {
        HARD_STOP
        NOTIFY: "I cannot find [exact_title] in the root of your Drive.
                 Please confirm the file exists and its exact name."
        NEVER:  proceed
      }
      IF result_count > 1 {
        HARD_STOP
        NOTIFY: "I found [N] files named [exact_title] in the root of your Drive.
                 Please confirm which is canonical and delete the duplicate(s)."
        NEVER:  proceed_until_resolved
      }
    }

    STEP 3: read {
      IF exact_title == "Allocation" {
        tool:   Google_Drive:read_file_content
        fileId: [id from search result]
      } ELSE {
        tool:   Google_Drive:download_file_content
        fileId: [id from search result]
      }
    }

    RETURN file_contents
  }

  // ─── HARD RULES ───────────────────────────────────────────────────────────

  GUARD HardRules {
    NEVER:  use web_fetch for any_Drive_file
    NEVER:  hardcode a file_ID
    NEVER:  search inside subfolders UNLESS explicitly_instructed for specific_task
    ALWAYS: resolve current_ID via search at start_of_each_session
    IF zero_results      → HARD_STOP and notify user  // do not proceed
    IF multiple_results  → HARD_STOP and notify user  // do not proceed until resolved
  }

  // ─── WRITE-BACK PROCEDURE (session end) ──────────────────────────────────
  // Executed automatically at session end — do not wait for client instruction.
  // Appends BOTH §5 (credit readings) and §6 (scenario state) in one operation.
  // @see M05_SessionInit.SessionStartSequence Step 10

  PROCEDURE WriteBack {
    WHEN: portfolio_discussion_concluded  // session end
    ALWAYS: execute_without_client_instruction
            // do not wait for prompt — session end triggers this automatically

    STEP 1: re_fetch Calibration_State.md from Drive
            // same search + download_file_content as session-start read
            // use fileId from session-start search — do NOT re-search
            // (file ID is stable within a session; re-search only at session start)

    STEP 2: append to §5 Session Observations Log {
      // Credit readings — enables velocity checks once 60+ trading days accumulate
      date:     [today's date]
      HY_OAS:   [value fetched this session from FRED BAMLH0A0HYM2]
      IG_OAS:   [value fetched this session from FRED BAMLC0A0CM]
      CCC_OAS:  [value fetched this session from FRED BAMLH0A3HYC]
      source:   FRED | Trading_Economics | other
      T1_flag:  confirmed | composite_only | stale
    }

    GUARD §5_WriteIntegrity {
      NEVER:  overwrite existing rows — append only
      NEVER:  write if T1_flag == stale AND no_better_source_available
              // log the gap instead: "[date] — readings unavailable this session"
      ALWAYS: preserve all existing content above the appended row
    }

    STEP 3: append to §6 Session State Log {
      // Scenario state — provides prior anchor for next session's 25pp cap enforcement
      // and pending item continuity. @see M03_ScenarioFramework.DeriveScenarioProbabilities
      // @see M05_SessionInit.INPUT_3 (consumed at next session start)
      date:                  [today's date]
      scenario_probabilities {
        A: [%]
        B: [%]
        C: [%]
        D: [%]
        E: [%]
        F: [%]
        // VERIFY: sum == 100% before writing
      }
      primary_driver:        [name of current dominant driver]
      derivation_method:     scored | manual_override
      // "scored"          = DeriveScenarioProbabilities() output used as-is
      // "manual_override" = analyst judgment departed from scoring output
      //                     REQUIRE: reason and specific T1 evidence documented here
      manual_override_reason: [if manual_override — T1 evidence and rationale] | null
      open_triggers: [
        // list of pending triggers not yet resolved at session end
        // FORMAT: '- [trigger description] — deadline [date] — watching_for [condition]'
      ]
      open_decisions: [
        // list of unresolved portfolio questions or recommended actions not yet executed
        // FORMAT: '- [decision description] — status [pending | awaiting_data | client_choice]'
      ]
      next_session_flags: [
        // items requiring immediate attention at next session load
        // FORMAT: '- [flag description]'
        // Examples: "MOVE index not fetched this session — retrieve at next start"
        //           "FRED velocity check not executable — needs 60-day log history"
        //           "Ceasefire deadline passed — reassess C/A probabilities immediately"
      ]
    }

    GUARD §6_WriteIntegrity {
      NEVER:  overwrite existing rows — append only
      NEVER:  write if scenario_probabilities do not sum to 100%
              // log the error instead: "[date] — scenario state write skipped:
              //                         probabilities did not sum to 100%"
      ALWAYS: preserve all existing content above the appended row
      ALWAYS: write §5 and §6 in a single file update operation
              // fetch → modify → write — not two separate write operations
    }

    STEP 4: write updated file back to Drive {
      tool:   Google_Drive:update_file_content
              // NOTE: Google Drive MCP tool may be create_file with overwrite
              // Use whatever tool updates an existing file's content in-place
      fileId: [id from session-start search — reuse, do not re-search]
    }

    // Velocity check reminder — executes automatically from §5 data:
    // IF oldest_§5_row >= 60_trading_days_ago
    //   → compute velocity = current_reading - reading_60d_ago
    //   → apply to M11 thresholds at next session
  }

  // ─── IMPLEMENTATION NOTE ──────────────────────────────────────────────────
  // April 20, 2026: Allocation sheet read via web_fetch → stale/incorrect render.
  // Seven false discrepancies flagged. Wrong portfolio display produced.
  // Session partially invalidated before error caught.
  // Correct data only retrieved after switching to Google Drive API (search_files).
  // This protocol prevents recurrence.

}
```
