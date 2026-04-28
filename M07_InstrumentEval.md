# M07 — Instrument Evaluation
<!-- Cross-references: @see M06_ClientAndAdvisory.TaxPlacement, @see M08_FunctionalRoles -->
<!-- Updated April 28, 2026: ThematicETFGate added — M08.ThematicETF_ClassificationAudit() required before policy_driven_thematic_equity finalized for any thematic ETF -->

```
MODULE InstrumentEval {

  // ─── REQUIRED METRICS (fetch and report for every instrument) ────────────

  METRICS {
    AUM: {
      threshold_caution:     < $500M
      threshold_disqualify:  < $100M  // for 10+ year hold
      reason: liquidity_risk_for_long_holds
    }
    avg_daily_volume: {
      flag_when: thin
      reason: exit_risk_in_volatile_markets
    }
    bid_ask_spread: {
      flag_when: wide
      reason: hidden_entry_exit_cost
    }
    expense_ratio: {
      note: compounding_drag_over_10–15_years
      reason: total_cost
    }
    inception_date: {
      threshold_disqualify: < 3 years
      reason: insufficient_track_record_no_drawdown_history
    }
    PE_ratio: {
      compare_to: category_average
      reason: valuation_context
    }
    yield: {
      determines: tax_placement  // @see M06_ClientAndAdvisory.TaxPlacement
    }
    foreign_exposure_pct: {
      apply: @see InstrumentEval.ForeignExposureRule
    }
    revenue_source: {
      classify: fee_based | commodity_dependent
      reason: thesis_durability
    }
  }

  // ─── FOREIGN EXPOSURE RULE (updated) ─────────────────────────────────────

  RULE ForeignExposureRule(instrument) {
    CASE active_funds | single_country_ETFs | concentrated_foreign_positions {
      IF foreign_exposure > 40% → DISQUALIFY
      reason: monitoring_burden
    }
    CASE passive_broad_market_index_ETFs {
      // 8,000+ holdings, diversified
      foreign_exposure_threshold: DOES_NOT_APPLY
      evaluate_on: [thesis_fit, scenario_weighting, transmission_mechanism_analysis]
    }
    CASE sector_ETFs_with_international_tilt {
      IF single_foreign_region_exposure > 40% → apply_original_disqualify_rule
      ELSE → case_by_case
    }
  }

  // ─── AUTOMATIC DISQUALIFICATION ──────────────────────────────────────────

  GUARD AutoDisqualify(instrument) {
    IF instrument.AUM < $100M AND hold_horizon >= 10y          → DISQUALIFY
    IF instrument.foreign_concentration > 40%
       AND instrument.type IN [active_fund, sector_ETF]        → DISQUALIFY
    IF instrument.revenue == pure_commodity_price_dependent
       AND NOT contract_backstop                               → DISQUALIFY
    IF instrument.track_record < 3y                            → DISQUALIFY
  }

  // ─── THEMATIC ETF CLASSIFICATION GATE ────────────────────────────────────
  // Applies to: any thematic or sector ETF whose label suggests
  // policy_driven_thematic_equity (infrastructure, clean energy, defense,
  // government-mandate-dependent themes).
  //
  // Root cause of April 28, 2026 PAVE misclassification: ETF label was applied
  // directly as classification without constituent-level analysis. NEVI rescission
  // (~$879M) was mapped to entire ETF, producing FLAGGED status and a 3% M13 target,
  // when in fact the core IIJA programs (highways, bridges) that PAVE's construction
  // and materials holdings depend on were not rescinded. Constituent audit revealed
  // <5% of ETF NAV genuinely at risk from the confirmed rescissions.
  //
  // SEQUENCE (mandatory for any thematic ETF evaluation):
  //   1. Check if ETF label suggests policy_driven_thematic_equity.
  //   2. IF yes → run M08.ThematicETF_ClassificationAudit(etf) BEFORE M07 metrics.
  //   3. Use confirmed classification from audit (not label) throughout M07 evaluation.
  //   4. IF classification confirmed as policy_driven_thematic_equity → also pre-register
  //      the specific legislative programs that constitute the mandate, so that any
  //      future M08.MandateImpairmentPropagation() call has program-to-holding map ready.
  //   5. ONLY after classification confirmed → proceed with AutoDisqualify and METRICS.
  //
  // NEVER: finalize policy_driven_thematic_equity for an ETF based on label alone.
  // NEVER: propagate a mandate impairment event to FLAGGED status without running
  //        MandateImpairmentPropagation() to confirm materiality.
  //
  // @see M08_FunctionalRoles.ThematicETF_ClassificationAudit()
  // @see M08_FunctionalRoles.MandateImpairmentPropagation()
  // @see CALIBRATION_STATE §10 (audit coverage and materiality thresholds)

  GATE ThematicETFGate(instrument) {
    IF instrument.type IN [thematic_ETF, sector_ETF]
       AND instrument.label SUGGESTS policy_driven_thematic_equity {

      REQUIRE: M08_FunctionalRoles.ThematicETF_ClassificationAudit(instrument)
               // Must complete BEFORE this M07 evaluation proceeds
      USE:     audit_result.classification_confirmed  // not label
      REGISTER: audit_result.mandate_programs_list
               // Stores specific programs driving the mandate thesis
               // Required input for MandateImpairmentPropagation() if needed later

      IF audit_result.classification_confirmed != policy_driven_thematic_equity {
        FLAG: "ETF label [policy_driven_thematic_equity] NOT confirmed by constituent audit.
               Actual dominant role: [audit_result.dominant_role].
               Proceeding with M07 evaluation under [audit_result.dominant_role]."
        // No DISQUALIFY — classification change only. Re-evaluate scenario weights.
      }
    }
  }

}
```
