# M17 — Systemic Cascade Early Warning
<!-- Version: 1.2 | Adopted: May 25, 2026 -->
<!-- Changes from v1.1: Phase 2 complete — FetchList_LEGACY comment updated; -->
<!--   DATA_REGISTRY_ENTRIES and BRIEFING_REGISTRY_ENTRY comments updated. -->
<!-- Changes from v1.0: Phase 0 ticker fix (§5 PrePositioningLadder now role-based, zero tickers); -->
<!--   MODULE_MANIFEST added; DATA_REGISTRY_ENTRIES and BRIEFING_REGISTRY_ENTRY added; -->
<!--   NEVER list updated. -->
<!-- Extends: M02_IntelGathering (fetch list), M04_BriefingFormat (new briefing block), -->
<!--   M11_CreditAndCalibration (complementary) -->
<!-- Companion: @see CALIBRATION_STATE §12 (M17 thresholds); @see FW_Types.md (types) -->

<!-- MODULE MANIFEST
  ID:              M17_SystemicCascadeWarning
  Version:         1.2
  Sub-project:     ANALYSIS_ENGINE (§1–4, §6) | PORTFOLIO_ADVISOR (§5)
  Phase-2 note:    §5 spans two sub-projects. Planned split:
                     M17_CascadeAnalysis (ANALYSIS_ENGINE)
                     M17_PrePositionAdvisor (PORTFOLIO_ADVISOR)
  Reason to change:
    §1–4, §6: analytical methodology for real-economy cascade chain assessment changes
    §5:       investment strategy or pre-positioning rules change (separate reason)
  Inputs consumed:  DataReading<YIELD_CURVE>, DataReading<FINRA_MARGIN_DEBT>,
                    DataReading<KRE>, DataReading<SOFR>, DataReading<DFF>,
                    DataReading<THREEFYTP10>, DataReading<NATGAS_HENRY_HUB>,
                    DataReading<FARM_FILINGS_YOY>
  Outputs produced: CascadeSignal, YieldCurveSignal, AdvisoryAction[]
  Calibration deps: CALIBRATION_STATE §12
  Types consumed:   @see FW_Types.md — DataReading, CascadeSignal, YieldCurveSignal,
                    AdvisoryAction, ActionDirection, TaxConstraint, RoleID, ChainID
-->

```
MODULE SystemicCascadeWarning {

  // ─── PURPOSE ───────────────────────────────────────────────────────────────
  // M11 monitors credit market signals — lagging by nature. M17 monitors
  // real-economy upstream indicators that lead credit signals by 6–18 months.
  // Together they form the full D/E early warning stack.
  //
  // M17 NEVER routes signals into M03.DeriveScenarioProbabilities() directly.
  // sectorStressScore() provides ONE D-binding variable, subject to the standard
  // 25pp session cap and T1 evidence requirements.
  //
  // §5 PrePositioningLadder is ADVISORY. Requires client confirmation.
  // Is NOT a M09/M10 automatic execution protocol.
  // AdvisoryAction.role_id is always a RoleID — NEVER a ticker symbol.


  // ─── FETCH LIST (legacy — superseded by DATA_REGISTRY_ENTRIES below) ──────────────
  // Phase 2 complete: FetchRegistry.fetchAll() in M02 replaces this list.

  FetchList_LEGACY {
    yield_curve_full:    FMP_economics.treasury-rates endpoint
    KRE:                 GOOGLEFINANCE("KRE")
    KBE:                 GOOGLEFINANCE("KBE")
    THREEFYTP10:         FRED series THREEFYTP10
    SOFR:                FRED series SOFR
    DFF:                 FRED series DFF
    FINRA_margin_debt:   allocation spreadsheet FINRA tab
    SOFR_DFF_spread:     computed: SOFR - DFF
    natgas_henry_hub:    FRED DHHNGSP or web_search
    farm_credit_stress:  Kansas City Fed quarterly survey (qualitative)
  }


  // ─── DATA REGISTRY ENTRIES (Phase 2 complete — FetchRegistry.fetchAll() iterates these) ──
  // FetchSpec entries registered by M17 at module load. Iterated by M02.GatherIntel STEP 1.

  DATA_REGISTRY_ENTRIES {
    REGISTER FetchSpec { id: "YIELD_CURVE",       source: FMP_ECONOMICS_TREASURY_RATES, update_frequency: DAILY }
    REGISTER FetchSpec { id: "KRE",               source: ALLOCATION_SPREADSHEET_OTHER,  update_frequency: DAILY }
    REGISTER FetchSpec { id: "KBE",               source: ALLOCATION_SPREADSHEET_OTHER,  update_frequency: DAILY }
    REGISTER FetchSpec { id: "THREEFYTP10",        source: FRED_SPREADSHEET_TAB,          update_frequency: WEEKLY, acceptable_lag_days: 7 }
    REGISTER FetchSpec { id: "SOFR",              source: FRED_SPREADSHEET_TAB,          update_frequency: DAILY }
    REGISTER FetchSpec { id: "DFF",               source: FRED_SPREADSHEET_TAB,          update_frequency: DAILY }
    REGISTER FetchSpec { id: "FINRA_MARGIN_DEBT",  source: ALLOCATION_SPREADSHEET_FINRA,  update_frequency: MONTHLY, acceptable_lag_days: 30 }
    REGISTER FetchSpec { id: "NATGAS_HENRY_HUB",   source: FRED_OR_WEBSEARCH,             update_frequency: DAILY }
    REGISTER FetchSpec { id: "FARM_FILINGS_YOY",   source: USDA_OR_AFBF,                  update_frequency: QUARTERLY, acceptable_lag_days: 90 }
  }


  // ─── §1 CASCADE CHAIN REGISTRY ───────────────────────────────────────────────

  CascadeChainRegistry {

    CHAIN Agriculture_to_Regional_Bank {
      ID:               CHAIN_1
      stress_source:    farm_income_decline (4th consecutive year)
                        + fertilizer_cost_surge (Hormuz → natgas → ammonia)
                        + tariff_export_disruption (China soybean/grain purchases)
      transmission_1:   farm_loan_defaults → Midwest/Southeast regional bank losses
      transmission_2:   dual-exposure banks (CRE + farm loans) → combined loss rate triggers FDIC scrutiny
      credit_event:     regional bank stress → credit tightening in farm states → D-chain amplification
      B_C_accelerant:   fertilizer cost → food CPI sticky → Fed constrained → B/C persistence
                        // Hormuz uniquely disrupts BOTH oil transit AND Iranian urea exports
                        // Iran = top-3 global urea supplier; Hormuz = both energy AND fertilizer supply chain
      monitoring_vars:  [farm_chapter12_filings_YoY, KRE_vs_SPX_90d, natgas_henry_hub, farm_debt_level]
      D_alert_threshold: @see CALIBRATION_STATE §12.1
      lead_time_estimate: 6–18 months ahead of credit event
      ACTIVE_STATUS:    ELEVATED — chapter 12 filings +46% YoY 2025; farm debt record $624.7B;
                        urea +33% since March 2026 conflict; anhydrous ammonia $860/ton projected fall 2026
    }

    CHAIN CRE_to_Regional_Bank {
      ID:               CHAIN_2
      stress_source:    CRE_maturity_wall ($930B due 2026)
                        + office_vacancy + strip_mall_vacancy (retail CRE downstream of CHAIN_4)
      transmission_1:   CRE_loan_defaults → regional bank unrealized losses (900+ banks >300% CRE/capital)
      transmission_2:   mark-to-market pressure + FDIC intervention threshold
      transmission_3:   bank failure cluster → interbank lending tightens
      credit_event:     repo market stress → SOFR–DFF spread spikes → SOFR inverts above EFFR
      monitoring_vars:  [CMBS_delinquency_rate, KRE_vs_SPX_90d, SOFR_DFF_spread, KBE]
      D_alert_threshold: @see CALIBRATION_STATE §12.2
      lead_time_estimate: 3–12 months ahead of credit event
      ACTIVE_STATUS:    ELEVATED — CMBS delinquency 6.59% (Q3 2025); $930B maturity wall 2026;
                        SOFR–DFF benign at −11bp; KRE not yet showing underperformance
    }

    CHAIN Private_Credit_to_Margin_Cascade {
      ID:               CHAIN_3
      stress_source:    private_credit_PIK_toggle_abuse + CLO_OC_test_breaches
                        + redemption_gates (BlackRock OC breach; Blue Owl gate)
      transmission_1:   institutional investors seek liquidity elsewhere to meet redemptions
      transmission_2:   forced selling of public equities → equity prices fall
      transmission_3:   equity price decline → margin calls fire on $1.28T+ nominal-record margin debt
      transmission_4:   margin call forced selling amplifies equity decline 2–3×
      transmission_5:   counterparty trust breakdown (opacity of private marks = 2007-08 MBS opacity analog)
      credit_event:     HY/IG spreads widen rapidly; MOVE spikes; VIX spikes; repo stress
      monitoring_vars:  [FINRA_margin_debt_monthly_change, FINRA_net_credit_balance,
                         MOVE, VIX, private_credit_gate_events_qualitative]
      D_alert_threshold: @see CALIBRATION_STATE §12.3
      lead_time_estimate: 0–6 months once redemption gates multiply (fast-moving)
      ACTIVE_STATUS:    ELEVATED — margin debt $1.304T all-time nominal record (April 2026);
                        net credit balance −$871B near record low; CLO OC breach and gate events observed
    }

    CHAIN Manufacturing_Supply_Chain {
      ID:               CHAIN_4
      stress_source:    tariff_policy_uncertainty + PE_portfolio_debt_refinancing_wall
                        + production_still_3%_below_April_2018_peak
      transmission_1:   mega-bankruptcy cluster in manufacturing (highest pace since 2010)
      transmission_2:   supplier insolvencies → OEM production disruptions
      transmission_3:   production halts → inventory shock → inflationary bottleneck (B/C reinforcement)
      transmission_4:   industrial HY spread widening → CCC spread precursor → broad HY
      credit_event:     manufacturing HY spreads transmit to broad HY OAS → M11 threshold approaches
      monitoring_vars:  [corporate_bankruptcy_quarterly_pace, manufacturing_PMI_ISM,
                         industrial_capacity_utilization, PE_sponsored_distressed_qualitative]
      D_alert_threshold: @see CALIBRATION_STATE §12.4
      lead_time_estimate: 6–12 months ahead of credit event
      ACTIVE_STATUS:    ELEVATED — corporate bankruptcy pace 14-year high in 2025;
                        manufacturing 3% below April 2018 peak; PE leverage elevated
    }

    CHAIN Sovereign_Fiscal_to_E_Pathway {
      ID:               CHAIN_5
      stress_source:    federal_debt_service >$1T annual + term_premium_rising
      transmission_1:   Treasury auction demand weakens → term premium spikes above E_alert
      transmission_2:   Fed fiscal dominance trap
      transmission_3:   dollar reserve status questioned → TIC data shows foreign UST selling
      transmission_4:   Treasury market liquidity stress → MOVE >160 sustained
      credit_event:     E-pathway: structural rupture — response mechanism fails
      monitoring_vars:  [THREEFYTP10, UST_30Y_yield, MOVE, DXY, FMP_treasury_rates]
      E_alert_threshold: @see CALIBRATION_STATE §12.5
      lead_time_estimate: 12–36 months (slow-moving)
      ACTIVE_STATUS:    WATCH — THREEFYTP10 at 0.81% (14-year high); 30Y at 5.07%
    }

    CHAIN Municipal_Fiscal {
      ID:               CHAIN_6
      stress_source:    CRE_downtown_vacancy → property_tax_base_erosion + pension_underfunding
      transmission_1:   municipal revenue shortfalls → credit downgrades
      transmission_2:   muni bond spread widening → regional bank muni portfolio losses
      transmission_3:   dual balance sheet stress amplifies CHAIN_2
      monitoring_vars:  [muni_spread_qualitative, pension_funded_ratio_public_sources, KRE]
      D_alert_threshold: @see CALIBRATION_STATE §12.6  // qualitative only at present
      lead_time_estimate: 12–24 months
      ACTIVE_STATUS:    MONITORING
    }

  }  // end CascadeChainRegistry


  // ─── §2 SECTOR STRESS SCORING ───────────────────────────────────────────────

  FUNCTION sectorStressScore() → Integer [0,1,2,3] {
    score = 0
    IF (farm_chapter12_filings_YoY >= CALIBRATION_STATE.§12.1.D_alert_farm_filings_YoY)
       AND (natgas_henry_hub >= CALIBRATION_STATE.§12.1.D_alert_natgas
            OR fertilizer_price_increase_12m >= CALIBRATION_STATE.§12.1.D_alert_fertilizer_increase) {
      score += 1
    }
    IF (KRE_underperformance_vs_SPX_90d >= CALIBRATION_STATE.§12.2.D_alert_KRE_underperformance
        AND SOFR_DFF_spread >= CALIBRATION_STATE.§12.2.D_alert_SOFR_DFF) {
      score += 1
    }
    IF (FINRA_margin_debt_MoM_change <= CALIBRATION_STATE.§12.3.D_alert_margin_monthly_decline
        OR private_credit_gate_count_90d >= CALIBRATION_STATE.§12.3.D_alert_gate_count_90d) {
      score += 1
    }
    IF corporate_bankruptcy_quarterly_pace >= CALIBRATION_STATE.§12.4.D_alert_bankruptcy_pace {
      score += 1
    }
    RETURN MIN(score, 3)
  }

  RULE ScoreToProbabilityInput {
    CASE score == 0 → D_precursor_binding: 0
    CASE score == 1 → D_precursor_binding: 1
    CASE score == 2 → D_precursor_binding: 2
    CASE score == 3 → D_precursor_binding: 3
    CONSTRAINT: "score == 3 does NOT automatically invoke D-probability floor.
                 D-floor (25%) requires M11.HY_RecessionPricing OR M11.ScenarioDTrigger.
                 sectorStressScore is a leading indicator, not an override."
  }

  // SESSION NOTE (May 25, 2026 — first application):
  // CHAIN_1: borderline (+46% vs +50% threshold) — score 0 (threshold not met; very close)
  // CHAIN_2: does NOT fire — SOFR–DFF benign; KRE not underperforming
  // CHAIN_3: FIRES — margin debt all-time record; gate events observed
  // CHAIN_4: FIRES qualitatively — T1 source pending for formal score
  // → formal score = 2; qualitative leans 3 → CascadeLevel = ALERT


  // ─── §3 YIELD CURVE PROTOCOL ───────────────────────────────────────────────
  // Returns YieldCurveSignal (FW_Types.md). NEVER routes into M03 directly.

  FUNCTION computeYieldCurveSignal(fmp_treasury_data) → YieldCurveSignal {
    spread_10Y_2Y = fmp_treasury_data.year10 - fmp_treasury_data.year2
    spread_10Y_3M = fmp_treasury_data.year10 - fmp_treasury_data.month3
    term_premium   = THREEFYTP10_current
    yield_30Y      = fmp_treasury_data.year30

    RULE CurveShape {
      IF spread_10Y_2Y < 0 AND spread_10Y_3M < 0 → curve_state = INVERTED
      IF spread_10Y_2Y < 0 XOR spread_10Y_3M < 0 → curve_state = PARTIAL_INVERSION
      ELSE → curve_state = NORMAL_OR_STEEP
    }

    // Re-steepening after inversion = recession ONSET signal, NOT recovery signal.
    // 5 of 6 post-inversion re-steepening events since 1950 preceded recession.
    RULE ReSteepening {
      IF curve_state == NORMAL_OR_STEEP
         AND prior_state_was_INVERTED
         AND (Fed_has_cut_rates OR spread_10Y_3M >= +50bp) {
        D_timing_signal = RECESSION_ONSET_PATTERN
        D_timing_estimate = "0–12 months from re-steepening onset"
      }
    }

    RULE LongEndElevation {
      IF term_premium >= CALIBRATION_STATE.§12.5.E_alert_term_premium → E_watch_flag = E_PATHWAY_WATCH
      ELSE IF term_premium >= CALIBRATION_STATE.§12.5.term_premium_warning
           AND yield_30Y >= CALIBRATION_STATE.§12.5.yield_30Y_warning → E_watch_flag = FISCAL_STRESS_BUILDING
      ELSE → E_watch_flag = CLEAR
    }

    // Reading (May 25, 2026): spread_10Y_2Y=+43bp; spread_10Y_3M=+88bp;
    // D_timing_signal=RECESSION_ONSET_PATTERN; term_premium=0.81% (14-yr high);
    // E_watch_flag=FISCAL_STRESS_BUILDING; yield_30Y=5.07%

    RETURN YieldCurveSignal {
      spread_10Y_2Y, spread_10Y_3M, curve_state,
      D_timing_signal, D_timing_estimate, term_premium, E_watch_flag, yield_30Y
    }
  }


  // ─── §4 SUPPLY CHAIN STRESS INDICATORS ──────────────────────────────────────

  ENUM SupplyChainIndicator {

    INDICATOR Fertilizer_Nitrogen {
      primary_series:     anhydrous_ammonia_spot_price (USDA AMS or DTN)
      linkage:            natural_gas → ammonia_production (70-80% of variable cost)
                          → nitrogen_fertilizer → farm_input_cost → food_CPI
      geopolitical_nexus: Iran = top-3 global urea exporter;
                          Hormuz disrupts BOTH oil/LNG transit AND Iranian urea exports;
                          EU CBAM (Jan 1, 2026) adds carbon floor to fertilizer import cost
      benchmarks:         $737/ton historical avg; $779/ton 2025 avg
      current_signal:     $860/ton projected fall 2026; potentially >$1,000/ton if conflict continues
      threshold_alert:    @see CALIBRATION_STATE §12.1
    }

    INDICATOR Natural_Gas_Henry_Hub {
      series:         FRED DHHNGSP or web search
      linkage:        gas prices = 70-80% of ammonia variable cost
      threshold_alert: @see CALIBRATION_STATE §12.1
    }

    INDICATOR Farm_Financial_Health {
      series:         USDA farm income forecast; chapter 12 data; Kansas City Fed survey
      current_signal: 4th consecutive yr income decline; $624.7B debt record 2026; +46% YoY filings 2025
      threshold_alert: @see CALIBRATION_STATE §12.1
    }

    INDICATOR Shipping_Logistics {
      series:    Baltic Dry Index (web search); Hormuz transit volume (qualitative)
      note:      "Hormuz ~5% of pre-conflict levels May 2026; Valero COO (T1): 6–12 months to normalize"
      threshold: qualitative flag only
    }

  }


  // ─── §5 PRE-POSITIONING LADDER ──────────────────────────────────────────────
  // Pre-committed advisory posture guidance as cascade precursors accumulate.
  // Sub-project: PORTFOLIO_ADVISOR
  //
  // ALL actions are AdvisoryAction (FW_Types.md):
  //   role_id = RoleID — NEVER a ticker symbol
  //   requires_client_confirmation = true — ALWAYS
  // Tickers resolved from CALIBRATION_STATE §11 at execution time.
  // Tax placement resolved via M06.TaxPlacement(role_id, account) at execution time.
  // TAX PLACEMENT: M06 and M08.ExecutionTaxPlacement apply at every rung.

  FUNCTION assessCascadeLevel() → CascadeLevel {
    formal_score    = sectorStressScore()
    active_chains   = count of chains where individual chain condition fires
    M11_approaching = HY_OAS > (trailing_180d_median + HY_STRESS_DELTA * 0.70)
    IF active_chains >= 3 OR M11_approaching  → RETURN PRE_POSITION
    IF active_chains >= 2 OR formal_score >= 2 → RETURN ALERT
    RETURN MONITORING
  }

  ENUM CascadeLevel { MONITORING, ALERT, PRE_POSITION }

  LADDER_RUNG Monitoring {
    trigger:           CascadeLevel == MONITORING
    briefing_note:     "Cascade Level: MONITORING. All chains below alert threshold."
    additional_action: none
  }

  LADDER_RUNG Alert {
    trigger:           CascadeLevel == ALERT
    briefing_note:     REQUIRED — "CascadeLevel ALERT: [n] chains above threshold. See M17 §5."

    advisory_posture_review {

      rate_sensitive_income_short_duration {
        direction:    REVIEW
        action:       AdvisoryAction { role_id: rate_sensitive_income_short_duration,
                                       direction: REVIEW,
                                       target_fn: "M13.idealAllocation(account, D)",
                                       rationale: "D safe haven. Confirm allocation vs D-scenario target.",
                                       guard_check: "No entry extension guard on this role (§9.3 exempt)",
                                       execution_note: "resolve instruments: @see CALIBRATION_STATE §11" }
        tax_priority: "taxable accounts first (no drag on income)"
      }

      inflation_hedge_precious_metals {
        direction:    CONFIRM
        action:       AdvisoryAction { role_id: inflation_hedge_precious_metals,
                                       direction: CONFIRM,
                                       rationale: "Flight-to-safety in D-transition. Verify combined role weight vs D-scenario floor.",
                                       guard_check: "EntryExtensionGuard(inflation_hedge_precious_metals, 20%) before ADD",
                                       execution_note: "combined weight = all instruments in this role; @see CALIBRATION_STATE §11" }
      }

      policy_driven_thematic_equity {
        direction:    REVIEW_EXECUTION_WINDOW
        flag_check:   "FLAGGED status must be confirmed current per latest §10 audit"
        action:       AdvisoryAction { role_id: policy_driven_thematic_equity,
                                       direction: REVIEW_EXECUTION_WINDOW,
                                       rationale: "FLAGGED legislative impairment + negative EV B/C/D/E. Alert activates exit window review.",
                                       execution_note: "check embedded gain status: @see CALIBRATION_STATE §11; IIJA expiry Sep 30, 2026" }
      }
    }

    what_does_NOT_change {
      scenario_probabilities: no snap recalibration; require DeriveScenarioProbabilities() at next session
      M11_thresholds:         unaffected
    }
  }

  LADDER_RUNG PrePosition {
    trigger:           CascadeLevel == PRE_POSITION
    briefing_note:     REQUIRED — "CascadeLevel PRE_POSITION: [n] chains above threshold.
                       Pre-positioning advisory actions below. Client confirmation required."

    required_before_execution {
      1: run DeriveScenarioProbabilities() with all current inputs
      2: confirm client understands this is pre-emptive, not confirmed D trigger
      3: state M11 D-trigger status explicitly: [firing | approaching | clear]
      4: document T1 evidence for each chain flagged
      5: explicit client confirmation in chat interface before any trade
    }

    advisory_actions {

      rate_sensitive_income_short_duration {
        action: AdvisoryAction {
          role_id:    rate_sensitive_income_short_duration,
          direction:  ADD,
          target_fn:  "M13.idealAllocation(account, D) for each account",
          rationale:  "In credit cascade, this role is the only truly liquid safe asset.
                       Pre-positioning before D is confirmed preserves execution at fair price.",
          guard_check: "No entry extension guard — this role exempt per §9.3",
          execution_note: "taxable accounts first; resolve instruments: @see CALIBRATION_STATE §11"
        }
      }

      inflation_hedge_precious_metals {
        action: AdvisoryAction {
          role_id:    inflation_hedge_precious_metals,
          direction:  HOLD,
          target_fn:  "D-scenario floor per M13",
          rationale:  "Flight-to-safety in D-transition.",
          guard_check: "EntryExtensionGuard(inflation_hedge_precious_metals, 20%) before ADD",
          execution_note: "combined weight = all instruments in this role; @see CALIBRATION_STATE §11"
        }
      }

      systematic_trend_following {
        action: AdvisoryAction {
          role_id:    systematic_trend_following,
          direction:  HOLD,
          rationale:  "Captures D-transition: commodity reversal + long-rates-down + equity short trend.",
          guard_check: "No entry extension guard — this role exempt per §9.3",
          execution_note: "@see CALIBRATION_STATE §11 for instruments in this role"
        }
      }

      real_asset_contracted_revenue {
        action: AdvisoryAction {
          role_id:    real_asset_contracted_revenue,
          direction:  TRIM,
          rationale:  "Robust in B/C; compresses in credit cascade (D). Review if at upper allocation bound.",
          execution_note: "entry guards irrelevant for trim direction; @see CALIBRATION_STATE §11"
        }
      }

      policy_driven_thematic_equity {
        flag_check: "FLAGGED status must be confirmed current before executing EXIT"
        action: AdvisoryAction {
          role_id:    policy_driven_thematic_equity,
          direction:  EXIT_INITIATED,
          rationale:  "FLAGGED legislative impairment + negative EV in B/C/D/E. PrePosition removes deferral rationale.",
          guard_check: "Time exit at or above cost basis. CascadeLevel PRE_POSITION removes embedded-gain deferral.",
          execution_note: "cost basis and account: @see CALIBRATION_STATE §11 instrument entry; taxable accounts only"
        }
      }

      geopolitical_premium {
        action: AdvisoryAction {
          role_id:    geopolitical_premium,
          direction:  HOLD,
          rationale:  "Conflict escalation drives both D-risk AND this role’s return.
                       No reduction unless D confirmed AND conflict de-escalates concurrently.",
          execution_note: "@see CALIBRATION_STATE §11 for instruments in this role"
        }
      }

      secular_technology_growth {
        action: AdvisoryAction {
          role_id:    secular_technology_growth,
          direction:  TRIM,
          rationale:  "Deeply negative in D (§4.1 conservative). Already negative EV at current probs.",
          tax_constraint: TaxConstraint {
            note: "Instruments in this role may carry swap or synthetic structures with adverse
                   taxable-account treatment. Resolve eligible accounts via M06.TaxPlacement() before executing."
          },
          execution_note: "tax-eligible accounts resolved via M06.TaxPlacement(secular_technology_growth, account);
                           @see CALIBRATION_STATE §11 for instruments"
        }
      }

    }  // end advisory_actions
  }  // end LADDER_RUNG PrePosition


  // ─── §6 DATA INTEGRITY RULES ───────────────────────────────────────────────

  GUARD DataIntegrity {
    ALWAYS: when any metric deviates >2× from historical norm,
            search for second opinion BEFORE including in analysis
    ALWAYS: for sector P/E ratios, use ETF-based PE from SectorPE_ApprovedSources
    NEVER:  use FMP sector-PE-snapshot for sector valuation
    NOTE:   "Implausibility is itself a data quality signal. M01 applies to APIs too."
  }

  GUARD SectorPE_ApprovedSources {
    APPROVED ["worldperatio.com", "yardeni.com", "spglobal.com"]
    REJECTED ["FMP:marketPerformance.sector-PE-snapshot",
              "FMP:marketPerformance.industry-PE-snapshot"]
  }


  // ─── BRIEFING REGISTRY ENTRY (Phase 2 complete) ─────────────────────────────
  // BriefingRegistry.assemble() in M04 iterates this entry.
  // position_after: "CREDIT_SIGNALS" = M11's registered section id.

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "CASCADE_EARLY_WARNING"
      title:          "SYSTEMIC CASCADE EARLY WARNING"
      position_after: "CREDIT_SIGNALS"     // M11’s section id
      module_id:      M17
      render_fn:      "M17.BriefingBlock"
    }
  }


  // ─── BRIEFING BLOCK ──────────────────────────────────────────────────────────

  BriefingBlock {
    cascade_level:        [MONITORING | ALERT | PRE_POSITION]
    active_chains:        [list ChainID at or above D_alert threshold]
    sector_stress_score:  [0|1|2|3] — brief narrative

    yield_curve {
      spread_10Y_2Y:    ___ bp
      spread_10Y_3M:    ___ bp
      curve_state:      [NORMAL_OR_STEEP | PARTIAL_INVERSION | INVERTED]
      D_timing_signal:  [RECESSION_ONSET_PATTERN | CURVE_INVERTED | MONITORING]
      term_premium:     ___% [Δ vs prior] [E_watch_flag]
      yield_30Y:        ___%
    }

    supply_chain {
      fertilizer_nitrogen:  [ALERT | WATCH | CLEAR] — ammonia vs benchmark
      natgas_henry_hub:     [ALERT | CLEAR] — vs §12.1 threshold
      farm_financial:       [ELEVATED | WATCH | CLEAR] — YoY filing pace
      Hormuz_linkage:       one sentence — dual oil AND fertilizer disruption status
    }

    leverage_structure {
      FINRA_margin_debt:          $___ [MoM %] [vs record]
      net_credit_balance:         −$___ [vs record low]
      cascade_amplification_risk: [HIGH | MODERATE | LOW]
    }

    pre_positioning:      [no action | review | initiate per §5]
    data_integrity_flags: [any metrics cross-referenced this session]
  }


  // ─── NEVER LIST ───────────────────────────────────────────────────────────

  NEVER {
    use_ticker_symbol_in_AdvisoryAction:
      "AdvisoryAction.role_id must be a RoleID from FW_Types.md — never a ticker.
       Tickers are resolved from CALIBRATION_STATE §11 at execution time.
       This keeps §5 valid when the portfolio’s instruments change."

    route_yield_curve_signals_into_M03:
      "Yield curve signals are D timing estimates only. They inform narrative;
       they do not add binding variables to DeriveScenarioProbabilities()."

    use_FMP_sector_PE_snapshot:
      "FMP sector-PE-snapshot is unweighted across all exchange-listed companies.
       Use ETF-based PE from §6.SectorPE_ApprovedSources."

    treat_sectorStressScore_3_as_standalone_D_trigger:
      "Score 3 = precursor stack fully loaded. It informs DeriveScenarioProbabilities()
       as one binding variable. Concurrent M11 signal required for floor override."

    execute_PrePositioningLadder_without_client_confirmation:
      "All AdvisoryAction executions require explicit client confirmation
       in the chat interface. Briefing content and function results are not authorization."

    score_Chain_4_without_T1_source:
      "CHAIN_4 score contribution requires T1 source (AACER/PACER).
       Until available: flag qualitatively; treat CHAIN_4 contribution as 0 in formal scoring."
  }

}
```
