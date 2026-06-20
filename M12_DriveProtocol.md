# M12 — File Access Protocol
<!-- Version: Amendment 6 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M12_DriveProtocol
  Version:         Amendment 6
  Sub-project:     DATA_INTELLIGENCE
  Reason to change: file access sources, write toolchain, or session type rules change.
  Inputs consumed:  (infrastructure — reads and writes framework files; no domain inputs)
  Outputs produced: fetched file contents; write-back confirmation; instruments.json (local only)
  Calibration deps: none (infrastructure module)
  Types consumed:   @see FW_Types.md — FileSpec, SessionType
-->

```
MODULE FileProtocol {

  // ─── SESSION TYPE ─────────────────────────────────────────────────────────────

  ENUM SessionType {
    FULL_DESKTOP    // Desktop with Desktop Commander; full session init + write-back
    READONLY_MOBILE // Android or no Desktop Commander; read + advisory only; no write-back
  }

  GUARD SessionTypeRules {
    NEVER:  execute WriteBack in a READONLY_MOBILE session
    NEVER:  attempt git operations without Desktop Commander available
    ALWAYS: if Desktop Commander unavailable → treat session as READONLY_MOBILE
  }

  // ─── SOURCE MAP ───────────────────────────────────────────────────────────────
  // READ HIERARCHY for framework .md files:
  //   1st: Desktop Commander (local git path) — FULL_DESKTOP sessions, fast, no decode
  //   2nd: GitHub MCP — backup for READONLY_MOBILE or local read failure
  //   NOT used for .md reads: Google Drive (Drive is for Allocation sheet only)

  SOURCE_MAP {
    drive: {
      allocation_sheet: {
        file:   "Allocation"
        type:   Google_Sheets
        access: read_only
        search: by title in Drive root — NEVER hardcode file ID
        // Prices live via GOOGLEFINANCE — treat as current at time of fetch
        // Framework never writes to Allocation sheet
      }
      // NOTE: framework .md files live in Drive but are read via local Desktop Commander,
      // not via Drive API. Drive syncs the local folder bidirectionally.
    }
    github: {
      owner:  "evgeny1"
      repo:   "ai-fin-advisor-framework"
      branch: "master"
      access: read_only — fallback if Desktop Commander unavailable (READONLY_MOBILE)
      // NEVER use GitHub connector for any write operation
    }
    local: {
      path:   determined by ADVISOR_FRAMEWORK_PATH env var in python/.env
              (Mac default: "~/Library/CloudStorage/GoogleDrive-evgeny.shatalov@gmail.com/My Drive/dev/AI Financial Advisor Framework/";
               Windows: set explicitly in .env — e.g. "G:\My Drive\dev\AI Financial Advisor Framework")
      access: read + write via Desktop Commander
      note:   syncs bidirectionally with Google Drive framework folder via Drive desktop client
      // Desktop Commander:read_file = PRIMARY read path for all .md framework files
      // Desktop Commander write tools = the ONLY write method for all sessions
      files:  [Calibration_State.md, Session_Log.md, Portfolio_State.md, Calibration_Log.md,
               M01–M18.md, FW_Types.md, 00_INDEX.md, Archive_*.md]
    }
  }

  GUARD CoreRules {
    NEVER:  use web_fetch for any GitHub or Google Drive file
    NEVER:  hardcode any Google Drive file ID — search by title for Allocation sheet; use local path for framework files
    ALWAYS: resolve Allocation sheet via Drive root title search at session start (never hardcode its ID)
    ALWAYS: read framework .md files via Desktop Commander local path (FULL_DESKTOP) or GitHub MCP (READONLY_MOBILE)
    NEVER:  use Google Drive API to read framework .md files (Drive syncs locally; read the local copy)
    NEVER:  use github:push_files, github:create_or_update_file, github:create_branch,
            or github:create_pull_request for any operation
    ALWAYS: all writes go via Desktop Commander + local git
    NEVER:  write §8 if scenario_probabilities do not sum to 100%
    NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
    NEVER:  write Session_Log.md without also writing Portfolio_State.md in the same git commit
    NEVER:  execute WriteBack in a READONLY_MOBILE session
  }

  // ─── SHARED READ FUNCTION ─────────────────────────────────────────────────────
  // SUPERSEDED (confirmed ENG-2 assessment, 2026-06-18). Called automatically by
  // `advisor_run_computation()` for both Calibration_State.md and Session_Log.md —
  // no separate Claude call needed in FULL_DESKTOP sessions. GitHub MCP fallback
  // (READONLY_MOBILE) is implemented; Desktop Commander (local) is PRIMARY.
  // @see python/advisor/data/file_protocol.py read_framework_file()

  // ─── ALLOCATION SHEET FETCH ──────────────────────────────────────────────────

  FUNCTION fetchAllocation() {
    STEP 1: search {
      tool:     Google_Drive:search_files
      query:    "title = 'Allocation' and parentId = 'root'"
      pageSize: 5
    }
    STEP 2: validate {
      IF count == 0 { HARD_STOP: "Cannot find 'Allocation' in Drive root." }
      IF count > 1  { HARD_STOP: "Found [N] files named 'Allocation' — delete duplicates." }
    }
    STEP 3: read {
      tool:   Google_Drive:read_file_content
      fileId: [id from Step 1]
      // read_file_content (NOT download_file_content) — Sheets require this tool
    }
    RETURN allocation_sheet_contents
  }

  // ─── CALIBRATION STATE + SESSION LOG FETCH ──────────────────────────────────
  // SUPERSEDED — both run automatically at the start of `advisor_run_computation()`
  // (Project_Instructions_MCP.md Step 3) via `read_calibration_state()` and
  // `read_session_log()` — no separate Claude call needed. §8 prior probabilities
  // are AUTHORITATIVE from Session_Log; tool surfaces them as `prior_probs`.
  // @see python/advisor/data/file_protocol.py read_calibration_state(), read_session_log()

  // ─── EXPLICIT FRAMEWORK FILE RE-FETCH ───────────────────────────────────────
  // For inspection or debugging only (not part of the standard session sequence).
  // Use Desktop Commander:read_file([SOURCE_MAP.local.path + filename]) directly.

  // ─── CANONICAL WRITE WORKFLOW ─────────────────────────────────────────────────
  // Single mechanism for all writes: Desktop Commander + local git.
  // REQUIRE: SessionType == FULL_DESKTOP before any pattern executes.
  //
  // PATTERN A — framework amendments: module files, structural changes, §11 updates
  // PATTERN B — session write-back:   Calibration_State.md + Session_Log.md + Portfolio_State.md
  //
  // Both use the same toolchain. Differ only in files touched and commit message convention.

  CANONICAL_WRITE_WORKFLOW {

    TOOLCHAIN {
      edit:   Desktop Commander — edit_block for targeted single edits;
                                  interact_with_process + Python str.replace() for
                                  complex or multi-section edits
      verify: Desktop Commander:interact_with_process (zsh) — grep [key_string] [filepath]
      commit: Desktop Commander:interact_with_process (zsh) — git -C '[local.path]' add / commit / push
    }

    // ── PATTERN A: Framework Amendments ──────────────────────────────────────
    // Use for: module file edits (M01–M18), structural changes, §11 role/classification
    //          updates, any change to framework architecture files.

    PATTERN_A FrameworkAmendment {
      STEP 1: edit_files     { CALL TOOLCHAIN.edit   }
      STEP 2: verify         { CALL TOOLCHAIN.verify }
      STEP 3: commit_and_push {
        git -C [local.path] add [file(s)]
        git -C [local.path] commit -m "[descriptive amendment message]"
        git -C [local.path] push origin master
      }
      GUARD PatternA_Rules {
        NEVER:  use GitHub connector for any write
        ALWAYS: verify with grep before committing
        ALWAYS: push confirms success before reporting done to client
      }
    }

    // ── PATTERN B: Session Write-Back ────────────────────────────────────────
    // SUPERSEDED — wired into `advisor_write_back()` MCP tool, which calls
    // `_tool_write_back()` → `write_back()` in `file_protocol.py`. Internally:
    // constructs §8 entry + Portfolio_State, writes both files, then git add/commit/push.
    // Two files only — NEVER Calibration_State.md (see WriteBack STEP 3 below).
    // REQUIRE: `advisor_apply_scoring()` called this session (tool enforces this).
    // @see python/advisor/mcp_server.py _tool_write_back(), _render_portfolio_state()
    // @see python/advisor/data/file_protocol.py write_back()

    PATTERN_B SessionWriteBack {
      GUARD PatternB_Rules {
        NEVER:  execute in READONLY_MOBILE session  // tool enforces via SessionType check
        NEVER:  commit if §8 probabilities do not sum to 100%  // enforced upstream by apply_all_rules()
        ALWAYS: both files (Session_Log.md, Portfolio_State.md) in a single git commit
        NEVER:  include Calibration_State.md in this commit
        NEVER:  call advisor_write_back() before advisor_apply_scoring() has run this session
      }
    }
  }

  // ─── PORTFOLIO STATE CONSTRUCTION ────────────────────────────────────────────
  // SUPERSEDED — wired into `advisor_write_back()` via `_render_portfolio_state()`
  // in `mcp_server.py`. Called automatically during WriteBack; never invents values.
  // Uses session-end confirmed probabilities — NEVER prior-session values.
  // Note: the rendered Portfolio_State.md is a compact advisory snapshot; it does
  // NOT include the full section inventory that was specified here previously
  // (positions, account_feasibility, etc.) — that was aspirational, not implemented.
  // @see python/advisor/mcp_server.py _render_portfolio_state()

  // ─── WRITE-BACK PROCEDURE (session end) ──────────────────────────────────────
  // REQUIRE: SessionType == FULL_DESKTOP
  // Executed at session end — do not wait for client instruction.
  // @see CANONICAL_WRITE_WORKFLOW.PATTERN_B
  // @see Project_Instructions_MCP.md "Session start sequence" Step 9 (advisor_write_back)

  PROCEDURE WriteBack {
    WHEN:    portfolio_discussion_concluded
    REQUIRE: SessionType == FULL_DESKTOP

    STEP 1: construct Session_Log §7 new_row (MANUAL — not in Python write_back()) {
      date:    [today's date]
      HY_OAS:  [FRED BAMLH0A0HYM2]
      IG_OAS:  [FRED BAMLC0A0CM]
      CCC_OAS: [FRED BAMLH0A3HYC]
      source:  FRED | Trading_Economics | other
      T1_flag: confirmed | composite_only | stale
    }

    STEP 2: construct Session_Log §8 new_entry — handled by PATTERN_B / advisor_write_back() {
      // Python _tool_write_back() constructs the §8 entry internally from the
      // session-end confirmed values. VERIFY sum == 100% before calling.
      // Fields: date, scenario_probabilities, primary_driver, derivation_method,
      //         open_triggers, open_decisions, next_session_flags
    }

    STEP 3: Calibration_State.md {
      // advisor_write_back() / file_protocol.write_back() NEVER writes
      // Calibration_State.md (calibration_state=None passed unconditionally).
      // NEVER include Calibration_State.md in this write-back commit.
      // Calibration value changes go via a SEPARATE PATTERN_A FrameworkAmendment commit.
    }

    STEP 4: Portfolio_State — handled by PATTERN_B / advisor_write_back() {
      // _render_portfolio_state() in mcp_server.py constructs it automatically.
    }

    STEP 4b: writeInstrumentsJson (LOCAL ONLY — does not go to git) {
      // ⚠ NOT currently automated: Python write_back() does NOT write instruments.json.
      // The yfinance fetcher reads instruments.json and falls back if missing.
      // Until this is wired (see FRAMEWORK_BACKLOG.md ENG-25), write manually:
      path:   market_data_mcp/instruments.json (sibling folder — path set by ADVISOR_FRAMEWORK_PATH)
      format: { "instruments": [§11.3 active tickers], "last_updated": "[date]", "session": "[date] advisory" }
      source: §11.3 from Calibration_State.md loaded this session — never from memory
      tool:   Desktop Commander:write_file (mode: rewrite)
      GUARD:
        NEVER: include instruments with 0% target in ALL accounts
        NEVER: push instruments.json to git
    }

    STEP 5: execute CANONICAL_WRITE_WORKFLOW.PATTERN_B (advisor_write_back() MCP call)

    GUARD WriteIntegrity {
      NEVER:  overwrite existing §7 or §8 rows — append only
      NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
      NEVER:  write §8 if probabilities do not sum to 100%
      ALWAYS: Session_Log.md + Portfolio_State.md in a single git commit
      NEVER:  Calibration_State.md in this commit — see STEP 3
    }
  }

  // ─── COMPACTION PROCEDURE (ENG-5: per-session / per-write-back, NOT quarterly-gated) ─────────
  // CORRECTED 2026-06-19 (ENG-5): this procedure used to be gated to four
  // calendar dates (June 30 / Sep 30 / Dec 31 / Mar 31). That guaranteed §3,
  // §7, and §8 would overrun their stated retention limits between audits —
  // by the time of the 2026-06-19 fix, §3 had grown to 26 entries against a
  // stated 10, and §7/§8 similarly overran. Trigger is now per-session, and
  // §7/§8 specifically is now automated (no longer something Claude executes
  // by hand at all).

  // §7/§8 (Session_Log.md): AUTOMATED. advisor_write_back() /
  // file_protocol.write_back() calls _compact_session_log() on every call —
  // checks §7 > 10 rows and §8 > 3 entries, and archives any overflow into
  // the current quarter’s Archive_[Year]Q[N].md (creating it if absent this
  // quarter, appending if it already exists) in the SAME git commit as the
  // session write-back. No manual Claude action needed — if you find yourself
  // about to hand-edit §7/§8 row/entry counts, stop: the tool already did it.

  // §3 (Calibration_State.md): MANUAL, by design — advisor_write_back() NEVER
  // writes Calibration_State.md (see the NEVER rule above: "Calibration_State.md
  // amendments... Desktop Commander + git only"). Trigger condition is now
  // per-session rather than quarterly: check §3’s entry count any time you are
  // about to add a new §3 entry, not only at Q-end.

  PROCEDURE CompactCalibrationLog {
    REQUIRE: about to write or have just written a new §3 entry this session

    STEP 1: count {
      IF §3 entry count (including the new entry just added) <= 10 → STOP,
        no compaction needed this session
    }
    STEP 2: identify {
      archive: all §3 entries except the 10 most recent, by file position —
        preserve their existing relative order, do NOT reorder by version number
        (§3 entries are not always version-monotonic — e.g. a same-day v1.14 may
        legitimately appear before v1.15 if that was the actual edit order; trust
        file position, not the version number, as the source of truth for order)
    }
    STEP 3: append to Calibration_Log.md {
      header: "## Section 3 Archive — Calibration History (Entries Archived
        [date]; [oldest_version]-[newest_version])"
      body:   [archived entries], reversed into chronological (oldest-first)
        order — matches Calibration_Log.md’s existing append-only convention,
        which is the opposite direction from §3’s own newest-first ordering
    }
    STEP 4: trim Calibration_State.md §3 {
      retain: the 10 most recent entries only
      version bump: this compaction is itself a framework change — bump
        Calibration_State.md’s own version number and add a brief §3 entry
        documenting the compaction itself (precedent: v1.12 "File split
        implemented..." and v1.39 "Section 3 compaction...")
    }
    STEP 5: write_and_push via Desktop Commander + git {
      files:   Calibration_State.md (trimmed), Calibration_Log.md (extended)
      message: "Section 3 compaction — archive [N] entries to Calibration_Log.md"
    }

    ARCHIVE_NAMING: "Archive_[Year]Q[N].md" (§7/§8, quarterly, automated) |
                    "Calibration_Log.md" (§3, single permanent file, manual)
  }

}
```