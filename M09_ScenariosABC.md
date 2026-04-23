# M09 — Scenario Execution Protocols: A, B, C
<!-- All protocols apply: @see M08_FunctionalRoles.ExecutionGuards -->
<!-- All protocols apply: @see M08_FunctionalRoles.ExecutionTaxPlacement -->
<!-- All protocols apply: @see M08_FunctionalRoles.DeEscalation -->
<!-- Minimum conviction weight: @see M03_ScenarioFramework.minimumConvictionWeight() -->

```
MODULE ScenarioA {  // Soft Landing

  // ─── TRIGGER ─────────────────────────────────────────────────────────────

  TRIGGER {
    probability_threshold: >= 40%  // begin partial rotation at 30%
    REQUIRE T1_evidence {
      AND: Fed_forward_guidance_shift_toward_cuts
           // confirmed by FOMC_statement or meeting_minutes
      AND: sustained_energy_price_decline >= 5 consecutive_trading_days
      AND | OR: verified_supply_route_normalization from_primary_sources
    }
    NEVER: act_on single_news_report
  }

  // ─── POSITION RESPONSES ──────────────────────────────────────────────────

  RESPONSES {
    geopolitical_premium: {
      action:   reduce_to 50%_of_current_weight
      NEVER:    exit_fully
      rationale: "Procurement commitments extend years beyond ceasefire/resolution. Thesis partially intact."
      urgency:  Medium  // not first mover
    }
    inflation_hedge_precious_metals: {
      action:   Hold
      monitor:  @see ScenarioA.PreciousMetalsInvalidation
      rationale: "Dollar weakness, de-dollarization, fiscal expansion persist. Real yield decline from Fed cuts is supportive."
      urgency:  Low
    }
    inflation_hedge_commodity_linked: {
      action:   Hold
      monitor:  demand_signals
      rationale: "Soft landing sustains economic activity and commodity demand."
      urgency:  Low
    }
    real_asset_contracted_revenue: {
      action:   Hold
      rationale: "Contracted revenue not tied to commodity price or geopolitical premium. Thesis intact."
      urgency:  None
    }
    policy_driven_thematic_equity: {
      action:   Hold
      monitor:  legislative_continuity
      CONFIRM:  spending_mandate_not_materially_cut_or_repealed
      rationale: "Soft landing preserves government revenues. Risk-on environment supports multiples."
      urgency:  Low
    }
    rate_sensitive_income_short_duration: {
      action:   begin_rotation_to_risk_assets
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Fed cuts compress short-rate income. Opportunity cost rises as yields fall."
      urgency:  Medium
    }
    rate_sensitive_income_long_duration: {
      action:   Hold  // do NOT rotate
      rationale: "Fed cuts drive long-duration bond prices higher. Rotating surrenders capital appreciation."
      urgency:  Low
    }
    broad_market_equity_domestic: {
      action:   Add
      apply:    tax_sheltered_first
      rationale: "Risk-on environment favors broad domestic equities."
      urgency:  High  // first mover in Scenario A
    }
    broad_market_equity_international: {
      action:   Reassess via DXY_trajectory before_adding
      condition: IF DXY_strengthening → do_NOT_add  // dollar strength reverses tailwind
      urgency:  High  // conditional on DXY assessment
    }
  }

  // ─── ROTATION SEQUENCE ───────────────────────────────────────────────────

  SEQUENCE RotationA {
    1: confirm_trigger_with T1_evidence  // NEVER act on headline
    2: assess_DXY_trajectory
       // dollar strengthening reverses international equity tailwind
       // determine domestic vs international weighting before deploying equity capital
    3: reduce geopolitical_premium to 50%_of_current_weight
       redeploy_into broad_equity per_DXY_assessment
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    4: rotate short_duration_income to risk_assets
       hold: long_duration_income  // benefits from rate cut environment
    5: hold [inflation_hedge, policy_driven_thematic_equity, real_asset_contracted_revenue]
       // do NOT touch without specific invalidation signal
       confirm: legislative_mandate_status for_any_policy_driven_thematic_equity
  }

  // ─── DE-ESCALATION ───────────────────────────────────────────────────────

  DE_ESCALATION {
    threshold: 25%  // @see M08_FunctionalRoles.DeEscalation
    unwind_order: [
      1: restore short_duration_income
      2: restore geopolitical_premium to original_weight
      3: exit any equity_additions made_under_this_protocol
    ]
    REQUIRE: T1_evidence_of_directional_reversal before_unwinding
  }

  // ─── PRECIOUS METALS INVALIDATION CONDITIONS ──────────────────────────────
  // Three conditions. Until one materializes, thesis is intact regardless of price drawdown.

  INVALIDATION PreciousMetalsInvalidation {
    condition_1: Fed_pivoting_to ACTIVE_rate_hikes
                 // NOT pauses — active hikes only
    condition_2: DXY_sustaining ABOVE 105
                 // on fundamental grounds — NOT temporary safe-haven spike
                 // ⚑ CALIBRATION_DATED — @see CALIBRATION_STATE §2.2
    condition_3: sustained_energy_collapse BELOW
                 MAX($55_WTI, trailing_90d_WTI_settlement_avg × 0.70)
                 // sustained 30+ consecutive days (EIA, CME)
                 // ⚑ CALIBRATION_DATED nominal $55 — review quarterly
                 // IF trailing_90d_avg unavailable:
                 //   apply $55 nominal AND flag: "Nominal threshold applied — trailing average unavailable, confirmation required."
  }

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE ScenarioB {  // Stagflation Lock

  // ─── TRIGGER ─────────────────────────────────────────────────────────────

  TRIGGER {
    probability_threshold: >= 40%  // begin partial rotation at 30%
    REQUIRE T1_evidence {
      AND: CPI > 4% FOR >= 3 consecutive_monthly_prints  // source: BLS
      AND: real_GDP_growth <= 0%                          // source: BEA advance estimate
      AND: Fed_explicitly_holding_rates
           OR Fed_signaling_continued_constraint          // confirmed: FOMC_statement
    }
    NOTE: "No discrete supply event required — B is a persistent equilibrium, not a new trigger."
    NEVER: act_on single_news_report

    // Before triggering B, verify no discrete supply event exists.
    // IF discrete supply event present → re-evaluate B vs C: @see M03_ScenarioFramework.BvsCRule
  }

  // ─── POSITION RESPONSES ──────────────────────────────────────────────────

  RESPONSES {
    geopolitical_premium: {
      action:   Hold
      rationale: "Elevated geopolitical tension structurally associated with stagflationary supply disruptions."
      urgency:  None
    }
    inflation_hedge_precious_metals: {
      action:   Add IF below_scenario_weighted_target_weight
      apply:    @see M03_ScenarioFramework.scenarioWeightedAllocation()
      rationale: "Stagflation = highest-conviction macro environment for precious metals. Constrained Fed + persistent inflation is the structural bull case."
      urgency:  High
    }
    inflation_hedge_commodity_linked: {
      action:   Add IF below_scenario_weighted_target_weight
      rationale: "Commodity prices outperform in sustained supply-constrained stagflationary environments."
      urgency:  High
    }
    real_asset_contracted_revenue: {
      action:   Hold
      rationale: "Contracted infrastructure outperforms in sustained high-price environments."
      urgency:  None
    }
    policy_driven_thematic_equity: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Stagflationary fiscal pressure constrains discretionary government spending. Input cost inflation compresses contractor margins."
      urgency:  High
    }
    rate_sensitive_income_short_duration: {
      action:   Hold  // do NOT extend duration
      rationale: "Nominal yields elevated with uncertain rate path; rolling at elevated short rates captures reinvestment income while preserving optionality."
      urgency:  Low
    }
    rate_sensitive_income_long_duration: {
      action:   Reduce
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Long-duration directly impaired by elevated and uncertain nominal yield trajectory. Mark-to-market losses compound if inflation persists."
      urgency:  High
    }
    broad_market_equity_domestic: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Stagflation compresses equity multiples — elevated input costs, stagnant revenue, margin pressure."
      urgency:  High
    }
    broad_market_equity_international: {
      action:   Reduce  // first priority
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Additional currency and supply chain transmission risk."
      urgency:  High  // first reduction priority
    }
  }

  // ─── ROTATION SEQUENCE ───────────────────────────────────────────────────

  SEQUENCE RotationB {
    1: confirm_trigger with 3+_CPI_prints(BLS) AND GDP_data(BEA)
       verify: no_discrete_new_supply_event  // if exists → re-evaluate B vs C
    2: reduce international_equity first
       reduce domestic_equity to minimumConvictionWeight()
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    3: reduce long_duration_income
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    4: reduce policy_driven_thematic_equity to minimumConvictionWeight()
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    5: assess inflation_hedge_weights against scenario_weighted_targets
       add: precious_metals AND commodity_linked IF underweight
    6: hold [short_duration_income, geopolitical_premium, real_asset_contracted_revenue]
       // no action without specific invalidation signal
  }

  // ─── DE-ESCALATION ───────────────────────────────────────────────────────

  DE_ESCALATION {
    threshold: 25%
    unwind_order: [
      1: restore international_equity
      2: restore domestic_equity to scenario_weighted_target
      3: restore policy_driven_thematic_equity to scenario_weighted_target
      4: reassess inflation_hedge_weights against recalculated scenario_weighted_targets
    ]
    REQUIRE: T1_evidence [CPI_deceleration OR Fed_pivot] before_unwinding
  }

  // ─── INVALIDATION ────────────────────────────────────────────────────────

  INVALIDATION ScenarioBInvalidation {
    condition_1: CPI < 3% YoY FOR >= 2 consecutive_monthly_prints  // BLS
    condition_2: Fed_resuming_rate_cuts confirmed_by FOMC_statement
    condition_3: real_GDP_growth > 1.5% on BEA_advance_estimate
  }

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE ScenarioC {  // Inflationary Shock

  // ─── TRIGGER ─────────────────────────────────────────────────────────────

  TRIGGER {
    probability_threshold: >= 40%  // begin partial rotation at 30%
    REQUIRE T1_evidence {
      AND: Brent_crude SUSTAINED ABOVE
           MAX($110, trailing_90d_Brent_settlement_avg × 1.40)
           FOR >= 10 consecutive_trading_days
           // sources: EIA_weekly_report, CME_Group_settlement_data
           // ⚑ CALIBRATION_DATED nominal $110 — review quarterly or after sustained baseline shift
           // IF trailing_90d_avg unavailable:
           //   apply $110 nominal AND flag: "Nominal threshold applied — trailing average unavailable, confirmation required."
      AND: CPI_reacceleration confirmed_by >= 2 consecutive_monthly_prints  // BLS
      AND: new_or_deepening_supply_chokepoint verified_by
           primary_geopolitical_sources(ACLED, ISW, IEA_raw)
    }
    NOTE: "Supply event MUST be dateable and event-driven.
           Persistent inflation without new discrete supply trigger → routes to B, not C."
    NEVER: act_on single_news_report
  }

  // ─── POSITION RESPONSES ──────────────────────────────────────────────────

  RESPONSES {
    geopolitical_premium: {
      action:   Add IF below_scenario_weighted_target_weight
      NEVER:    add_beyond_target_weight
      rationale: "Discrete supply disruption with kinetic escalation expands procurement pipelines directly."
      urgency:  High
    }
    inflation_hedge_precious_metals: {
      action:   Hold  // do NOT trim
      rationale: "Energy shock is inflationary. Real yields suppressed. Thesis strengthened — drawdown is noise against structural signal."
      urgency:  None  // hold unconditionally
    }
    inflation_hedge_commodity_linked: {
      action:   Hold  // do NOT trim
      rationale: "Supply shock drives commodity prices higher. Thesis directly supported."
      urgency:  None  // hold unconditionally
    }
    real_asset_contracted_revenue: {
      action:   Hold
      rationale: "Sustained energy demand supports volume throughput. Contracted structure insulates from volatility."
      urgency:  None
    }
    policy_driven_thematic_equity: {
      action:   Hold
      monitor:  legislative_continuity
      CONFIRM:  program_funding_intact via T1_sources
      rationale: "Infrastructure/energy spending programs may accelerate as supply-side policy response. Equity multiples under pressure but mandate not impaired."
      urgency:  Low
    }
    rate_sensitive_income_short_duration: {
      action:   Hold  // do NOT rotate into equities
      rationale: "Volatility elevated. Short-duration preserves capital and optionality for redeployment after stabilization."
      urgency:  Low
    }
    rate_sensitive_income_long_duration: {
      action:   Reduce
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Inflationary shock drives nominal yields higher. Long-duration directly impaired mark-to-market."
      urgency:  High
    }
    broad_market_equity_domestic: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Inflationary shock compresses consumer demand and corporate margins."
      urgency:  High
    }
    broad_market_equity_international: {
      action:   Reduce  // first priority
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Layered transmission risk: currency devaluation, supply chain, energy import costs."
      urgency:  High  // first reduction priority
    }
  }

  // ─── ROTATION SEQUENCE ───────────────────────────────────────────────────

  SEQUENCE RotationC {
    1: confirm_trigger with Brent_settlement_data AND 2_CPI_prints
       verify: chokepoint_escalation(ACLED or ISW)
       confirm: event_is_dateable_and_discrete
       // if not dateable → re-evaluate C vs B: @see M03_ScenarioFramework.BvsCRule
    2: reduce international_equity first
       reduce domestic_equity to minimumConvictionWeight()
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
    3: reduce long_duration_income
       apply: @see M08_FunctionalRoles.ExecutionTaxPlacement
       hold:  short_duration_income
    4: add geopolitical_premium IF below_scenario_weighted_target
       NEVER: add_beyond_target_weight
    5: hold [precious_metals, commodity_linked, policy_driven_thematic_equity, real_asset_contracted_revenue]
       confirm: legislative_mandate_continuity for_policy_driven_thematic_equity
  }

  // ─── DE-ESCALATION ───────────────────────────────────────────────────────

  DE_ESCALATION {
    threshold: 25%
    unwind_order: [
      1: restore long_duration_income
      2: restore equity_positions
      3: reassess geopolitical_premium against recalculated scenario_weighted_target
         reduce IF above_target
    ]
    REQUIRE: T1_evidence [chokepoint_resolution OR sustained_energy_decline] before_unwinding
  }

  // ─── INVALIDATION ────────────────────────────────────────────────────────

  INVALIDATION ScenarioCInvalidation {
    condition_1: Brent_crude BELOW
                 MAX($80, trailing_90d_Brent_settlement_avg × 0.80)
                 SUSTAINED >= 10 consecutive_trading_days  // EIA, CME
                 // ⚑ CALIBRATION_DATED nominal $80 — review quarterly
                 // IF trailing_90d_avg unavailable:
                 //   apply $80 nominal AND flag: "Nominal threshold applied — trailing average unavailable, confirmation required."
    condition_2: verified_supply_chokepoint_resolution
                 confirmed_by T1_primary_sources(IEA, ACLED, ISW)
    condition_3: CPI_decelerating FOR >= 2 consecutive_monthly_prints  // BLS
  }

}
```
