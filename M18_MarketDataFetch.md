# M18 — Market Data Fetch
<!-- Version: 1.0 | Adopted: May 25, 2026 -->
<!-- Purpose: Centralized financial data retrieval. Single module containing all
     DATA_REGISTRY_ENTRIES for the framework. Replaces the distributed registration
     pattern across M02/M11/M14/M17 with one authoritative source. -->
<!-- Sub-project: DATA_INTELLIGENCE -->
<!-- Reason to change: a new data series is needed, a source changes, or lag tolerance
     changes. NEVER register DATA_REGISTRY_ENTRIES in any other module — add here. -->
<!-- Companion: @see FW_Types.md (FetchSpec, DataReading, DataSource types) -->
<!-- Consumed by: FetchRegistry.fetchAll() — called from M02.GatherIntel STEP 1 -->

<!-- MODULE MANIFEST
  ID:              M18_MarketDataFetch
  Version:         1.0
  Sub-project:     DATA_INTELLIGENCE
  Reason to change: new series added, source changed, lag tolerance changed.
                    NEVER change M02, M11, M14, or M17 to add a data series.
  Inputs consumed:  (none — M18 is a registry; FetchRegistry.fetchAll() pulls from it)
  Outputs produced: List<DataReading>   // via FetchRegistry.fetchAll()
  Calibration deps: none
  Types consumed:   @see FW_Types.md — FetchSpec, DataReading, DataSource, FetchRegistry
-->

```
MODULE MarketDataFetch {

  // ─── PURPOSE ────────────────────────────────────────────────────────────────
  // All DATA_REGISTRY_ENTRIES for the framework live here.
  // M02, M11, M14, M17 no longer register their own FetchSpecs — they reference
  // entry ids produced by M18 and consumed by FetchRegistry.fetchAll().
  //
  // The distributed DATA_REGISTRY_ENTRIES blocks in M02/M11/M14/M17 are superseded.
  // Those modules retain their blocks as _LEGACY comments for traceability.
  //
  // QUALITATIVE_GATHER_LIST: qualitative items (geopolitical, Fed guidance) remain
  // in M02 because they require open-ended interpretation, not structured fetch.
  // They are NOT DataReadings and are NOT registered here.


  // ─── DATA REGISTRY ENTRIES ───────────────────────────────────────────────────
  // All structured data series used by any module in the framework.
  // Registered with FetchRegistry at module load. FetchRegistry.fetchAll() iterates all.
  //
  // Note on series IDs / tickers: stored in description only, not in FetchSpec.id —
  // consistent with existing framework convention (M02, M11, M14, M17 all do this).
  //
  // Source constants (DataSource enum values from FW_Types.md):
  //   FRED_SPREADSHEET_TAB, ALLOCATION_SPREADSHEET_OTHER, ALLOCATION_SPREADSHEET_FINRA,
  //   FMP_ECONOMICS_TREASURY_RATES, GOOGLEFINANCE, WEBSEARCH_T1, WEBSEARCH_T2,
  //   USDA_OR_AFBF, FRED_OR_WEBSEARCH, MANUAL_CLIENT_INPUT

  DATA_REGISTRY_ENTRIES {

    // ── ENERGY ──────────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "BRENT_CRUDE"
      source:              WEBSEARCH_T1
      description:         "Brent crude futures BZ=F — dedicated Yahoo Finance BZ=F page or FMP:quote.
                            NOT Trading Economics CFD (confirmed $3-4 discrepancy May 13, 2026).
                            BZ=F is canonical Brent reference per Calibration_State §2.1 (v1.17)."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M03, M17]
    }

    REGISTER FetchSpec {
      id:                  "WTI"
      source:              WEBSEARCH_T1
      description:         "WTI crude futures CL=F — EIA weekly or CME Group settlement data."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "NATURAL_GAS"
      source:              FRED_OR_WEBSEARCH
      description:         "Henry Hub natural gas front-month — FRED DHHNGSP preferred.
                            ⚠ PERSISTENT DATA GAP: fetch is MANDATORY when CHAIN_1 farm_filings
                            are within 10pp of the 50% threshold. Do not omit silently."
      update_frequency:    DAILY
      acceptable_lag_days: 3
      consumer:            [M02, M17]
      calibration_use:     "CHAIN_1 §12.1: ≥$6.00/mmBtu sustained 30 days"
    }


    // ── PRECIOUS METALS ──────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "GOLD_SPOT"
      source:              GOOGLEFINANCE/WEBSEARCH_T1
      description:         "Gold spot XAUUSD — GOOGLEFINANCE(CURRENCY:XAUUSD) via allocation sheet.
                            Approved fallback: LBMA, Kitco spot."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "SILVER"
      source:              GOOGLEFINANCE/WEBSEARCH_T1
      description:         "Silver spot XAGUSD — GOOGLEFINANCE(CURRENCY:XAGUSD) via allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── BROAD EQUITIES ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "SP500"
      source:              GOOGLEFINANCE
      description:         "S&P 500 Index INDEXSP:.INX — GOOGLEFINANCE via allocation sheet (Other tab).
                            NYSE official closing print as fallback."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M14]
    }

    REGISTER FetchSpec {
      id:                  "NASDAQ_COMP"
      source:              WEBSEARCH_T1
      description:         "NASDAQ Composite — NASDAQ official closing level."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "DOW"
      source:              WEBSEARCH_T1
      description:         "Dow Jones Industrial Average — NYSE official."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "RUSSELL2000"
      source:              WEBSEARCH_T1
      description:         "Russell 2000 — NYSE official closing level."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── VOLATILITY ────────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "VIX"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "VIX current daily close — GOOGLEFINANCE(INDEXCBOE:VIX) via allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M14]
    }

    REGISTER FetchSpec {
      id:                  "VIX_30D_AVG"
      source:              WEBSEARCH_T1
      description:         "VIX 30-day rolling average — CBOE or FRED VIXCLS series."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

    REGISTER FetchSpec {
      id:                  "VIX_90D_AVG"
      source:              WEBSEARCH_T1
      description:         "VIX 90-day rolling average — CBOE or FRED VIXCLS series."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

    REGISTER FetchSpec {
      id:                  "MOVE"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "ICE BofA MOVE Index — GOOGLEFINANCE(INDEXNYSEGIS:MOVE) via allocation sheet.
                            Approved fallback: investing.com/indices/ice-bofaml-move."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11, M02]
      calibration_use:     "Watch level 80. Alert level 100 (accelerate formal M11/M14 integration)."
    }


    // ── REGIONAL BANKS / CASCADE CHAIN EQUITIES ────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "KRE"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "SPDR S&P Regional Banking ETF — GOOGLEFINANCE(KRE) via allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M17]
      calibration_use:     "CHAIN_2 §12.2: KRE vs SPX 90d underperformance ≥ −15pp"
    }

    REGISTER FetchSpec {
      id:                  "KBE"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "SPDR S&P Bank ETF — GOOGLEFINANCE(KBE) via allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M17]
    }


    // ── RATES & YIELD CURVE ────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "TREASURY_10Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "DGS10 — 10-year Treasury yield — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "TREASURY_2Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "DGS2 — 2-year Treasury yield — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "YIELD_CURVE"
      source:              FMP_ECONOMICS_TREASURY_RATES
      description:         "Full US Treasury par yield curve — FMP:economics treasury-rates endpoint.
                            All tenors: 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y.
                            Fallback: treasury.gov Daily Par Yield Curve Rates."
      update_frequency:    DAILY
      acceptable_lag_days: 2
      consumer:            [M17, M02]
    }

    REGISTER FetchSpec {
      id:                  "SOFR"
      source:              FRED_SPREADSHEET_TAB
      description:         "SOFR — Secured Overnight Financing Rate — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 2
      consumer:            [M17, M11]
    }

    REGISTER FetchSpec {
      id:                  "DFF"
      source:              FRED_SPREADSHEET_TAB
      description:         "DFF — Effective Federal Funds Rate — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 2
      consumer:            [M17, M11, M02]
    }

    REGISTER FetchSpec {
      id:                  "THREEFYTP10"
      source:              FRED_SPREADSHEET_TAB
      description:         "THREEFYTP10 — 10-year Treasury term premium (Adrian-Crump-Moench)
                            — FRED tab in allocation sheet."
      update_frequency:    WEEKLY
      acceptable_lag_days: 7
      consumer:            [M17, M02]
      calibration_use:     "§12.5: E_term_premium_warning=100bp; E_term_premium_alert=150bp"
    }

    REGISTER FetchSpec {
      id:                  "BREAKEVEN_10Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "T10YIE — 10-year breakeven inflation rate — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M03]
    }

    REGISTER FetchSpec {
      id:                  "BREAKEVEN_5Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "T5YIE — 5-year breakeven inflation rate — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── CREDIT SPREADS ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "HY_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA US High Yield OAS — BAMLH0A0HYM2 — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
      calibration_use:     "M11 §1.1 HY_STRESS_DELTA and HY_RECESSION_DELTA thresholds"
    }

    REGISTER FetchSpec {
      id:                  "CCC_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA CCC & Lower OAS — BAMLH0A3HYC — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
      calibration_use:     "M11 §1.3 CCC tail divergence signal"
    }

    REGISTER FetchSpec {
      id:                  "IG_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA US IG OAS — BAMLC0A0CM — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
      calibration_use:     "M11 §1.2 IG_TRANSMISSION_DELTA threshold"
    }

    REGISTER FetchSpec {
      id:                  "BBB_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA BBB US Corporate OAS — BAMLC0A4CBBB — FRED tab in allocation sheet."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
    }


    // ── FX ─────────────────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "DXY"
      source:              WEBSEARCH_T1
      description:         "US Dollar Index — investing.com/indices/usdollar or MarketWatch DXY."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
      calibration_use:     "§2.2: DXY ≥105 sustained → SGOL invalidation risk"
    }


    // ── INFLATION & MONETARY POLICY ───────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "CPI_YOY"
      source:              WEBSEARCH_T1
      description:         "Latest BLS CPI YoY print — BLS.gov press release.
                            Current: April 2026 = 3.8% (print 2/3 toward B trigger).
                            Run DeriveScenarioProbabilities() immediately on 8:30am ET release."
      update_frequency:    MONTHLY
      acceptable_lag_days: 35
      consumer:            [M02, M03]
      calibration_use:     "§2.3 B-trigger: ≥4.0% YoY, 3+ consecutive prints"
    }

    REGISTER FetchSpec {
      id:                  "FED_FUNDS_RATE"
      source:              FRED_SPREADSHEET_TAB
      description:         "DFF — effective federal funds rate — FRED tab in allocation sheet.
                            Current: 3.50–3.75% (on hold). Next FOMC: June 16–17, 2026."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M03]
    }


    // ── CASCADE CHAIN STRUCTURAL INPUTS ──────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "FINRA_MARGIN_DEBT"
      source:              ALLOCATION_SPREADSHEET_FINRA
      description:         "FINRA monthly margin debit balances — FINRA tab in allocation sheet.
                            Current: $1.304T (April 2026 — all-time nominal record).
                            CHAIN_3_WATCH = TRUE (record loaded; cascade onset requires ≥−5% MoM decline)."
      update_frequency:    MONTHLY
      acceptable_lag_days: 30
      consumer:            [M17]
      calibration_use:     "CHAIN_3 §12.3 two-mode: WATCH on record; FIRES on ≥−5% MoM or gate_count ≥3"
    }

    REGISTER FetchSpec {
      id:                  "NATGAS_HENRY_HUB"
      source:              FRED_OR_WEBSEARCH/FRED_SPREADSHEET_TAB
      description:         "Henry Hub natural gas spot — FRED DHHNGSP or web search.
                            ⚠ MANDATORY when FARM_FILINGS_YOY within 10pp of threshold.
                            Current: not fetched this session (data gap)."
      update_frequency:    DAILY
      acceptable_lag_days: 3
      consumer:            [M17]
      calibration_use:     "CHAIN_1 §12.1: ≥$6.00/mmBtu sustained 30 days (partial condition)"
    }

    REGISTER FetchSpec {
      id:                  "FARM_FILINGS_YOY"
      source:              USDA_OR_AFBF
      description:         "Chapter 12 farm bankruptcy YoY change — USDA quarterly or AFBF.
                            Current: +46% YoY (2025 data). Borderline CHAIN_1 threshold (+50%)."
      update_frequency:    QUARTERLY
      acceptable_lag_days: 90
      consumer:            [M17]
      calibration_use:     "CHAIN_1 §12.1: ≥+50% YoY (AND natgas or fertilizer threshold)"
    }


    // ── HOLDINGS PRICES ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "HOLDINGS_PRICES"
      source:              GOOGLEFINANCE
      description:         "All client portfolio holding prices — live via GOOGLEFINANCE in allocation sheet.
                            Already available from Step 1 allocation fetch; registered here for manifest
                            completeness only. No separate fetch needed."
      update_frequency:    DAILY
      acceptable_lag_days: 0
      consumer:            [M02, M06, M13]
    }

    REGISTER FetchSpec {
      id:                  "BROAD_EQUITY_TRAILING"
      source:              WEBSEARCH_T1
      description:         "VTI or SPX 30/60/90d trailing pct-change — NYSE/NASDAQ official historical prices."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

  }  // end DATA_REGISTRY_ENTRIES


  // ─── PRICE DATA INTEGRITY RULE ────────────────────────────────────────────────
  // M18 consolidates this guard from M02 (retained in M02 for reference — see M02 diff).

  GUARD PriceDataIntegrity {
    REQUIRE: specific_price_quote sourced_from dedicated_instrument_page
    NEVER: accept_price_from [
      sidebar_widgets,
      tickers_embedded_in_unrelated_articles,
      derivative_aggregators,
      Trading_Economics_CFD_for_BZ=F   // confirmed inaccurate May 13, 2026
    ]

    APPROVED_SOURCES {
      brent_crude:    ["finance.yahoo.com/quote/BZ=F (dedicated page)", "FMP:quote BZ=F", "ICE settlement"]
      wti_crude:      ["EIA weekly", "CME Group settlement data"]
      gold_silver:    ["GOOGLEFINANCE XAUUSD/XAGUSD via allocation sheet", "LBMA", "Kitco spot"]
      equities:       ["GOOGLEFINANCE via allocation sheet", "NYSE official", "NASDAQ official"]
      rates:          ["FRED tab in allocation sheet", "treasury.gov par yield", "FMP:economics"]
      credit_spreads: ["FRED tab in allocation sheet (T1 confirmed May 13, 2026)"]
      MOVE:           ["GOOGLEFINANCE INDEXNYSEGIS:MOVE via allocation sheet",
                       "investing.com/indices/ice-bofaml-move"]
      DXY:            ["investing.com/indices/usdollar", "MarketWatch DXY"]
    }

    IF single_instrument_move > 40% OVER any_90d_window {
      CLASSIFY: extraordinary_claim
      REQUIRE:  >= 2 independent approved_sources before including in analysis
    }
  }


  // ─── NEVER LIST ───────────────────────────────────────────────────────────────

  NEVER {
    register_in_any_other_module:
      "All DATA_REGISTRY_ENTRIES for structured market data live in M18 only.
       M02, M11, M14, M17 DATA_REGISTRY_ENTRIES blocks are superseded by M18.
       Those blocks are retained as _LEGACY for reference only.
       To add a new series: add it here. No other module changes."

    register_qualitative_items_here:
      "QUALITATIVE_GATHER_LIST items (geopolitical, Fed guidance) are not DataReadings.
       They require open-ended interpretation, not structured fetch.
       They remain in M02.QUALITATIVE_GATHER_LIST — not in M18."

    hardcode_series_ticker_in_FetchSpec_id:
      "FetchSpec.id is a logical name (e.g. 'HY_OAS'), not a ticker.
       The actual series code (BAMLH0A0HYM2) lives in FetchSpec.description.
       Consistent with M02/M11/M14/M17 convention."

    skip_NATURAL_GAS_when_CHAIN1_borderline:
      "NATURAL_GAS is a MANDATORY fetch when FARM_FILINGS_YOY is within 10pp of the
       +50% threshold. The data gap in prior sessions is a protocol violation — not
       an acceptable omission. CHAIN_1 scoring is incomplete without it."
  }

}
```
