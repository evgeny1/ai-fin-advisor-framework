# M17 — Systemic Cascade Early Warning
<!-- Version: 1.0 | Adopted: May 25, 2026 -->
<!-- Extends: M02_IntelGathering (fetch list), M04_BriefingFormat (new briefing block), -->
<!--   M11_CreditAndCalibration (complementary — M11 handles market credit signals; -->
<!--   M17 handles real-economy upstream signals that lead credit by 6–18 months) -->
<!-- Companion: @see CALIBRATION_STATE §12 (M17 thresholds — load every session) -->

```
MODULE SystemicCascadeWarning {

  // ─── PURPOSE ──────────────────────────────────────────────────────────────────
  // M11 monitors credit market signals — lagging by nature (spreads widen after
  // stress begins). M17 monitors real-economy upstream indicators that typically
  // lead credit signals by 6–18 months. Together they form the full D/E early
  // warning stack.
  //
  // M17 NEVER routes signals into M03.DeriveScenarioProbabilities() directly.
  // sectorStressScore() provides ONE D-binding variable to the scoring function —
  // additive to existing binding variables, subject to standard 25pp session cap
  // and T1 evidence requirements.
  //
  // M17 pre-positioning ladder is ADVISORY — requires client confirmation
  // before any execution. It is NOT a M09/M10 automatic execution protocol.


  // ─── FETCH LIST ADDITION (extends M02_IntelGathering.FETCH_LIST) ─────────────

  FetchList {
    // All available from allocation spreadsheet via M12.fetchAllocation()
    yield_curve_full:    FMP_economics.treasury-rates endpoint        // full curve 1M–30Y, live
    KRE:                 GOOGLEFINANCE("KRE")                         // SPDR S&P Regional Banking ETF
    KBE:                 GOOGLEFINANCE("KBE")                         // SPDR S&P Bank ETF
    THREEFYTP10:         FRED series THREEFYTP10                      // NY Fed ACM 10Y term premium (~weekly lag)
    SOFR:                FRED series SOFR                             // secured overnight financing rate
    DFF:                 FRED series DFF                              // effective federal funds rate
    FINRA_margin_debt:   allocation spreadsheet FINRA tab             // monthly; debit balances + net credit balance

    // Supplementary — compute from spreadsheet data or web search if unavailable
    SOFR_DFF_spread:     computed: SOFR - DFF                         // interbank funding stress proxy
    natgas_henry_hub:    FRED DHHNGSP or web_search current Henry Hub price
    farm_credit_stress:  Kansas City Fed quarterly ag credit survey   // qualitative; flag when available
  }


  // ─── §1 CASCADE CHAIN REGISTRY ───────────────────────────────────────────────
  // Real-economy stress chains that precede credit market signals.
  // Each chain: stress source → transmission steps → credit/financial event.
  // Monitoring variables and alert thresholds: @see CALIBRATION_STATE §12.
  // ACTIVE_STATUS assessed at session start from available data.

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
                        net credit balance −$871B near record low; CLO OC breach and gate events observed;
                        MOVE suppressed at 78 (complacency — not reassurance)
    }

    CHAIN Manufacturing_Supply_Chain {
      ID:               CHAIN_4
      stress_source:    tariff_policy_uncertainty + PE_portfolio_debt_refinancing_wall
                        + production_still_3%_below_April_2018_peak
      transmission_1:   mega-bankruptcy cluster in manufacturing (highest pace since 2010;
                         67% of mega-bankruptcies cite regulatory/policy landscape)
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
      stress_source:    federal_debt_service >$1T annual (fastest-growing budget line)
                        + term_premium_rising (THREEFYTP10 at 14-year high)
      transmission_1:   Treasury auction demand weakens → term premium spikes above E_alert
      transmission_2:   Fed fiscal dominance trap: cannot cut (stoking inflation) NOR
                         allow long yields to spike (triggering recession/bank losses)
      transmission_3:   dollar reserve status questioned → TIC data shows foreign UST selling
      transmission_4:   Treasury market liquidity stress → MOVE >160 sustained
      credit_event:     E-pathway: structural rupture — response mechanism fails;
                         sovereign credit event; institutional breakdown
      monitoring_vars:  [THREEFYTP10, UST_30Y_yield, MOVE, DXY, FMP_treasury_rates]
      E_alert_threshold: @see CALIBRATION_STATE §12.5
      lead_time_estimate: 12–36 months (slow-moving; monitoring only at current levels)
      ACTIVE_STATUS:    WATCH — THREEFYTP10 at 0.81% (14-year high); 30Y at 5.07%;
                         both trending upward; well below E_alert thresholds but direction matters
    }

    CHAIN Municipal_Fiscal {
      ID:               CHAIN_6
      stress_source:    CRE_downtown_vacancy → property_tax_base_erosion
                        + pension_underfunding (Illinois $213B+, Chicago, other cities)
      transmission_1:   municipal revenue shortfalls → credit downgrades
      transmission_2:   muni bond spread widening → regional bank muni portfolio losses
      transmission_3:   dual balance sheet stress: same regional banks carry CRE + muni exposure
      credit_event:     amplifies CHAIN_2 (CRE_to_Regional_Bank) when both fire concurrently
      monitoring_vars:  [muni_spread_qualitative, pension_funded_ratio_public_sources, KRE]
      D_alert_threshold: @see CALIBRATION_STATE §12.6  // qualitative only at present
      lead_time_estimate: 12–24 months ahead of credit event
      ACTIVE_STATUS:    MONITORING — slow-moving; not yet at alert level
    }

  }  // end CascadeChainRegistry


  // ─── §2 SECTOR STRESS SCORING ─────────────────────────────────────────────────
  // Provides ONE D-binding variable to M03.DeriveScenarioProbabilities().
  // Scored 0–3 per standard M03 binding variable scale.
  // Requires T1 evidence for each contributing chain — no narrative-only scoring.
  // Does NOT independently override D-probability floors.
  // Concurrent M11 signal required for any D-floor override.

  FUNCTION sectorStressScore() → Integer [0,1,2,3] {
    score = 0

    // Chain 1: Agriculture + fertilizer
    IF (farm_chapter12_filings_YoY >= CALIBRATION_STATE.§12.1.D_alert_farm_filings_YoY)
       AND (natgas_henry_hub >= CALIBRATION_STATE.§12.1.D_alert_natgas
            OR fertilizer_price_increase_12m >= CALIBRATION_STATE.§12.1.D_alert_fertilizer_increase) {
      score += 1
    }

    // Chain 2: CRE + regional banks
    IF (KRE_underperformance_vs_SPX_90d >= CALIBRATION_STATE.§12.2.D_alert_KRE_underperformance
        AND SOFR_DFF_spread >= CALIBRATION_STATE.§12.2.D_alert_SOFR_DFF) {
      score += 1
    }

    // Chain 3: Private credit + margin cascade
    IF (FINRA_margin_debt_MoM_change <= CALIBRATION_STATE.§12.3.D_alert_margin_monthly_decline
        OR private_credit_gate_count_90d >= CALIBRATION_STATE.§12.3.D_alert_gate_count_90d) {
      score += 1
    }

    // Chain 4: Manufacturing / corporate
    IF corporate_bankruptcy_quarterly_pace >= CALIBRATION_STATE.§12.4.D_alert_bankruptcy_pace {
      score += 1
    }

    RETURN MIN(score, 3)  // cap at 3 — consistent with M03 binding variable scale
  }

  RULE ScoreToProbabilityInput {
    CASE score == 0 → D_precursor_binding: 0  // no additional D support from real-economy layer
    CASE score == 1 → D_precursor_binding: 1  // one chain elevated; monitoring warranted
    CASE score == 2 → D_precursor_binding: 2  // significant precursor stack; brief client
    CASE score == 3 → D_precursor_binding: 3  // critical mass; precursors fully loaded

    CONSTRAINT: "score == 3 does NOT automatically invoke D-probability floor.
                 D-floor (25%) requires M11.HY_RecessionPricing threshold to fire
                 OR M11.ScenarioDTrigger conditions met.
                 sectorStressScore is a leading indicator — it informs probability weighting
                 in the next DeriveScenarioProbabilities() run, not an override."
  }

  // SESSION NOTE (May 25, 2026 — first application):
  // CHAIN_1 (Agriculture): FIRES — farm filings +46% (≥50% threshold: approaching; borderline)
  //   NOTE: +46% is below the +50% formal threshold. Score contribution: 0 (threshold not met).
  //   Flag: very close to threshold; one more quarterly data point may fire.
  // CHAIN_2 (CRE/RegBank): does NOT fire — SOFR–DFF benign (−11bp); KRE not underperforming SPX
  // CHAIN_3 (Private/Margin): FIRES — margin debt at all-time nominal record; gate events observed
  // CHAIN_4 (Manufacturing): FIRES — corporate bankruptcy pace qualitatively at 14-year high
  //   NOTE: Formal quarterly pace data requires PACER/AACER — use qualitative T2 flag at present;
  //   upgrade to T1 when AACER subscription or PACER access available.
  // → sectorStressScore() = 2 (formal); qualitative assessment leans toward 3
  // → CascadeLevel = ALERT (2 formal chains; PRE_POSITION if CHAIN_1 threshold confirmed)


  // ─── §3 YIELD CURVE PROTOCOL ──────────────────────────────────────────────────
  // Formal rules for interpreting Treasury yield curve signals in D/E context.
  // Data source: FMP economics.treasury-rates endpoint (full curve 1M–30Y, live).
  // YIELD CURVE SIGNALS NEVER ROUTE INTO M03.DeriveScenarioProbabilities() DIRECTLY.
  // They produce D timing estimates and reinforce M11 signal weight only.

  FUNCTION computeYieldCurveSignal(fmp_treasury_data) → YieldCurveSignal {

    spread_10Y_2Y  = fmp_treasury_data.year10 - fmp_treasury_data.year2
    spread_10Y_3M  = fmp_treasury_data.year10 - fmp_treasury_data.month3
    term_premium    = THREEFYTP10_current  // from FRED via allocation spreadsheet
    yield_30Y       = fmp_treasury_data.year30

    // Step 1: Classify curve shape
    RULE CurveShape {
      IF spread_10Y_2Y < 0 AND spread_10Y_3M < 0 → curve_state = INVERTED
      IF spread_10Y_2Y < 0 XOR spread_10Y_3M < 0 → curve_state = PARTIAL_INVERSION
      ELSE → curve_state = NORMAL_OR_STEEP
    }

    // Step 2: Re-steepening detection
    // CRITICAL: Re-steepening after inversion = recession ONSET signal, NOT recovery signal.
    // Historical pattern (since 1950): recession followed re-steepening in 5 of 6 post-inversion
    // re-steepening events. The mechanism: Fed cuts short rates → short end falls → curve steepens
    // → but this occurs because the recession has already begun, not because it is being avoided.
    RULE ReSteepening {
      IF curve_state == NORMAL_OR_STEEP
         AND prior_state_was_INVERTED  // loaded from Session_Log §8 or prior briefing
         AND (Fed_has_cut_rates OR spread_10Y_3M >= +50bp) {
        D_timing_signal = RECESSION_ONSET_PATTERN
        D_timing_estimate = "0–12 months from re-steepening onset"
        NOTE: "Do NOT interpret as soft-landing confirmation.
               Re-steepening is the recession arriving, not the recession being avoided."
      }
    }

    // Step 3: Long-end elevated / E-pathway flags
    RULE LongEndElevation {
      IF term_premium >= CALIBRATION_STATE.§12.5.E_alert_term_premium {
        E_watch_flag = E_PATHWAY_WATCH
        action: "Flag in briefing; assess TIC foreign UST holdings data"
      }
      ELSE IF term_premium >= CALIBRATION_STATE.§12.5.term_premium_warning
           AND yield_30Y >= CALIBRATION_STATE.§12.5.yield_30Y_warning {
        E_watch_flag = FISCAL_STRESS_BUILDING
        action: "Note in briefing; direction of term premium change is the key variable"
      }
      ELSE { E_watch_flag = CLEAR }
    }

    // Current reading (May 25, 2026):
    // spread_10Y_2Y = +43bp (May 22); spread_10Y_3M = +88bp
    // curve_state = NORMAL_OR_STEEP (recently re-steepened from prior inversion)
    // D_timing_signal = RECESSION_ONSET_PATTERN — curve re-steepened post-inversion
    // term_premium = 0.81% (THREEFYTP10 May 15, 14-year high, rising)
    // E_watch_flag = FISCAL_STRESS_BUILDING (0.81% > warning threshold; 30Y at 5.07%)

    RETURN YieldCurveSignal {
      spread_10Y_2Y:       spread_10Y_2Y
      spread_10Y_3M:       spread_10Y_3M
      curve_state:         curve_state
      D_timing_signal:     [RECESSION_ONSET_PATTERN | CURVE_INVERTED | MONITORING]
      D_timing_estimate:   String
      term_premium:        term_premium
      E_watch_flag:        [E_PATHWAY_WATCH | FISCAL_STRESS_BUILDING | CLEAR]
      yield_30Y:           yield_30Y
    }
  }


  // ─── §4 SUPPLY CHAIN STRESS INDICATORS ────────────────────────────────────────
  // Upstream real-economy inputs feeding B/C inflation persistence and D-precursor
  // agricultural credit stress. These are B/C ACCELERANTS and D PRECURSORS —
  // they inform probability weighting and provide context for the briefing.
  // They do NOT independently trigger scenario changes.

  ENUM SupplyChainIndicator {

    INDICATOR Fertilizer_Nitrogen {
      primary_series:   anhydrous_ammonia_spot_price (USDA AMS or DTN)
      linkage:          natural_gas → ammonia_production (70-80% of variable cost)
                        → nitrogen_fertilizer → farm_input_cost → food_CPI
      geopolitical_nexus: Iran = top-3 global urea exporter;
                          Hormuz disrupts BOTH oil/LNG transit AND Iranian urea exports;
                          EU CBAM (Jan 1, 2026) adds carbon floor to fertilizer import cost
      benchmarks:       $737/ton historical avg; $779/ton 2025 avg
      current_signal:   $860/ton projected fall 2026; potentially >$1,000/ton if conflict continues;
                        urea prices +33% since Operation Epic Fury (March 2026)
      B_C_mechanism:    elevated fertilizer → elevated food CPI → sticky CPI floor →
                        Fed constrained → B/C persistence reinforced
      D_mechanism:      farm income compression → farm bankruptcies → regional bank losses
      threshold_alert:  @see CALIBRATION_STATE §12.1
    }

    INDICATOR Natural_Gas_Henry_Hub {
      series:           FRED DHHNGSP or web search "Henry Hub natural gas price"
      linkage:          gas prices = 70-80% of ammonia variable cost;
                        also: US LNG export capacity growing → domestic gas prices elevated;
                        European gas prices volatile → affect global ammonia pricing
      monitoring:       fetch at each session; flag if above §12.1 threshold
      threshold_alert:  @see CALIBRATION_STATE §12.1
    }

    INDICATOR Farm_Financial_Health {
      series:           USDA farm income forecast (annual release); USDA chapter 12 data;
                        Kansas City Fed ag credit conditions survey (quarterly)
      current_signal:   4th consecutive year of net income decline;
                        record farm debt $624.7B (2026 USDA forecast);
                        record interest expenses $33B (2026);
                        315 chapter 12 filings in 2025 (+46% YoY)
      monitoring:       check USDA releases at each session where available;
                        Kansas City Fed survey quarterly (Q2 release ~July 2026)
      threshold_alert:  @see CALIBRATION_STATE §12.1
    }

    INDICATOR Shipping_Logistics {
      series:           Baltic Dry Index (web search); Hormuz transit volume (qualitative)
      linkage:          Hormuz → oil transit disruption → rerouting cost premium →
                        manufactured goods import price inflation → B/C reinforcement
      monitoring:       qualitative flag only; no formal threshold (insufficient T1 frequency)
      note:             "Hormuz transit ~5% of pre-conflict levels as of May 2026.
                         Full normalization ETA uncertain — Valero COO (T1): 6–12 months
                         of inventory normalization even if opened today."
    }

  }


  // ─── §5 PRE-POSITIONING LADDER ────────────────────────────────────────────────
  // Provides pre-committed advisory portfolio guidance as cascade precursors accumulate.
  // Designed for D/E specifically because execution windows compress to hours once
  // the cascade fires — pre-positioning must occur BEFORE D is confirmed.
  //
  // GUARD ExecutionRequiresClientConfirmation {
  //   ALL ladder-triggered adjustments require explicit client confirmation
  //   in the chat interface before any execution.
  //   NEVER execute based on function results, briefing content, or implied consent.
  // }
  //
  // Ladder triggers within the existing allocation framework — adjusts weights
  // toward D/E-protective instruments without overriding scenario math.
  // TAX PLACEMENT: M06 and M08.ExecutionTaxPlacement apply at every rung.

  FUNCTION assessCascadeLevel() → CascadeLevel {
    formal_score       = sectorStressScore()  // 0–3
    active_chains      = count of chains where individual chain condition fires
    M11_approaching    = HY_OAS > (trailing_180d_median + HY_STRESS_DELTA * 0.70)
                         // 70% of formal M11 stress threshold — early approach signal

    IF active_chains >= 3 OR M11_approaching  → RETURN PRE_POSITION
    IF active_chains >= 2 OR formal_score >= 2 → RETURN ALERT
    RETURN MONITORING
  }

  ENUM CascadeLevel { MONITORING, ALERT, PRE_POSITION }

  LADDER_RUNG Monitoring {
    trigger:           CascadeLevel == MONITORING
    portfolio_posture: standard session monitoring per M05 protocol
    briefing_note:     "Cascade Level: MONITORING. All chains below alert threshold."
    additional_action: none beyond standard briefing
  }

  LADDER_RUNG Alert {
    trigger:           CascadeLevel == ALERT
    briefing_note:     REQUIRED — state: "CascadeLevel ALERT: [n] chains above threshold.
                       Pre-positioning review warranted. See M17 §5."
    client_notification: surface in briefing; discuss at portfolio discussion

    advisory_posture_review {
      SGOV {
        direction:  REVIEW — confirm current allocation vs D-scenario idealAllocation() target
        rationale:  "Short-duration Treasuries are the D-safe haven. SGOV provides
                     liquidity that illiquid positions cannot in a credit cascade."
        priority:   taxable accounts first (no tax drag on SGOV income)
        guard:      "No entry extension guard on rate_sensitive_income_short_duration"
      }
      SGOL_plus_SIVR {
        direction:  CONFIRM — verify combined precious metals weight vs D-scenario floor
        rationale:  "Precious metals flight-to-safety in D-transition. SIVR industrial
                     component also relevant if B/C continues before D."
        guard:      "Check EntryExtensionGuard (20% threshold) before any ADD"
      }
      PAVE {
        direction:  REVIEW execution window — IIJA expiry September 30, 2026 approaching
        rationale:  "FLAGGED legislative impairment + negative EV B/C/D/E.
                     Alert level activates PAVE exit window review."
        note:       "Confirm PAVE FLAGGED status current before action"
      }
    }

    what_does_NOT_change {
      scenario_probabilities: no snap recalibration;
                              require DeriveScenarioProbabilities() at next full session
      M11_thresholds:         unaffected; M17 supplementary, not overriding
    }
  }

  LADDER_RUNG PrePosition {
    trigger:           CascadeLevel == PRE_POSITION
    briefing_note:     REQUIRED — state: "CascadeLevel PRE_POSITION: [n] chains above threshold.
                       Pre-positioning advisory actions below. Client confirmation required."

    required_before_execution {
      1: run DeriveScenarioProbabilities() with all current inputs
      2: confirm client understands this is pre-emptive positioning, not confirmed D trigger
      3: state M11 D-trigger status explicitly: [firing | approaching | clear]
      4: document T1 evidence for each chain flagged
      5: explicit client confirmation in chat interface before any trade
    }

    advisory_actions {
      SGOV {
        direction:  ADD — increase toward D-scenario target weight
        target:     M13.idealAllocation(account, scenario_D) for each account
        rationale:  "In credit cascade, SGOV is the only truly safe short-duration asset.
                     Pre-positioning before D is confirmed preserves execution at fair price."
        accounts:   taxable accounts preferred; retirement accounts if taxable at target
        guard:      "No entry extension guard on rate_sensitive_income_short_duration"
      }
      SGOL {
        direction:  HOLD or ADD to D-scenario floor
        rationale:  "Flight-to-safety in D-transition."
        guard:      "EntryExtensionGuard(inflation_hedge_precious_metals, 20%) applies"
      }
      DBMF {
        direction:  HOLD at target
        rationale:  "Trend-following captures D-transition: commodity trend reversal +
                     long-rates-down trend + equity short trend. Already best D hedge
                     in framework after B/C positions unwind."
        guard:      "No entry extension guard — systematic_trend_following exempt"
      }
      MLPX {
        direction:  REVIEW for trim — do NOT add
        rationale:  "Real asset contracted revenue robust in B/C; MLPs compress in
                     credit cascade (D). Review if at upper allocation bound."
        note:       "Entry guards irrelevant for trim direction"
      }
      PAVE {
        direction:  EXIT INITIATED — PrePosition removes embedded-gain deferral rationale
        rationale:  "FLAGGED legislative impairment + negative EV in all scenarios
                     (B/C/D/E). CascadeLevel PRE_POSITION = no further deferral justified."
        execution:  "Taxable Acc4 only. Time exit at or above cost basis $54.09/share."
      }
      XAR {
        direction:  HOLD
        rationale:  "Conflict escalation drives both D-risk AND XAR geopolitical_premium.
                     No reduction unless D confirmed AND conflict de-escalates concurrently."
      }
      MAGS {
        direction:  REVIEW for trim — retirement accounts only
        rationale:  "secular_technology_growth deeply negative in D (conservative −14%).
                     Already negative EV at current probs. PrePosition strengthens trim thesis."
        constraint: "TAX PLACEMENT: retirement accounts only (swap phantom gain risk in taxable).
                     Trim in Primary IRA and Primary Roth only."
      }
    }
  }


  // ─── §6 DATA INTEGRITY RULES ──────────────────────────────────────────────────
  // M17 requires cross-referencing for all out-of-range values before
  // including in sector stress scoring, cascade level assessment, or briefing.
  // Encoded after Consumer Cyclical PE 87.8× incident (FMP broad-universe
  // average reported without cross-reference; true S&P 500 sector PE ≈30×).

  GUARD DataIntegrity {
    ALWAYS: when any metric deviates >2× from historical norm,
            search for second opinion BEFORE including in analysis
    ALWAYS: for sector P/E ratios, use ETF-based PE from approved sources
            (XLY, XLE, XLF, XLV, XLI, XLP, XLU, XLB, XLRE)
    NEVER:  use FMP sector-PE-snapshot endpoint for sector valuation
            // FMP returns unweighted average across ALL exchange-listed companies;
            // micro-caps and loss-makers distort simple mean to implausible levels
    NOTE:   "Implausibility is itself a data quality signal. M01 applies to APIs
             and data tools, not just news sources."
  }

  GUARD SectorPE_ApprovedSources {
    APPROVED [
      "worldperatio.com — ETF-based trailing PE by sector",
      "yardeni.com — weekly S&P 500 sector valuations",
      "spglobal.com — official S&P 500 sector earnings releases"
    ]
    REJECTED [
      "FMP:marketPerformance.sector-PE-snapshot",  // unweighted broad-universe average
      "FMP:marketPerformance.industry-PE-snapshot"  // same distortion issue
    ]
  }


  // ─── BRIEFING BLOCK ───────────────────────────────────────────────────────────
  // Insert as "SYSTEMIC CASCADE EARLY WARNING" section in M04.IntelligenceBriefing,
  // positioned after M11 CREDIT SIGNALS section.

  BriefingBlock {
    cascade_level:        [MONITORING | ALERT | PRE_POSITION]
    active_chains:        [list chain IDs at or above D_alert threshold]
    sector_stress_score:  [0|1|2|3] — brief narrative

    yield_curve {
      spread_10Y_2Y:      ___ bp
      spread_10Y_3M:      ___ bp
      curve_state:        [NORMAL_OR_STEEP | PARTIAL_INVERSION | INVERTED]
      D_timing_signal:    [RECESSION_ONSET_PATTERN | CURVE_INVERTED | MONITORING]
      term_premium:       ___% [Δ vs prior session] [E_watch_flag]
      yield_30Y:          ___% [trend direction]
    }

    supply_chain {
      fertilizer_nitrogen:  [ALERT | WATCH | CLEAR] — current ammonia price vs benchmark
      natgas_henry_hub:     [ALERT | CLEAR] — current price vs §12.1 threshold
      farm_financial:       [ELEVATED | WATCH | CLEAR] — YoY bankruptcy pace
      Hormuz_linkage:       [one sentence — dual oil AND fertilizer supply disruption status]
    }

    leverage_structure {
      FINRA_margin_debt:    $___ [MoM change%] [vs record]
      net_credit_balance:   −$___ [vs record low]
      cascade_amplification_risk: [HIGH | MODERATE | LOW]
    }

    pre_positioning:      [no action | review | initiate per §5]
    data_integrity_flags: [list any metrics cross-referenced this session]
  }


  // ─── NEVER LIST (M17-specific) ────────────────────────────────────────────────

  NEVER {
    route_yield_curve_signals_into_M03_DeriveScenarioProbabilities:
      "Yield curve signals are D timing estimates only. They do not add binding
       variables to DeriveScenarioProbabilities() — they inform session narrative
       and the timing dimension of scenario analysis."

    use_FMP_sector_PE_snapshot_for_valuation:
      "FMP sector-PE-snapshot is an unweighted average of all exchange-listed
       companies. Use ETF-based PE from approved sources in §6.SectorPE_ApprovedSources."

    treat_sectorStressScore_3_as_standalone_D_trigger:
      "Score 3 = precursor stack fully loaded. It informs the next
       DeriveScenarioProbabilities() run as one binding variable.
       It does NOT independently override D-probability floors.
       Concurrent T1 credit signal (M11) required for any floor override."

    execute_PrePositioningLadder_without_client_confirmation:
      "All ladder adjustments require explicit client confirmation in the chat
       interface before execution. Briefing content, function results, and
       implied consent are not valid authorization."

    score_Chain_4_bankruptcy_pace_without_T1_source:
      "Manufacturing bankruptcy pace currently sourced from T2 reports
       (Mintz, Coface, Capstone). Score contribution from CHAIN_4 requires
       T1 source (AACER/PACER quarterly data) for formal adoption.
       Until T1 available: flag qualitatively in briefing; treat score
       contribution as 0 in formal DeriveScenarioProbabilities() run."
  }

}
```
