# M02 — Intelligence Gathering
<!-- Version: 2.1 | Adopted: May 25, 2026 -->
<!-- Changes from v2.0: M18 integration — DATA_REGISTRY_ENTRIES block moved to M18_MarketDataFetch. -->
<!--   M02's DATA_REGISTRY_ENTRIES are now _LEGACY (superseded by M18). -->
<!--   GatherIntel STEP 1 now references M18 explicitly. -->
<!--   To add a new data series: register in M18_MarketDataFetch.DATA_REGISTRY_ENTRIES only. -->
<!-- Cross-references: @see M01_SourceIntegrity, @see M03_ScenarioFramework, @see M04_BriefingFormat -->
<!-- Extended by: M11 (HY_OAS, CCC_OAS, IG_OAS, BBB_OAS, MOVE) -->
<!-- Extended by: M14 (VIX_30D_AVG, VIX_90D_AVG, BROAD_EQUITY_TRAILING) -->
<!-- Extended by: M17 (YIELD_CURVE, KRE, KBE, THREEFYTP10, SOFR, DFF, FINRA_MARGIN_DEBT, NATGAS_HENRY_HUB, FARM_FILINGS_YOY) -->

<!-- MODULE MANIFEST
  ID:              M02_IntelGathering
  Version:         2.1
  Sub-project:     DATA_INTELLIGENCE
  Reason to change: core M02-owned data sources change (energy, equities, rates, FX, inflation);
                    OR qualitative gather methodology changes.
                    Adding a new module's structured data: register DATA_REGISTRY_ENTRIES in that
                    module; M02 does not change.
  Inputs consumed:  (none — M02 is the DATA_INTELLIGENCE origin layer; produces DataReading)
  Outputs produced: List<DataReading>   // via FetchRegistry.fetchAll()
  Calibration deps: none (PriceDataIntegrity rules are structural)
  Types consumed:   @see FW_Types.md — FetchSpec, DataReading, FetchRegistry
-->

```
MODULE IntelGathering {

  // ─── DATA REGISTRY ENTRIES (LEGACY — superseded by M18_MarketDataFetch, v2.1) ────────
  // All DATA_REGISTRY_ENTRIES moved to M18_MarketDataFetch.DATA_REGISTRY_ENTRIES (v1.20).
  // M18 is the single source of truth for all structured data series.
  // Block retained here for reference only. FetchRegistry.fetchAll() pulls from M18.

  DATA_REGISTRY_ENTRIES_LEGACY {

    // Energy
    REGISTER FetchSpec { id: "BRENT_CRUDE",     source: WEBSEARCH_T1, description: "Brent crude spot BZ=F — verify against EIA or CME settlement", update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "WTI",             source: WEBSEARCH_T1, description: "WTI crude spot CL=F — verify against EIA or CME settlement",   update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "NATURAL_GAS",     source: WEBSEARCH_T1, description: "Henry Hub natural gas front-month",                            update_frequency: DAILY, acceptable_lag_days: 1 }

    // Safe haven / precious metals
    REGISTER FetchSpec { id: "GOLD_SPOT",       source: WEBSEARCH_T1, description: "Gold spot XAUUSD — verify against LBMA or Kitco",  update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "SILVER",          source: WEBSEARCH_T1, description: "Silver spot XAGUSD — verify against LBMA or Kitco", update_frequency: DAILY, acceptable_lag_days: 1 }

    // Broad equities
    REGISTER FetchSpec { id: "SP500",           source: WEBSEARCH_T1, description: "S&P 500 closing level — NYSE official",            update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "NASDAQ_COMP",     source: WEBSEARCH_T1, description: "NASDAQ Composite closing level — NASDAQ official", update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "DOW",             source: WEBSEARCH_T1, description: "Dow Jones Industrial Average — NYSE official",    update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "RUSSELL2000",     source: WEBSEARCH_T1, description: "Russell 2000 closing level — NYSE official",      update_frequency: DAILY, acceptable_lag_days: 1 }

    // Volatility (current close — trailing averages registered by M14)
    REGISTER FetchSpec { id: "VIX",             source: ALLOCATION_SPREADSHEET_OTHER, description: "VIX current daily close", update_frequency: DAILY, acceptable_lag_days: 1 }

    // Fixed income / rates
    REGISTER FetchSpec { id: "TREASURY_10Y",    source: FRED_SPREADSHEET_TAB, description: "DGS10 — 10-year Treasury yield", update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "TREASURY_2Y",     source: FRED_SPREADSHEET_TAB, description: "DGS2 — 2-year Treasury yield",  update_frequency: DAILY, acceptable_lag_days: 1 }

    // Currency
    REGISTER FetchSpec { id: "DXY",             source: WEBSEARCH_T1, description: "US Dollar Index DX=F", update_frequency: DAILY, acceptable_lag_days: 1 }

    // Inflation breakevens (FRED)
    REGISTER FetchSpec { id: "BREAKEVEN_10Y",   source: FRED_SPREADSHEET_TAB, description: "T10YIE — 10-year breakeven inflation rate", update_frequency: DAILY, acceptable_lag_days: 1 }
    REGISTER FetchSpec { id: "BREAKEVEN_5Y",    source: FRED_SPREADSHEET_TAB, description: "T5YIE — 5-year breakeven inflation rate",  update_frequency: DAILY, acceptable_lag_days: 1 }

    // CPI (monthly release — lag reflects BLS release cadence)
    REGISTER FetchSpec { id: "CPI_YOY",         source: WEBSEARCH_T1, description: "Latest BLS CPI YoY print — check release date",
                                                 update_frequency: MONTHLY, acceptable_lag_days: 35 }

    // Monetary policy
    REGISTER FetchSpec { id: "FED_FUNDS_RATE",  source: FRED_SPREADSHEET_TAB, description: "DFF — effective federal funds rate", update_frequency: DAILY, acceptable_lag_days: 1 }

    // Holdings prices — already in allocation sheet (Step 1); registered for manifest completeness
    REGISTER FetchSpec { id: "HOLDINGS_PRICES", source: GOOGLEFINANCE, description: "Live prices via GOOGLEFINANCE in allocation sheet — no separate fetch needed",
                                                 update_frequency: DAILY, acceptable_lag_days: 0 }
  }


  // ─── QUALITATIVE GATHER LIST ─────────────────────────────────────────────────────────
  // Items requiring open-ended web search + interpretation. Not representable as FetchSpec
  // (no fixed series ID, qualitative output, or inherently interpretive).
  // Gathered in GatherIntel STEP 1 alongside FetchRegistry.fetchAll().
  // Source tier assessed per M01_SourceIntegrity.classify() before use.
  // Outputs are NOT DataReading — they are working inputs to GatherIntel STEPS 2–5.

  QUALITATIVE_GATHER_LIST {
    active_conflict_status:         web_search (T1 preferred) — current conflict zones and status
    escalation_or_deescalation:     web_search — geopolitical signals from last 48h
    breaking_geopolitical_events:   web_search — window: last 48h
    fed_forward_guidance_changes:   web_search — latest Fed statements, press conferences, minutes
    NOTE: "NEVER treat qualitative outputs as DataReading.
           Apply M01_SourceIntegrity.classify() to every item before use in analysis."
  }


  // ─── PRICE DATA INTEGRITY RULE ───────────────────────────────────────────────────────

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
      equities:     [NYSE_official, NASDAQ_official]
      rates:        [treasury.gov, FRED(DGS10, DGS2, T10YIE, T5YIE)]
    }

    IF price_sourced_from: unapproved_source {
      LABEL: 'Unverified price — requires dedicated source confirmation.'
    }

    IF single_instrument_move > 40% OVER any_90d_window {
      CLASSIFY: extraordinary_claim
      REQUIRE: cross_verification from >= 2 dedicated T1_price_sources
                before_entering_digest_as_fact
    }
  }


  // ─── GATHERING PROCEDURE (Steps 1–5) ────────────────────────────────────────────────

  PROCEDURE GatherIntel {

    STEP 1: FetchCurrentData {
      // Phase 2 complete (M18 integration, v2.1): all structured FetchSpecs in M18_MarketDataFetch.
      // M18 is the single registry; FetchRegistry.fetchAll() iterates M18.DATA_REGISTRY_ENTRIES.

      execute_structured:   FetchRegistry.fetchAll()
      // All entries sourced from M18_MarketDataFetch.DATA_REGISTRY_ENTRIES:
      //   Energy: BRENT_CRUDE, WTI, NATURAL_GAS
      //   Metals: GOLD_SPOT, SILVER
      //   Equities: SP500, NASDAQ_COMP, DOW, RUSSELL2000
      //   Volatility: VIX, VIX_30D_AVG, VIX_90D_AVG, MOVE, BROAD_EQUITY_TRAILING
      //   Regional banks: KRE, KBE
      //   Rates: TREASURY_10Y, TREASURY_2Y, YIELD_CURVE, SOFR, DFF, THREEFYTP10,
      //          BREAKEVEN_10Y, BREAKEVEN_5Y
      //   Credit: HY_OAS, CCC_OAS, IG_OAS, BBB_OAS
      //   FX: DXY
      //   Macro: CPI_YOY, FED_FUNDS_RATE
      //   Cascade: FINRA_MARGIN_DEBT, NATGAS_HENRY_HUB, FARM_FILINGS_YOY
      //   Holdings: HOLDINGS_PRICES (from Step 1 allocation sheet fetch)
      // RETURN: List<DataReading>   // @see FW_Types.md

      execute_qualitative:  QUALITATIVE_GATHER_LIST
      // Web searches for: active_conflict_status, escalation_or_deescalation,
      //                   breaking_geopolitical_events, fed_forward_guidance_changes

      REQUIRE: structured_readings.timestamp within acceptable_lag_days for each FetchSpec
      apply:   @see PriceDataIntegrity
      OUTPUT:  List<DataReading>
    }

    STEP 2: ApplySourceIntegrity {
      FOR each significant_claim {
        identify: tier
        check:    propaganda_fingerprints
        determine: T1_corroboration
        classify_as: Verified | Unverified | AdversarialSignal
      }
    }

    STEP 3: EnumerateTransmissionMechanisms {
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
        }
      }
    }

    STEP 4: IdentifyOmissions {
      ACTIVELY_SEEK: what_is_NOT_being_reported
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


  // ─── PRIMARY DRIVER IDENTIFICATION ──────────────────────────────────────────────────

  FUNCTION identifyPrimaryDriver() {
    OUTPUT_FORMAT {
      PRIMARY_DRIVER_ASSESSMENT {
        current_dominant_driver:   [name explicitly]
        evidence:                  [T1 source]
        duration_of_dominance:     [how long this has been primary driver]
        challenger_drivers:        [emerging secondary drivers that could displace it]
        recalibration_trigger_check: Yes | No
      }
    }
  }

}
```
