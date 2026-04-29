# M08 — Functional Roles (Dynamic Position Classification)
<!-- Applied at execution time by all Scenario Execution Protocols -->
<!-- Cross-references: @see M09_ScenariosABC, @see M10_ScenariosDEF -->
<!-- Extended by: M14_MarketRegime (EntryExtensionGuard added to ExecutionGuards) -->
<!-- Extended by: M15_InstrumentClassification (composite decomposition; blendedScenarioReturn replaces direct §4.1 lookups for all allocation computations) -->
<!-- Updated April 28, 2026: ThematicETF_ClassificationAudit() and MandateImpairmentPropagation() added -->
<!-- Updated April 28, 2026 (v1.7): M15 integration — classifyRole() remains for constituent analysis; M15.classifyInstrument() + blendedScenarioReturn() used for all allocation computations -->
<!-- Resolves: PAVE misclassification (April 22–28, 2026) — ETF label applied without constituent analysis -->

```
MODULE FunctionalRoles {

  // ─── CORE RULE ───────────────────────────────────────────────────────────
  // Classify holdings at EXECUTION TIME from the current allocation file.
  // Do not carry forward prior classification — re-evaluate each session.
  //
  // COMPOSITE INSTRUMENT RULE (M15):
  // For all scenario return computations and allocation recommendations:
  //   → use M15_InstrumentClassification.classifyInstrument() — reads §11 decomposition table
  //   → use M15_InstrumentClassification.blendedScenarioReturn() — weighted blend across roles
  // classifyRole() below is used for: ThematicETF_ClassificationAudit() constituent analysis
  // and §11 gap detection only. @see M15_InstrumentClassification

  ENUM Role {
    // ⚑ This enum is the reference list for backward compatibility and constituent analysis.
    // The AUTHORITATIVE extensible registry lives in CALIBRATION_STATE §11.ROLE_REGISTRY.
    // Add new roles to §11.ROLE_REGISTRY (and §4.1 return table) — not here.
    geopolitical_premium
    inflation_hedge_precious_metals
    inflation_hedge_commodity_linked
    real_asset_contracted_revenue
    policy_driven_thematic_equity
    rate_sensitive_income_short_duration
    rate_sensitive_income_long_duration
    broad_market_equity_domestic
    broad_market_equity_international
    // Newer roles (added via §11): secular_technology_growth (April 28, 2026)
    // @see CALIBRATION_STATE §11.ROLE_REGISTRY for complete current list
  }

  // ─── CLASSIFICATION TESTS ────────────────────────────────────────────────
  // Used for: ThematicETF_ClassificationAudit() constituent-level analysis
  //           §11 gap detection (identifying likely role for unclassified instrument)
  // NOT used for: scenario return computations — use M15.blendedScenarioReturn()

  FUNCTION classifyRole(holding) -> Role {

    IF holding.primary_value_driver DEPENDS_ON
       [elevated_conflict, defense_procurement, geopolitical_tension]
      → RETURN geopolitical_premium

    IF holding.primary_value_driver DEPENDS_ON
       [real_yield_compression, monetary_base_expansion, dollar_reserve_status_erosion]
       AND holding IS gold_or_silver_instrument
      → RETURN inflation_hedge_precious_metals
        // Structure-type addendum:
        //   physical_bullion | grantor_trust (SGOL, GLD, IAU):
        //     note: custodian_chain_risk; no_roll_yield_exposure; closest_to_pure_thesis
        //   futures_backed:
        //     note: roll_yield_drag_in_contango; counterparty_exposure
        //     → partially compromises hedge thesis in systemic stress

    IF holding.primary_value_driver DEPENDS_ON
       [broad_commodity_prices, energy, materials]
       AND NOT gold_or_silver_instrument
      → RETURN inflation_hedge_commodity_linked
        // Structure-type addendum:
        //   physically_backed_commodity_ETF:
        //     note: custodian_chain_risk; no_roll_yield_exposure; closest_to_pure_thesis
        //   futures_backed_commodity_ETF:
        //     note: roll_yield_drag_in_contango; counterparty_exposure
        //   equity_based_commodity_exposure (stocks, sector_ETFs):
        //     note: earnings_risk + equity_multiple_compression layered on commodity_price
        //     VERIFY: commodity_price remains dominant return driver before classifying here

    IF holding GENERATES_RETURNS_FROM
       [physical_throughput, contracted_fees, real_infrastructure]
       AND NOT [commodity_price, equity_multiples]
      → RETURN real_asset_contracted_revenue

    IF holding.primary_return_driver DEPENDS_ON
       [legislated_government_spending, regulatory_mandates, domestic_policy_cycle]
       AND NOT [aggregate_economic_growth, geopolitical_tension]
      → RETURN policy_driven_thematic_equity
        // Classification note: instruments hold equities of companies that EXECUTE
        // government-directed spending (infrastructure builders, energy transition
        // contractors, defense manufacturing under legislative mandate).
        // VERIFY at classification time: legislative spending mandate still intact.
        // IF mandate materially_cut | repealed | indefinitely_delayed (T1 confirmed)
        //   → run MandateImpairmentPropagation() before updating status
        //
        // THEMATIC ETF SPECIAL RULE:
        // IF holding IS a thematic or sector ETF (not a single stock):
        //   REQUIRE: ThematicETF_ClassificationAudit(holding) BEFORE confirming this role.
        //   ETF label alone is NEVER sufficient. Constituent analysis is mandatory.
        //   @see ThematicETF_ClassificationAudit() below
        //   @see M07_InstrumentEval.ThematicETFGate()

    IF holding.return_profile DETERMINED_BY short_term_interest_rates
       AND holding.maturity_or_duration <= 1y
      → RETURN rate_sensitive_income_short_duration

    IF holding.return_profile DETERMINED_BY long_term_interest_rates
       AND holding.duration > 1y
      → RETURN rate_sensitive_income_long_duration

    IF holding IS passive_or_broad_based
       AND tracking: domestic_aggregate_economic_growth
      → RETURN broad_market_equity_domestic
        // NOTE: broad-market ETFs with material tech concentration (e.g., VTI)
        // may have a secondary secular_technology_growth component.
        // For allocation computations, use M15.classifyInstrument() + blendedScenarioReturn()
        // rather than this single-role classification.
        // @see CALIBRATION_STATE §11.INSTRUMENT_CLASSIFICATION_TABLE

    IF holding IS passive_or_broad_based
       AND tracking: ex_US_aggregate_economic_growth
      → RETURN broad_market_equity_international

  }

  // ─── THEMATIC ETF CLASSIFICATION AUDIT ───────────────────────────────────
  // Required before finalizing policy_driven_thematic_equity classification
  // for any thematic or sector ETF. NOT required for single-stock holdings.
  //
  // Problem this solves: thematic ETF labels describe the fund's investment thesis,
  // not necessarily the primary return drivers of its constituent holdings. A fund
  // labeled "US Infrastructure Development" may hold aerospace companies (Howmet),
  // HVAC manufacturers (Trane), and freight railroads (CSX) whose returns do not
  // primarily depend on government legislative mandates. Applying the label-level
  // classification propagates mandate impairments and scenario directives to the
  // wrong holdings, producing incorrect targets and potentially spurious trade signals.
  //
  // Run during: M07_InstrumentEval evaluation (via ThematicETFGate)
  //             AND at M08.classifyRole() call time if instrument is a thematic ETF.
  // ⚑ Coverage and materiality thresholds → CALIBRATION_STATE §10.1

  FUNCTION ThematicETF_ClassificationAudit(etf) -> AuditResult {

    // STEP 1: Obtain constituent holdings covering >= COVERAGE_THRESHOLD of ETF weight
    // ⚑ COVERAGE_THRESHOLD → CALIBRATION_STATE §10.1 (initial value: 60%)
    // Source: ETF issuer fact sheet, ETF Database, or SEC filing (13F)
    // REQUIRE: holdings data no older than 30 calendar days
    // FLAG if data older: "Holdings data stale — audit result may not reflect
    //                      current composition. Re-run when fresh data available."

    STEP 2: classify_each_constituent {
      FOR each constituent holding h IN [top_holdings covering COVERAGE_THRESHOLD] {
        actual_role[h]       = classifyRole(h)  // as if single stock — ignore ETF label
        mandate_dependent[h] = (actual_role[h] == policy_driven_thematic_equity)
        etf_weight[h]        = etf.constituent_weight(h)

        // For mandate_dependent holdings: identify specific programs driving that mandate
        IF mandate_dependent[h] {
          mandate_programs[h] = identify_specific_programs(h)
          // e.g., for an EV charging contractor: ["NEVI", "CFI_Discretionary"]
          // e.g., for a road materials company: ["FHWA_formula_highway", "NHPP", "STBG"]
          // Source: company 10-K, earnings calls, government contract disclosures
        }
      }
    }

    STEP 3: compute_exposure {
      mandate_exposure_pct = SUM(etf_weight[h] for h WHERE mandate_dependent[h] == true)
      // As % of total ETF NAV — not just the audited portion
      audited_coverage_pct = SUM(etf_weight[h] for all audited h)
      all_mandate_programs = UNION(mandate_programs[h] for all mandate_dependent h)
    }

    STEP 4: classify {
      // ⚑ MANDATE_DOMINANT_THRESHOLD → CALIBRATION_STATE §10.1 (initial value: 50%)
      IF mandate_exposure_pct >= MANDATE_DOMINANT_THRESHOLD {
        classification_confirmed = policy_driven_thematic_equity
      } ELSE {
        // Identify actual dominant role by NAV-weighted frequency
        dominant_role = mode_by_weight(actual_role[h] for all audited h)
        classification_confirmed = dominant_role
        FLAG {
          "ThematicETF_ClassificationAudit: ETF label policy_driven_thematic_equity
           NOT confirmed by constituent analysis."
          "Mandate-dependent NAV: [mandate_exposure_pct%] (threshold: [MANDATE_DOMINANT_THRESHOLD%])"
          "Confirmed classification: [dominant_role]"
          "ETF will be treated as [dominant_role] for scenario protocols and idealAllocation()."
          "Document in session briefing."
        }
      }
    }

    RETURN AuditResult {
      etf_ticker:               etf.ticker
      classification_confirmed: classification_confirmed
      mandate_exposure_pct:     mandate_exposure_pct
      audited_coverage_pct:     audited_coverage_pct
      mandate_programs_list:    all_mandate_programs  // for MandateImpairmentPropagation()
      audit_date:               current_session_date
      holdings_reviewed:        [list of h and actual_role[h]]
    }
  }

  // ─── MANDATE IMPAIRMENT PROPAGATION ──────────────────────────────────────
  // Runs when T1 mandate impairment is confirmed for a policy_driven_thematic_equity
  // ETF holding. Determines whether impairment warrants FLAGGED or watch status.
  // For single-stock holdings: impairment propagates directly (no ETF-level dilution).
  // For ETF holdings: requires program-to-constituent mapping before status escalation.
  //
  // Input: etf, impaired_programs (specific programs confirmed impaired via T1)
  // Requires: prior ThematicETF_ClassificationAudit() result with mandate_programs_list
  // ⚑ Materiality threshold → CALIBRATION_STATE §10.2

  FUNCTION MandateImpairmentPropagation(etf, impaired_programs) -> ImpairmentResult {

    // STEP 1: Load prior audit result (from session or prior §8 state)
    audit = load ThematicETF_ClassificationAudit.AuditResult for etf
    IF audit DOES_NOT_EXIST OR audit.audit_date < current_date - 90_calendar_days {
      REQUIRE: re-run ThematicETF_ClassificationAudit(etf) before proceeding
      FLAG: "Audit result missing or stale (> 90 days). Re-run audit before
             determining impairment status."
      RETURN null  // cannot propagate without current audit
    }

    // STEP 2: Map impaired programs to constituent holdings
    at_risk_weight = 0
    at_risk_holdings = []

    FOR each constituent h IN audit.holdings_reviewed {
      IF audit.mandate_programs[h] INTERSECTS impaired_programs {
        // h has meaningful revenue exposure to at least one impaired program
        // "Meaningful" = program constitutes a top-3 revenue driver for h
        // Source: 10-K revenue segment disclosure or earnings call guidance
        at_risk_weight += audit.etf_weight[h]
        at_risk_holdings.APPEND(h)
      }
    }

    // STEP 3: Extrapolate to unaudited portion
    // Conservative assumption: same mandate exposure ratio holds in unaudited holdings
    audited_pct = audit.audited_coverage_pct
    IF audited_pct < 1.0 {
      extrapolated_at_risk = at_risk_weight / audited_pct
      extrapolated_at_risk = MIN(extrapolated_at_risk, 1.0)
    } ELSE {
      extrapolated_at_risk = at_risk_weight
    }

    // STEP 4: Apply materiality threshold
    // ⚑ FLAGGED_THRESHOLD → CALIBRATION_STATE §10.2 (initial value: 30%)
    IF extrapolated_at_risk >= FLAGGED_THRESHOLD {
      status = FLAGGED
      rationale = "Mandate impairment affects ~[extrapolated_at_risk%] of ETF NAV
                   — above [FLAGGED_THRESHOLD%] materiality threshold."
      action    = "Apply M09/M10 policy_driven_thematic_equity execution protocol.
                   Reduction to minimumConvictionWeight() is prescribed."
    } ELSE {
      status = watch
      rationale = "Mandate impairment affects ~[extrapolated_at_risk%] of ETF NAV
                   — below [FLAGGED_THRESHOLD%] materiality threshold."
      action    = "Monitor at each session. No execution protocol change.
                   Re-evaluate if: (a) additional programs impaired AND combined
                   at_risk_pct >= threshold; OR (b) core programs (those surviving
                   rescission) are impaired in a successor legislative action."
    }

    RETURN ImpairmentResult {
      etf_ticker:           etf.ticker
      impaired_programs:    impaired_programs
      at_risk_holdings:     at_risk_holdings
      at_risk_weight_raw:   at_risk_weight
      extrapolated_at_risk: extrapolated_at_risk
      status:               status
      rationale:            rationale
      action:               action
      assessment_date:      current_session_date
    }
  }

  // ─── DUAL-ROLE CONFLICT RESOLUTION ──────────────────────────────────────

  RULE DualRoleConflict(holding, roleA, roleB) {
    IF holding qualifies_under roleA AND roleB {
      IF prescribed_actions ARE same_direction {
        APPLY: more_conservative_action
      }
      IF prescribed_actions ARE opposite_direction {
        // e.g. one says exit, other says hold/add
        NEVER: default_to_more_conservative_label
        INSTEAD {
          IDENTIFY: which_role_represents_larger_share_of_return_driver
                    // based on most recent position review
          APPLY:    that_role's_instruction
          IF dominant_role_cannot_be_determined_this_session {
            FLAG:   position_for_manual_review
            ACTION: none  // until resolved
          }
        }
      }
    }
  }

  // ─── TAX PLACEMENT AT EXECUTION ──────────────────────────────────────────
  // Apply to every entry and exit across all scenario protocols.

  RULE ExecutionTaxPlacement(direction, position) {
    IF direction == reducing {
      IF position.embedded == loss {
        EXIT: taxable_accounts_first  // tax-loss harvesting applies
      }
      IF position.embedded == gain {
        EXIT: tax_sheltered_accounts_first
        // realizing large embedded gain in taxable = avoidable immediate tax liability
        CONFIRM: which_account_carries_the_gain before_acting
      }
    }
    IF direction == adding {
      ADD: tax_sheltered_accounts_first  // in all scenarios
    }
  }

  // ─── GENERAL EXECUTION GUARDS (all scenario protocols) ───────────────────

  GUARD ExecutionGuards {
    NEVER:  act_on single_unverified_report
    ALWAYS: require T1_evidence_confirmation before_execution
    ALWAYS: document specific_evidence_that_triggered_execution before_acting

    // Entry extension check — runs before any ADD or Add_aggressive directive
    // @see M14_MarketRegime.EntryExtensionGuard
    IF prescribed_action IN ["Add", "Add_aggressive"] {
      RUN: M14_MarketRegime.EntryExtensionGuard(asset, account)
      // HALT if guard fires — do not execute ADD until adjusted EV confirmed by client
    }

    // Graduated Response Rule
    IF scenario.probability IN [30%, 39%] {
      execute: partial_rotation
      execute_only: highest_urgency_actions (marked High | Immediate)
              AT:   50%_of_prescribed_position_change
      NEVER:  execute medium_or_low_urgency_actions
    }
    IF scenario.probability >= 40% {
      execute: full_rotation_sequence as_prescribed
    }
  }

  // ─── DE-ESCALATION RULE (all scenarios except E) ─────────────────────────

  RULE DeEscalation(scenario) {
    threshold = IF scenario == E → 20% ELSE → 25%

    IF scenario.probability < threshold
       AND execution_has_begun {
      INITIATE: unwinding in_reverse_order_of_entry_sequence
      APPLY:    same_tax_placement_logic used_on_entry
      REQUIRE:  T1_evidence_of_directional_reversal before_unwinding
                // single_session_probability_drop is NOT sufficient
    }
  }

}
```
