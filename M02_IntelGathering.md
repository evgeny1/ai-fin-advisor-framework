# M02 — Intelligence Gathering
<!-- Cross-references: @see M01_SourceIntegrity, @see M03_ScenarioFramework, @see M04_BriefingFormat -->
<!-- Extended by: M11_CreditAndCalibration (adds credit spreads to fetch list) -->
<!-- Extended by: M14_MarketRegime (adds VIX trailing averages and position trailing performance to fetch list) -->

```
MODULE IntelGathering {

  // ─── PRIORITY FETCH LIST (every session) ────────────────────────────────
  // Execute at session start before any analysis. @see M05_SessionInit for order.

  FETCH_LIST priority {
    geopolitical: [
      active_conflict_status,
      escalation_or_deescalation_signals,
      breaking_geopolitical_events(window: last_48h)
    ]
    energy: [
      Brent_crude, WTI, natural_gas
    ]
    safe_haven: [
      gold_spot, silver
    ]
    equities: [
      SP500, NASDAQ, Dow, Russell2000
    ]
    volatility: [
      VIX
    ]
    fixed_income: [
      treasury_10Y, treasury_2Y, MOVE_index
    ]
    currency: [
      DXY
    ]
    inflation: [
      latest_CPI_print,
      breakeven_inflation_rates(FRED: T10YIE, T5YIE)
    ]
    fed: [
      current_fed_funds_rate,
      forward_guidance_changes
    ]
    holdings: [
      live_prices_all_client_positions   // from allocation file @see M05_SessionInit
    ]
    credit: @see M11_CreditAndCalibration.FetchList  // added by Extension v1
    market_regime: @see M14_MarketRegime.FetchList   // added by M14
                   // VIX trailing averages (30d, 90d); broad equity 30/60/90d trailing performance;
                   // position-level 30/60/90d trailing closes
                   // runs concurrently with credit fetch in Step 4
  }

  // ─── PRICE DATA INTEGRITY RULE ───────────────────────────────────────────

  GUARD PriceDataIntegrity {
    REQUIRE: specific_price_quote sourced_from dedicated_instrument_page
    NEVER:   accept_price_from [
      sidebar_widgets,
      tickers_embedded_in_unrelated_articles,
      derivative_aggregators
    ]

    APPROVED_SOURCES {
      gold_silver:  [LBMA, Kitco_spot, World_Gold_Council]
      oil:          [EIA_weekly_reports, CME_Group_settlement_data]
      equities:     [NYSE_official, NASDAQ_official]  // exchange closing print only
      rates:        [
        treasury.gov,        // Daily Treasury Par Yield Curve Rates
        FRED(DGS10, DGS2, T10YIE, T5YIE)
      ]
    }

    IF price_sourced_from: unapproved_source {
      LABEL: 'Unverified price — requires dedicated source confirmation.'
    }

    // Extraordinary movement rule
    IF single_instrument_move > 40% OVER any_90d_window {
      CLASSIFY: extraordinary_claim
      REQUIRE: cross_verification from >= 2 dedicated T1_price_sources
                before_entering_digest_as_fact
      // Note: threshold is a relative move — inherently self-adjusting.
      // Review only if structural volatility regime changes materially.
    }
  }

  // ─── GATHERING PROCEDURE (Steps 1–5) ────────────────────────────────────

  PROCEDURE GatherIntel {

    STEP 1: FetchCurrentData {
      execute: @see IntelGathering.FETCH_LIST
      REQUIRE: source_date <= 48h_ago  // for fast-moving situations
      apply:   @see PriceDataIntegrity
    }

    STEP 2: ApplySourceIntegrity {
      FOR each significant_claim {
        identify: tier           // @see M01_SourceIntegrity.Tier
        check:    propaganda_fingerprints  // @see M01_SourceIntegrity.PropagandaMarker
        determine: T1_corroboration
        classify_as: Verified | Unverified | AdversarialSignal
      }
    }

    STEP 3: EnumerateTransmissionMechanisms {
      // For every market-moving development — enumerate ALL mechanisms first.
      // Stopping at first plausible mechanism is an ERROR.

      FOR each market_moving_development {
        OUTPUT_FORMAT {
          Development: [what happened]
          Transmission_mechanisms {
            → MechanismA: [effect]  Weight: Primary | Secondary | Tertiary
            → MechanismB: [effect]  Weight: Primary | Secondary | Tertiary
            → MechanismC: [effect]  Weight: Primary | Secondary | Tertiary
          }
          Dominant_mechanism: [which drives most portfolio impact]
          Net_portfolio_signal: [one sentence — weighted synthesis]
        }
        AFTER identifying any market_moving_narrative {
          RUN: dedicated_search(primary_geopolitical_actors)
          // One search pass is NOT sufficient on days with active diplomatic developments
        }
      }
    }

    STEP 4: IdentifyOmissions {
      ACTIVELY_SEEK: what_is_NOT_being_reported
      // Absence of coverage on financially consequential events is itself signal
    }

    STEP 5: FollowTheMoney {
      FOR each major_development {
        ASSESS [
          who_benefits_financially,
          which_asset_classes_affected_and_how,
          evidence_of_unusual_positioning(options, futures),
          second_order_effects(energy, rates, equities)
        ]
      }
    }

  }

  // ─── PRIMARY DRIVER IDENTIFICATION ──────────────────────────────────────
  // Run before updating scenario probabilities. @see M03_ScenarioFramework.

  FUNCTION identifyPrimaryDriver() {
    // Prevents scenario framework anchoring to prior regime after environment shift.
    OUTPUT_FORMAT {
      PRIMARY_DRIVER_ASSESSMENT {
        current_dominant_driver:   [name explicitly]
        evidence:                  [T1 source]
        duration_of_dominance:     [how long this has been primary driver]
        challenger_drivers:        [emerging secondary drivers that could displace it]
        recalibration_trigger_check: Yes | No
        // If Yes → recalibrate scenario probabilities @see M03_ScenarioFramework.RecalibrationRule
      }
    }
  }

}
```
