# M14 — Market Regime & Entry Discipline
<!-- Version: 1.2 | Adopted: May 25, 2026 -->
<!-- Changes from v1.1: DATA_REGISTRY_ENTRIES moved to M18_MarketDataFetch (v1.20 M18 integration). -->
<!--   M14 DATA_REGISTRY_ENTRIES block renamed _LEGACY. M18 is the single FetchSpec registry. -->
<!-- Addresses: market desensitization detection, underweight opportunity cost, entry price extension -->
<!-- Generalizes: WAR PREMIUM ENTRY GUARD (previously user-mandated, unmodularized) -->
<!-- Extends: M02_IntelGathering (FetchRegistry), M04_BriefingFormat (BriefingRegistry), M08_FunctionalRoles (execution guards) -->
<!-- Consumed by: M05_SessionInit (Steps 7–8), M08_FunctionalRoles.ExecutionGuards -->
<!-- Companion: @see FW_Types.md (types) -->

<!-- MODULE MANIFEST
  ID:              M14_MarketRegime
  Version:         1.1
  Sub-project:     ANALYSIS_ENGINE
  Reason to change: market desensitization detection methodology or entry guard thresholds change
  Inputs consumed:  DataReading<VIX_30D_AVG>, DataReading<VIX_90D_AVG>,
                    DataReading<BROAD_EQUITY_TRAILING>, DataReading<BRENT_CRUDE> (registered by M02)
  Outputs produced: RegimeSignal
  Calibration deps: CALIBRATION_STATE §9
  Types consumed:   @see FW_Types.md — DataReading, RegimeSignal, FetchSpec, BriefingSectionSpec
-->

```
MODULE MarketRegimeDiscipline {

  // ─── PURPOSE ────────────────────────────────────────────────────────────────────────
  //   GAP 1: No detection of market desensitization to an ongoing scenario.
  //   GAP 2: No systematic opportunity-cost reassessment when a scenario-underweighted
  //          position appreciates materially.
  //   GAP 3: No entry-price extension check before ADD directives execute for
  //          non-commodity instruments.
  //
  // ─── CRITICAL ARCHITECTURAL BOUNDARY ────────────────────────────────────────────────
  // ALL signals produced by this module route to entry-timing EV calculations ONLY.
  // NEVER feed M14 signals into DeriveScenarioProbabilities().
  // @see M03_ScenarioFramework.DeriveScenarioProbabilities.ScoringIntegrity

  // ─── DATA REGISTRY ENTRIES (LEGACY — superseded by M18_MarketDataFetch, v1.2) ─────────
  // Moved to M18_MarketDataFetch.DATA_REGISTRY_ENTRIES. Retained here for reference.

  DATA_REGISTRY_ENTRIES_LEGACY {
    REGISTER FetchSpec { id: "VIX_30D_AVG",          source: WEBSEARCH_T1, description: "VIX 30-day rolling avg — CBOE or FRED VIXCLS series",   update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "VIX_90D_AVG",          source: WEBSEARCH_T1, description: "VIX 90-day rolling avg — CBOE or FRED VIXCLS series",   update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "BROAD_EQUITY_TRAILING", source: WEBSEARCH_T1, description: "VTI or SPX 30/60/90d trailing pct-change — approved source", update_frequency: DAILY, acceptable_lag_days: 1 }
  }

  // ─── FETCH LIST (legacy — superseded by DATA_REGISTRY_ENTRIES above) ─────────────────
  // Retained for reference only. FetchRegistry.fetchAll() owns all structured fetches.

  FetchList_LEGACY {
    VIX_trailing {
      VIX_30d_avg:  rolling 30-day average of VIX daily close
      VIX_90d_avg:  rolling 90-day average of VIX daily close
      source:       CBOE official or FRED (VIXCLS series)
    }
    broad_equity_trailing_performance {
      instrument:   VTI (or SPX as proxy if VTI unavailable)
      windows:      [30d, 60d, 90d]
      compute:      pct_change from [30d | 60d | 90d] prior close to current price
      source:       @see M02_IntelGathering.PriceDataIntegrity.APPROVED_SOURCES
      IF trailing_close unavailable from approved source {
        FLAG: "Trailing close unavailable — nominal threshold applied."
      }
    }
    position_trailing_performance {
      FOR each held position:
        windows:    [30d, 60d, 90d]
        current_price:    AllocationSheet.price(asset)
        reference_price:  web fetch of 30/60/90d prior close from approved source
        IF reference_price unavailable {
          FLAG: "[asset.ticker] — trailing reference price unavailable.
                 Apply conservative assumption: treat as threshold met."
        }
    }
  }

  // ─── BRIEFING REGISTRY ENTRY ──────────────────────────────────────────────────────────
  // Phase 2 complete: BriefingRegistry.assemble() in M04 iterates this entry.
  // M04 FIXED_INCOME_AND_RATES uses position_after: "MARKET_REGIME_SIGNAL" — this id.

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "MARKET_REGIME_SIGNAL"
      title:          "MARKET REGIME SIGNAL"
      position_after: "EQUITY_MARKETS"   // M04's registered section id
      module_id:      M14
      render_fn:      "M14.BriefingBlock"
    }
  }

  // ─── TRAILING REFERENCE PRICE COMPUTATION ────────────────────────────────────────────

  FUNCTION compute_90d_trailing_avg(asset) -> Float {
    STEP 1: identify_source {
      FOR asset.role IN [broad_market_equity_domestic, policy_driven_thematic_equity,
                         geopolitical_premium] {
        source: NYSE or NASDAQ official historical closing prices
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
    }
    STEP 3: compute {
      avg = arithmetic_mean(all_closing_prices_in_window)
      RETURN avg
    }
    STEP 4: validate {
      IF datapoint_count < 30 {
        FLAG: "[asset.ticker] — fewer than 30 datapoints. Apply conservative assumption: treat as threshold met."
        RETURN null
      }
      IF avg <= 0 { HARD_STOP }
    }
    IF last_datapoint_in_window > 5_trading_days_old {
      FLAG: "[asset.ticker] trailing avg stale. Flag in briefing."
    }
  }

  // ─── CALIBRATION-DATED THRESHOLDS ⚑ → CALIBRATION_STATE §9 ──────────────────────────

  THRESHOLDS M14_Thresholds {
    // §9.1 — Divergence signal thresholds
    commodity_fear_divergence_HIGH:     energy_90d >= +15% AND VIX_change_90d_pts <= 0
    commodity_fear_divergence_MODERATE: energy_90d >= +10% AND VIX_change_90d_pts <= +5
    equity_divergence_HIGH:             broad_equity_30d >= +5%
                                        WHILE scenario_directive IN [Reduce, reduce_to_minimumConvictionWeight]
    equity_divergence_MODERATE:         broad_equity_30d >= +2%
                                        WHILE scenario_directive IN [Reduce, reduce_to_minimumConvictionWeight]
    // §9.2 — Underweight review trigger thresholds
    underweight_gap_trigger:            5 pp
    appreciation_trigger_30d:           5%
    // §9.3 — Entry extension guard thresholds (appreciation above 90d trailing avg)
    entry_extension {
      broad_market_equity:              15%
      thematic_sector_equity:           20%
      commodity_linked:                 20%
      inflation_hedge_precious_metals:  20%
      real_asset_contracted_revenue:    15%
      rate_sensitive_income_short:      N/A
      rate_sensitive_income_long:       N/A
    }
  }

  // ─── 1. MARKET PRICING DIVERGENCE SIGNAL ─────────────────────────────────────────────

  FUNCTION ComputeDivergenceSignal() -> DivergenceSignal {

    energy_change_90d    = (Brent_current - Brent_90d_prior_close) / Brent_90d_prior_close
    VIX_change_90d_pts   = VIX_current - VIX_90d_avg

    IF energy_change_90d >= +0.15 AND VIX_change_90d_pts <= 0 {
      commodity_fear_divergence = HIGH
    } ELSE IF energy_change_90d >= +0.10 AND VIX_change_90d_pts <= +5 {
      commodity_fear_divergence = MODERATE
    } ELSE {
      commodity_fear_divergence = NONE
    }

    dominant_scenario  = M02_IntelGathering.identifyPrimaryDriver().current_dominant_driver
    equity_directive   = lookup_directive("broad_market_equity_domestic", dominant_scenario)

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
    }

    IF commodity_fear_divergence == HIGH OR equity_scenario_divergence == HIGH {
      composite = HIGH
    } ELSE IF commodity_fear_divergence == MODERATE OR equity_scenario_divergence == MODERATE {
      composite = MODERATE
    } ELSE {
      composite = NONE
    }

    RETURN DivergenceSignal { commodity_fear_divergence, equity_scenario_divergence, composite, implication }

    NEVER: use this output as input to DeriveScenarioProbabilities()
  }

  // ─── 2. UNDERWEIGHT REVIEW TRIGGER ───────────────────────────────────────────────────

  FUNCTION UnderweightReviewTrigger(account) {
    flagged = []
    FOR each asset a IN account.holdings {
      current_alloc    = AllocationSheet.currentAllocation(a, account)
      target_alloc     = M03.scenarioWeightedAllocation(a, account)
      underweight_gap  = target_alloc - current_alloc
      appreciation_30d = trailing_performance(a, 30d)
      IF underweight_gap >= M14_Thresholds.underweight_gap_trigger
         AND appreciation_30d >= M14_Thresholds.appreciation_trigger_30d {
        new_threshold_fired = check_new_M11_triggers_vs_prior_§8_entry()
        IF NOT new_threshold_fired {
          flagged.APPEND({ asset: a, underweight_gap, appreciation_30d,
                           opportunity_cost_estimate: underweight_gap × appreciation_30d })
        }
      }
    }
    IF flagged NOT EMPTY {
      FOR each position p IN flagged {
        OUTPUT {
          "── UNDERWEIGHT REVIEW REQUIRED: [p.asset.ticker] ──"
          "Gap: [underweight_gap pp] | 30d appreciation: [appreciation_30d%]"
          "REQUIRED — HoldJustification EV calc before any re-entry decision."
          "Do NOT auto-re-enter even if composite DivergenceSignal == HIGH."
        }
      }
    }
    RETURN flagged
  }

  // ─── 3. ENTRY EXTENSION GUARD ────────────────────────────────────────────────────────
  // Called from M08_FunctionalRoles.ExecutionGuards before ADD executes.

  GUARD EntryExtensionGuard(asset, account) {
    role      = M08_FunctionalRoles.classifyRole(asset)
    threshold = M14_Thresholds.entry_extension[role]
    IF threshold == N/A { PASS; RETURN }

    current_price   = AllocationSheet.price(asset)
    reference_price = compute_90d_trailing_avg(asset)

    IF reference_price == null OR reference_price UNAVAILABLE {
      FLAG: "[asset.ticker] — 90d trailing average unavailable. Conservative: treat as threshold met."
      HALT; RETURN
    }

    appreciation = (current_price - reference_price) / reference_price

    IF appreciation >= threshold {
      adjusted_returns = {}
      FOR each scenario s IN [A, B, C, D, E, F] {
        r_published         = CALIBRATION_STATE §4.1[role][s].conservative
        r_adjusted          = r_published - appreciation
        adjusted_returns[s] = r_adjusted
      }
      FLAG {
        "══ ENTRY EXTENSION GUARD — [asset.ticker] ([role]) ══"
        "Extension: [appreciation%]  (threshold: [threshold%])"
        "Adjusted conservative returns shown per scenario."
        "REQUIRED: Recalculate EV. HALT until EV confirmed."
      }
      IF active_discrete_supply_event
         AND role IN [inflation_hedge_commodity_linked, geopolitical_premium,
                      inflation_hedge_precious_metals] {
        NOTE: "WAR PREMIUM ENTRY GUARD also applies independently."
      }
      HALT; RETURN
    }
    PASS
  }

  // ─── BRIEFING BLOCK (render function — called by BriefingRegistry.assemble()) ─────────

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

  // ─── SESSION EXECUTION MAP ───────────────────────────────────────────────────────────

  SESSION_HOOKS {
    Step 4: → Phase 2 complete: FetchRegistry.fetchAll() includes M14.DATA_REGISTRY_ENTRIES
    Step 7: → ComputeDivergenceSignal()
            → IF composite IN [HIGH, MODERATE]: UnderweightReviewTrigger(account) for each account
    Step 8: → Phase 2 complete: BriefingRegistry.assemble() includes MARKET_REGIME_SIGNAL
    Step 9: → EntryExtensionGuard(asset, account) — before any ADD
  }

}
```
