# M07 — Instrument Evaluation
<!-- Version: 1.2 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M07_InstrumentEval
  Version:         1.2
  Sub-project:     PORTFOLIO_ADVISOR
  Reason to change: evaluation criteria, AUM/volume/spread thresholds, or disqualification rules change.
  Inputs consumed:  instrument metadata (AUM, volume, spread, inception date, foreign exposure)
                    AuditResult (from M08.ThematicETF_ClassificationAudit — if thematic ETF)
  Outputs produced: AutoDisqualify result; ThematicETFGate classification
  Calibration deps: CALIBRATION_STATE §10 (audit coverage and materiality thresholds)
  Types consumed:   @see FW_Types.md — AuditResult
-->

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
  // SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-17; wiring
  // closed via ENG-16). The four hard GUARD conditions below are now executed by
  // `advisor_check_instrument_candidate(ticker, aum_millions?, track_record_years?,
  // foreign_concentration_pct?, instrument_type, revenue_type, has_contract_backstop,
  // hold_horizon_years)` — see Project_Instructions_MCP.md. Re-run it for existing
  // holdings too, not only new candidates, if any of these metrics may have changed.
  // Retained here as the spec these four conditions implement (ForeignExposureRule
  // above governs how to set instrument_type/foreign_concentration_pct correctly
  // before calling the tool — that judgment is NOT in Python):
  //   1. AUM < $100M AND hold_horizon >= 10y                        → DISQUALIFY
  //   2. foreign_concentration > 40% AND type IN [active_fund,
  //      sector_ETF]                                                 → DISQUALIFY
  //   3. revenue == commodity_dependent AND NOT contract_backstop    → DISQUALIFY
  //   4. track_record < 3y                                           → DISQUALIFY
  // @see python/advisor/portfolio/evaluation.py auto_disqualify()

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
