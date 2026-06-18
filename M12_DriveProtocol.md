# M12 — File Access Protocol
<!-- Version: Amendment 5 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M12_DriveProtocol
  Version:         Amendment 5
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

  // ─── COMPACTION PROCEDURE (quarterly — Q-end audit) ──────────────────────────
  // Execute at: June 30, September 30, December 31, March 31

  PROCEDURE CompactSessionLog {

    STEP 1: identify {
      archive: all §7 rows except 10 most recent
      archive: all §8 entries except 3 most recent
    }
    STEP 2: create Archive_[Year]Q[N].md {
      header: "# Session Log Archive — [Year] Q[N]\nArchived: [date]\n"
      body:   [archived §7 rows] + [archived §8 entries]
    }
    STEP 3: compact Session_Log.md {
      retain: last 10 §7 rows, last 3 §8 entries
      add compaction note: "Entries before [cutoff] archived to Archive_[Year]Q[N].md"
    }
    STEP 4: write_and_push via PATTERN_A {
      files:   Archive_[Year]Q[N].md (new), Session_Log.md (compacted),
               Calibration_State.md (if §3 trimmed), Portfolio_State.md (re-rendered)
      message: "Q[N] session log compaction — archive [Year]Q[N]"
    }

    ARCHIVE_NAMING: "Archive_[Year]Q[N].md" (quarterly) | "Archive_[Year].md" (annual)
  }

}
```