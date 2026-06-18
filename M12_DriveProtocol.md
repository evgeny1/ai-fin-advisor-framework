# M12 — File Access Protocol
<!-- Version: Amendment 4 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M12_DriveProtocol
  Version:         Amendment 4
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
      path:   "/Users/evgeny/Library/CloudStorage/GoogleDrive-evgeny.shatalov@gmail.com/My Drive/dev/AI Financial Advisor Framework/"
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
  // Used by fetchCalibrationState(), fetchSessionLog(), fetchFrameworkFile().
  // Desktop Commander is PRIMARY for all .md framework files (no base64 decode needed).
  // GitHub MCP is the backup when Desktop Commander is unavailable (READONLY_MOBILE session).
  // Google Drive is NOT used for framework .md files — only for the Allocation sheet.

  FUNCTION readFrameworkFile(filename: String) -> String {

    TRY {  // Primary: Desktop Commander (local git path)
      RETURN Desktop_Commander:read_file(
        path: SOURCE_MAP.local.path + filename
      )
      // Returns plain text — no base64 decode needed.
      // Works only in FULL_DESKTOP sessions.
    }
    CATCH {  // Backup: GitHub MCP (READONLY_MOBILE or if local read fails)
      WARN: "Desktop Commander read failed for [filename] — falling back to GitHub MCP"
      RETURN github:get_file_contents(
        owner:  SOURCE_MAP.github.owner,
        repo:   SOURCE_MAP.github.repo,
        path:   filename,
        branch: SOURCE_MAP.github.branch
      ).content
    }
  }

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

  // ─── CALIBRATION STATE FETCH ─────────────────────────────────────────────────

  FUNCTION fetchCalibrationState() {
    content = readFrameworkFile("Calibration_State.md")
    APPLY:
      §1  // credit thresholds
      §2  // energy, currency, macro thresholds
      §4  // growth objectives return table + multipliers
      §9  // M14 market regime thresholds
      §11 // M15 role registry + instrument classification table
      §12 // M17 cascade thresholds
    // §8 session state lives in Session_Log.md → load via fetchSessionLog()
    RETURN content
  }

  // ─── SESSION LOG FETCH ───────────────────────────────────────────────────────
  // Run CONCURRENTLY with fetchCalibrationState() — only after fetchAllocation() succeeds.

  FUNCTION fetchSessionLog() {
    content = readFrameworkFile("Session_Log.md")
    APPLY:
      §7  // credit readings history (reference only)
      §8  // AUTHORITATIVE source for: prior scenario probabilities (25pp cap enforcement),
          //   open triggers, open decisions, next_session_flags
    RETURN content
  }

  // ─── FRAMEWORK FILE FETCH ────────────────────────────────────────────────────
  // Explicit re-fetch or inspection of any module file.

  FUNCTION fetchFrameworkFile(path: String) -> String {
    RETURN readFrameworkFile(path)
  }

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
    // Use for: session-end write of §8 + Portfolio_State.
    // CORRECTED during ENG-2 review (2026-06-17): this used to describe a manual
    // Desktop-Commander-driven edit/grep/git sequence. Confirmed that's stale —
    // data/file_protocol.py.write_back() now does file writes AND
    // git add/commit/push as a single Python function call, invoked by the
    // advisor_write_back() MCP tool. No manual edit_block/grep/git steps run for
    // session write-back anymore. Two files only — NEVER Calibration_State.md
    // (see STEP 3 above).

    PATTERN_B SessionWriteBack {
      CALL: advisor_write_back(primary_driver, open_triggers, open_decisions,
                                session_type, next_session_flags)
      // Internally: writes Session_Log.md + Portfolio_State.md, then
      // git add / commit / push — all inside one Python call (file_protocol.write_back()).
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
  // Render function — assembles existing session data into Portfolio_State.md.
  // Called during WriteBack. Never invents new values.
  // Uses session-end confirmed values — NEVER prior-session values for probabilities.

  FUNCTION constructPortfolioState() -> String {

    HEADER {
      "# Portfolio State\n"
      "<!-- Living snapshot — updated after each advisory session write-back -->\n"
      "<!-- Source of truth: Calibration_State.md [version] + Session_Log.md ([date]) -->\n"
      "<!-- Last updated: [today's date] -->\n"
      "<!-- Purpose: context document for the conversational companion project -->\n"
      "<!-- Do NOT use for execution decisions — use the advisory project for that -->\n"
    }

    SECTION scenario_probabilities {
      source: Session_Log §8 new_entry.scenario_probabilities
      include: probability + one-line rationale per scenario
      include: primary_driver + challenger_drivers from identifyPrimaryDriver()
    }
    SECTION regime_context {
      source: M03 scenario descriptions + current probability vector
      include: 2–3 sentences per active scenario (≥10%); single most important implication
    }
    SECTION credit_and_market_signals {
      source: §7 new_row + FetchRegistry readings
      include: HY_OAS, IG_OAS, CCC_OAS, MOVE, VIX, S&P, DFF, SOFR, THREEFYTP10,
               30Y yield, yield curve spreads, BZ=F/WTI, DXY, FINRA margin debt, KRE
      include: threshold status per reading (NORMAL / WATCH / FIRED)
      include: M14 composite regime signal + cascade level
    }
    SECTION positions {
      source: Allocation sheet + CALIBRATION_STATE §11
      include per instrument: ticker, role(s), EV, scenario verdict summary,
                              target allocations, current status note
      include: portfolio total; instruments not held + adoption triggers
    }
    SECTION open_triggers  { source: Session_Log §8 new_entry }
    SECTION open_decisions { source: Session_Log §8 new_entry }
    SECTION account_feasibility {
      source: M13.FeasibilityCheck results this session
      include: required EV, achieved EV, gap, status per account
    }
    SECTION next_session_priorities { source: Session_Log §8 new_entry.next_session_flags }
    SECTION framework_version       { source: Calibration_State.md header + session metadata }

    RETURN assembled_markdown_content
  }

  // ─── WRITE-BACK PROCEDURE (session end) ──────────────────────────────────────
  // REQUIRE: SessionType == FULL_DESKTOP
  // Executed automatically at session end — do not wait for client instruction.
  // @see CANONICAL_WRITE_WORKFLOW.PATTERN_B
  // @see M05_SessionInit.SessionStartSequence Step 10

  PROCEDURE WriteBack {
    WHEN:    portfolio_discussion_concluded
    REQUIRE: SessionType == FULL_DESKTOP

    STEP 1: construct Session_Log §7 new_row {
      date:    [today's date]
      HY_OAS:  [FRED BAMLH0A0HYM2]
      IG_OAS:  [FRED BAMLC0A0CM]
      CCC_OAS: [FRED BAMLH0A3HYC]
      source:  FRED | Trading_Economics | other
      T1_flag: confirmed | composite_only | stale
    }

    STEP 2: construct Session_Log §8 new_entry {
      date:                   [today's date]
      scenario_probabilities: { A: [%], B: [%], C: [%], D: [%], E: [%], F: [%] }
      // VERIFY: sum == 100% before proceeding
      primary_driver:         [current dominant driver]
      derivation_method:      scored | manual_override
      manual_override_reason: [T1 evidence + rationale] | null
      open_triggers:          [list]
      open_decisions:         [list]
      next_session_flags:     [list]
    }

    STEP 3: Calibration_State.md {
      // CORRECTED during ENG-2 review (2026-06-17) — this step previously said to
      // "always include" Calibration_State.md in the write-back commit. That was wrong
      // and contradicted confirmed, intentional code behavior:
      // advisor_write_back() / file_protocol.write_back() NEVER writes
      // Calibration_State.md — calibration_state=None is passed unconditionally.
      // NEVER include Calibration_State.md in this write-back commit.
      // Calibration value changes (§3 log entries, §11 EV updates, threshold changes)
      // go through a SEPARATE manual edit + git commit via PATTERN_A FrameworkAmendment
      // — not through this procedure, and not in the same commit as §8/Portfolio_State.
    }

    STEP 4: construct Portfolio_State {
      CALL constructPortfolioState()
    }

    STEP 4b: writeInstrumentsJson (LOCAL ONLY — does not go to git) {
      path:   LOCAL_MCP_DIR/instruments.json
      format: { "instruments": [§11.3 active tickers], "last_updated": "[date]", "session": "[date] advisory" }
      source: §11.3 from CALIBRATION_STATE_FETCH — never from memory or prior session
      tool:   Desktop Commander:write_file (mode: rewrite)
      GUARD:
        NEVER:  include instruments with 0% target in ALL accounts
        NEVER:  push instruments.json to git
        REQUIRE: Calibration_State.md successfully fetched this session
      LOCAL_MCP_DIR: /Users/evgeny/Library/CloudStorage/GoogleDrive-evgeny.shatalov@gmail.com/My Drive/dev/market_data_mcp
    }

    STEP 5: write_verify_push {
      CALL CANONICAL_WRITE_WORKFLOW.PATTERN_B
    }

    GUARD WriteIntegrity {
      NEVER:  overwrite existing §7 or §8 rows — append only
      NEVER:  write §7 row if T1_flag == stale AND no_better_source_available
      NEVER:  write §8 if probabilities do not sum to 100%
      ALWAYS: both files (Session_Log.md, Portfolio_State.md) in a single git commit
              // NEVER Calibration_State.md — see STEP 3 above
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