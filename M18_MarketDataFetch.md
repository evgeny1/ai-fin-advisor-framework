# M18 — Market Data Fetch
<!-- Version: 1.1 | Adopted: May 25, 2026 | Updated: May 26, 2026 -->
<!-- Changes v1.1: VIX_30D_AVG and VIX_90D_AVG source changed from WEBSEARCH_T1 to FMP_CHART
     (confirmed working May 26 — FMP:chart historical-price-eod-light ^VIX with 90-day date
     range returns full EOD array; averages computed from returned data).
     BROAD_EQUITY_TRAILING source changed from WEBSEARCH_T1 to FMP_CHART; symbol specified
     as SPY (FMP:indexes ^SPX requires higher plan tier — confirmed ACCESS DENIED May 26;
     SPY via FMP:chart is the confirmed working substitute).
     APPROVED_SOURCES block updated with FMP entries and plan-tier caveat. -->
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
  Version:         1.1
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


  // ─── DATA SOURCE CONSTANTS ────────────────────────────────────────────────────
  // DataSource enum values used in FetchSpec.source fields below.
  // These must match the DataSource enum defined in FW_Types.md.
  //
  //   FRED_SPREADSHEET_TAB        — FRED series embedded in allocation spreadsheet tab.
  //                                 T1. Available at session Step 1 allocation fetch.
  //                                 ⚠ Returns only the rows visible in the tab; long
  //                                 historical series may be present but only the most
  //                                 recent ~5 rows are reliably surfaced in read_file_content
  //                                 output. For 180d median computation use the full tab.
  //
  //   ALLOCATION_SPREADSHEET_OTHER — Non-FRED data in the allocation sheet "Other Indexes"
  //                                  tab (VIX, S&P 500, MOVE, KRE, KBE, XLY via
  //                                  GOOGLEFINANCE). T1 (live, ~20-min delay).
  //
  //   ALLOCATION_SPREADSHEET_FINRA — FINRA margin statistics tab in allocation sheet.
  //                                  T1 (monthly update, sourced from FINRA.org).
  //
  //   FMP_CHART                   — FMP:chart MCP tool. historical-price-eod-light endpoint.
  //                                 Accepts symbol + from_date/to_date. Returns EOD array
  //                                 newest-first. Used to compute rolling averages.
  //                                 ⚠ PLAN TIER NOTE: FMP:indexes ^SPX requires higher
  //                                 plan tier (ACCESS DENIED confirmed May 26, 2026).
  //                                 Use SPY (ETF) via FMP:chart as confirmed substitute
  //                                 for broad equity trailing return computation.
  //                                 FMP:chart ^VIX confirmed working at current plan tier.
  //
  //   FMP_ECONOMICS_TREASURY_RATES — FMP:economics treasury-rates endpoint. Full US par
  //                                  yield curve all tenors. Confirmed working.
  //
  //   FMP_COMMODITY               — FMP:commodity MCP tool. For commodity quotes/history.
  //                                 Not yet confirmed for BZ=F at current plan tier — verify
  //                                 before adopting as primary Brent source.
  //
  //   GOOGLEFINANCE               — GOOGLEFINANCE formula in allocation sheet. Live, ~20-min
  //                                 delay. Available at Step 1 allocation fetch.
  //
  //   WEBSEARCH_T1                — Structured web search targeting a named primary source.
  //                                 Use only when FMP and spreadsheet sources are unavailable.
  //
  //   WEBSEARCH_T2                — Web search with uncertain provenance. Flag explicitly.
  //
  //   USDA_OR_AFBF                — USDA quarterly report or AFBF (American Farm Bureau
  //                                 Federation). Quarterly cadence.
  //
  //   FRED_OR_WEBSEARCH           — FRED preferred; web search fallback if FRED unavailable.
  //
  //   MANUAL_CLIENT_INPUT         — Client-provided value (e.g. confirmed T2 screenshot).


  // ─── DATA REGISTRY ENTRIES ───────────────────────────────────────────────────
  // All structured data series used by any module in the framework.
  // Registered with FetchRegistry at module load. FetchRegistry.fetchAll() iterates all.
  //
  // Note on series IDs / tickers: stored in description only, not in FetchSpec.id —
  // consistent with existing framework convention (M02, M11, M14, M17 all do this).

  DATA_REGISTRY_ENTRIES {

    // ── ENERGY ──────────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "BRENT_CRUDE"
      source:              WEBSEARCH_T1
      description:         "Brent crude futures BZ=F — dedicated Yahoo Finance BZ=F page
                            (finance.yahoo.com/quote/BZ=F) as primary approved source.
                            NOT Trading Economics CFD (confirmed $3-4 discrepancy May 13, 2026).
                            BZ=F is canonical Brent reference per Calibration_State §2.1 (v1.17).
                            FMP:commodity BZUSD not yet confirmed at current plan tier — verify
                            at Q2 audit; if confirmed, upgrade source to FMP_COMMODITY."
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
      description:         "Henry Hub natural gas front-month — FRED DHHNGSP preferred
                            (embedded in allocation spreadsheet FRED tab; typically 3-5 day lag).
                            Web search fallback: Google Finance NGM26/NGN26 futures.
                            ⚠ MANDATORY fetch when FARM_FILINGS_YOY within 10pp of the
                            +50% threshold (currently +46% — MANDATORY every session).
                            Do not omit silently."
      update_frequency:    DAILY
      acceptable_lag_days: 3
      consumer:            [M02, M17]
      calibration_use:     "CHAIN_1 §12.1: ≥$6.00/mmBtu sustained 30 days"
    }


    // ── PRECIOUS METALS ──────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "GOLD_SPOT"
      source:              GOOGLEFINANCE
      description:         "Gold spot XAUUSD — GOOGLEFINANCE(CURRENCY:XAUUSD) via allocation
                            sheet Other Indexes tab. Approved fallback: LBMA, Kitco spot."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "SILVER"
      source:              GOOGLEFINANCE
      description:         "Silver spot XAGUSD — GOOGLEFINANCE(CURRENCY:XAGUSD) via allocation
                            sheet Other Indexes tab."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── BROAD EQUITIES ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "SP500"
      source:              GOOGLEFINANCE
      description:         "S&P 500 Index INDEXSP:.INX — GOOGLEFINANCE via allocation sheet
                            Other Indexes tab. NYSE official closing print as fallback."
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
      description:         "VIX current daily close — GOOGLEFINANCE(INDEXCBOE:VIX) via
                            allocation sheet Other Indexes tab."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M14]
    }

    REGISTER FetchSpec {
      id:                  "VIX_30D_AVG"
      source:              FMP_CHART
      description:         "VIX 30-day rolling average — computed from FMP:chart
                            historical-price-eod-light ^VIX with from_date = 30 trading
                            days prior to current session date.
                            Confirmed working at current FMP plan tier (May 26, 2026).
                            Computation: sum(close[0..29]) / 30 from returned EOD array
                            (array is newest-first; index 0 = most recent close).
                            Fallback: FRED VIXCLS series if FMP unavailable.
                            Session result (May 26): VIX_30D_AVG = 17.99 (Apr 13–May 22)."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

    REGISTER FetchSpec {
      id:                  "VIX_90D_AVG"
      source:              FMP_CHART
      description:         "VIX 90-day rolling average — computed from FMP:chart
                            historical-price-eod-light ^VIX with from_date = 90 calendar
                            days prior to current session date (≈ 62 trading days).
                            Confirmed working at current FMP plan tier (May 26, 2026).
                            Computation: sum(all returned closes) / count from EOD array.
                            Also used to derive VIX_change_90d_pts for M14 divergence signal:
                            VIX_change_90d_pts = close[0] − close[last_index].
                            Fallback: FRED VIXCLS series if FMP unavailable.
                            Session result (May 26): VIX_90D_AVG = 21.24;
                            VIX_change_90d_pts = 16.70 − 17.93 = −1.23 pts."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

    REGISTER FetchSpec {
      id:                  "MOVE"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "ICE BofA MOVE Index — GOOGLEFINANCE(INDEXNYSEGIS:MOVE) via
                            allocation sheet Other Indexes tab.
                            Approved fallback: investing.com/indices/ice-bofaml-move."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11, M02]
      calibration_use:     "Watch level 80. Alert level 100 (accelerate formal M11/M14
                            integration). Formal threshold TBD at Q2 audit."
    }


    // ── REGIONAL BANKS / CASCADE CHAIN EQUITIES ────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "KRE"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "SPDR S&P Regional Banking ETF — GOOGLEFINANCE(KRE) via
                            allocation sheet Other Indexes tab."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M17]
      calibration_use:     "CHAIN_2 §12.2: KRE vs SPX 90d underperformance ≥ −15pp"
    }

    REGISTER FetchSpec {
      id:                  "KBE"
      source:              ALLOCATION_SPREADSHEET_OTHER
      description:         "SPDR S&P Bank ETF — GOOGLEFINANCE(KBE) via allocation sheet
                            Other Indexes tab."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M17]
    }


    // ── RATES & YIELD CURVE ────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "TREASURY_10Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "DGS10 — 10-year Treasury yield — FRED tab in allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26,
                            2026 — tab may not exist). Add DGS10 GOOGLEFINANCE formula or
                            FRED tab at Q2 audit. Until confirmed: obtain from YIELD_CURVE
                            FMP fetch (10Y tenor) or web search fallback."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "TREASURY_2Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "DGS2 — 2-year Treasury yield — FRED tab in allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26,
                            2026). Add at Q2 audit. Until confirmed: obtain from YIELD_CURVE
                            FMP fetch (2Y tenor) or web search fallback."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "YIELD_CURVE"
      source:              FMP_ECONOMICS_TREASURY_RATES
      description:         "Full US Treasury par yield curve — FMP:economics treasury-rates
                            endpoint. All tenors: 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y,
                            20Y, 30Y. Confirmed working at current FMP plan tier.
                            Fallback: treasury.gov Daily Par Yield Curve Rates.
                            Derives: TREASURY_10Y, TREASURY_2Y, 10Y-2Y spread,
                            10Y-3M spread, 30Y yield (all readable from this single fetch)."
      update_frequency:    DAILY
      acceptable_lag_days: 2
      consumer:            [M17, M02]
    }

    REGISTER FetchSpec {
      id:                  "SOFR"
      source:              FRED_SPREADSHEET_TAB
      description:         "SOFR — Secured Overnight Financing Rate — FRED tab in
                            allocation sheet. Confirmed present (May 26: 3.51%)."
      update_frequency:    DAILY
      acceptable_lag_days: 2
      consumer:            [M17, M11]
    }

    REGISTER FetchSpec {
      id:                  "DFF"
      source:              FRED_SPREADSHEET_TAB
      description:         "DFF — Effective Federal Funds Rate — FRED tab in allocation
                            sheet. Confirmed present (May 26: 3.62%)."
      update_frequency:    DAILY
      acceptable_lag_days: 2
      consumer:            [M17, M11, M02]
    }

    REGISTER FetchSpec {
      id:                  "THREEFYTP10"
      source:              FRED_SPREADSHEET_TAB
      description:         "THREEFYTP10 — 10-year Treasury term premium (Adrian-Crump-Moench)
                            — FRED tab in allocation sheet. Confirmed present (May 15: 0.8117%).
                            Weekly cadence — acceptable_lag_days reflects this."
      update_frequency:    WEEKLY
      acceptable_lag_days: 7
      consumer:            [M17, M02]
      calibration_use:     "§12.5: E_term_premium_warning=100bp; E_term_premium_alert=150bp"
    }

    REGISTER FetchSpec {
      id:                  "BREAKEVEN_10Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "T10YIE — 10-year breakeven inflation rate — FRED tab in
                            allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26,
                            2026). Add at Q2 audit. Until confirmed: web search fallback
                            (FRED T10YIE series page)."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M03]
    }

    REGISTER FetchSpec {
      id:                  "BREAKEVEN_5Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "T5YIE — 5-year breakeven inflation rate — FRED tab in
                            allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26,
                            2026). Add at Q2 audit. Until confirmed: web search fallback."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── CREDIT SPREADS ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "HY_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA US High Yield OAS — BAMLH0A0HYM2 — FRED tab in
                            allocation sheet. Confirmed T1 source since May 13, 2026."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
      calibration_use:     "M11 §1.1 HY_STRESS_DELTA and HY_RECESSION_DELTA thresholds"
    }

    REGISTER FetchSpec {
      id:                  "CCC_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA CCC & Lower OAS — BAMLH0A3HYC — FRED tab in
                            allocation sheet. Confirmed T1 source since May 13, 2026."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
      calibration_use:     "M11 §1.3 CCC tail divergence signal"
    }

    REGISTER FetchSpec {
      id:                  "IG_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA US IG OAS — BAMLC0A0CM — FRED tab in allocation
                            sheet. Confirmed T1 source since May 13, 2026."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
      calibration_use:     "M11 §1.2 IG_TRANSMISSION_DELTA threshold"
    }

    REGISTER FetchSpec {
      id:                  "BBB_OAS"
      source:              FRED_SPREADSHEET_TAB
      description:         "ICE BofA BBB US Corporate OAS — BAMLC0A4CBBB — FRED tab in
                            allocation sheet. Confirmed present (May 21: 0.94%)."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11]
    }


    // ── FX ─────────────────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "DXY"
      source:              WEBSEARCH_T1
      description:         "US Dollar Index — investing.com/indices/usdollar or MarketWatch DXY.
                            ⚠ NOT YET IN ALLOCATION SPREADSHEET (as of May 26, 2026).
                            Add GOOGLEFINANCE(CURRENCY:USDEUR) proxy or dedicated DXY tab
                            at Q2 audit. Until confirmed: WEBSEARCH_T1."
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
                            Current: April 2026 = 3.8% YoY (print 2/3 toward B trigger).
                            Next print: mid-June 2026 (May data). Run
                            DeriveScenarioProbabilities() immediately on 8:30am ET release."
      update_frequency:    MONTHLY
      acceptable_lag_days: 35
      consumer:            [M02, M03]
      calibration_use:     "§2.3 B-trigger: ≥4.0% YoY, 3+ consecutive prints"
    }

    REGISTER FetchSpec {
      id:                  "FED_FUNDS_RATE"
      source:              FRED_SPREADSHEET_TAB
      description:         "DFF — effective federal funds rate — FRED tab in allocation sheet.
                            Current: 3.50–3.75% (on hold). Kevin Warsh confirmed as Fed Chair
                            May 22, 2026. Next FOMC: June 16–17, 2026."
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
                            CHAIN_3_WATCH = TRUE (record loaded; cascade onset requires
                            ≥−5% MoM decline or ≥3 gate events)."
      update_frequency:    MONTHLY
      acceptable_lag_days: 30
      consumer:            [M17]
      calibration_use:     "CHAIN_3 §12.3 two-mode: WATCH on record; FIRES on ≥−5% MoM
                            or gate_count ≥3"
    }

    REGISTER FetchSpec {
      id:                  "NATGAS_HENRY_HUB"
      source:              FRED_OR_WEBSEARCH
      description:         "Henry Hub natural gas spot — FRED DHHNGSP (embedded in allocation
                            spreadsheet FRED tab; ~3-5 day lag) or Google Finance NGM26/NGN26
                            futures as current proxy.
                            ⚠ MANDATORY when FARM_FILINGS_YOY within 10pp of +50% threshold.
                            Current FARM_FILINGS_YOY = +46% — MANDATORY every session.
                            Session result (May 26): $2.71–$2.85/mmBtu (front-month futures).
                            Well below $6 CHAIN_1 threshold."
      update_frequency:    DAILY
      acceptable_lag_days: 3
      consumer:            [M17]
      calibration_use:     "CHAIN_1 §12.1: ≥$6.00/mmBtu sustained 30 days (partial condition)"
    }

    REGISTER FetchSpec {
      id:                  "FARM_FILINGS_YOY"
      source:              USDA_OR_AFBF
      description:         "Chapter 12 farm bankruptcy YoY change — USDA quarterly or AFBF.
                            Current: +46% YoY (2025 data). Borderline CHAIN_1 threshold (+50%).
                            Next USDA quarterly update may cross threshold — watch."
      update_frequency:    QUARTERLY
      acceptable_lag_days: 90
      consumer:            [M17]
      calibration_use:     "CHAIN_1 §12.1: ≥+50% YoY (AND natgas or fertilizer threshold)"
    }


    // ── HOLDINGS PRICES ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "HOLDINGS_PRICES"
      source:              GOOGLEFINANCE
      description:         "All client portfolio holding prices — live via GOOGLEFINANCE in
                            allocation sheet. Already available from Step 1 allocation fetch;
                            registered here for manifest completeness only. No separate fetch
                            needed."
      update_frequency:    DAILY
      acceptable_lag_days: 0
      consumer:            [M02, M06, M13]
    }

    REGISTER FetchSpec {
      id:                  "BROAD_EQUITY_TRAILING"
      source:              FMP_CHART
      description:         "SPY (SPDR S&P 500 ETF) 30-day and 90-day trailing pct-change —
                            computed from FMP:chart historical-price-eod-light SPY with
                            from_date = 90 calendar days prior to session date.
                            Confirmed working at current FMP plan tier (May 26, 2026).
                            ⚠ PLAN TIER NOTE: FMP:indexes ^SPX requires higher tier
                            (ACCESS DENIED confirmed May 26, 2026). SPY is the confirmed
                            working substitute.
                            Computation:
                              30d_return = (close[0] − close[30_trading_days_back]) / close[30_trading_days_back]
                              90d_return = (close[0] − close[last_index]) / close[last_index]
                            Note: index 0 in FMP response = most recent close.
                            Count back 30 trading days manually from the returned array.
                            Session result (May 26): 30-trading-day return = +8.68%
                            (SPY Apr 13→May 22: 686.10→745.64).
                            Fallback: NYSE/NASDAQ official historical prices via WEBSEARCH_T1."
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
      brent_crude:           ["finance.yahoo.com/quote/BZ=F (dedicated page)",
                              "ICE settlement (ICE.com official daily settlement prices)",
                              "FMP:commodity BZUSD — NOT YET CONFIRMED at current plan tier;
                               verify before adopting"]
      wti_crude:             ["EIA weekly", "CME Group settlement data"]
      gold_silver:           ["GOOGLEFINANCE XAUUSD/XAGUSD via allocation sheet",
                              "LBMA", "Kitco spot"]
      equities_spot:         ["GOOGLEFINANCE via allocation sheet", "NYSE official",
                              "NASDAQ official"]
      equities_historical:   ["FMP:chart historical-price-eod-light (confirmed working
                               for SPY and ^VIX at current plan tier)",
                              "NYSE/NASDAQ official historical prices"]
      broad_equity_index:    ["SPY via FMP:chart (confirmed working)",
                              "NOTE: FMP:indexes ^SPX requires higher plan tier —
                               ACCESS DENIED confirmed May 26, 2026"]
      rates:                 ["FRED tab in allocation sheet (T1 confirmed May 13, 2026)",
                              "treasury.gov par yield", "FMP:economics treasury-rates
                               (confirmed working at current plan tier)"]
      credit_spreads:        ["FRED tab in allocation sheet (T1 confirmed May 13, 2026)"]
      MOVE:                  ["GOOGLEFINANCE INDEXNYSEGIS:MOVE via allocation sheet",
                              "investing.com/indices/ice-bofaml-move"]
      DXY:                   ["investing.com/indices/usdollar", "MarketWatch DXY",
                              "NOTE: not yet in allocation spreadsheet — add at Q2 audit"]
      VIX_trailing_avg:      ["FMP:chart historical-price-eod-light ^VIX (confirmed working)"]
      natural_gas:           ["FRED DHHNGSP tab in allocation sheet",
                              "Google Finance NGM26/NGN26 futures as current proxy"]
    }

    IF single_instrument_move > 40% OVER any_90d_window {
      CLASSIFY: extraordinary_claim
      REQUIRE:  >= 2 independent approved_sources before including in analysis
    }
  }


  // ─── ALLOCATION SPREADSHEET TAB STATUS ────────────────────────────────────────
  // Current confirmed state of allocation spreadsheet tabs (as of May 26, 2026).
  // Update at each Q-end audit when new tabs are added.
  //
  // read_file_content returns all tab content in a single flattened text blob.
  // Tab headers are not consistently surfaced as separators in the output —
  // identify tab content by the FRED series codes (e.g. "BAMLH0A0HYM2") or
  // GOOGLEFINANCE ticker names visible in cell content.
  //
  // ⚠ KNOWN ISSUE: Long historical FRED series (e.g. BAMLC0A0CM going back to 2023)
  // consume significant context window tokens. A "Session Summary" tab containing
  // only the most recent 5 values per series would make session fetches faster
  // and more reliable. Add at Q2 audit (see §5 item in Calibration_State).

  ALLOCATION_SPREADSHEET_TABS {
    TAB "Main Allocation" {
      confirmed:     true
      content:       "Account blocks (all 6 accounts), combined summaries,
                      account parameters table, tax lot summary"
      series_ids:    [HOLDINGS_PRICES]
    }

    TAB "FRED Series" {
      confirmed:     true
      content:       "BAMLH0A0HYM2 (HY_OAS), BAMLC0A0CM (IG_OAS),
                      BAMLH0A3HYC (CCC_OAS), BAMLC0A4CBBB (BBB_OAS),
                      BAMLH0A1HYBB (BB_OAS), BAMLH0A2HYB (HY_B_OAS),
                      SOFR, DFF, THREEFYTP10, DHHNGSP (NATGAS)"
      series_ids:    [HY_OAS, IG_OAS, CCC_OAS, BBB_OAS, SOFR, DFF,
                      THREEFYTP10, NATGAS_HENRY_HUB]
      known_gap:     "Long historical series (3+ years) included — wasteful for sessions.
                      Add Session Summary tab at Q2 to surface only most-recent values."
    }

    TAB "FINRA Statistics" {
      confirmed:     true
      content:       "FINRA monthly margin debit balances (FINRA_MARGIN_DEBT)"
      series_ids:    [FINRA_MARGIN_DEBT]
    }

    TAB "Other Indexes" {
      confirmed:     true
      content:       "INDEXCBOE:VIX (VIX), INDEXSP:.INX (SP500),
                      INDEXNYSEGIS:MOVE (MOVE), KRE, KBE, XLY"
      series_ids:    [VIX, SP500, MOVE, KRE, KBE]
    }

    TAB "Session Summary" {
      confirmed:     false
      status:        "NOT YET CREATED — add at Q2 audit (June 30, 2026)"
      proposed_content: "Most recent value + last 5 data points for each M18 series.
                         Eliminates need to scan long historical series at session start.
                         Would reduce context token usage and clarify which series are
                         present vs absent."
    }

    SERIES_NOT_YET_IN_SPREADSHEET {
      // These are registered in M18 but not yet confirmed in the allocation spreadsheet.
      // Source falls back to WEBSEARCH_T1 or FMP until confirmed added.
      // ADD ALL at Q2 audit (June 30, 2026):
      missing: [
        "DGS10 (TREASURY_10Y)",
        "DGS2 (TREASURY_2Y)",
        "T10YIE (BREAKEVEN_10Y)",
        "T5YIE (BREAKEVEN_5Y)",
        "DXY (US Dollar Index)",
        "NASDAQ Composite",
        "Dow Jones Industrial Average",
        "Russell 2000"
      ]
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
       +50% threshold. Currently +46% — MANDATORY every session. Omitting it
       is a protocol violation. CHAIN_1 scoring is incomplete without it."

    use_SPX_index_via_FMP_indexes:
      "FMP:indexes endpoint for ^SPX requires higher plan tier — ACCESS DENIED confirmed
       May 26, 2026. Always use SPY via FMP:chart as the confirmed working substitute
       for BROAD_EQUITY_TRAILING computation. Do not retry FMP:indexes ^SPX."

    assume_allocation_tab_content_without_verifying:
      "The allocation spreadsheet has known series gaps (DGS10, DGS2, T10YIE, T5YIE,
       DXY, NASDAQ, DOW, Russell 2000 not yet confirmed present). If a series is absent
       from read_file_content output, fall back to the registered fallback source — do
       not assume the data simply was not surfaced. Distinguish: (a) tab exists but
       content not visible in flattened output vs (b) tab does not exist yet."
  }

}
```
