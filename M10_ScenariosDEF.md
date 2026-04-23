# M10 — Scenario Execution Protocols: D, E, F
<!-- All protocols apply: @see M08_FunctionalRoles.ExecutionGuards -->
<!-- All protocols apply: @see M08_FunctionalRoles.ExecutionTaxPlacement -->
<!-- All protocols apply: @see M08_FunctionalRoles.DeEscalation -->
<!-- Minimum conviction weight: @see M03_ScenarioFramework.minimumConvictionWeight() -->
<!-- Scenario D trigger updated by: @see M11_CreditAndCalibration.ScenarioDTrigger -->

```
MODULE ScenarioD {  // Deflationary Recession

  // ─── TRIGGER (updated by Extension v1) ───────────────────────────────────
  // Original trigger superseded by @see M11_CreditAndCalibration.ScenarioDTrigger

  TRIGGER {
    probability_threshold: >= 40%  // begin partial rotation at 30%
    REQUIRE T1_evidence {
      AND: unemployment_rising >= 0.5% OVER any_3_month_window  // BLS
      AND: Fed_cutting_aggressively (
             >= 75bps_cumulative_within_60_days
             OR any_emergency_inter_meeting_cut
           )  // confirmed: Fed_statement
      AND: credit_stress confirmed_by AT_LEAST_ONE_OF [
             (a) IG_OAS "transmission_reached" threshold_fired    // @see M11 §1.5a
             (b) HY_OAS "recession_pricing" threshold_fired        // @see M11 §1.5a → D_floor = 25%
             (c) CCC_OAS widening >= 100bps OVER 30d
                 WHILE composite_calm
                 SUSTAINED through_next_session
           ]
    }
    GDP_confirmation: {
      two_consecutive_negative_quarters  // BEA advance estimate
      status: confirmatory_signal_only  // NOT required for partial rotation
              // absence delays full execution
    }
    NEVER: act_on single_news_report
    NOTE: "D floor = 25% imposed by HY recession-pricing threshold triggers partial rotation
           automatically unless T1 counter-evidence is documented in session briefing."
  }

  // ─── POSITION RESPONSES ──────────────────────────────────────────────────

  RESPONSES {
    geopolitical_premium: {
      action:   Reduce
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Fiscal contraction in deflationary recession compresses procurement budgets."
      urgency:  Medium
    }
    inflation_hedge_precious_metals: {
      action:   evaluate_invalidation_conditions BEFORE acting
      // Mixed signal: aggressive Fed easing = supportive; demand collapse = not supportive
      // Complete invalidation check FIRST — do NOT act without it
      apply:    @see ScenarioA.PreciousMetalsInvalidation
      urgency:  Evaluate_first  // do not act without completing invalidation check
    }
    inflation_hedge_commodity_linked: {
      action:   Reduce
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Demand collapse directly impairs commodity prices. No Fed easing offset — unlike precious metals."
      urgency:  High
    }
    real_asset_contracted_revenue: {
      action:   Hold WITH monitoring
      status:   downgrade_to watch
      monitor:  volume_throughput_signals each_session
      rationale: "Contracted structure insulates from commodity collapse. But volume throughput at risk if demand contracts materially."
      urgency:  Watch  // no action until throughput signals deteriorate
    }
    policy_driven_thematic_equity: {
      action:   Reduce
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Deflationary recession forces fiscal austerity; government capex = early target for cuts. Demand collapse reduces case for new infrastructure."
      urgency:  High
    }
    rate_sensitive_income_short_duration: {
      action:   evaluate_rotation_to_longer_duration
      REQUIRE:  explicit_EV_calculation per @see M06_ClientAndAdvisory.HoldJustification
                before_acting
      rationale: "Fed cutting aggressively creates opportunity to extend duration and capture long-bond appreciation."
      urgency:  Evaluate  // conditional on yield curve assessment
    }
    rate_sensitive_income_long_duration: {
      action:   Hold OR Add IF EV_calculation_supports
      rationale: "Long-duration bonds are primary beneficiary in deflationary recession as Fed cuts aggressively."
      urgency:  Hold; Add_if_EV_confirms
    }
    broad_market_equity_domestic: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Demand collapse impairs earnings across sectors. Multiples compress."
      urgency:  High
    }
    broad_market_equity_international: {
      action:   Exit
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Demand collapse + dollar uncertainty = compounded transmission risk. No thesis basis to hold."
      urgency:  High  // first reduction priority
    }
  }

  // ─── ROTATION SEQUENCE ───────────────────────────────────────────────────

  SEQUENCE RotationD {
    1: confirm_trigger with [unemployment, Fed_action, credit_spread_data] from T1
       // GDP confirmation strengthens conviction but not required for partial rotation
    2: exit international_equity
       reduce domestic_equity to minimumConvictionWeight()
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    3: reduce commodity_linked_inflation_hedge
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    4: reduce policy_driven_thematic_equity
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    5: reduce geopolitical_premium
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    6: run_EV_calculation for short_duration_to_long_duration rotation
       IF EV_confirms → execute rotation
    7: evaluate precious_metals invalidation_conditions
       hold | reduce | add based_on_that_assessment
    8: hold real_asset_contracted_revenue on watch
       monitor: throughput_signals
  }

  // ─── DE-ESCALATION ───────────────────────────────────────────────────────

  DE_ESCALATION {
    threshold: 25%
    unwind_order: [
      1: restore long_duration_income IF extended_during_protocol
      2: restore domestic_equity to scenario_weighted_target
      3: restore geopolitical_premium to scenario_weighted_target
      4: reassess commodity_linked_inflation_hedge against scenario_weighted_target
      5: restore policy_driven_thematic_equity to scenario_weighted_target
    ]
    REQUIRE: T1_evidence [unemployment_declining OR credit_spreads_tightening
             OR Fed_pausing_cuts] before_unwinding
  }

  // ─── INVALIDATION ────────────────────────────────────────────────────────

  INVALIDATION ScenarioDInvalidation {
    condition_1: unemployment_stabilizing_or_declining  // BLS, 2+ months
    condition_2: credit_spreads_tightening sustainably
                 [HY below stress_beginning threshold, IG normalizing]
    condition_3: Fed_pausing_or_slowing_cuts confirmed_by FOMC_statement
  }

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE ScenarioE {  // Structural Rupture

  // ─── TRIGGER ─────────────────────────────────────────────────────────────

  TRIGGER {
    probability_threshold: >= 40%  // begin partial rotation at 30%
    REQUIRE T1_evidence {
      AND: dollar_reserve_status_materially_challenged
           // confirmed by: sovereign_de-dollarization_announcements(T1),
           // SWIFT_exclusion_data, central_bank_reserve_composition_data(IMF)
      AND: systemic_financial_stress [
             sovereign_CDS_widening significantly,
             IG_OAS transmission_reached @see M11_CreditAndCalibration,
             interbank_funding_stress
           ]
      AND: DXY_falling on_fundamental_grounds
           // NOT safe-haven flow reversal
    }
    NEVER: act_on single_news_report
    NOTE: "Scenario E de-escalation threshold is 20% — not 25%. @see M08_FunctionalRoles.DeEscalation"
  }

  // ─── POSITION RESPONSES ──────────────────────────────────────────────────

  RESPONSES {
    geopolitical_premium: {
      action:   Hold
      rationale: "Structural rupture typically accompanied by elevated geopolitical tension. Procurement pipelines intact or expanding."
      urgency:  Low
    }
    inflation_hedge_precious_metals: {
      action:   Add aggressively to scenario_weighted_target
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Reserve status erosion is the core driver of this scenario — directly supports the precious metals thesis at maximum conviction."
      urgency:  Immediate  // highest priority action in Scenario E
    }
    inflation_hedge_commodity_linked: {
      action:   Hold
      rationale: "Real assets outperform in reserve system stress. Commodity-linked exposure contributes to real asset positioning."
      urgency:  Low
    }
    real_asset_contracted_revenue: {
      action:   Hold
      rationale: "Hard asset contracted revenue is structurally defensive in reserve system stress."
      urgency:  None
    }
    policy_driven_thematic_equity: {
      action:   Reduce to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Fiscal and governance stress in Scenario E impairs government spending capacity and program continuity."
      urgency:  High
    }
    rate_sensitive_income_short_duration: {
      action:   Evaluate
      note:     "Sovereign debt stress may impair even short-duration government instruments.
                 If holding is sovereign → assess counterparty. If money-market or T-bill → evaluate flight-to-quality vs stress."
      urgency:  Evaluate  // case-by-case
    }
    rate_sensitive_income_long_duration: {
      action:   Reduce or Exit
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Sovereign debt stress directly impairs long-duration government bonds. Reserve status challenge compresses demand for US Treasuries."
      urgency:  High
    }
    broad_market_equity_domestic: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Systemic financial stress severely impairs equity multiples."
      urgency:  High
    }
    broad_market_equity_international: {
      action:   Exit
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Reserve rupture creates maximum currency and transmission uncertainty in international holdings."
      urgency:  Immediate  // exit with precious metals addition as twin first actions
    }
  }

  // ─── ROTATION SEQUENCE ───────────────────────────────────────────────────

  SEQUENCE RotationE {
    1: confirm_trigger with sovereign_CDS, DXY_trajectory, credit_spread_data from T1
    2: exit international_equity AND add precious_metals  // twin immediate actions
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    3: reduce long_duration_income (sovereign exposure)
       evaluate short_duration_income counterparty
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    4: reduce domestic_equity to minimumConvictionWeight()
    5: reduce policy_driven_thematic_equity to minimumConvictionWeight()
    6: hold [geopolitical_premium, commodity_linked, real_asset_contracted_revenue]
  }

  // ─── DE-ESCALATION ───────────────────────────────────────────────────────

  DE_ESCALATION {
    threshold: 20%  // lower than all other scenarios
    unwind_order: [
      1: reduce precious_metals toward new scenario_weighted_target
      2: restore long_duration_income if thesis recovers
      3: restore equity positions to scenario_weighted_targets
    ]
    REQUIRE: T1_evidence [DXY_stabilizing, sovereign_CDS_tightening,
             reserve_diversification_trend_reversing] before_unwinding
  }

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE ScenarioF {  // Growth Overheat

  // ─── TRIGGER ─────────────────────────────────────────────────────────────

  TRIGGER {
    probability_threshold: >= 40%  // begin partial rotation at 30%
    REQUIRE T1_evidence {
      AND: nominal_GDP_growth strong
           // confirmed: BEA advance estimate GDP > 3% annualized, >= 2 consecutive quarters
           // ⚑ CALIBRATION_DATED — @see CALIBRATION_STATE §2.3
      AND: inflation_rising BUT below_stagflationary_threshold
           // CPI trending up but < 4% YoY — @see CALIBRATION_STATE §2.3
      AND: Fed_tightening BUT not_yet_constraining_demand
           // confirmed: FOMC_statement; hikes present but demand data still strong
      AND: NO supply_shock  // verified absence; if supply shock present → reassess B or C
    }
    NEVER: act_on single_news_report
  }

  // ─── POSITION RESPONSES ──────────────────────────────────────────────────

  RESPONSES {
    geopolitical_premium: {
      action:   Hold at scenario_weighted_target
      rationale: "Growth overheat does not directly impair or expand geopolitical procurement. Hold at current weight."
      urgency:  Low
    }
    inflation_hedge_precious_metals: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Rising real yields in growth overheat environment reduce precious metals appeal. Inflation hedges underperform vs risk assets."
      urgency:  Medium
    }
    inflation_hedge_commodity_linked: {
      action:   Hold or trim_modestly IF above_scenario_weighted_target
      rationale: "Strong demand supports commodity prices but rising rates compress commodity multiple. Monitor relative to target weight."
      urgency:  Low
    }
    real_asset_contracted_revenue: {
      action:   Hold
      rationale: "Contracted throughput benefits from strong economic activity. Thesis intact."
      urgency:  None
    }
    policy_driven_thematic_equity: {
      action:   Hold
      monitor:  legislative_continuity
      rationale: "Strong growth sustains government revenues and supports spending mandate execution. Equity multiples expanding in risk-on environment."
      urgency:  Low
    }
    rate_sensitive_income_short_duration: {
      action:   Hold  // do NOT extend duration
      rationale: "Fed tightening keeps short rates elevated. Rolling at high short rates captures income. Do not extend duration into a hiking cycle."
      urgency:  Low
    }
    rate_sensitive_income_long_duration: {
      action:   Reduce
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Growth overheat drives long yields higher as Fed tightens and inflation expectations rise. Long-duration bonds sell off."
      urgency:  High
    }
    broad_market_equity_domestic: {
      action:   Add  // cyclicals and financials specifically
      apply:    tax_sheltered_first
      note:     "Within domestic equity, overweight cyclicals and financials over growth/long-duration equities."
      rationale: "Strong nominal growth directly supports cyclical corporate earnings. Financials benefit from steeper curve."
      urgency:  High
    }
    broad_market_equity_international: {
      action:   Assess via DXY_trajectory
      condition: IF DXY_weakening → consider_add
                 IF DXY_strengthening → hold_or_reduce
      rationale: "Dollar trajectory determines whether international equity outperforms domestic in growth overheat."
      urgency:  Medium  // conditional on DXY
    }
  }

  // ─── ROTATION SEQUENCE ───────────────────────────────────────────────────

  SEQUENCE RotationF {
    1: confirm_trigger with GDP_data(BEA) AND Fed_guidance(FOMC) AND CPI(BLS)
       verify: no_supply_shock present
    2: reduce long_duration_income
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    3: reduce precious_metals to minimumConvictionWeight()
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    4: add domestic_equity (cyclicals and financials emphasis)
       apply: tax_sheltered_first
    5: assess DXY → determine international_equity direction
    6: hold [short_duration_income, real_asset_contracted_revenue,
             policy_driven_thematic_equity, geopolitical_premium]
  }

  // ─── DE-ESCALATION ───────────────────────────────────────────────────────

  DE_ESCALATION {
    threshold: 25%
    unwind_order: [
      1: reduce domestic_equity additions back to prior scenario_weighted_target
      2: restore long_duration_income IF yield trajectory has reversed
      3: restore precious_metals to new scenario_weighted_target
    ]
    REQUIRE: T1_evidence [GDP_slowing, Fed_pausing OR cutting] before_unwinding
  }

  // ─── INVALIDATION ────────────────────────────────────────────────────────

  INVALIDATION ScenarioFInvalidation {
    condition_1: GDP_growth < 2% on BEA_advance_estimate
                 // ⚑ CALIBRATION_DATED — @see CALIBRATION_STATE §2.3
    condition_2: CPI >= 4% YoY → reassess B_or_C
    condition_3: supply_shock_verified → reclassify to C
    condition_4: credit_spreads_widening_materially → assess D
  }

}
```
