# M15 — Instrument Classification
<!-- Version: 1.0 | Adopted: April 28, 2026 -->
<!-- Extends: M08_FunctionalRoles — composite decomposition; blendedScenarioReturn replaces direct §4.1 lookups -->
<!-- Provides: extensible role registry, composite decomposition, blended scenario returns, session-start validation -->
<!-- Companion: @see CALIBRATION_STATE §11 (role registry + instrument classification table) -->
<!-- Consumed by: M03_ScenarioFramework, M08_FunctionalRoles, M13_GrowthObjectives, M09_ScenariosABC, M10_ScenariosDEF -->

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
  // Runs as part of M05_SessionInit Step 3 — after both allocation file and
  // Calibration State are confirmed loaded.

  PROCEDURE ValidateClassifications() {

    instruments_in_file = AllocationSheet.all_tickers()
    classified          = CALIBRATION_STATE.§11.INSTRUMENT_CLASSIFICATION_TABLE.keys()
    registered_roles    = CALIBRATION_STATE.§11.ROLE_REGISTRY.registered_roles

    // Check 1: Every instrument in allocation file must have a §11 entry
    unclassified = instruments_in_file EXCLUDING classified
    IF unclassified NOT EMPTY {
      HARD_STOP
      FLAG: "Unclassified instruments in allocation file: [list]
             Add entries to CALIBRATION_STATE §11.INSTRUMENT_CLASSIFICATION_TABLE.
             Required: components[] with {role, weight}, weights summing to 1.0,
             last_reviewed date, methodology note.
             Session is invalid for allocation computations until resolved."
    }

    // Check 2: Every component role must exist in §11.ROLE_REGISTRY
    FOR each instrument IN classified {
      FOR each component IN §11.classification(instrument).components {
        IF component.role NOT IN registered_roles {
          HARD_STOP
          FLAG: "[instrument]: component references unregistered role '[component.role]'.
                 Register role in §11.ROLE_REGISTRY before proceeding."
        }
      }
    }

    // Check 3: Every registered role must have a row in §4.1 return table
    FOR each role IN registered_roles {
      IF role NOT IN CALIBRATION_STATE.§4_1 {
        HARD_STOP
        FLAG: "Role '[role]' registered in §11 has no §4.1 return table row.
               Add conservative/upside estimates for all six scenarios before proceeding."
      }
    }

    // Check 4: Component weights must sum to 1.0 per instrument (tolerance 0.001)
    FOR each instrument IN classified {
      total_weight = SUM(c.weight for c IN §11.classification(instrument).components)
      IF abs(total_weight - 1.0) > 0.001 {
        HARD_STOP
        FLAG: "[instrument] component weights sum to [total_weight] (expected 1.0).
               Correct §11.INSTRUMENT_CLASSIFICATION_TABLE."
      }
    }

    // Check 5: Staleness warning (non-blocking)
    FOR each instrument IN classified {
      last_reviewed = §11.classification(instrument).last_reviewed
      IF last_reviewed < current_date - 90_calendar_days {
        FLAG: "[instrument] classification last reviewed [last_reviewed] — over 90 days ago.
               Queue for next scheduled calibration review."
        // Warning only — does not block session
      }
    }

    RETURN validation_passed
  }

  // ─── INSTRUMENT CLASSIFICATION LOOKUP ────────────────────────────────────
  // Replaces M08_FunctionalRoles.classifyRole() for all scenario return computations.
  // Returns a vector of {role, weight} pairs summing to 1.0.

  FUNCTION classifyInstrument(ticker) -> ComponentVector {
    IF ticker NOT IN CALIBRATION_STATE.§11.INSTRUMENT_CLASSIFICATION_TABLE {
      HARD_STOP
      FLAG: "[ticker] missing from §11 — ValidateClassifications() should have caught this at session start."
    }
    RETURN CALIBRATION_STATE.§11.INSTRUMENT_CLASSIFICATION_TABLE[ticker].components
  }

  // ─── BLENDED SCENARIO RETURN ─────────────────────────────────────────────
  // REPLACES all direct §4.1[role][scenario] lookups throughout the framework.
  // All scenario return computations MUST route through this function.
  // For pure single-role instruments: result equals §4.1[role][scenario] exactly.
  // For composite instruments: weighted blend across components.

  FUNCTION blendedScenarioReturn(ticker, scenario, return_type) -> Float {
    // return_type: "conservative" | "upside"
    // Default for ALL feasibility math, idealAllocation(), FeasibilityCheck(): "conservative"
    // Upside: disclosed in briefing only — NEVER used in any computation

    components = classifyInstrument(ticker)
    result = 0
    FOR each component c IN components {
      result += c.weight × CALIBRATION_STATE.§4_1[c.role][scenario][return_type]
    }
    RETURN result
  }

  // ─── DOMINANT DIRECTIVE (for M09/M10 execution protocols) ────────────────
  // Scenario execution protocols prescribe directives by role.
  // For composite instruments: apply directive of highest-weight material component
  // unless directives conflict — in which case surface for resolution.
  // Material component threshold: weight >= 0.15

  FUNCTION dominantDirective(ticker, scenario) -> Directive {
    components        = classifyInstrument(ticker)
    sorted            = sort_descending(components by weight)
    primary_role      = sorted[0].role
    primary_directive = lookup_directive(primary_role, scenario)  // from M09 or M10

    // Single-component: trivial
    IF sorted.length == 1 { RETURN primary_directive }

    // Material components only (weight >= 0.15)
    material   = [c for c IN components WHERE c.weight >= 0.15]
    directives = [lookup_directive(c.role, scenario) for c IN material]

    IF all_same_direction(directives) {
      RETURN most_conservative(directives)
      // Same-direction conflict: apply more conservative — @see M08.DualRoleConflict
    }

    IF conflicting_directions(directives) {
      FLAG: "[ticker] has conflicting directives in [scenario]:
             [list c.role: directive for material components].
             Applying dominant role [primary_role]: [primary_directive].
             Surface in briefing — may require manual review."
      RETURN primary_directive
    }
  }

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
    M15.ValidateClassifications()                          // run after M05 Steps 1 + 3
    // Absence or validation failure = session invalid for allocation computations
  }

}
```
