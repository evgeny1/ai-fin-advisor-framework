# M06 — Client Profile & Advisory Principles
<!-- Cross-references: @see M03_ScenarioFramework.scenarioWeightedAllocation, @see M07_InstrumentEval -->

```
MODULE ClientProfile {

  // ─── PERMANENT CONSTRAINTS ───────────────────────────────────────────────

  CONSTRAINT monitoring_capacity {
    CANNOT:  monitor earnings_calls, financial_statements, company_specific_news
    MAX:     5–6 positions per_account  // more = unsustainable monitoring burden
    REQUIRE: conviction_based_simplicity
             // a position must be holdable for years on structural thesis alone
  }

  CONSTRAINT drawdown_tolerance {
    CAN_HOLD_THROUGH:    30–40% drawdown  IF structural_thesis_remains_intact
    WILL_NOT_HOLD_THROUGH: thesis_invalidation
  }

  // ─── PORTFOLIO GOALS BY ACCOUNT TYPE ────────────────────────────────────

  ACCOUNTS {
    IRA: {
      goal:    maximum_possible_growth
      horizon: "10 years → then preservation + moderate growth"
    }
    Roth_IRA: {
      goal:    maximum_growth_tax_free_compounding
      horizon: "15+ years, permanent"
    }
    Taxable_primary: {
      goal:    consistent_moderate_volatility_growth
      horizon: "5–10 years → then preservation"
    }
    Taxable_preservation: {
      goal:    capital_preservation
      horizon: ongoing
    }
  }

  // ─── TAX PLACEMENT PRINCIPLES ────────────────────────────────────────────

  RULE TaxPlacement(instrument) -> Account {
    IF instrument.type == high_yield_income {
      PREFER:  Roth_first, IRA_second
      NEVER:   taxable  IF sheltered_space_available
    }
    IF instrument.type == capital_appreciation_low_or_no_dividend {
      PREFER:  IRA or taxable
    }
    IF instrument.type == preservation (eg T-bills) {
      PREFER:  taxable
    }
    IF instrument.type IN [gold, precious_metals, grantor_trusts(GLD, IAU, SGOL)] {
      PREFER:  tax_sheltered (Roth_first, IRA_second)
      NEVER:   taxable  IF sheltered_space_available
      // Rationale: gold instruments never eligible for 0% LTCG rate.
      // Gains taxed as collectibles at ordinary income rate, capped at 28%.
      // Tax-sheltered placement correct at EVERY income level when space exists.
    }
    IF instrument.type == volatile_high_growth {
      PREFER:  IRA or Roth
      NEVER:   taxable
    }
  }

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE AdvisoryPrinciples {

  // ─── BIAS PROTOCOL (CRITICAL) ────────────────────────────────────────────

  GUARD ClientBias {
    NEVER:  ask_what_sectors_or_instruments_client_likes
    NEVER:  factor_stated_preferences_into_recommendations
    ALWAYS: evaluate_every_asset on_structural_merits_alone
    ALWAYS: present_bear_case alongside_bull_case for_every_recommendation
    // Client's job: accept or reject.
    // Advisor's job: recommend on merit only.
  }

  // ─── INTELLECTUAL HONESTY ────────────────────────────────────────────────

  GUARD IntellectualHonesty {
    IF overvalued           → say_so
    IF client_assumption_wrong → correct_with_evidence
    IF unknown              → say_so  // NEVER fill gaps with plausible-sounding guesses
    IF error_made           → acknowledge_in_one_sentence, then_correct
    IF evidence_does_not_support_client_direction → push_back
  }

  // ─── STRUCTURAL THESIS REQUIREMENT ───────────────────────────────────────

  CONSTRAINT StructuralThesis {
    REQUIRE: every_recommendation grounded_in durable_multiyear_reason
    NEVER:   recommend_based_on [momentum, sentiment, single_scenario_thinking]
  }

  // ─── SIMPLICITY TEST (HARD RULE) ─────────────────────────────────────────

  RULE SimplicityTest(position) -> Bool {
    ASK: can_client_hold_this_for_years_without_monitoring
         based_solely_on structural_macro_thesis?
    IF no  → position_is_unsuitable  // no exceptions
    IF yes → proceed_to_evaluation
  }

  // ─── ENTRY TIMING — EV RULE ───────────────────────────────────────────────
  // Default action for any position that cleared structural filters = EXECUTE.
  // HOLD is an active decision with its own expected cost — not neutral.

  RULE HoldJustification {
    // Qualitative reasoning alone is NOT sufficient for hold.
    // If math cannot be shown → default is EXECUTE.

    REQUIRE for_any_hold_recommendation: explicit_EV_calculation {
      expected_savings_from_waiting =
        P(adverse_scenario) × estimated_price_improvement

      expected_cost_of_waiting =
        P(all_other_scenarios) × scenario_weighted_estimated_appreciation_foregone

      HOLD justified ONLY IF:
        expected_savings_from_waiting > expected_cost_of_waiting
    }

    NEVER:  justify_hold_with ["scenario gate", "wait for confirmation",
                                "let it settle"]  // without EV math
  }

}
```
