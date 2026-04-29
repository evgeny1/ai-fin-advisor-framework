# M12 — File Access Protocol
<!-- Amendment 2 — April 23, 2026 -->
<!-- Replaces: M12_DriveProtocol (Amendment 1, April 20, 2026) -->
<!-- Updated April 28, 2026: CANONICAL_GITHUB_WRITE_WORKFLOW section added -->
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
      write_method: push_files (multi-file) | create_or_update_file (single file session write-back)
      // SHA required ONLY for create_or_update_file — always use SHA from session-start fetch
      // push_files does NOT require SHA for any file
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
    ALWAYS: use SHA from session-start fetch for create_or_update_file write-back
    NEVER:  write to GitHub without first fetching current SHA this session (for create_or_update_file)
    NEVER:  write framework amendments directly to master — always branch + PR
  }

  // ─── CANONICAL GITHUB WRITE WORKFLOW ─────────────────────────────────────────
  // TWO patterns. Use the correct one. Using the wrong one causes failures.
  //
  // PATTERN A: Framework Amendments (new files, multi-file updates, module changes)
  //   → create_branch → push_files → create_pull_request
  //   → push_files handles any number of files (new + existing) in ONE atomic call
  //   → NO SHA required for any file in push_files
  //   → PR body must be .md formatted
  //
  // PATTERN B: Session Write-Back (§7 credit + §8 scenario state — single file)
  //   → create_or_update_file directly to master with SHA
  //   → SHA must come from session-start fetchCalibrationState()
  //   → This is the ONLY permitted direct-to-master write

  CANONICAL_GITHUB_WRITE_WORKFLOW {

    // ── PATTERN A: Framework Amendments ──────────────────────────────────────
    // Use for: new module files, multi-file updates, §11 role/classification changes,
    //          any change touching 2+ files or requiring review before merge.

    PATTERN_A FrameworkAmendment {

      STEP 1: create_branch {
        tool:        github:create_branch
        branch:      "descriptive-name-YYYY-MM-DD"  // always date-stamp
        from_branch: "master"                        // NOT a SHA — branch name
        owner:       SOURCE_MAP.github.owner
        repo:        SOURCE_MAP.github.repo
        // Returns: branch ref. No SHA needed here.
      }

      STEP 2: push_files {
        // SINGLE call — handles any number of files atomically
        // Works for new files AND existing files — no SHA required for any
        // Uses git tree API internally — atomic: all files commit together or none
        tool:    github:push_files
        branch:  [branch name from Step 1]
        owner:   SOURCE_MAP.github.owner
        repo:    SOURCE_MAP.github.repo
        message: "descriptive commit message"
        files:   [
          { path: "NewModule.md",     content: "full file content" },
          { path: "ExistingFile.md",  content: "updated full file content" },
          // ... any number of files
        ]
        // CRITICAL: content must be the COMPLETE file, not a diff
        // NEVER loop create_or_update_file for multiple files — use push_files
      }

      STEP 3: create_pull_request {
        tool:  github:create_pull_request
        head:  [branch name from Step 1]
        base:  "master"
        owner: SOURCE_MAP.github.owner
        repo:  SOURCE_MAP.github.repo
        title: "descriptive title"
        body:  "[.md formatted PR notes — see PR_BODY_FORMAT below]"
      }

      GUARD PatternA_Rules {
        NEVER: write directly to master for framework amendments
        NEVER: use create_or_update_file for multi-file commits
        NEVER: pass a SHA to create_branch — it takes from_branch NAME
        NEVER: assume push_files requires SHA — it does not
        NEVER: push partial file content — always complete file
        ALWAYS: date-stamp branch names
        ALWAYS: use push_files for 2+ files (single call)
        ALWAYS: PR body in .md format
      }
    }

    // ── PATTERN B: Session Write-Back ────────────────────────────────────────
    // Use for: session-end write of §7 + §8 to Calibration_State.md on master.
    // This is the ONE exception to the no-direct-master-write rule.
    // Rationale: single file, SHA-protected, frequent, low-risk, must be atomic with session.

    PATTERN_B SessionWriteBack {
      // @see WriteBack procedure below
      STEP 1: use calibration_state_sha from session-start fetchCalibrationState()
      STEP 2: construct updated_content (append §7 row + §8 entry)
      STEP 3: create_or_update_file {
        tool:    github:create_or_update_file
        path:    "Calibration_State.md"
        branch:  "master"
        content: updated_content
        sha:     calibration_state_sha
        message: "Session write-back: [today's date] — §7 credit + §8 scenario state"
      }

      GUARD PatternB_Rules {
        NEVER:  use Pattern B for framework amendments (multi-file or module changes)
        ALWAYS: use SHA from session-start fetch — never assume or re-fetch
        NEVER:  write §8 if scenario_probabilities do not sum to 100%
        NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
        ALWAYS: §7 and §8 written in single create_or_update_file call
      }
    }

    // ── PR BODY FORMAT ────────────────────────────────────────────────────────

    PR_BODY_FORMAT {
      // .md formatted. Required sections:
      "## Summary\n"
      "## Problem solved\n"
      "## Changes\n"  // list of files changed + what changed in each
      "## Design decisions\n"
      "## Migration / backward compatibility\n"
      "## Calibration State impact\n"  // which §§ were added/modified
      "## Testing / validation\n"
    }
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
      // Required for session write-back (Pattern B) — do not discard
    }

    STEP 3: apply {
      parse content and apply:
        CALIBRATION_STATE §1   // credit thresholds
        CALIBRATION_STATE §2   // energy, currency, macro thresholds
        CALIBRATION_STATE §4   // growth objectives return table + multipliers
        CALIBRATION_STATE §8   // session state log (prior probabilities)
        CALIBRATION_STATE §9   // M14 market regime thresholds
        CALIBRATION_STATE §11  // M15 role registry + instrument classification table
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
  // Uses PATTERN B. Executed automatically at session end.
  // @see CANONICAL_GITHUB_WRITE_WORKFLOW.PATTERN_B
  // @see M05_SessionInit.SessionStartSequence Step 10

  PROCEDURE WriteBack {
    WHEN: portfolio_discussion_concluded
    ALWAYS: execute_without_client_instruction

    STEP 1: use calibration_state_sha from session-start fetchCalibrationState()
            // SHA captured at Step 2 of fetchCalibrationState() — reuse; do not re-fetch

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
      sha:     calibration_state_sha
      message: "Session write-back: [today's date] — §7 credit + §8 scenario state"
    }
  }

  // ─── IMPLEMENTATION NOTES ─────────────────────────────────────────────────────────
  // April 20, 2026: Allocation sheet fetched via web_fetch → stale/incorrect data.
  // Seven false discrepancies. Session partially invalidated.
  // Fixed by switching to Google Drive API (search_files + read_file_content).
  //
  // April 23, 2026: Calibration_State.md migrated from Google Drive to GitHub.
  // Drive write-back required create_file + manual duplicate deletion each session.
  // GitHub create_or_update_file overwrites cleanly in place using SHA.
  //
  // April 28, 2026: CANONICAL_GITHUB_WRITE_WORKFLOW codified.
  // Root cause of recurring write failures: using create_or_update_file in a loop
  // for multi-file amendments (requires SHA per file, fails on new files, sequential
  // API calls multiply failure probability). Fixed by:
  //   - push_files for all framework amendments (atomic, no SHA, any number of files)
  //   - create_or_update_file reserved for session write-back only (single file, SHA-protected)
  //   - create_branch always uses from_branch name, never SHA

}
```
