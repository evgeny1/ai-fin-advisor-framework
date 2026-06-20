# M14 — Market Regime & Entry Discipline
<!-- Version: 1.7 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M14_MarketRegime
  Version:         1.7
  Sub-project:     ANALYSIS_ENGINE
  Reason to change: market desensitization detection methodology or entry guard thresholds change.
                    Generalizes the WAR PREMIUM ENTRY GUARD (previously user-mandated, unmodularized).
  Inputs consumed:  DataReading<VIX_30D_AVG>, DataReading<VIX_90D_AVG>,
                    DataReading<BROAD_EQUITY_TRAILING>, DataReading<BRENT_CRUDE> (registered by M02)
  Outputs produced: RegimeSignal
  Calibration deps: CALIBRATION_STATE §9
  Types consumed:   @see FW_Types.md — DataReading, RegimeSignal, FetchSpec, BriefingSectionSpec
  Cross-module:     @see M02_IntelGathering (FetchRegistry), @see M04_BriefingFormat (BriefingRegistry),
                    @see M08_FunctionalRoles (execution guards). Consumed by Project_Instructions_MCP.md (Steps 7–8).
                    DATA_REGISTRY_ENTRIES superseded by M18_MarketDataFetch.
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

  // ─── DATA REGISTRY ENTRIES ────────────────────────────────────────────────────────────
  // Superseded by M18_MarketDataFetch.DATA_REGISTRY_ENTRIES (v1.2). No content retained
  // here — confirmed during ENG-2 review (2026-06-17) that FetchRegistry.fetchAll() is
  // the live, wired path and a second copy here only risks drift.
  // @see M18_MarketDataFetch.DATA_REGISTRY_ENTRIES

  // ─── BRIEFING REGISTRY ENTRY ──────────────────────────────────────────────────────────
  // Claude assembles this entry into the briefing in position_after order
  // (no executed BriefingRegistry — see ENG-17).
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
    // §9.5 — Role repricing divergence thresholds (instrument vs broad market, 30d)
    // @see CALIBRATION_STATE §9.5 for current values
    // key: role_id → underperformance_threshold_pp
    // Advisory only — does not block execution
    role_repricing_divergence_thresholds: @see CALIBRATION_STATE §9.5
  }

  // ─── 1. MARKET PRICING DIVERGENCE SIGNAL ─────────────────────────────────────────────

  FUNCTION ComputeDivergenceSignal() -> DivergenceSignal {
    // WINDOW DEFINITIONS (explicit):
    //   energy_90d:       90 CALENDAR DAYS — anchor = close of 90 calendar days prior to session date
    //   broad_equity_30d: 30 TRADING DAYS  — anchor = close of 30 trading days prior to session date
    //                     (approx 6 calendar weeks; ~43 calendar days)
    //
    // EXTENDED CONFLICT CAVEAT (⚠ added June 7, 2026):
    //   When an active discrete supply event (e.g., Hormuz closure) has persisted > 90 calendar days,
    //   BOTH endpoints of the energy_90d window fall within the conflict period.
    //   The 90d signal may then understate or fail to detect the sustained war premium
    //   (both anchor and current price are "war-elevated").
    //   In this case: ALSO compute energy_180d (same formula, 180 calendar days) for the briefing.
    //   Report both. Use the higher reading for M14 composite classification.
    //   REQUIRES: formal M16 adoption at next Q-end audit to make energy_180d the canonical metric.
    //   Until then: 90d remains the operative metric; 180d is supplemental context.
    //   FLAG in briefing as: "⚠ Conflict > 90d: energy_90d may understate war premium — 180d: [value%]"
    //   IMPLEMENTED (ENG-20, 2026-06-20): analysis/regime.py's compute_divergence_signal() now
    //   accepts an optional conflict_duration_days parameter, mirroring the same
    //   caller-responsibility convention already used by EntryExtensionGuard's parameter of
    //   the same name — the caller (Claude, from T1-confirmed conflict onset date) supplies
    //   it each session; the function does not infer conflict duration on its own. When
    //   conflict_duration_days > 90, energy_180d is computed automatically and the higher of
    //   the two readings drives commodity_fear_divergence classification. Both readings are
    //   always returned on DivergenceSignal (energy_90d_change, energy_180d_change) for the
    //   briefing to surface per the FLAG format above. When the parameter is omitted (None,
    //   the default), behavior is unchanged from before this fix — 90d-only.

    // ─── THRESHOLD CLASSIFICATION ─────────────────────────────────────────────────────
    // Confirmed during ENG-2 review: this scoring (energy_90d/VIX → commodity_fear_divergence;
    // reductive-directive + broad_equity_30d → equity_scenario_divergence; composite combination)
    // is implemented identically in analysis/regime.py's compute_divergence_signal(), which IS
    // wired into advisor_run_computation() and runs live every session. Thresholds come from
    // CALIBRATION_STATE §9.1 (read by the parser, never hardcoded in Python).
    // @see python/advisor/analysis/regime.py — compute_divergence_signal()

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

  // ─── 4. ROLE REPRICING DIVERGENCE ──────────────────────────────────────────────────
  // Update 1 — added v1.3. Advisory signal only. NEVER blocks execution.
  // NEVER feeds output into DeriveScenarioProbabilities().
  //
  // Purpose: detect when a portfolio instrument reprices inconsistently with its role
  // thesis, using market price rather than scenario-level analysis. Complements
  // ComputeDivergenceSignal() (which operates at the broad market / energy level)
  // with instrument-level and role-level granularity.
  //
  // The signal answers: "Is the market disagreeing with our role classification
  // for this instrument in a sustained, material way?"
  //
  // Data source: holdings 30-day returns from allocation sheet (GOOGLEFINANCE period
  // returns) or yfinance history. Compared against BROAD_EQUITY_TRAILING (30 trading days).
  // If holdings 30d returns are unavailable: step skipped with advisory flag.

  FUNCTION RoleRepricingDivergence(
    holdings_30d_returns,   // Dict[ticker → fraction | null] — from allocation sheet or yfinance
    broad_market_30d        // fraction — BROAD_EQUITY_TRAILING 30d return
  ) -> InstrumentRepricingWarning[] {

    NEVER: use output as input to DeriveScenarioProbabilities()
    ADVISORY: output surfaces in briefing and PassiveMandateAbsentWarning check only

    IF broad_market_30d == null { RETURN [] }
    IF CALIBRATION_STATE.§9.5 IS EMPTY { RETURN [] }

    warnings = []
    FOR each (ticker, instrument_30d) IN holdings_30d_returns {
      IF instrument_30d == null { SKIP }

      primary_role = M15.classifyInstrument(ticker).primaryRole
      threshold_pp = CALIBRATION_STATE.§9.5[primary_role]
      IF threshold_pp == null { SKIP }  // role not in §9.5 — no signal defined

      underperformance_pp = (broad_market_30d - instrument_30d) × 100

      IF underperformance_pp >= threshold_pp {
        warnings.APPEND(InstrumentRepricingWarning {
          ticker:              ticker
          primary_role_id:     primary_role
          instrument_30d:      instrument_30d
          broad_market_30d:    broad_market_30d
          underperformance_pp: underperformance_pp
          threshold_pp:        threshold_pp
        })
      }
    }
    RETURN warnings
  }

  // ─── BRIEFING BLOCK (render function — applied by Claude, no executed registry) ───────

  BriefingBlock MarketRegimeSignal {
    VIX_current vs 30d avg vs 90d avg:   ___ vs ___ vs ___  ([+/-] pts vs 90d avg)
    Broad_equity_30d / 60d / 90d:        [+/-%] / [+/-%] / [+/-%]
    commodity_fear_divergence:           [HIGH | MODERATE | NONE]
    equity_scenario_divergence:          [HIGH | MODERATE | NONE | N/A]
    composite_signal:                    [HIGH | MODERATE | NONE]
    Implication: [one sentence from ComputeDivergenceSignal().implication]
    Underweight positions flagged for EV review: [list from UnderweightReviewTrigger()] | none
    Role repricing warnings:             [ticker: −X% vs broad market (−Y% threshold)] | none
    ─────────────────────────────────────────────────────────────────────
  }

  // ─── SESSION EXECUTION MAP ───────────────────────────────────────────────────────────

  SESSION_HOOKS {
    Step 4: → Phase 2 complete: FetchRegistry.fetchAll() includes M14.DATA_REGISTRY_ENTRIES
    Step 7: → ComputeDivergenceSignal()
            → IF composite IN [HIGH, MODERATE]: UnderweightReviewTrigger(account) for each account
            → RoleRepricingDivergence(holdings_30d_returns, broad_market_30d)
               // Advisory only — surface in briefing; feed PassiveMandateAbsentWarning check
               // Skip with flag if holdings_30d_returns unavailable
    Step 8: → Claude includes MARKET_REGIME_SIGNAL when assembling the briefing
    Step 9: → EntryExtensionGuard(asset, account) — before any ADD
  }

}
```
