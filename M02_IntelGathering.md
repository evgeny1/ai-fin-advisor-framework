# M02 — Intelligence Gathering
<!-- Version: 2.3 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M02_IntelGathering
  Version:         2.3
  Sub-project:     DATA_INTELLIGENCE
  Reason to change: core M02-owned data sources change (energy, equities, rates, FX, inflation);
                    OR qualitative gather methodology changes.
                    Adding a new module's structured data: register DATA_REGISTRY_ENTRIES in that
                    module; M02 does not change.
  Inputs consumed:  (none — M02 is the DATA_INTELLIGENCE origin layer; produces DataReading)
  Outputs produced: List<DataReading>   // via FetchRegistry.fetchAll()
  Calibration deps: none (PriceDataIntegrity rules are structural)
  Types consumed:   @see FW_Types.md — FetchSpec, DataReading, FetchRegistry
  Cross-module:     @see M01_SourceIntegrity, @see M03_ScenarioFramework, @see M04_BriefingFormat.
                    DATA_REGISTRY_ENTRIES superseded by M18_MarketDataFetch (extended there by
                    M11, M14, M17, M19 — @see M18 for the full series list).
-->

```
MODULE IntelGathering {

  // DATA_REGISTRY_ENTRIES moved to M18_MarketDataFetch (v2.1). @see M18.

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
    cb_gold_reserve_accumulation:   web_search (T2 acceptable) — central bank gold reserve accumulation
                                     narrative; consumer: M19 (SGOL/SIVR sustaining condition)
    nuclear_policy_trajectory:      web_search (T1 preferred) — nuclear policy support/reversal across
                                     {US, EU, Japan, UK}; consumer: M19 (URA sustaining condition)
    NOTE: "NEVER treat qualitative outputs as DataReading.
           Apply M01_SourceIntegrity.classify() to every item before use in analysis.
           cb_gold_reserve_accumulation and nuclear_policy_trajectory feed M19 Call 2 ScoringQuestions
           only — M19 itself never interprets free text directly. @see M19_ThesisSustainingConditions."
  }


  // ─── PRICE DATA INTEGRITY RULE ───────────────────────────────────────────────────────
  // ⚠ SUPERSEDED by M18_MarketDataFetch.PriceDataIntegrity (v1.2, June 4, 2026).
  // This block is retained for reference only. M18 is authoritative for:
  //   - Approved source hierarchy (YFINANCE_MCP → FMP → FRED → allocation sheet → screenshot)
  //   - HARD_GATE NoWebSearchForPriceData (web search prohibited for all price/return/level data)
  //   - AllocationPriceCrossCheck (>5% discrepancy between yfinance and allocation sheet = HALT)
  //   - FMP_PLAN_TIER_MAP (confirmed working vs ACCESS DENIED endpoints at current plan tier)
  // @see M18_MarketDataFetch.PriceDataIntegrity
  // @see M18_MarketDataFetch.HARD_GATE NoWebSearchForPriceData
  // @see M18_MarketDataFetch.AllocationPriceCrossCheck

  GUARD PriceDataIntegrity {
    // LEGACY — apply M18 rules instead. Structural principles below remain valid.
    REQUIRE: specific_price_quote sourced_from dedicated_instrument_page
    NEVER:   accept_price_from [
      sidebar_widgets,
      tickers_embedded_in_unrelated_articles,
      derivative_aggregators
    ]

    // APPROVED_SOURCES below are OUTDATED — use M18.PriceDataIntegrity.APPROVED_SOURCES.
    // Primary sources now: YFINANCE_MCP (market_get_quotes / market_get_macro / market_get_history),
    //   FMP_COMMODITY (BZUSD/GCUSD/SIUSD), FMP_INDEXES (^VIX/^GSPC).
    // Web search is PROHIBITED for price/return/level data — see M18 HARD_GATE.
    APPROVED_SOURCES_LEGACY {
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
      // All entries from M18_MarketDataFetch.DATA_REGISTRY_ENTRIES. @see M18.
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
