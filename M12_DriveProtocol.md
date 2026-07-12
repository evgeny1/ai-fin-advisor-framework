# M12 — File Access Protocol
<!-- Version: Amendment 11 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M12_DriveProtocol
  Version:         Amendment 11
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
  // READ HIERARCHY for framework .md files — this describes CLAUDE's own direct-tool
  // read path (Desktop Commander / GitHub MCP calls Claude makes itself, e.g. in a
  // READONLY_MOBILE or coding session):
  //   1st: Desktop Commander (local git path) — FULL_DESKTOP sessions, fast, no decode
  //   2nd: GitHub MCP — backup for READONLY_MOBILE or local read failure
  //   NOT used for .md reads (by Claude): Google Drive (Drive is for the Allocation files only)
  //
  // RESOLVED 2026-06-20 (ENG-21): this is a SEPARATE system from the
  // `financial-advisor` Python MCP server's OWN internal read fallback
  // (file_protocol.read_framework_file(): local filesystem → Google Drive API,
  // never GitHub). The two don't conflict — they're different actors with
  // different failure modes — but the Python server's Drive fallback is
  // currently dormant by design, not a live alternate path: it reuses
  // allocation_sheet.py's _get_drive_service(), which requires a service-account
  // or OAuth credential file under ~/.advisor/ that isn't configured (the
  // Allocation sheet itself is read by Claude via the Google Drive MCP connector
  // directly, not through this Python-native client — that client is a possible
  // future feature, not needed today). Confirmed via test coverage
  // (tests/test_stage1/test_file_protocol_read_fallback.py) that the failure mode
  // is clean either way: a missing local file with no Drive credentials raises a
  // HardStopException naming both causes, not an unhandled exception.

  SOURCE_MAP {
    drive: {
      // Split 2026-07-12 from one multi-tab "Allocation" file into three
      // single-tab files, after discovering Google Drive's read_file_content
      // reliably surfaces only ONE tab per file — a hard per-call limitation
      // of the tool, not a length/token-budget issue as first assumed. Which
      // tab it returns from a multi-tab file depends on which was last active
      // in the Sheets UI, not a fixed index — so a multi-tab file is
      // fundamentally unreliable here regardless of tab order, and the fix is
      // one file per tab, not reordering tabs within one file.
      allocation_schwab_accounts: {
        file:   "Allocation"
        type:   Google_Sheets
        access: read_only
        search: by title in Drive root — NEVER hardcode file ID
        // Holds the Schwab Accounts tab (Evgeny's 4 own accounts + Summary +
        // tax-loss table). May still also carry leftover Objectives/Color-
        // Palette tabs from before the split — if so, don't treat this file
        // as reliably single-purpose until those are removed from it.
      }
      allocation_relative_accounts: {
        file:   "Allocation - Relative's Schwab Accounts"
        type:   Google_Sheets
        access: read_only
        search: by title in Drive root — NEVER hardcode file ID
        // Holds the Relative's Schwab Accounts tab (IRA …469, Roth …466) —
        // the source for Step 1b's floor_account_weights_json computation.
      }
      allocation_objectives: {
        file:   "Allocation - Objectives"
        type:   Google_Sheets
        access: read_only
        search: by title in Drive root — NEVER hardcode file ID
        // Holds the Objectives tab (account_id, owner, planning_horizon_years,
        // objective_type, floor_nominal_loss, concentration_cap,
        // drawdown_tolerance) — the source for advisor_evaluate_allocation()'s
        // per-account scalar parameters.
      }
      // All three: Prices live via GOOGLEFINANCE — treat as current at time of
      // fetch. Framework never writes to any Allocation file. Read by Claude
      // via the Google Drive MCP connector — NOT by Python.
      // allocation_sheet.py also contains a Python-native FRED/FINRA-via-sheet
      // fetcher (fetch_fred_series, fetch_finra_margin) for a possible future
      // feature; it is not registered in advisor_run_computation()'s live
      // FetchRegistry today and requires no action (ENG-21).
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
      files:  [Calibration_State.md, Instrument_Classification.md, Session_Log.md, Portfolio_State.md, Calibration_Log.md,
               M01–M19.md, FW_Types.md, 00_INDEX.md, Archive_*.md]
    }
  }

  GUARD CoreRules {
    NEVER:  use web_fetch for any GitHub or Google Drive file
    NEVER:  hardcode any Google Drive file ID — search by title for each Allocation file; use local path for framework files
    ALWAYS: resolve all three Allocation files via Drive root title search at session start (never hardcode any of their IDs)
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

  // ─── ALLOCATION FILES FETCH (three files as of 2026-07-12) ──────────────────

  // Three separate calls as of 2026-07-12 (@see SOURCE_MAP.drive above for why
  // this is one file per tab, not one multi-tab file). Each file's exact title
  // must match — NEVER hardcode a file ID, resolve fresh every session.

  FUNCTION fetchAllocationFile(exact_title) {
    STEP 1: search {
      tool:     Google_Drive:search_files
      query:    "title = '[exact_title]' and parentId = 'root'"
      pageSize: 5
    }
    STEP 2: validate {
      IF count == 0 { HARD_STOP: "Cannot find '[exact_title]' in Drive root." }
      IF count > 1  { HARD_STOP: "Found [N] files named '[exact_title]' — delete duplicates." }
    }
    STEP 3: read {
      tool:   Google_Drive:read_file_content
      fileId: [id from Step 1]
      // read_file_content (NOT download_file_content) — Sheets require this tool
    }
    RETURN file_contents
  }

  FUNCTION fetchAllocation() {
    schwab_accounts    = fetchAllocationFile("Allocation")
    relative_accounts  = fetchAllocationFile("Allocation - Relative's Schwab Accounts")
    objectives         = fetchAllocationFile("Allocation - Objectives")
    // STOP (via the HARD_STOPs inside fetchAllocationFile) if any of the three fails —
    // do not proceed on two-of-three; all three are required for a normal M05 session.
    RETURN { schwab_accounts, relative_accounts, objectives }
  }

  // ─── CALIBRATION STATE + INSTRUMENT CLASSIFICATION + SESSION LOG FETCH ──────
  // SUPERSEDED — all three run automatically at the start of `advisor_run_computation()`
  // (Project_Instructions_MCP.md Step 3) via `read_calibration_state()`,
  // `read_instrument_classification()`, and `read_session_log()` — no separate
  // Claude call needed. §8 prior probabilities are AUTHORITATIVE from Session_Log;
  // tool surfaces them as `prior_probs`.
  //
  // ENG-51 (2026-07-06): §11 (role registry + instrument classification table)
  // was extracted verbatim out of Calibration_State.md into its own file,
  // Instrument_Classification.md — a storage-location change only. Motivation:
  // the planned trend/rotation layer (ENG-50) needs to read/write per-instrument
  // state without every read/write touching credit thresholds, the return
  // table, or anything else living in Calibration_State.md. Section numbering
  // (§11.1-§11.4) is unchanged — every existing "§11.x" cross-reference in this
  // framework still resolves, just in the other file now.
  // @see python/advisor/data/file_protocol.py read_calibration_state(),
  //      read_instrument_classification(), read_session_log()
  // @see python/advisor/config/calibration.py parse_calibration_state() —
  //      now takes an optional second `instrument_classification_text` param

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

    STEP 4b: writeInstrumentsJson — AUTOMATED, NOT part of this WriteBack procedure {
      // RESOLVED 2026-06-20 (ENG-25): wired into advisor_run_computation() itself —
      // it runs at session Step 3 (right after §11.3 is parsed), not here at
      // session end. Retained at this numbering only for historical continuity
      // with Project_Instructions_MCP.md's old step references.
      path:   market_data_mcp/instruments.json (sibling folder — path set by ADVISOR_MCP_DIR,
                                                  defaults to a path computed relative to
                                                  ADVISOR_FRAMEWORK_PATH's sibling)
      format: { "instruments": [§11.3 active tickers], "last_updated": "[date]", "session": "[date] advisory" }
      source: §11.3 from Instrument_Classification.md loaded THIS session (ENG-51:
              moved out of Calibration_State.md 2026-07-06) — never from memory
      impl:   yfinance_fetcher.write_instruments_json(), called from
              mcp_server._tool_run_computation() — non-fatal on failure (flagged;
              load_instruments() falls back to its own hardcoded list)
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

  // ─── COMPACTION PROCEDURE (ENG-53: calendar-age based; ENG-5: per-write-back, NOT quarterly-gated) ─────
  // CORRECTED 2026-06-19 (ENG-5): this procedure used to be gated to four
  // calendar dates (June 30 / Sep 30 / Dec 31 / Mar 31). That guaranteed §3,
  // §7, and §8 would overrun their stated retention limits between audits —
  // by the time of the 2026-06-19 fix, §3 had grown to 26 entries against a
  // stated 10, and §7/§8 similarly overran. Trigger is now per-session, and
  // §7/§8 specifically is now automated (no longer something Claude executes
  // by hand at all).
  //
  // SUPERSEDED 2026-07-06 (ENG-53): §7/§8's trigger changed from entry-count
  // (last-10 / last-3) to calendar age (90 days) — client's explicit stated
  // preference was "rotate by calendar age, not entry count or file size."
  // There is no longer a count-based fallback either. Gated on ENG-52
  // landing first so the age check could key off a real `date:` YAML field
  // rather than parsing prose.

  // §7/§8 (Session_Log.md): AUTOMATED. advisor_write_back() /
  // file_protocol.write_back() calls _compact_session_log() on every call —
  // any §7 row or §8 entry whose OWN date is more than 90 calendar days
  // before today archives to the Archive_[Year]Q[N].md matching THAT
  // item's own quarter (not today's quarter — a single write-back whose
  // archived items span more than one quarter can touch more than one
  // archive file), creating each as needed, in the SAME git commit as the
  // session write-back. No manual Claude action needed — if you find
  // yourself about to hand-edit §7/§8 row/entry counts or ages, stop: the
  // tool already did it.

  // §3 (Calibration_State.md): MANUAL, by design — advisor_write_back() NEVER
  // writes Calibration_State.md (see the NEVER rule above: "Calibration_State.md
  // amendments... Desktop Commander + git only"). Trigger condition is now
  // per-session rather than quarterly: check §3’s entry count any time you are
  // about to add a new §3 entry, not only at Q-end. (§3 was NOT brought under
  // ENG-53's age-based rule — it stayed count-based and manual; only §7/§8
  // changed.)

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