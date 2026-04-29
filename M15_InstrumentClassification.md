# M15 — Instrument Classification & Decomposition
<!-- Version: 1.0 | Adopted: April 28, 2026 -->
<!-- Supersedes: M08_FunctionalRoles.classifyRole() -->
<!-- Supersedes: M08_FunctionalRoles.DualRoleConflict() -->
<!-- Supersedes: M08_FunctionalRoles.ENUM Role (hardcoded) -->
<!-- Motivation: roles were hardcoded in M08; classifyRole() returned single value forcing binary -->
<!--   DualRoleConflict; composite instruments (e.g. VTI = broad_market + secular_tech) lost -->
<!--   return attribution accuracy; adding a new role required a framework amendment -->
<!-- Solution: roles live in CALIBRATION_STATE §11 (add/remove without amendment); instruments -->
<!--   decompose into weighted components; scenario return is a weighted blend -->
<!-- Cross-references: @see CALIBRATION_STATE §11, @see M03_ScenarioFramework, @see M13_GrowthObjectives -->
<!-- Consumed by: M03, M06, M08, M09, M10, M13 — anywhere classifyRole() or DualRoleConflict() was called -->
<!-- Companion: @see CALIBRATION_STATE §11 (role registry + instrument table, must load every session) -->

```
MODULE InstrumentClassification {

  // ─── DESIGN PRINCIPLES ───────────────────────────────────────────────────
  // 1. Roles are NOT hardcoded — they live in CALIBRATION_STATE §11.ROLE_REGISTRY.
  //    Add or remove a role by editing §11 only. No M15 amendment required.
  // 2. Instruments are NOT hardcoded — classification lives in §11.INSTRUMENT_TABLE.
  //    Any instrument in the allocation file must have a §11 entry.
  // 3. Instruments decompose into weighted role components (weights must sum to 1.0).
  //    Pure instruments: one component at weight 1.0.
  // 4. Scenario return = weighted blend across components.
  //    Replaces every direct §4.1[role][scenario] lookup throughout the framework.
  // 5. Execution directive resolved from dominant component when conflict exists.

  // ─── SESSION LOAD REQUIREMENT ─────────────────────────────────────────────

  REQUIRE at_session_start {
    CALIBRATION_STATE §11.ROLE_REGISTRY        // all registered roles
    CALIBRATION_STATE §11.INSTRUMENT_TABLE     // all instrument decompositions
    // Loaded as part of Calibration_State.md via M12_FileProtocol.fetchCalibrationState()
    // VALIDATE: every instrument in allocation file has a §11 entry
    // IF any instrument missing → HARD_STOP with classification instructions
  }

  // ─── CLASSIFY INSTRUMENT ──────────────────────────────────────────────────
  // Replaces: M08_FunctionalRoles.classifyRole()
  // Returns: ComponentVector (array of {role, weight} pairs), NOT a single role

  FUNCTION classifyInstrument(ticker) -> ComponentVector {

    IF ticker NOT IN CALIBRATION_STATE §11.INSTRUMENT_TABLE {
      HARD_STOP
      FLAG: "[ticker] not found in §11 INSTRUMENT_TABLE.
             Session cannot proceed for this instrument.
             Required steps:
               1. Identify binding return drivers
               2. Map to roles in §11.ROLE_REGISTRY
               3. Assign weights using ClassifyMethodology() — must sum to 1.0
               4. Add entry to §11.INSTRUMENT_TABLE with methodology documented
               5. Confirm each assigned role has a §4.1 return table row
             @see ClassifyMethodology() below"
    }

    components = §11.INSTRUMENT_TABLE[ticker].components

    // Validate weights sum to 1.0
    weight_sum = SUM(c.weight for c in components)
    IF ABS(weight_sum - 1.0) > 0.01 {
      HARD_STOP
      FLAG: "[ticker] component weights sum to [weight_sum] — must be 1.0.
             Correct §11.INSTRUMENT_TABLE before proceeding."
    }

    // Validate all roles exist in registry
    FOR each component c IN components {
      IF c.role NOT IN CALIBRATION_STATE §11.ROLE_REGISTRY {
        HARD_STOP
        FLAG: "[ticker] references unregistered role [c.role].
               Add to §11.ROLE_REGISTRY or correct the classification."
      }
    }

    RETURN components
  }

  // ─── BLENDED SCENARIO RETURN ──────────────────────────────────────────────
  // Replaces: direct §4.1[M08.classifyRole(a)][s] lookup throughout the framework
  // conservative used in ALL computations; upside in briefing disclosure only

  FUNCTION blendedScenarioReturn(ticker, scenario, return_type) -> Float {
    // return_type: "conservative" | "upside"
    components = classifyInstrument(ticker)
    result     = 0.0
    FOR each component c IN components {
      row    = CALIBRATION_STATE §4.1[c.role][scenario]
      value  = IF return_type == "conservative" THEN row.conservative ELSE row.upside
      result += c.weight * value
    }
    RETURN result
  }

  // ─── RESOLVE EXECUTION DIRECTIVE ──────────────────────────────────────────
  // Replaces: M08_FunctionalRoles.DualRoleConflict()
  // Used by M09/M10 execution protocols to get a single directive per instrument

  FUNCTION resolveDirective(ticker, scenario) -> DirectiveResult {

    components = classifyInstrument(ticker)

    // Pure instrument — single directive, no conflict possible
    IF components.length == 1 {
      RETURN DirectiveResult {
        directive:       lookup_directive(components[0].role, scenario)
        dominant_role:   components[0].role
        dominant_weight: 1.0
        blend_method:    "pure"
      }
    }

    // Composite — collect all directives
    component_directives = [
      { role: c.role, weight: c.weight, directive: lookup_directive(c.role, scenario) }
      FOR c IN components
    ]

    // Case 1: all components agree on directive
    unique_directives = SET(cd.directive for cd in component_directives)
    IF unique_directives.length == 1 {
      RETURN DirectiveResult {
        directive:     unique_directives[0]
        dominant_role: "consensus"
        blend_method:  "consensus"
      }
    }

    // Case 2: conflict — resolve by dominant weight
    dominant = MAX(component_directives, key=weight)

    IF dominant.weight >= 0.50 {
      FLAG: "Composite [ticker]: directive conflict resolved by dominant driver
             [dominant.role] at [dominant.weight*100]% weight.
             Minority directives: [list remaining]. Surface in session briefing."
      RETURN DirectiveResult {
        directive:       dominant.directive
        dominant_role:   dominant.role
        dominant_weight: dominant.weight
        blend_method:    "dominant_driver"
      }
    }

    // Case 3: no component >= 50% — cannot resolve automatically
    FLAG: "[ticker]: no dominant role (max weight [dominant.weight*100]%).
           Directive conflict cannot be resolved automatically.
           Manual review required before any execution action on this instrument.
           Surface in briefing as MANUAL_REVIEW_REQUIRED."
    RETURN DirectiveResult {
      directive:    "MANUAL_REVIEW_REQUIRED"
      blend_method: "unresolved"
    }
  }

  // ─── CLASSIFICATION METHODOLOGY ──────────────────────────────────────────
  // Use when adding a new instrument to §11 INSTRUMENT_TABLE,
  // or reviewing an existing classification at quarterly audit.

  PROCEDURE ClassifyMethodology(ticker) {

    STEP 1: obtain_holdings_or_sector_breakdown {
      source: fund_sponsor_website | ETF_provider_data | SEC_13F | Bloomberg
      require: >= 60% NAV coverage; data no older than 30 calendar days
      FLAG if stale: "Holdings data > 30 calendar days — classification is provisional"
    }

    STEP 2: map_sectors_to_roles {
      // Map each sector/sub-sector to a role in §11.ROLE_REGISTRY
      // This requires judgment — document rationale in methodology field
      // Guidance:
      //   Technology (AI / semiconductor / software dominant) → secular_technology_growth
      //   Technology (diversified / not AI-dominated)         → broad_market_equity_domestic
      //   Energy (E&P / commodity-price-linked)               → inflation_hedge_commodity_linked
      //   Energy (pipeline / midstream / fee-based)           → real_asset_contracted_revenue
      //   Industrials (defense / aerospace)                   → geopolitical_premium
      //   Industrials (infrastructure, mandate-confirmed)     → policy_driven_thematic_equity
      //     NOTE: requires ThematicETF_ClassificationAudit() @see M08_FunctionalRoles
      //   All other sectors                                   → broad_market_equity_domestic (residual)
    }

    STEP 3: validate_and_document {
      VERIFY: SUM(component.weight) == 1.0
      DOCUMENT in §11 INSTRUMENT_TABLE:
        ticker:         [ticker]
        components:     [{ role: String, weight: Float } list]
        last_reviewed:  [today's date]
        methodology:    [brief description of sector mapping and key decisions]
        review_trigger: [what would prompt re-review before quarterly schedule]
    }
  }

  // ─── CLASSIFICATION REVIEW TRIGGERS ──────────────────────────────────────

  RULE ClassificationReviewTrigger(ticker) {
    IF §11.INSTRUMENT_TABLE[ticker].last_reviewed > 90_calendar_days_ago {
      FLAG: "[ticker] classification overdue for quarterly review."
    }
    IF dominant_component_weight_has_shifted > 10pp_since_last_review {
      FLAG: "[ticker] dominant role weight may have shifted. Re-classify."
    }
    IF primary_driver_recalibration_declared {
      // @see M02_IntelGathering.identifyPrimaryDriver()
      REVIEW: all instruments whose dominant role is affected by the driver shift
    }
    IF new_role_added_to_§11_ROLE_REGISTRY {
      REVIEW: all existing classifications for potential re-decomposition
              // Some instruments may now have a cleaner fit to the new role
    }
  }

  // ─── INTEGRATION SUMMARY ──────────────────────────────────────────────────
  //
  // REPLACE everywhere in framework:
  //   M08.classifyRole(a)              → M15.classifyInstrument(a.ticker)
  //   M08.DualRoleConflict()           → M15.resolveDirective(a.ticker, scenario)
  //   §4.1[M08.classifyRole(a)][s]     → M15.blendedScenarioReturn(a.ticker, s, "conservative")
  //
  // UNCHANGED in M08 (still call directly):
  //   M08.ThematicETF_ClassificationAudit()   // constituent-level audit for thematic ETFs
  //   M08.MandateImpairmentPropagation()      // impairment propagation for policy_driven ETFs
  //   M08.ExecutionGuards                     // graduated response, EntryExtensionGuard gate
  //   M08.ExecutionTaxPlacement               // tax placement at execution
  //   M08.DeEscalation                        // unwinding rule

}
```
