# M05 — Session Initialization
<!-- Version: 1.6 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M05_SessionInit
  Version:         1.6
  Sub-project:     ORCHESTRATION
  Reason to change: the step cross-reference table needs updating because
                    Project_Instructions_MCP.md's step numbering changed.
                    The session sequence itself is owned by Project_Instructions_MCP.md.
  Inputs consumed:  (entry point — orchestrates all other modules)
  Outputs produced: (side effects only: intelligence briefing rendered; write-back committed)
  Calibration deps: all — session init loads full CALIBRATION_STATE and SESSION_LOG at every session
  Types consumed:   @see FW_Types.md — all types (orchestration module)
-->

```
MODULE SessionInit {

  // ─── SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-17) ─────────
  // The full Session Start Sequence — input requirements, step-by-step execution order,
  // floor-check timing, write-back protocol — now lives in Project_Instructions_MCP.md.
  // That file is what Claude actually reads and follows during a live advisory session,
  // has its own current step numbering, and is kept in sync with the MCP tool surface
  // (advisor_run_computation / advisor_apply_scoring / advisor_write_back).
  //
  // This module predates the MCP tools. Its content had drifted: Step 10 below (in the
  // pre-shrink version, recoverable from git history) instructed write-back via
  // github:push_files — wrong, and directly contradicted by M12's CoreRules NEVER list.
  // Project_Instructions_MCP.md's Step 9 has the correct, current write-back instruction.
  //
  // Retained here only as a step-number cross-reference, since several module files
  // cite "@see M05.SessionStartSequence Step N" using this file's original numbering.
  //
  // @see Project_Instructions_MCP.md — "Session start sequence" (authoritative)

  STEP_CROSS_REFERENCE {
    // M05 step (original numbering, this file) → Project_Instructions_MCP.md (current)
    "0  declare_session_type"                        : "implicit in opening message — READONLY_MOBILE iff financial-advisor MCP tools unavailable"
    "1  confirm_allocation_file_loaded"               : "Step 1"
    "1b compute_floor_account_weights"                : "Step 1b"
    "2  confirm_pending_decisions"                    : "Step 2"
    "3  fetch_calibration_state_AND_session_log"      : "Step 3 — advisor_run_computation()"
    "3b current_holdings_floor_check"                 : "Step 3 — advisor_run_computation() floor_breach_alerts"
    "4  fetch_current_market_data"                    : "Step 3 — advisor_run_computation() market_data"
    "5  identify_primary_driver"                      : "Step 4 — qualitative research"
    "6  derive_scenario_probabilities"                : "Step 6 — advisor_apply_scoring()"
    "6b re_run_floor_check_at_current_probabilities"  : "Step 6 — advisor_apply_scoring() floor_breach_alerts_6b (auto-runs if any scenario shifts >= 5pp)"
    "7  complete_intel_gathering_steps_2_to_5"        : "Steps 4-5 — qualitative research + scoring"
    "8  produce_intelligence_briefing"                : "Step 7"
    "9  begin_portfolio_discussion"                   : "Step 8"
    "10 write_session_state_and_credit_readings"      : "Step 9 — advisor_write_back(); Desktop Commander + local git ONLY, never GitHub push_files"
  }

  // Full original procedure (INPUT_1/2/3, SEQUENCE SessionStartSequence with all step
  // detail) recoverable from git history of this file, version 1.5 and earlier.

}
```
