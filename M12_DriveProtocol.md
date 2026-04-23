# M12 — File Access Protocol
<!-- Amendment 2 — April 23, 2026 -->
<!-- Replaces: M12_DriveProtocol (Amendment 1, April 20, 2026) -->
<!-- GitHub: all framework .md files including Calibration_State.md (read + write) -->
<!-- Google Drive: Allocation sheet only (read only) -->
<!-- Applies to: M05_SessionInit INPUT_1 (Drive), INPUT_3 (GitHub) -->

```
MODULE FileProtocol {

  // ─── SOURCE MAP ───────────────────────────────────────────────────────────────────

  SOURCE_MAP {
    github: {
      owner:  "evgeny1"
      repo:   "ai-fin-advisor-framework"
      branch: "master"
      files:  [all .md files including Calibration_State.md]
      access: read + write
      write_method: create_or_update_file  // clean overwrite; no duplicate issue
      // SHA required for updates — always use SHA from session-start fetch
    }
    drive: {
      file:   "Allocation"
      type:   Google_Sheets
      access: read_only
      // Prices live via GOOGLEFINANCE — treat as current at time of fetch
      // Framework never writes to Allocation sheet
    }
  }

  GUARD CoreRules {
    NEVER:  use_web_fetch for any GitHub file or Google Drive file
    NEVER:  hardcode any file ID (Drive) or assume any SHA (GitHub)
    ALWAYS: resolve Drive ID via search at session start
    ALWAYS: use SHA from session-start fetch for GitHub write-back
    NEVER:  write to GitHub without first fetching current SHA this session
  }

  // ─── ALLOCATION SHEET FETCH (Google Drive) ──────────────────────────────────────

  FUNCTION fetchAllocation() {

    STEP 1: search {
      tool:      Google_Drive:search_files
      query:     "title = 'Allocation' and parentId = 'root'"
      pageSize:  5
      scope:     root_only
    }

    STEP 2: validate_result {
      IF result_count == 0 {
        HARD_STOP
        NOTIFY: "Cannot find 'Allocation' in Drive root.
                 Confirm file exists and its exact name."
      }
      IF result_count > 1 {
        HARD_STOP
        NOTIFY: "Found [N] files named 'Allocation' in Drive root.
                 Delete duplicates and retry."
      }
    }

    STEP 3: read {
      tool:   Google_Drive:read_file_content
      fileId: [id from search result]
      // read_file_content (NOT download_file_content) — Drive returns binary for Sheets via download
    }

    RETURN allocation_sheet_contents
    // Includes: Schwab Accounts, Relative's Schwab Accounts, Objectives tabs
  }

  // ─── CALIBRATION STATE FETCH (GitHub) ────────────────────────────────────────

  FUNCTION fetchCalibrationState() {

    STEP 1: fetch {
      tool:   github:get_file_contents
      owner:  SOURCE_MAP.github.owner
      repo:   SOURCE_MAP.github.repo
      path:   "Calibration_State.md"
      branch: SOURCE_MAP.github.branch
    }

    STEP 2: store_sha {
      calibration_state_sha = result.sha
      // Required for write-back at session end — do not discard
    }

    STEP 3: apply {
      parse content and apply:
        CALIBRATION_STATE §1   // credit thresholds
        CALIBRATION_STATE §2   // energy, currency, macro thresholds
        CALIBRATION_STATE §4   // growth objectives return table + multipliers
        CALIBRATION_STATE §8   // session state log (prior probabilities)
    }

    RETURN calibration_state_contents
  }

  // ─── FRAMEWORK FILE FETCH (GitHub) ───────────────────────────────────────────
  // For any framework module file other than Calibration_State.md.
  // Framework modules are Project Knowledge (always in context) —
  // this function is for explicit re-fetch or inspection when needed.

  FUNCTION fetchFrameworkFile(path: String) {
    tool:   github:get_file_contents
    owner:  SOURCE_MAP.github.owner
    repo:   SOURCE_MAP.github.repo
    path:   path
    branch: SOURCE_MAP.github.branch
    RETURN file_contents
  }

  // ─── WRITE-BACK PROCEDURE (session end) ────────────────────────────────────────
  // Executed automatically at session end — do not wait for client instruction.
  // Appends BOTH §7 (credit readings) and §8 (scenario state) in one operation.
  // GitHub write: clean overwrite using SHA from session-start fetch.
  // No duplicate file problem — create_or_update_file updates in place.
  // @see M05_SessionInit.SessionStartSequence Step 10

  PROCEDURE WriteBack {
    WHEN: portfolio_discussion_concluded
    ALWAYS: execute_without_client_instruction

    STEP 1: use calibration_state_sha from session-start fetchCalibrationState()
            // SHA captured at Step 2 of fetchCalibrationState() — reuse; do not re-fetch
            // SHA is stable within a session

    STEP 2: construct updated_content {
      // Take full content loaded at session start
      // Append new row to §7 Session Observations Log:
      §7_new_row {
        date:     [today's date]
        HY_OAS:   [value fetched this session from FRED BAMLH0A0HYM2]
        IG_OAS:   [value fetched this session from FRED BAMLC0A0CM]
        CCC_OAS:  [value fetched this session from FRED BAMLH0A3HYC]
        source:   FRED | Trading_Economics | other
        T1_flag:  confirmed | composite_only | stale
      }

      // Append new entry to §8 Session State Log:
      §8_new_entry {
        date:                  [today's date]
        scenario_probabilities { A: [%], B: [%], C: [%], D: [%], E: [%], F: [%] }
        // VERIFY: sum == 100% before writing
        primary_driver:        [name of current dominant driver]
        derivation_method:     scored | manual_override
        manual_override_reason: [if manual_override — T1 evidence and rationale] | null
        open_triggers:         [list of pending triggers]
        open_decisions:        [list of unresolved portfolio actions]
        next_session_flags:    [items requiring immediate attention at next session load]
      }
    }

    GUARD WriteIntegrity {
      NEVER:  overwrite existing rows in §7 or §8 — append only within those sections
      NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
              // log the gap: "[date] — readings unavailable this session"
      NEVER:  write §8 entry if scenario_probabilities do not sum to 100%
              // log the error: "[date] — scenario state write skipped:
              //                 probabilities did not sum to 100%"
      ALWAYS: write §7 and §8 in a single file update operation
    }

    STEP 3: write to GitHub {
      tool:    github:create_or_update_file
      owner:   SOURCE_MAP.github.owner
      repo:    SOURCE_MAP.github.repo
      path:    "Calibration_State.md"
      branch:  SOURCE_MAP.github.branch
      content: updated_content
      sha:     calibration_state_sha  // from session-start fetch
      message: "Session write-back: [today's date] — §7 credit + §8 scenario state"
    }

    // Velocity check reminder — executes automatically from §7 data:
    // IF oldest_§7_row >= 60_trading_days_ago
    //   → compute velocity = current_reading - reading_60d_ago
    //   → apply to M11 thresholds at next session
  }

  // ─── IMPLEMENTATION NOTE ─────────────────────────────────────────────────────────────
  // April 20, 2026: Allocation sheet fetched via web_fetch → stale/incorrect data.
  // Seven false discrepancies. Session partially invalidated.
  // Fixed by switching to Google Drive API (search_files + read_file_content).
  //
  // April 23, 2026: Calibration_State.md migrated from Google Drive to GitHub.
  // Drive write-back required create_file + manual duplicate deletion each session.
  // GitHub create_or_update_file overwrites cleanly in place using SHA.
  // No duplicate file problem. No manual deletion required.
  // GitHub MCP tool: github:get_file_contents (read) + github:create_or_update_file (write).

}
```
