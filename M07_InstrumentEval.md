# M07 — Instrument Evaluation
<!-- Cross-references: @see M06_ClientAndAdvisory.TaxPlacement, @see M08_FunctionalRoles -->

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

}
```
