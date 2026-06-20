# M15 — Instrument Classification
<!-- Version: 1.2 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M15_InstrumentClassification
  Version:         1.2
  Sub-project:     ANALYSIS_ENGINE
  Reason to change: classification logic, blendedScenarioReturn methodology, or ValidateClassifications() rules change.
                    Role registry and instrument decomposition: add to CALIBRATION_STATE §11 only — not here.
  Inputs consumed:  instrument metadata; ComponentVector (§11 decomposition from CALIBRATION_STATE)
  Outputs produced: ComponentVector; BlendedReturn; ValidateClassifications result; dominantDirective
  Calibration deps: CALIBRATION_STATE §11 (role registry + instrument classification table)
                    CALIBRATION_STATE §4.1 (return table — consumed via M13)
  Types consumed:   @see FW_Types.md — ComponentVector, BlendedReturn, RoleID, Directive
-->

```
MODULE InstrumentClassification {

  // ─── DESIGN PRINCIPLES ───────────────────────────────────────────────────
  // 1. No instrument ticker or role name is hardcoded in any framework module.
  //    Roles live in CALIBRATION_STATE §11.ROLE_REGISTRY.
  //    Instrument decompositions live in CALIBRATION_STATE §11.INSTRUMENT_CLASSIFICATION_TABLE.
  // 2. Any instrument may have multiple role components with fractional weights summing to 1.0.
  //    Single-driver instruments have one component at weight 1.0 — identical to prior behavior.
  // 3. ALL scenario return computations route through blendedScenarioReturn() —
  //    never direct §4.1[role][scenario] lookups.
  // 4. New instruments found in allocation file but absent from §11 → HARD_STOP at session start.
  // 5. New roles are added via CALIBRATION_STATE §11 only — no module file edits required.
  // 6. Backward compatible: pure single-role instruments produce identical results to prior sessions.

  // ─── SESSION-START VALIDATION ────────────────────────────────────────────
  // SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-17; wiring
  // closed via ENG-16/pre-existing). Runs automatically inside `advisor_run_computation()`
  // (Project_Instructions_MCP.md Step 3) — HARD_STOP surfaces in the tool's status field,
  // no separate call needed. Retained here as the spec for what gets checked:
  //   1. Every instrument in the allocation file has a §11 entry (else HARD_STOP)
  //   2. Every component role exists in §11.ROLE_REGISTRY (else HARD_STOP)
  //   3. Every registered role has a §4.1 return table row (else HARD_STOP)
  //   4. Component weights sum to 1.0 per instrument, tolerance 0.001 (else HARD_STOP)
  //   5. Staleness: flag (non-blocking) any classification last_reviewed > 90 days ago
  // @see python/advisor/analysis/instruments.py validate_classifications()

  // ─── INSTRUMENT CLASSIFICATION LOOKUP ────────────────────────────────────
  // SUPERSEDED — wired into `advisor_evaluate_allocation()`'s `components` field
  // (Project_Instructions_MCP.md). Replaces M08_FunctionalRoles.classifyRole() for
  // all scenario return computations. Returns a vector of {role, weight} pairs
  // summing to 1.0; ticker missing from §11 → HARD_STOP (caught at session start
  // by ValidateClassifications() above, so this should never fire mid-session).
  // @see python/advisor/analysis/instruments.py classify_instrument()

  // ─── BLENDED SCENARIO RETURN ─────────────────────────────────────────────
  // SUPERSEDED — wired into `advisor_evaluate_allocation()`'s `per_scenario` /
  // `blended_conservative_return_pct` fields. REPLACES all direct §4.1[role][scenario]
  // lookups throughout the framework — never present allocation numbers without this
  // having run (the full per-scenario breakdown, not just the blended total).
  // Formula: result = Σ component.weight × §4.1[component.role][scenario][return_type]
  // ("conservative" for all feasibility/allocation math; "upside" disclosed in
  // briefing only, NEVER used in any computation). For a pure single-role
  // instrument, result equals §4.1[role][scenario] exactly.
  // @see python/advisor/analysis/instruments.py blended_scenario_return()

  // ─── DOMINANT DIRECTIVE (for M09/M10 execution protocols) ────────────────
  // SUPERSEDED — wired into `advisor_evaluate_allocation()`'s
  // `dominant_directive_conflict_aware` field; supersedes the naive directive for
  // presentation. Spec: for composite instruments, apply the directive of the
  // highest-weight material component (weight >= 0.15) unless material components'
  // directives conflict — in which case surface the conflict, apply the dominant
  // (largest-weight) role's directive anyway, and flag for manual review. Single
  //-component instruments: trivial, the one role's directive applies.
  // @see python/advisor/analysis/instruments.py dominant_directive()

  // ─── CLASSIFICATION METHODOLOGY ──────────────────────────────────────────
  // Reference procedure for deriving component weights at initial classification
  // and at each periodic review. Human judgment required — not automated.
  // Document methodology and sources in §11 table entry.

  PROCEDURE DetermineComponentWeights(ticker) {

    // STEP 1: Obtain fund composition data from T1 source
    // Sources: fund provider fact sheet, ETF.com holdings tab, SEC 13F filing
    // Required: sector weights OR top holdings with approximate portfolio weights
    // Preferred: holdings covering >= 60% of fund NAV

    // STEP 2: Map each material holding/sector to a registered role in §11
    // Mapping requires binding-driver judgment — sector labels ≠ functional roles.
    //
    // Reference mappings (illustrative, not exhaustive):
    //   "Technology"  → secular_technology_growth if AI/software-driven
    //               → broad_market_equity_domestic if legacy hardware/services
    //   "Energy"      → inflation_hedge_commodity_linked if E&P/refining
    //               → real_asset_contracted_revenue if pipeline/MLP structure
    //   "Industrials" → policy_driven_thematic_equity if defense/infrastructure mandate
    //               → broad_market_equity_domestic if cyclical without mandate dependence
    //
    // REQUIRE per component: state the binding driver explicitly, not just sector label

    // STEP 3: Aggregate to role-level weights
    // Residual weight → assign to dominant role (largest component)
    // Verify sum == 1.0

    // STEP 4: Document in §11.INSTRUMENT_CLASSIFICATION_TABLE:
    //   components: [{role, weight, basis, source}]
    //   last_reviewed: current_session_date
    //   methodology: "sector_weight_analysis | holdings_analysis | judgment"
    //   notes: any caveats, limitations, pending verifications

    // STEP 5: If a new role was created for this instrument:
    //   → Run AddRole() procedure before session can proceed
    //   → §4.1 return table row required — ValidateClassifications() will HARD_STOP without it
  }

  // ─── ROLE REGISTRY MANAGEMENT ────────────────────────────────────────────
  // Add/remove roles via CALIBRATION_STATE §11 only.
  // No framework module file edits required to add a role.

  PROCEDURE AddRole(role_name, binding_driver, scenario_sensitivity_notes) {
    // 1: Verify role_name not already in §11.ROLE_REGISTRY
    // 2: Add to §11.ROLE_REGISTRY.registered_roles with binding_driver and notes
    // 3: Add row to §4.1 return table — conservative + upside per scenario (A–F)
    //    Methodology: historical analogue analysis per M11.CalibrationDiscipline
    //    REQUIRE: at least 2 historical analogue periods identified and cited
    //    Document in §3 Calibration Log: role name, rationale, analogues, return estimates
    // 4: Reclassify any instruments where new role improves accuracy
    //    Update §11.INSTRUMENT_CLASSIFICATION_TABLE entries accordingly
    // 5: Write-back to GitHub — framework amendment PR if module files also change;
    //    direct session write-back if §11 + §4.1 only
    NEVER: add role without §4.1 row — ValidateClassifications() will HARD_STOP
  }

  PROCEDURE RemoveRole(role_name) {
    // 1: Verify no instrument in §11 table references this role
    //    IF any instrument uses it → reclassify instrument first
    // 2: Remove from §11.ROLE_REGISTRY.registered_roles
    // 3: Archive §4.1 row in §3 Calibration Log (do not delete — audit trail)
    // 4: Log rationale in §3
    NEVER: remove role while any §11 classification entry references it
  }

  PROCEDURE RemoveInstrument(ticker) {
    // ENG-8 (2026-06-19): added after PAVE’s §11.3 entry sat orphaned for two
    // versions after the position was fully exited and logged in §3 (v1.33,
    // reconfirmed v1.37) — nobody deleted the classification entry when the
    // position closed. PAVE is the concrete example this procedure fixes.
    // 1: Confirm exit is fully logged in §3 (proceeds, realized gain/loss, tax
    //    treatment, redeployment) before removing the §11.3 entry — never the
    //    reverse order
    // 2: Delete the ticker’s entire §11.3 entry (ComponentVector, target
    //    allocations, guard status, hold/exit-trigger analysis — all of it, not a
    //    partial trim; an exited position has no forward decision use for any of
    //    this)
    // 3: Do NOT archive the §11.3 entry text anywhere — unlike §3/§4.1 rows,
    //    §11.3 is current-state configuration, not an audit trail. The §3 exit
    //    entry IS the permanent record of why and when the position closed.
    // 4: If any other module (e.g. M19 §13 thesis conditions) carries a parallel
    //    entry for this ticker, remove that too in the same pass — same principle
    NEVER: leave an exited instrument’s §11.3 entry past the same session/version
      bump that logs its exit in §3 — "cleanup later" in practice means never
  }

  // ─── INTEGRATION WITH EXISTING FRAMEWORK ─────────────────────────────────
  //
  // M08.classifyRole() remains in use for:
  //   (a) ThematicETF_ClassificationAudit() constituent-level analysis
  //       where individual stocks (not ETFs) are assessed
  //   (b) §11 gap detection context — identifying what a new instrument likely is
  //       before formal classification entry is created
  //
  // For ALL allocation computations (M13.idealAllocation, M13.FeasibilityCheck,
  // M09/M10 scenario directives, M03.scenarioWeightedAllocation):
  //   → use M15.classifyInstrument() + M15.blendedScenarioReturn()
  //   → NOT M08.classifyRole() + direct §4.1 lookup
  //
  // M13.RecommendationFlow step 3 updated:
  //   OLD: M08_FunctionalRoles.classifyRole(asset)
  //   NEW: M15_InstrumentClassification.classifyInstrument(asset)
  //        → M15_InstrumentClassification.blendedScenarioReturn(asset, scenario, "conservative")
  //
  // M13.idealAllocation() step 1 updated:
  //   OLD: role = M08.classifyRole(asset)
  //   NEW: components = M15.classifyInstrument(asset)
  //        directive = M15.dominantDirective(asset, scenario)
  //
  // §4.1 return table: structure unchanged (roles × scenarios).
  //   Now consumed via blendedScenarioReturn() — never directly.

  // ─── SESSION LOAD REQUIREMENT ────────────────────────────────────────────

  REQUIRE at_session_start {
    CALIBRATION_STATE.§11.ROLE_REGISTRY                    // loaded with Calibration_State.md
    CALIBRATION_STATE.§11.INSTRUMENT_CLASSIFICATION_TABLE  // loaded with Calibration_State.md
    M15.ValidateClassifications()                          // run after Project_Instructions_MCP.md Steps 1 + 3
    // Absence or validation failure = session invalid for allocation computations
  }

}
```
