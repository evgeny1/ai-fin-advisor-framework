# M12 — File Access Protocol
<!-- Amendment 2 — April 23, 2026 -->
<!-- Replaces: M12_DriveProtocol (Amendment 1, April 20, 2026) -->
<!-- GitHub: all framework .md files including Calibration_State.md (read + write) -->
<!-- Google Drive: Allocation sheet only (read only) -->
<!-- Applies to: M05_SessionInit INPUT_1 (Drive), INPUT_3 (GitHub) -->
<!-- Updated April 28, 2026: FrameworkAmendmentPR() added — push_files pattern for multi-file PRs -->

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
      // TWO write patterns — use correct one for context:
      write_method_writeback:   create_or_update_file  // single file session write; requires file SHA
      write_method_amendment:   push_files              // multi-file PR; NO SHA required at any step
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
    NEVER:  hardcode any file ID (Drive) or assume any file SHA (GitHub)
    ALWAYS: resolve Drive ID via search at session start

    // Session write-back (WriteBack — single file, create_or_update_file):
    ALWAYS: use file SHA from session-start fetchCalibrationState() for WriteBack
    NEVER:  call create_or_update_file on existing file without its file SHA

    // Framework amendment PR (FrameworkAmendmentPR — push_files):
    NEVER:  provide SHA to push_files — it does not accept or require SHA
    NEVER:  use create_or_update_file for multi-file amendments — use push_files
    ALWAYS: run tool_search("github create branch") before FrameworkAmendmentPR steps
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
      // FILE SHA — required for WriteBack via create_or_update_file at session end
      // Do NOT discard — reuse at session end without re-fetching
      // This is the file blob SHA, NOT the commit/tree SHA
    }

    STEP 3: apply {
      parse content and apply:
        CALIBRATION_STATE §1   // credit thresholds
        CALIBRATION_STATE §2   // energy, currency, macro thresholds
        CALIBRATION_STATE §4   // growth objectives return table + multipliers
        CALIBRATION_STATE §8   // session state log (prior probabilities)
        CALIBRATION_STATE §11  // instrument classification registry (M15)
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
  // Uses create_or_update_file (single file) — requires FILE SHA from session-start fetch.
  // @see M05_SessionInit.SessionStartSequence Step 10

  PROCEDURE WriteBack {
    WHEN: portfolio_discussion_concluded
    ALWAYS: execute_without_client_instruction

    STEP 1: use calibration_state_sha from session-start fetchCalibrationState()
            // FILE SHA captured at Step 2 of fetchCalibrationState() — reuse; do not re-fetch
            // SHA is stable within a session (no concurrent writes)

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
      sha:     calibration_state_sha  // FILE SHA from session-start fetch — NOT commit SHA
      message: "Session write-back: [today's date] — §7 credit + §8 scenario state"
    }

    // Velocity check reminder — executes automatically from §7 data:
    // IF oldest_§7_row >= 60_trading_days_ago
    //   → compute velocity = current_reading - reading_60d_ago
    //   → apply to M11 thresholds at next session
  }

  // ─── FRAMEWORK AMENDMENT PR PROCEDURE ────────────────────────────────────────
  // Use for ALL framework amendments: any commit with new or modified .md file(s).
  // RELIABLE PATTERN: NO SHA required at any step.
  // Creates branch → pushes all files in single commit → opens PR.
  // This is NOT for session write-back (use WriteBack above for Calibration_State only).

  PROCEDURE FrameworkAmendmentPR(branch_name, files_list, pr_title, pr_body) {

    PREREQUISITE: tool_search {
      query: "github create branch"
      // This query reliably loads: create_branch + push_files + create_pull_request
      // NEVER skip — tools are not pre-loaded and may not be available without search
      // Run this BEFORE Step 1 in every session that uses this procedure
    }

    STEP 1: read_existing_files_if_needed {
      // For files being MODIFIED: read current content to preserve it
      // tool: github:get_file_contents
      // Capture: file text content ONLY — SHA from this call is NOT needed
      // For NEW files: skip this step
    }

    STEP 2: create_branch {
      tool:        github:create_branch
      owner:       SOURCE_MAP.github.owner
      repo:        SOURCE_MAP.github.repo
      branch:      branch_name  // convention: "framework-[short-topic]-YYYY-MM-DD"
      from_branch: "master"
      // No SHA parameter — create_branch resolves HEAD of master automatically
    }

    STEP 3: push_all_files {
      tool:    github:push_files
      owner:   SOURCE_MAP.github.owner
      repo:    SOURCE_MAP.github.repo
      branch:  branch_name  // must match Step 2
      files:   files_list   // Array[{path: String, content: String}]
                            // content = PLAIN TEXT (NOT base64)
                            // include ALL changed files (new + modified) in one call
                            // push_files handles new creation and existing update identically
      message: "Framework amendment: [pr_title]"
      // NO sha field — push_files does not require or accept file SHA
    }

    STEP 4: create_pull_request {
      tool:  github:create_pull_request
      owner: SOURCE_MAP.github.owner
      repo:  SOURCE_MAP.github.repo
      title: pr_title
      body:  pr_body     // Markdown formatted — use headers, bullets, code blocks
      head:  branch_name // branch from Step 2
      base:  "master"
    }

    GUARD AmendmentPRRules {
      NEVER:  use create_or_update_file for multi-file amendments — fragile, error-prone
      NEVER:  provide sha to push_files — it does not accept SHA
      NEVER:  create branch from anything other than master
      NEVER:  skip PREREQUISITE tool_search
      ALWAYS: include ALL modified files in single push_files call — single clean commit
      ALWAYS: write PR body in Markdown with headers, bullets, and code references
      ALWAYS: use date-stamped branch name convention
      IF push_files fails: diagnose first — do NOT fall back to create_or_update_file
                           most likely cause: branch from Step 2 not created successfully
    }
  }

  // ─── IMPLEMENTATION NOTES ─────────────────────────────────────────────────────────────
  // April 20, 2026: Allocation sheet fetched via web_fetch → stale/incorrect data.
  // Seven false discrepancies. Session partially invalidated.
  // Fixed by switching to Google Drive API (search_files + read_file_content).
  //
  // April 23, 2026: Calibration_State.md migrated from Google Drive to GitHub.
  // Drive write-back required create_file + manual duplicate deletion each session.
  // GitHub create_or_update_file overwrites cleanly in place using file SHA.
  // No duplicate file problem. No manual deletion required.
  // GitHub MCP tools: github:get_file_contents (read) + github:create_or_update_file (single-file write).
  //
  // April 28, 2026: FrameworkAmendmentPR() procedure formalized.
  // Root cause of repeated session failures on multi-file amendments:
  //   create_or_update_file requires the correct FILE SHA (blob SHA) for each file being updated.
  //   Confusion between commit SHA (from create_branch result) and file blob SHA
  //   (from get_file_contents result.sha) caused consistent failures.
  //   push_files eliminates this entirely — NO SHA required for any file, new or existing.
  // Reliable 3-step pattern: create_branch → push_files (all files) → create_pull_request.
  // push_files content is PLAIN TEXT, not base64.
  // tool_search("github create branch") must run before each use — tools not pre-loaded.

}
```
