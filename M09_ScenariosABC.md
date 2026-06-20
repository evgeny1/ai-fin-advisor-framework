# M09 — Scenario Execution Protocols: A, B, C
<!-- Version: 1.2 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M09_ScenariosABC
  Version:         1.2
  Sub-project:     PORTFOLIO_ADVISOR
  Reason to change: execution protocol, position responses, or rotation sequence for Scenarios A, B, or C changes.
  Inputs consumed:  ScenarioProbabilities; current allocations; DataReading (energy, credit)
  Outputs produced: ExecutionDirective[]
  Calibration deps: CALIBRATION_STATE §2.1 (Brent thresholds for C trigger/invalidation)
                    CALIBRATION_STATE §2.2 (DXY threshold for precious metals invalidation)
  Types consumed:   @see FW_Types.md — ScenarioProbabilities, ExecutionDirective, AllocationTarget
  Cross-module:     all protocols @see M08.ExecutionGuards, M08.ExecutionTaxPlacement, M08.DeEscalation
                    minimumConvictionWeight: @see M13_GrowthObjectives.minimumConvictionWeight()
-->

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

    // ── NEWER §11 ROLES (ENG-19, added 2026-06-20) ──────────────────────────
    // Directives derived from §4.1 return table + each role's §11.1 binding driver.
    // @see FRAMEWORK_BACKLOG.md ENG-19 resolution for full methodology.
    secular_technology_growth: {
      action:   Add
      apply:    tax_sheltered_first
      rationale: "AI capex cycle and multiple expansion accelerate in risk-on soft landing. §4.1 conservative +6%."
      urgency:  Medium
    }
    inflation_linked_sovereign: {
      action:   Reduce
      rationale: "Disinflation reduces CPI accrual faster than real yield decline from Fed cuts can offset. §4.1 conservative -2%★."
      urgency:  Low
    }
    real_estate_equity_income: {
      action:   Evaluate — explicit EV calculation required before acting
      rationale: "ALL §4.1 values LOW confidence (irreconcilable 1970s NAREIT vs 2022 VNQ analogs). Do not default to Hold without an EV calc."
      urgency:  Evaluate
    }
    systematic_trend_following: {
      action:   reduce_to minimumConvictionWeight()
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "Trend-reversal whipsaw on normalization historically severe. §4.1 conservative -12%★ (HIGH confidence)."
      urgency:  Medium
    }
    consumer_defensive_equity: {
      action:   Hold
      rationale: "Mild positive (§4.1 [0,+4]★) but not the role's defining scenario (B/C alpha). No incremental thesis to add here."
      urgency:  Low
    }
    healthcare_defensive_equity: {
      action:   Hold
      rationale: "Mild positive, MEDIUM confidence pending June 30. No strong directive either way."
      urgency:  Low
    }
    floating_rate_credit_income: {
      action:   Reduce
      rationale: "Floating coupon resets down as Fed cuts; opportunity cost vs risk-on assets. Mirrors short_duration_income treatment."
      urgency:  Low
    }
    emerging_market_equity: {
      action:   Reassess via DXY_trajectory before_adding
      condition: IF DXY_strengthening → do_NOT_add  // same mechanism as international, amplified
      rationale: "USD_direction is an explicit §11.1 binding driver; EM sensitivity to dollar strength exceeds developed international. §4.1 conservative +10%★ if cleared."
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

    // ── NEWER §11 ROLES (ENG-19, added 2026-06-20) ──────────────────────────
    secular_technology_growth: {
      action:   Hold
      rationale: "Q1 2026 sustained-B analogue confirms contract lock-in roughly offsets multiple compression. §4.1 [-2,+4]★ ADOPTED HIGH — thesis intact, but not the stagflation signature trade."
      urgency:  Low
    }
    inflation_linked_sovereign: {
      action:   Add IF below_scenario_weighted_target_weight
      apply:    @see M03_ScenarioFramework.scenarioWeightedAllocation()
      rationale: "CPI accrual directly supportive; sovereign_credit_quality intact domestically. §4.1 conservative +1% — modest vs precious metals/commodity but thesis-aligned."
      urgency:  Medium
    }
    real_estate_equity_income: {
      action:   Evaluate — explicit EV calculation required before acting
      rationale: "This scenario is the SPECIFIC locus of the irreconcilable 1970s NAREIT (+3-6%) vs 2022 VNQ (-26%) analog conflict driving the row's LOW confidence flag. Defer to EV calc, not default action."
      urgency:  Evaluate
    }
    systematic_trend_following: {
      action:   Add IF below_scenario_weighted_target_weight
      rationale: "§4.1 [+15,+30]★ ADOPTED HIGH — the highest-magnitude B return of any role in the framework. Commodity/rate trend persistence is the structural driver (1973-82 proxy, DBMF/SG-CTA 2022 empirical)."
      urgency:  High
    }
    consumer_defensive_equity: {
      action:   Add IF below_scenario_weighted_target_weight
      rationale: "Pricing power thesis. This is one of the role's two defining scenarios (B/C alpha) per §4.1 commentary. §4.1 [+2,+6]★ ADOPTED HIGH."
      urgency:  High
    }
    healthcare_defensive_equity: {
      action:   Hold
      rationale: "Modest positive (§4.1 [1,4]⚑), MEDIUM confidence. Pricing-power benefit present but not the signature B trade."
      urgency:  Low
    }
    floating_rate_credit_income: {
      action:   Hold
      rationale: "Fed holding rates supports floating coupon reset. Roll at elevated rates — mirrors short_duration_income treatment."
      urgency:  Low
    }
    emerging_market_equity: {
      action:   Exit
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "§4.1 conservative -12%⚑ exceeds the framework's own EXIT threshold (~-8 to -10%, per broad_market_equity_international's D/E directives). EM-specific currency/political risk compounds stagflation transmission."
      urgency:  High
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

    // ── NEWER §11 ROLES (ENG-19, added 2026-06-20) ──────────────────────────
    secular_technology_growth: {
      action:   Hold
      rationale: "§4.1 [+2,+8] positive — AI enterprise contracts insulate from inflationary shock — but not the scenario's signature add (geopolitical_premium)."
      urgency:  Low
    }
    inflation_linked_sovereign: {
      action:   Hold  // do NOT trim
      rationale: "CPI accrual positive but modest (§4.1 [1,4]⚑). Same treatment as precious_metals/commodity_linked in C — thesis intact, but C's signature add is geopolitical_premium only."
      urgency:  None
    }
    real_estate_equity_income: {
      action:   Evaluate — explicit EV calculation required before acting
      rationale: "LOW confidence row across all scenarios. Explicit EV calc required before action."
      urgency:  Evaluate
    }
    systematic_trend_following: {
      action:   Add IF below_scenario_weighted_target_weight
      rationale: "§4.1 [+18,+35]★ ADOPTED HIGH — the framework's single highest-magnitude scenario return of any role. Acute commodity trend acceleration (1973-74, 1979-80 analogs)."
      urgency:  High
    }
    consumer_defensive_equity: {
      action:   Add IF below_scenario_weighted_target_weight
      rationale: "Second of the role's two defining scenarios (B/C alpha). §4.1 [+2,+6]★ ADOPTED HIGH — pricing power offsets input cost inflation."
      urgency:  High
    }
    healthcare_defensive_equity: {
      action:   Hold
      rationale: "§4.1 [-2,3]⚑ straddles zero, MEDIUM confidence. No clear directive."
      urgency:  Low
    }
    floating_rate_credit_income: {
      action:   Hold
      rationale: "§4.1 [1,3]⚑ — same reasoning as Scenario B. Stable income; credit spreads not yet stressed."
      urgency:  Low
    }
    emerging_market_equity: {
      action:   Exit
      apply:    @see M08_FunctionalRoles.ExecutionTaxPlacement
      rationale: "§4.1 conservative -15%⚑ — deeper than the framework's own EXIT threshold. Layered currency, supply-chain, and commodity-import transmission compounds specifically for EM."
      urgency:  High
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
