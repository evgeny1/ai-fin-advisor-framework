# M14 — Market Regime & Entry Discipline
<!-- Version: 1.0 | Adopted: April 27, 2026 -->
<!-- Addresses: market desensitization detection, underweight opportunity cost, entry price extension -->
<!-- Generalizes: WAR PREMIUM ENTRY GUARD (previously user-mandated, unmodularized) -->
<!-- Extends: M02_IntelGathering (fetch list), M04_BriefingFormat (new section), M08_FunctionalRoles (execution guards) -->
<!-- Consumed by: M05_SessionInit (Steps 7–8), M08_FunctionalRoles.ExecutionGuards -->

```
MODULE MarketRegimeDiscipline {

  // ─── PURPOSE ────────────────────────────────────────────────────────────
  // Addresses three structural gaps not covered by the core framework:
  //
  //   GAP 1: No detection of market desensitization to an ongoing scenario.
  //          Scenarios persist; market pricing can absorb them and move on.
  //          The framework previously had no mechanism to detect this shift.
  //
  //   GAP 2: No systematic opportunity-cost reassessment when a scenario-
  //          underweighted position appreciates materially. The directive
  //          "reduce to minimumConvictionWeight" has no expiry or review gate.
  //
  //   GAP 3: No entry-price extension check before ADD directives execute
  //          for non-commodity instruments. The WAR PREMIUM ENTRY GUARD
  //          (previously user-mandated) covered commodity-linked instruments
  //          under active supply shocks only. This module generalizes it.
  //
  // ─── CRITICAL ARCHITECTURAL BOUNDARY ────────────────────────────────────
  // ALL signals produced by this module route to entry-timing EV calculations ONLY.
  // NEVER feed M14 signals into DeriveScenarioProbabilities() — ScoringIntegrity
  // guard applies absolutely. Market pricing describes positioning, not macro conditions.
  // @see M03_ScenarioFramework.DeriveScenarioProbabilities.ScoringIntegrity

  // ─── FETCH ADDITIONS (extends M02_IntelGathering.FETCH_LIST) ─────────────
  // These run as part of M05 Step 4 alongside the main FETCH_LIST.

  FetchList {
    VIX_trailing {
      VIX_30d_avg:  rolling 30-day average of VIX daily close
      VIX_90d_avg:  rolling 90-day average of VIX daily close
      // VIX_current already in M02.FETCH_LIST — trailing averages only added here
      source:       CBOE official or FRED (VIXCLS series)
    }

    broad_equity_trailing_performance {
      instrument:   VTI (or SPX as proxy if VTI unavailable)
      windows:      [30d, 60d, 90d]
      compute:      pct_change from [30d | 60d | 90d] prior close to current price
      source:       @see M02_IntelGathering.PriceDataIntegrity.APPROVED_SOURCES
                    (NYSE/NASDAQ official closing prices)
      IF trailing_close unavailable from approved source {
        FLAG: "Trailing close unavailable — nominal threshold applied.
               Confirm via dedicated exchange source before using in EV calc."
      }
    }

    position_trailing_performance {
      FOR each held position:
        windows:    [30d, 60d, 90d]
        compute:    pct_change from [30d | 60d | 90d] prior close to current price
        source:     @see M02_IntelGathering.PriceDataIntegrity.APPROVED_SOURCES
        current_price:    AllocationSheet.price(asset)  // live GOOGLEFINANCE — treat as current
        reference_price:  web fetch of 30/60/90d prior close from approved source
        IF reference_price unavailable {
          FLAG: "[asset.ticker] — trailing reference price unavailable.
                 EntryExtensionGuard cannot confirm threshold.
                 Apply conservative assumption: treat as threshold met."
        }
    }
  }

  // ─── TRAILING REFERENCE PRICE COMPUTATION ───────────────────────────────

  FUNCTION compute_90d_trailing_avg(asset) -> Float {
    // Computes the 90-calendar-day trailing average closing price for [asset].
    // Used by EntryExtensionGuard as the neutral-entry reference point.
    // Current price is always AllocationSheet.price(asset) — GOOGLEFINANCE, live.
    // Trailing closes require a separate approved-source fetch — NOT from AllocationSheet.

    STEP 1: identify_source {
      FOR asset.role IN [broad_market_equity_domestic, policy_driven_thematic_equity,
                         geopolitical_premium] {
        source: NYSE or NASDAQ official historical closing prices
        // Acceptable proxies: Yahoo Finance historical data tab, FRED (where series exists)
        // NEVER: sidebar widgets, embedded tickers, aggregator summary tables
        // @see M02_IntelGathering.PriceDataIntegrity.APPROVED_SOURCES
      }
      FOR asset.role IN [inflation_hedge_precious_metals] {
        source: LBMA official historical PM fix, or Kitco historical spot
      }
      FOR asset.role IN [inflation_hedge_commodity_linked] {
        source: EIA weekly reports, CME Group historical settlement data
      }
      FOR asset.role IN [real_asset_contracted_revenue] {
        source: NYSE or NASDAQ official historical closing prices
      }
    }

    STEP 2: fetch_closing_prices {
      window:     90 calendar days prior to current session date
      datapoints: daily closing prices across the window
      // For ETFs: NAV-based closing price preferred over intraday.
      // If only weekly or monthly data available from approved source:
      //   FLAG: "Only [weekly|monthly] data available for [asset.ticker].
      //          90d avg computed from [N] datapoints — lower precision.
      //          Treat computed avg as approximate; apply conservative rounding."
    }

    STEP 3: compute {
      avg = arithmetic_mean(all_closing_prices_in_window)
      // Arithmetic mean, not median — consistent with how EV calculations
      // express "neutral entry price" in the return table empirical basis.
      RETURN avg
    }

    STEP 4: validate {
      IF datapoint_count < 30 {
        FLAG: "[asset.ticker] — fewer than 30 datapoints in 90d window.
               Average unreliable. Apply conservative assumption: treat as threshold met.
               Do not execute ADD until reference price confirmed."
        RETURN null  // EntryExtensionGuard treats null as threshold met → HALT
      }
      IF avg <= 0 {
        HARD_STOP
        FLAG: "Computed trailing avg is zero or negative — data error. Abort."
      }
    }

    // Staleness guard:
    IF last_datapoint_in_window > 5_trading_days_old {
      FLAG: "[asset.ticker] trailing avg — most recent close is [N] trading days stale.
             EntryExtensionGuard result may be imprecise. Flag in briefing."
      // Do NOT abort — stale data is better than no reference. Flag and proceed.
    }
  }

  // ─── IMPLEMENTATION NOTE — 30d and 60d windows ───────────────────────────
  // UnderweightReviewTrigger() and the briefing block also reference 30d and 60d
  // trailing performance figures. These use the same fetch pattern as above
  // with window = 30 or 60 calendar days and compute pct_change from
  // [first close in window] to [current AllocationSheet.price(asset)].
  // NOT a rolling average — a point-to-point return over the window.
  // Naming convention:
  //   compute_90d_trailing_avg()        → rolling mean, used by EntryExtensionGuard
  //   trailing_performance(asset, Nd)   → point-to-point return, used by UnderweightReviewTrigger
  //                                        and briefing block

  // ─── CALIBRATION-DATED THRESHOLDS ⚑ ─────────────────────────────────────
  // Review quarterly alongside CALIBRATION_STATE §1 and §2.
  // ⚑ ALL values CALIBRATION_DATED → CALIBRATION_STATE §9

  THRESHOLDS M14_Thresholds {

    // §9.1 — Divergence signal thresholds
    commodity_fear_divergence_HIGH:     energy_90d >= +15% AND VIX_change_90d_pts <= 0
    commodity_fear_divergence_MODERATE: energy_90d >= +10% AND VIX_change_90d_pts <= +5
    equity_divergence_HIGH:             broad_equity_30d >= +5%
                                        WHILE scenario_directive IN [Reduce, reduce_to_minimumConvictionWeight]
    equity_divergence_MODERATE:         broad_equity_30d >= +2%
                                        WHILE scenario_directive IN [Reduce, reduce_to_minimumConvictionWeight]

    // §9.2 — Underweight review trigger thresholds
    underweight_gap_trigger:            5 pp  // current vs scenarioWeightedAllocation()
    appreciation_trigger_30d:           5%    // 30d point-to-point window

    // §9.3 — Entry extension guard thresholds (appreciation above 90d trailing avg)
    entry_extension {
      broad_market_equity:              15%
      thematic_sector_equity:           20%   // policy_driven_thematic_equity, geopolitical_premium
      commodity_linked:                 20%   // general case; WAR PREMIUM ENTRY GUARD
                                              // also applies independently when discrete event active
      inflation_hedge_precious_metals:  20%
      real_asset_contracted_revenue:    15%
      rate_sensitive_income_short:      N/A   // price-stable; guard does not apply
      rate_sensitive_income_long:       N/A   // duration risk captured by scenario framework
    }
  }

  // ─── 1. MARKET PRICING DIVERGENCE SIGNAL ────────────────────────────────
  // Detects when the market has absorbed an ongoing scenario without the scenario
  // resolving. Two independent components — both computed each session.
  // Output routes to UnderweightReviewTrigger() and briefing only.
  // NEVER routes into DeriveScenarioProbabilities().

  FUNCTION ComputeDivergenceSignal() -> DivergenceSignal {

    // COMPONENT A: Commodity / Fear Divergence
    // Is market fear (VIX) no longer tracking an elevated energy/commodity premium?

    energy_change_90d    = (Brent_current - Brent_90d_prior_close) / Brent_90d_prior_close
    VIX_change_90d_pts   = VIX_current - VIX_90d_avg

    IF energy_change_90d >= +0.15 AND VIX_change_90d_pts <= 0 {
      commodity_fear_divergence = HIGH
    } ELSE IF energy_change_90d >= +0.10 AND VIX_change_90d_pts <= +5 {
      commodity_fear_divergence = MODERATE
    } ELSE {
      commodity_fear_divergence = NONE
    }

    // COMPONENT B: Broad Equity vs Scenario Directive Divergence
    // Is broad equity running against what the dominant scenario says it should do?
    // Only meaningful when directive is reductive — not when directive is Hold or Add.

    dominant_scenario  = M02_IntelGathering.identifyPrimaryDriver().current_dominant_driver
    equity_directive   = lookup_directive("broad_market_equity_domestic", dominant_scenario)
                         // from M09 or M10 RESPONSES

    IF equity_directive IN ["Reduce", "reduce_to minimumConvictionWeight()"] {
      IF broad_equity_trailing_performance.change_30d >= +0.05 {
        equity_scenario_divergence = HIGH
      } ELSE IF broad_equity_trailing_performance.change_30d >= +0.02 {
        equity_scenario_divergence = MODERATE
      } ELSE {
        equity_scenario_divergence = NONE
      }
    } ELSE {
      equity_scenario_divergence = NOT_APPLICABLE
      // Directive is Hold or Add — market moving with directive, not against it
    }

    // COMPOSITE
    IF commodity_fear_divergence == HIGH OR equity_scenario_divergence == HIGH {
      composite   = HIGH
      implication = "Market has materially absorbed current scenario risk without scenario "
                    "resolution. Thesis structurally intact — but market is no longer pricing "
                    "it as novel. Entry-timing EV for scenario-underweighted positions may be "
                    "improving. UnderweightReviewTrigger fires this session."
    } ELSE IF commodity_fear_divergence == MODERATE OR equity_scenario_divergence == MODERATE {
      composite   = MODERATE
      implication = "Partial market absorption signal. Monitor — not yet actionable."
    } ELSE {
      composite   = NONE
      implication = "Market pricing consistent with scenario directive. No divergence detected."
    }

    RETURN DivergenceSignal {
      commodity_fear_divergence:   commodity_fear_divergence
      equity_scenario_divergence:  equity_scenario_divergence
      composite:                   composite
      implication:                 implication
    }

    // HARD GUARD:
    NEVER: use this output as input to DeriveScenarioProbabilities()
    NEVER: cite composite == HIGH as evidence of scenario probability shift
    // Routes ONLY to: UnderweightReviewTrigger() and M04 briefing block
  }

  // ─── 2. UNDERWEIGHT REVIEW TRIGGER ──────────────────────────────────────
  // Fires when a scenario-underweighted position has appreciated materially
  // without a worsening scenario. Forces EV reassessment — does NOT generate
  // a recommendation. EV math always required before any re-entry decision.
  // @see M06_ClientAndAdvisory.HoldJustification (EV format)

  FUNCTION UnderweightReviewTrigger(account) {

    flagged = []

    FOR each asset a IN account.holdings {
      current_alloc    = AllocationSheet.currentAllocation(a, account)
      target_alloc     = M03.scenarioWeightedAllocation(a, account)
      underweight_gap  = target_alloc - current_alloc
      appreciation_30d = trailing_performance(a, 30d)

      IF underweight_gap  >= M14_Thresholds.underweight_gap_trigger
         AND appreciation_30d >= M14_Thresholds.appreciation_trigger_30d {

        // Check: has the scenario worsened this session?
        // A new M11 threshold fired this session (not fired in prior §8 entry)
        // in the direction that worsens the scenario directive for [a].
        new_threshold_fired = check_new_M11_triggers_vs_prior_§8_entry()
        // Compares current-session trigger status vs §8.latest_entry.open_triggers
        // IF any new trigger fires → scenario actively worsening → do NOT flag

        IF NOT new_threshold_fired {
          opportunity_cost_estimate = underweight_gap × appreciation_30d
          flagged.APPEND({
            asset:                     a,
            underweight_gap:           underweight_gap,
            appreciation_30d:          appreciation_30d,
            opportunity_cost_estimate: opportunity_cost_estimate
          })
        }
      }
    }

    IF flagged NOT EMPTY {
      FOR each position p IN flagged {
        OUTPUT {
          "── UNDERWEIGHT REVIEW REQUIRED: [p.asset.ticker] ──"
          "Current: [current_alloc%] | Scenario-weighted target: [target_alloc%]"
          "Gap: [underweight_gap pp] | 30d appreciation: [appreciation_30d%]"
          "Estimated opportunity cost of remaining underweight: ~[opportunity_cost_estimate pp]"
          ""
          "REQUIRED — HoldJustification EV calc before any re-entry decision:"
          "  EV_of_remaining_underweight:"
          "    P(scenario worsens materially) × estimated protection value of staying underweight"
          "  vs"
          "  EV_of_partial_re-entry:"
          "    P(scenario holds or improves) × [appreciation_30d%] foregone at [underweight_gap pp]"
          ""
          "Present EV result to client. Do NOT re-enter without EV math shown."
          "Do NOT auto-re-enter even if composite DivergenceSignal == HIGH."
          "If EntryExtensionGuard also fires → run both independently; both must confirm."
        }
      }
    }

    RETURN flagged  // empty list = no review required this session
  }

  // ─── 3. ENTRY EXTENSION GUARD ────────────────────────────────────────────
  // Runs before any ADD or Add_aggressive directive executes for ANY instrument.
  // The return table in CALIBRATION_STATE §4.1 assumes neutral entry (at or near
  // 90d trailing average). Extended entries require conservative return adjustment.
  //
  // Generalizes the WAR PREMIUM ENTRY GUARD:
  //   WAR PREMIUM ENTRY GUARD: commodity-linked, active discrete supply event
  //   EntryExtensionGuard:     all roles, any sustained price extension
  //   When both apply → both checks run independently; both must confirm EV positive.
  //
  // Called from M08_FunctionalRoles.ExecutionGuards before ADD executes.

  GUARD EntryExtensionGuard(asset, account) {

    role      = M08_FunctionalRoles.classifyRole(asset)
    threshold = M14_Thresholds.entry_extension[role]

    IF threshold == N/A {
      PASS  // guard does not apply to this role; proceed with ADD
      RETURN
    }

    current_price   = AllocationSheet.price(asset)       // live GOOGLEFINANCE
    reference_price = compute_90d_trailing_avg(asset)    // approved source fetch

    IF reference_price == null OR reference_price UNAVAILABLE {
      FLAG: "[asset.ticker] — 90d trailing average unavailable.
             Conservative assumption applied: treat as threshold met.
             Confirm reference price before executing ADD."
      HALT  // do not execute ADD until confirmed
      RETURN
    }

    appreciation = (current_price - reference_price) / reference_price

    IF appreciation >= threshold {

      // Adjust conservative scenario returns downward by the embedded premium paid.
      // Entry at (1 + appreciation) × reference_price means the published conservative
      // return must be reduced — the buyer has pre-paid that appreciation.

      adjusted_returns = {}
      FOR each scenario s IN [A, B, C, D, E, F] {
        r_published         = CALIBRATION_STATE §4.1[role][s].conservative
        r_adjusted          = r_published - appreciation
        adjusted_returns[s] = r_adjusted
      }

      FLAG {
        "══ ENTRY EXTENSION GUARD — [asset.ticker] ([role]) ══"
        "Current price: $[current_price] | 90d trailing avg: $[reference_price]"
        "Extension above reference: [appreciation%]  (threshold: [threshold%])"
        ""
        "Conservative return table assumes neutral entry. Adjusted returns:"
        FOR each scenario s:
          "  Scenario [s]: published [r_published%]  →  adjusted [r_adjusted%]"
        ""
        "REQUIRED: Recalculate EV using adjusted returns before executing ADD."
        "  IF adjusted EV positive across scenario-weighted vector → ADD proceeds."
        "  IF adjusted EV near-zero or negative → ADD not justified at current price."
        "Present adjusted EV to client. HALT until EV confirmed."
      }

      // WAR PREMIUM ENTRY GUARD interaction:
      IF active_discrete_supply_event
         AND role IN [inflation_hedge_commodity_linked, geopolitical_premium,
                      inflation_hedge_precious_metals] {
        NOTE: "WAR PREMIUM ENTRY GUARD also applies independently.
               Both guards require separate EV confirmation.
               A position may clear one and fail the other."
      }

      HALT  // do not execute ADD until adjusted EV confirmed by client
      RETURN
    }

    // IF appreciation < threshold: guard passes silently — no output, no delay
    PASS
  }

  // ─── BRIEFING BLOCK (M04 insertion) ─────────────────────────────────────
  // Inserted after EQUITY MARKETS section in M04_BriefingFormat.IntelligenceBriefing

  BriefingBlock MarketRegimeSignal {
    VIX_current vs 30d avg vs 90d avg:   ___ vs ___ vs ___  ([+/-] pts vs 90d avg)
    Broad_equity_30d / 60d / 90d:        [+/-%] / [+/-%] / [+/-%]
    commodity_fear_divergence:           [HIGH | MODERATE | NONE]
    equity_scenario_divergence:          [HIGH | MODERATE | NONE | N/A]
    composite_signal:                    [HIGH | MODERATE | NONE]
    Implication: [one sentence from ComputeDivergenceSignal().implication]
    Underweight positions flagged for EV review: [list from UnderweightReviewTrigger()] | none
    ─────────────────────────────────────────────────────────────────────
  }

  // ─── SESSION EXECUTION MAP ───────────────────────────────────────────────

  SESSION_HOOKS {
    Step 4 (fetch market data):
      → fetch M14.FetchList additions (VIX trailing averages; broad equity 30/60/90d
        trailing performance; position-level 30/60/90d trailing closes)
        // runs concurrently with M11 credit fetch

    Step 7 (complete intel gathering):
      → ComputeDivergenceSignal()    // feeds briefing block
      → IF DivergenceSignal.composite IN [HIGH, MODERATE]:
           UnderweightReviewTrigger(account) for each account
           // output surfaced in briefing under MarketRegimeSignal block
           // EV calc deferred to portfolio discussion (Step 9)

    Step 8 (produce briefing):
      → include MarketRegimeSignal briefing block after EQUITY MARKETS section

    Step 9 (portfolio discussion — before any ADD executes):
      → EntryExtensionGuard(asset, account)
      // called from M08_FunctionalRoles.ExecutionGuards — not separately
  }

}
```
