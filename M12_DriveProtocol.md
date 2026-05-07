# M12 — File Access Protocol
<!-- Amendment 2 — April 23, 2026 -->
<!-- Replaces: M12_DriveProtocol (Amendment 1, April 20, 2026) -->
<!-- Updated April 28, 2026: CANONICAL_GITHUB_WRITE_WORKFLOW section added -->
<!-- Updated May 6, 2026 (v1.12 framework-v2-architecture-split): -->
<!--   - fetchSessionLog() added (Session_Log.md fetched concurrently with Calibration_State.md) -->
<!--   - WriteBack updated: push_files([Calibration_State.md, Session_Log.md]) — atomic to master -->
<!--   - COMPACTION_PROCEDURE added (quarterly; defines Archive file naming convention) -->
<!--   - SOURCE_MAP updated to include Session_Log.md and Calibration_Log.md -->
<!-- GitHub: all framework .md files including Calibration_State.md and Session_Log.md (read + write) -->
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
      files: {
        LIVE_CONFIG:     "Calibration_State.md"   // §1-§6, §9-§11 thresholds and classifications
        SESSION_LOG:     "Session_Log.md"          // §7 credit readings, §8 scenario state — AUTHORITATIVE for prior probs
        CALIBRATION_LOG: "Calibration_Log.md"      // §3 archive — read only (history); updated on calibration events
        FRAMEWORK:       [all M01–M16 module .md files]
      }
      access: read + write
      write_method: {
        session_writeback:    push_files (two-file atomic: Calibration_State.md + Session_Log.md)
        framework_amendments: push_files (multi-file, branch + PR)
        calibration_events:   push_files (may include Calibration_Log.md in addition to above)
      }
      // push_files does NOT require SHA for any file
      // NEVER use create_or_update_file for multi-file operations
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
    NEVER:  write framework amendments directly to master — always branch + PR
    NEVER:  write §8 if scenario_probabilities do not sum to 100%
    NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
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
  // PATTERN B: Session Write-Back (§7 credit + §8 scenario state — two files)
  //   → push_files targeting master directly (atomic; no SHA required)
  //   → Both Calibration_State.md and Session_Log.md written in ONE push_files call
  //   → This is the ONLY permitted direct-to-master write for operational data

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
    // Use for: session-end write of §7 (credit) + §8 (scenario state) to master.
    // TWO files written atomically via push_files — no SHA required.
    // push_files is the only write method for session write-back as of v1.12.

    PATTERN_B SessionWriteBack {
      // @see WriteBack procedure below
      // Both Calibration_State.md and Session_Log.md written in ONE push_files call.
      // Calibration_State.md included IF any §1-§6/§9-§11 values changed this session.
      // Session_Log.md ALWAYS included (§7 and §8 updated every session).

      STEP 1: construct Session_Log_updated_content {
        // Take full Session_Log.md content loaded at session start
        // Append new row to §7 Session Observations Log
        // Append new entry to §8 Session State Log
        // Verify: scenario_probabilities sum == 100%
      }

      STEP 2: construct Calibration_State_updated_content {
        // Take full Calibration_State.md content loaded at session start
        // Apply any intra-session calibration changes (e.g., new §3 log entry, §11 EV updates)
        // IF no calibration changes: use content from session-start fetch unchanged
      }

      STEP 3: push_files {
        tool:    github:push_files
        branch:  SOURCE_MAP.github.branch  // "master"
        owner:   SOURCE_MAP.github.owner
        repo:    SOURCE_MAP.github.repo
        message: "Session write-back: [today's date] — §7 credit + §8 scenario state"
        files:   [
          { path: "Session_Log.md",       content: Session_Log_updated_content },
          { path: "Calibration_State.md", content: Calibration_State_updated_content }
        ]
        // push_files requires NO SHA — atomic write of both files
      }

      GUARD PatternB_Rules {
        NEVER:  use Pattern B for framework amendments (multi-file or module changes)
        NEVER:  write §8 entry if scenario_probabilities do not sum to 100%
        NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
                // log the gap: "[date] — readings unavailable this session"
        ALWAYS: §7 and §8 written in single push_files call with Calibration_State.md
        NEVER:  write only Session_Log.md without also writing Calibration_State.md —
                // both must be consistent as of the same session
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

    STEP 2: apply {
      parse content and apply:
        CALIBRATION_STATE §1   // credit thresholds
        CALIBRATION_STATE §2   // energy, currency, macro thresholds
        CALIBRATION_STATE §4   // growth objectives return table + multipliers
        CALIBRATION_STATE §9   // M14 market regime thresholds
        CALIBRATION_STATE §11  // M15 role registry + instrument classification table
      // NOTE: §8 session state is now in Session_Log.md — load via fetchSessionLog()
    }

    RETURN calibration_state_contents
  }

  // ─── SESSION LOG FETCH (GitHub) ───────────────────────────────────────────────
  // Added v1.12. Run CONCURRENTLY with fetchCalibrationState() — only after
  // fetchAllocation() (Step 1) is confirmed successful.

  FUNCTION fetchSessionLog() {

    STEP 1: fetch {
      tool:   github:get_file_contents
      owner:  SOURCE_MAP.github.owner
      repo:   SOURCE_MAP.github.repo
      path:   "Session_Log.md"
      branch: SOURCE_MAP.github.branch
    }

    STEP 2: apply {
      parse content and apply:
        SESSION_LOG §7  // credit readings history (for reference; not directly applied)
        SESSION_LOG §8  // session state log — AUTHORITATIVE source for:
                        //   prior_scenario_probabilities (25pp cap enforcement)
                        //   prior_open_triggers
                        //   prior_open_decisions
                        //   prior_next_session_flags
    }

    RETURN session_log_contents
  }

  // ─── FRAMEWORK FILE FETCH (GitHub) ───────────────────────────────────────────
  // For any framework module file (M01–M16).
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

    STEP 1: construct Session_Log_updated_content {
      // Take full content of Session_Log.md loaded at session start
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

    STEP 2: construct Calibration_State_updated_content {
      // Take full content of Calibration_State.md loaded at session start
      // Apply any §3 log entries, §11 EV updates, or threshold changes from this session
      // IF no calibration changes this session: use session-start content unchanged
      // ALWAYS include in push_files even if unchanged — ensures atomic consistency
    }

    GUARD WriteIntegrity {
      NEVER:  overwrite existing rows in §7 or §8 — append only
      NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
              // log the gap instead: "[date] — readings unavailable this session"
      NEVER:  write §8 entry if scenario_probabilities do not sum to 100%
              // log the error: "[date] — scenario state write skipped:
              //                 probabilities did not sum to 100%"
      ALWAYS: write §7 and §8 in a SINGLE push_files call with both files
    }

    STEP 3: push_files {
      tool:    github:push_files
      owner:   SOURCE_MAP.github.owner
      repo:    SOURCE_MAP.github.repo
      branch:  SOURCE_MAP.github.branch   // "master"
      message: "Session write-back: [today's date] — §7 credit + §8 scenario state"
      files:   [
        { path: "Session_Log.md",       content: Session_Log_updated_content },
        { path: "Calibration_State.md", content: Calibration_State_updated_content }
      ]
    }
  }

  // ─── COMPACTION PROCEDURE (quarterly — execute at Q-end audit) ─────────────────
  // Execute at each of: June 30, September 30, December 31, March 31

  PROCEDURE CompactSessionLog {
    WHEN: Q-end audit date

    STEP 1: identify_entries_to_archive {
      §7_rows_to_archive:    all §7 rows except the 10 most recent
      §8_entries_to_archive: all §8 entries except the 3 most recent full entries
    }

    STEP 2: create_archive_file {
      filename: "Archive_[Year]Q[N].md"
        // Examples: Archive_2026Q2.md (created June 30, 2026)
        //           Archive_2026Q3.md (created September 30, 2026)
      content:
        header: "# Session Log Archive — [Year] Q[N]\n"
               "Archived: [audit date]\n"
               "Source: Session_Log.md §7 and §8 prior to compaction\n"
        body:  [all §7 rows being archived]
               [all §8 full entries being archived]
    }

    STEP 3: compact_session_log {
      // Replace Session_Log.md with compacted version:
      §7_retained:  last 10 session credit readings
      §8_retained:  last 3 full session entries
                    // All prior entries collapsed to one-line summary table:
                    //   format: | date | A%/B%/C%/D%/E%/F% | key_decision |
      // Add compaction note at top of §8: "Entries before [cutoff_date] archived to [filename]"
    }

    STEP 4: push_framework_amendment {
      // Use PATTERN A (branch + push_files + PR)
      // Files in push:
      //   Archive_[Year]Q[N].md  (new file)
      //   Session_Log.md         (compacted)
      // Calibration_State.md included if §3 was also trimmed this session
      branch_name: "session-log-compaction-[Year]Q[N]"
    }

    ARCHIVE_NAMING_CONVENTION {
      quarterly:  "Archive_[Year]Q[N].md"   // e.g., Archive_2026Q2.md
      annual:     "Archive_[Year].md"        // created if quarterly archives are merged end-of-year
      contents:   "§7 credit rows + §8 session entries prior to compaction cutoff
                   + §3 calibration entries prior to trimming (if trimmed this session)"
    }
  }

  // ─── IMPLEMENTATION NOTES ─────────────────────────────────────────────────────────
  // April 20, 2026: Allocation sheet fetched via web_fetch → stale/incorrect data.
  // Seven false discrepancies. Session partially invalidated.
  // Fixed by switching to Google Drive API (search_files + read_file_content).
  //
  // April 23, 2026: Calibration_State.md migrated from Google Drive to GitHub.
  // Drive write-back required create_file + manual duplicate deletion each session.
  // GitHub push_files overwrites cleanly in place without requiring SHA.
  //
  // April 28, 2026: CANONICAL_GITHUB_WRITE_WORKFLOW codified.
  // Root cause of recurring write failures: using create_or_update_file in a loop
  // for multi-file amendments (requires SHA per file, fails on new files, sequential
  // API calls multiply failure probability). Fixed by:
  //   - push_files for all multi-file operations (atomic, no SHA, any number of files)
  //   - create_or_update_file retired from session write-back workflow
  //   - create_branch always uses from_branch name, never SHA
  //
  // May 6, 2026 (v1.12): File architecture split implemented.
  // Calibration_State.md was growing to 55KB+, causing push_files content size failures.
  // Fixed by splitting §7 and §8 into Session_Log.md (separate file).
  // Session write-back now uses push_files for two files (Calibration_State.md + Session_Log.md).
  // No SHA required. Both files remain in master branch for operational access.
  // Calibration_Log.md added for §3 archive history (updated only on calibration events).

}
```
