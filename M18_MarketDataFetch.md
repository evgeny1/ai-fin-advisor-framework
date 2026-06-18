# M18 — Market Data Fetch
<!-- Version: 1.4 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M18_MarketDataFetch
  Version:         1.4
  Sub-project:     DATA_INTELLIGENCE
  Reason to change: new series added, source changed, or lag tolerance changed.
                    NEVER register DATA_REGISTRY_ENTRIES in any other module — add here only;
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
  //                                  Used as T1 crosscheck gate — see ALLOCATION_PRICE_CROSSCHECK.
  //
  //   ALLOCATION_SPREADSHEET_FINRA — FINRA margin statistics tab in allocation sheet.
  //                                  T1 (monthly update, sourced from FINRA.org).
  //
  //   YFINANCE_MCP                — market_data MCP server (yfinance). Four tools:
  //                                 market_get_quotes  — current price + day change
  //                                 market_get_ytd     — YTD return (Dec 31 base)
  //                                 market_get_history — daily closes, any date range/period
  //                                 market_get_macro   — DXY, MOVE, VIX, SP500, KRE, KBE
  //                                 Server file: dev/market_data_mcp/server.py
  //                                 Instrument list: instruments.json (same dir)
  //                                 Confirmed working June 4, 2026: all portfolio instruments
  //                                 + DX-Y.NYB (DXY), ^MOVE (MOVE), ^VIX, ^GSPC, KRE, KBE.
  //
  //   FMP_CHART                   — FMP:chart MCP tool. historical-price-eod-light endpoint.
  //                                 Accepts symbol + from_date/to_date. Returns EOD array
  //                                 newest-first. Used to compute rolling averages.
  //                                 Confirmed working: ^VIX, SPY at current plan tier.
  //
  //   FMP_ECONOMICS_TREASURY_RATES — FMP:economics treasury-rates endpoint. Full US par
  //                                  yield curve all tenors. Confirmed working.
  //
  //   FMP_COMMODITY               — FMP:commodity MCP tool. Confirmed working free tier
  //                                 June 4, 2026: BZUSD (Brent $95.24), GCUSD (Gold $4504),
  //                                 SIUSD (Silver $74.16), commodities-quote endpoint.
  //
  //   FMP_INDEXES                 — FMP:indexes MCP tool. Confirmed working free tier
  //                                 June 4, 2026: ^VIX ($15.40), ^GSPC ($7584.82).
  //                                 ⚠ ACCESS DENIED: ^MOVE, ^SPX, DX-Y.NYB, all forex indexes.
  //                                 Use YFINANCE_MCP for blocked symbols.
  //
  //   GOOGLEFINANCE               — GOOGLEFINANCE formula in allocation sheet. Live, ~20-min
  //                                 delay. T1 crosscheck gate for holdings prices.
  //
  //   WEBSEARCH_T1                — Structured web search targeting a named primary source.
  //                                 ⚠ PROHIBITED for price, return, index level, and yield data.
  //                                 Permitted only for: qualitative macro narrative, CPI/BLS
  //                                 official press release text, FOMC statements, geopolitical
  //                                 events. See HARD_GATE NoWebSearchForPriceData.
  //
  //   WEBSEARCH_T2                — Web search with uncertain provenance. Flag explicitly.
  //                                 PROHIBITED for any numerical framework input.
  //
  //   USDA_OR_AFBF                — USDA quarterly report or AFBF (American Farm Bureau
  //                                 Federation). Quarterly cadence.
  //
  //   FRED_OR_WEBSEARCH           — FRED preferred; web search fallback if FRED unavailable.
  //                                 Only for series where the web search targets an official
  //                                 government statistical publication (not price aggregators).
  //
  //   MANUAL_CLIENT_INPUT         — Client-provided value (e.g. confirmed screenshot).


  // ─── DATA REGISTRY ENTRIES ───────────────────────────────────────
  // SUPERSEDED (confirmed during ENG-2 module necessity review, 2026-06-18).
  // Every FetchSpec entry is now registered in Python only:
  //   @see python/advisor/data/m18_registry.py
  // Python is the operative source — FetchRegistry.fetchAll() reads from it.
  // M18.md is no longer the authoritative source for individual series entries.
  //
  // To add a new series: add a FetchSpec block to m18_registry.py. Do NOT
  // re-add a REGISTER FetchSpec block here — the NEVER rule below still governs
  // which FILE owns entries; it has always meant Python m18_registry.py in practice.
  //
  // SERIES IN PYTHON REGISTRY (as of 2026-06-18):
  //   ENERGY:           BRENT_CRUDE, WTI, NATURAL_GAS
  //   METALS:           GOLD_SPOT, SILVER, COPPER_SPOT (*), URANIUM_SPOT (*)
  //   EQUITIES:         SP500, NASDAQ_COMP, DOW, RUSSELL2000
  //   VOLATILITY:       VIX, VIX_30D_AVG, VIX_90D_AVG, MOVE
  //   BANKS:            KRE, KBE
  //   RATES/CURVE:      YIELD_CURVE, SOFR, DFF, THREEFYTP10
  //   CREDIT:           HY_OAS, IG_OAS, CCC_OAS, BBB_OAS
  //   FX:               DXY
  //   INFLATION/POLICY: CPI_YOY, CHINA_PMI_MANUFACTURING (*)
  //   CASCADE INPUTS:   FINRA_MARGIN_DEBT, NATGAS_HENRY_HUB, FARM_FILINGS_YOY
  //   HOLDINGS:         HOLDINGS_PRICES, BROAD_EQUITY_TRAILING,
  //                     HISTORICAL_INSTRUMENT_PRICES
  //
  // (*) = entries added to m18_registry.py during M19 implementation; were not
  //       registered in M18.md. The Calibration_State.md "pending M18 registration"
  //       notes on COPX/URA are now resolved by this pointer (doc-cleanup complete).
  //
  // NOTE ON SOURCES: m18_registry.py uses DataSource.YFINANCE as primary for most
  // series because the standalone FMP API key returns 403 for most FMP endpoints.
  // M18.md historically showed FMP as primary (FMP MCP connector uses a higher-tier
  // account). The FMP_PLAN_TIER_MAP section below is still accurate for Claude
  // advisory sessions using the FMP MCP connector directly; it is NOT accurate for
  // Python advisor_run_computation() calls (which use standalone key).




  // ─── HARD GATE: NO WEB SEARCH FOR PRICE DATA ─────────────────────────────────
  // Adopted: v1.2, June 4, 2026
  // Trigger incident: financecharts.com T3 artifact (June 3, 2026) — stale -6% YTD
  // figure used as basis for return table validation when actual was +3.73%.
  // Root cause: WEBSEARCH_T1 listed as valid source for price series when
  // FMP/YFINANCE_MCP paths existed but were not required.

  HARD_GATE NoWebSearchForPriceData {

    SCOPE {
      // Applies to any DataReading where the value is:
      applies_when: data_type IN [
        instrument_price,        // stocks, ETFs, commodities, currencies
        instrument_return,       // YTD, 30d, 90d, period returns
        index_level,             // VIX, MOVE, DXY, S&P 500, etc.
        futures_price,           // oil, gas, metals
        yield_level,             // Treasury yields (when not from official publication)
        credit_spread            // HY, IG, CCC OAS
      ]
      does_not_apply_to: [
        cpi_bls_official_press_release,    // CPI: BLS.gov publication (T1 official stats)
        usda_farm_reports,                 // USDA quarterly official statistics
        fomc_statements_and_guidance,      // Fed official communications
        geopolitical_narrative,            // qualitative M02 items
        fred_series_official_page          // FRED.stlouisfed.org for statistical series
                                           //   (breakevens, term premium — not market prices)
      ]
    }

    APPROVED_SOURCE_HIERARCHY {
      // Use the first available source for each series. Do not skip to a lower tier
      // because a higher-tier source requires more calls.
      1: YFINANCE_MCP           // market_get_quotes, market_get_ytd, market_get_history,
                                //   market_get_macro — confirmed all series June 4, 2026
      2: FMP_COMMODITY          // BZUSD, GCUSD, SIUSD — confirmed free tier
      3: FMP_INDEXES            // ^VIX, ^GSPC — confirmed free tier; ^MOVE blocked
      4: FMP_CHART              // historical EOD: ^VIX, SPY — confirmed free tier
      5: FMP_ECONOMICS          // treasury-rates (yield curve) — confirmed free tier
      6: FRED_SPREADSHEET_TAB   // credit spreads, DFF, SOFR, THREEFYTP10, NATGAS
      7: ALLOCATION_SPREADSHEET_OTHER  // VIX, MOVE, KRE, KBE, SP500 via GOOGLEFINANCE
      8: GOOGLEFINANCE          // holdings prices (~20-min delay; use as crosscheck)
      9: MANUAL_CLIENT_INPUT    // Schwab screenshot — always T1; final fallback
    }

    PROHIBITED {
      NEVER: web_search         // for any value in SCOPE above
      NEVER: web_fetch_to_article  // financial news pages, aggregators, chart sites
      REASON: "Narrative sentences from financial aggregators are T3 regardless of
               the underlying site's reputation. A sentence is not a number.
               Aggregators cache return figures on unknown schedules — stale data
               passes no validity check. The incident that created this rule:
               financecharts.com returned -6% YTD for MAGS when actual was +3.73%,
               the figure was ~10pp wrong, and it passed undetected into analysis."
    }

    WHEN_ALL_APPROVED_SOURCES_FAIL {
      action:  REQUEST_CLIENT_SCREENSHOT
      message: "⚠ PRICE_DATA_UNAVAILABLE — [series] is not accessible via any approved
                MCP or spreadsheet source. Please provide a screenshot from Schwab
                or the allocation sheet."
      NEVER:   proceed with web_search as substitute
      NEVER:   proceed with a stale prior-session carry without flagging it explicitly
    }

    VIOLATION_RESPONSE {
      IF web_search_used_for_price_data: {
        FLAG: "🚨 PRICE_DATA_INTEGRITY_VIOLATION — web_search used for [series] price data.
               This reading is INVALID. Re-fetch from approved source or request screenshot."
        HALT: all analysis that depends on the invalid reading
      }
    }

    IMPLICIT_CROSSCHECK {
      // Arithmetic sanity test. Run when a return figure enters analysis.
      // Would have caught the -6% incident immediately (implied Jan 1 price
      // exceeded the 52-week high — a logical impossibility).
      WHEN: return_pct_present AND current_price_known AND price_range_known {
        implied_base = current_price / (1 + return_pct / 100)
        IF implied_base > instrument_52w_high: REJECT — impossible base price
        IF implied_base < instrument_52w_low:  REJECT — impossible base price
      }
    }
  }


  // ─── FMP PLAN TIER MAP ────────────────────────────────────────────────────────
  // Last verified: June 4, 2026. Re-verify at Q2 audit (June 30, 2026).
  // PURPOSE: avoid wasting session tokens retrying ACCESS DENIED endpoints.
  // When adding a new series, check this map before attempting FMP fetch.

  FMP_PLAN_TIER_MAP {

    CONFIRMED_WORKING {
      commodity_commodities_quote: [
        "BZUSD  (Brent crude)    $95.24 June 4, 2026",
        "GCUSD  (Gold)           $4,504.20 June 4, 2026",
        "SIUSD  (Silver)         $74.16 June 4, 2026"
      ]
      commodity_historical: [
        "commodities-historical-price-eod-light [any commodity symbol]"
      ]
      indexes_index_quote: [
        "^VIX   (CBOE VIX)       $15.40 June 4, 2026",
        "^GSPC  (S&P 500)        $7,584.82 June 4, 2026  ← use this, NOT ^SPX"
      ]
      indexes_historical: [
        "index-historical-price-eod-light ^VIX  (confirmed May 26)",
        "index-historical-price-eod-light ^GSPC (inferred; confirm at Q2)"
      ]
      chart_historical: [
        "historical-price-eod-light SPY  (confirmed May 26)",
        "historical-price-eod-light ^VIX (confirmed May 26)"
      ]
      economics: [
        "treasury-rates (full yield curve, current + history)  confirmed"
      ]
    }

    ACCESS_DENIED {
      // Do NOT retry these. They require a higher plan tier.
      // Note: plan tier may be upgraded in future — re-verify at Q2 audit.
      indexes_index_quote: [
        "^MOVE  (ICE BofA MOVE Index)  → use YFINANCE_MCP ^MOVE",
        "^SPX   (S&P 500)              → use ^GSPC (same data, works)",
        "DX-Y.NYB (DXY)               → use YFINANCE_MCP DX-Y.NYB",
        "[any forex index symbol]"
      ]
      forex: [
        "ALL forex-quote symbols   → use YFINANCE_MCP for any FX pair"
      ]
      quote_endpoint: [
        "quote [any ETF, stock]    → use YFINANCE_MCP market_get_quotes",
        "quote-change [any symbol] → use YFINANCE_MCP",
        "batch-quote [any symbols] → use YFINANCE_MCP",
        "full-etf-quotes           → use YFINANCE_MCP"
      ]
    }
  }


  // ─── ALLOCATION PRICE CROSSCHECK ─────────────────────────────────────────────
  // Adopted: v1.2, June 4, 2026
  // The allocation sheet has GOOGLEFINANCE prices at ~20-min delay.
  // These are T1 (live exchange feed) and are available at session Step 1.
  // They serve as the authoritative gate against major price discrepancies.

  GUARD AllocationPriceCrossCheck {

    APPLIES_TO: HOLDINGS_PRICES
    TRIGGER:    WHEN yfinance_price AND allocation_sheet_price BOTH available

    PROCEDURE {
      FOR each instrument IN fetched_holdings {
        yfinance_price    = YFINANCE_MCP result
        allocation_price  = GOOGLEFINANCE price from session Step 1 allocation fetch
        discrepancy_pct   = abs(yfinance_price - allocation_price) / allocation_price * 100

        IF discrepancy_pct > MAJOR_DISCREPANCY_THRESHOLD {
          HALT_AND_FLAG: "⚠ PRICE_CROSSCHECK_FAILURE: [symbol]
                          yfinance=$[X] vs allocation=$[Y] (discrepancy: [N]%).
                          One price is wrong. Verify before proceeding.
                          Possible causes: symbol mismatch, corporate action,
                          data feed error, post-market vs regular-hours mismatch."
          REQUIRE: client_confirmation OR third_source_verification before continuing
          NEVER:   proceed with either price without resolving the discrepancy
        }

        IF discrepancy_pct <= MAJOR_DISCREPANCY_THRESHOLD {
          ACCEPT:  yfinance_price as current (more recent than allocation ~20-min delay)
          LOG:     allocation_price as T1 confirmation (within normal delay tolerance)
        }
      }
    }

    MAJOR_DISCREPANCY_THRESHOLD: 5%
    // Calibration note: 5% accommodates normal intraday moves + 20-min feed delay.
    // For low-volatility instruments (SGOV, XLP) a 2% threshold may be appropriate.
    // Formal calibration at Q2 audit (June 30, 2026).

    NOTE: "This guard does not make allocation prices authoritative over yfinance prices
           in normal conditions. Yfinance is more current (real-time vs ~20-min delay).
           The guard fires only when both sources materially disagree, which should be
           rare. Its purpose is to catch instrument misidentification, data feed errors,
           or corporate events (splits, ticker changes) before they corrupt analysis."
  }


  // ─── PRICE DATA INTEGRITY RULE ────────────────────────────────────────────────
  // M18 consolidates this guard from M02 (retained in M02 for reference — see M02 diff).

  GUARD PriceDataIntegrity {
    REQUIRE: specific_price_quote sourced_from dedicated_instrument_page
    NEVER: accept_price_from [
      sidebar_widgets,
      tickers_embedded_in_unrelated_articles,
      derivative_aggregators,
      Trading_Economics_CFD_for_BZ=F,    // confirmed inaccurate May 13, 2026
      financecharts_com_return_sentences  // confirmed stale June 3, 2026
    ]

    APPROVED_SOURCES {
      brent_crude:           ["FMP:commodity BZUSD (confirmed free tier June 4)",
                              "ICE settlement (ICE.com official daily settlement prices)",
                              "YFINANCE_MCP market_get_quotes [BZ=F]"]
      wti_crude:             ["EIA weekly (EIA.gov official)", "CME Group settlement data",
                              "YFINANCE_MCP market_get_quotes [CL=F]"]
      gold_silver:           ["FMP:commodity GCUSD / SIUSD (confirmed free tier June 4)",
                              "YFINANCE_MCP market_get_quotes [GC=F / SI=F]",
                              "LBMA", "Kitco spot",
                              "GOOGLEFINANCE XAUUSD/XAGUSD via allocation sheet"]
      equities_spot:         ["YFINANCE_MCP market_get_quotes",
                              "FMP:indexes ^GSPC for S&P 500",
                              "GOOGLEFINANCE via allocation sheet"]
      equities_historical:   ["YFINANCE_MCP market_get_history",
                              "FMP:chart historical-price-eod-light",
                              "FMP:indexes index-historical-price-eod-light ^GSPC"]
      broad_equity_index:    ["FMP:indexes ^GSPC (confirmed)",
                              "YFINANCE_MCP market_get_macro [SP500]",
                              "NOTE: ^SPX ACCESS DENIED — always use ^GSPC"]
      rates:                 ["FRED tab in allocation sheet (T1 confirmed May 13)",
                              "FMP:economics treasury-rates (confirmed; preferred for full curve)"]
      credit_spreads:        ["FRED tab in allocation sheet (T1 confirmed May 13)"]
      VIX:                   ["FMP:indexes index-quote ^VIX (confirmed)",
                              "YFINANCE_MCP market_get_macro [VIX key]"]
      MOVE:                  ["YFINANCE_MCP market_get_macro [MOVE key] (^MOVE)",
                              "GOOGLEFINANCE INDEXNYSEGIS:MOVE via allocation sheet",
                              "NOTE: FMP ^MOVE ACCESS DENIED — do not retry"]
      DXY:                   ["YFINANCE_MCP market_get_macro [DXY key] (DX-Y.NYB)",
                              "NOTE: FMP forex and indexes paths ACCESS DENIED"]
      VIX_trailing_avg:      ["FMP:chart historical-price-eod-light ^VIX",
                              "YFINANCE_MCP market_get_history [^VIX]"]
      natural_gas:           ["FRED DHHNGSP tab in allocation sheet",
                              "Google Finance NGM26/NGN26 futures as current proxy"]
      portfolio_holdings:    ["YFINANCE_MCP market_get_quotes",
                              "GOOGLEFINANCE via allocation sheet (crosscheck only)"]
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
      note:          "These are now CROSSCHECK sources, not primaries (v1.2).
                      Primary sources: FMP_INDEXES for VIX and SP500;
                      YFINANCE_MCP for MOVE, KRE, KBE."
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
      // Most now have MCP fallbacks; web search fallback removed for all price series.
      // ADD at Q2 audit (June 30, 2026):
      missing_or_unconfirmed: [
        "DGS10 (TREASURY_10Y) — covered by YIELD_CURVE FMP fetch until added",
        "DGS2  (TREASURY_2Y)  — covered by YIELD_CURVE FMP fetch until added",
        "T10YIE (BREAKEVEN_10Y) — FRED official page fallback (stats exception)",
        "T5YIE  (BREAKEVEN_5Y)  — FRED official page fallback (stats exception)",
        "DXY — covered by YFINANCE_MCP; add GOOGLEFINANCE(CURRENCY:USDEUR) as crosscheck",
        "NASDAQ Composite — covered by YFINANCE_MCP ^IXIC",
        "Dow Jones — covered by YFINANCE_MCP ^DJI",
        "Russell 2000 — covered by YFINANCE_MCP ^RUT"
      ]
    }
  }


  // ─── YFINANCE MCP SERVER REFERENCE ───────────────────────────────────────────
  // server.py: dev/market_data_mcp/server.py (user Google Drive)
  // instruments.json: dev/market_data_mcp/instruments.json (same directory)
  //
  // INSTRUMENTS.JSON LIFECYCLE:
  //   Written by: manually via Desktop Commander:write_file during WriteBack Step 4b
  //              (@see M12_DriveProtocol.md WriteBack STEP 4b; NOT automated in Python — see ENG-25)
  //   Read by:    server.py on every tool call (dynamic, no restart needed)
  //   Format:     { "instruments": ["MLPX","SGOL",...], "last_updated": "YYYY-MM-DD",
  //                "session": "YYYY-MM-DD advisory" }
  //   Fallback:   hardcoded list in server.py (pre-first-session resilience)
  //   NOTE:       This replaces portfolio.json (manually maintained, deprecated v1.2).
  //               The advisory session is the single source of truth for active
  //               instruments — instruments.json syncs the MCP server to that truth.
  //
  // TOOL REFERENCE:
  //   market_get_quotes  — current price + day change for instruments list or any symbols
  //   market_get_ytd     — YTD % return from Dec 31 base; instruments list or any symbols
  //   market_get_history — daily closes for any symbol, any date range or period shorthand
  //                        periods: ytd | 1m | 3m | 6m | 1y | 2y | 5y
  //                        or explicit: start=YYYY-MM-DD, end=YYYY-MM-DD (optional)
  //   market_get_macro   — DXY, MOVE, VIX, SP500, KRE, KBE in one call
  //                        DXY and MOVE: ONLY available here (FMP blocked for both)


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

    use_web_search_for_price_or_return_data:
      "HARD_GATE prohibition (v1.2). Web search is prohibited for any instrument price,
       ETF/stock return, index level, futures price, or yield curve tenor. These must
       come from YFINANCE_MCP, FMP_COMMODITY, FMP_INDEXES, FMP_ECONOMICS, FRED tab,
       allocation sheet GOOGLEFINANCE, or MANUAL_CLIENT_INPUT. If all approved sources
       fail: request client screenshot. Never proceed with a web search snippet."

    skip_allocation_crosscheck_when_both_sources_available:
      "When both YFINANCE_MCP and allocation sheet prices are available, the crosscheck
       is mandatory. Skipping it defeats the purpose of the T1 gate. The check takes
       one comparison per instrument. If discrepancy > 5%: HALT. Always."

    retry_fmp_access_denied_endpoints:
      "FMP_PLAN_TIER_MAP documents confirmed ACCESS DENIED endpoints. Do not retry them.
       Use the YFINANCE_MCP fallback specified in each FetchSpec description.
       ^MOVE, ^SPX, forex-quote, ETF quote — all blocked at current tier."

    use_SPX_index_via_FMP_indexes:
      "FMP:indexes endpoint for ^SPX requires higher plan tier — ACCESS DENIED confirmed
       May 26, 2026. Always use ^GSPC (confirmed working). Do not retry ^SPX."

    assume_allocation_tab_content_without_verifying:
      "The allocation spreadsheet has known series gaps (DGS10, DGS2, T10YIE, T5YIE,
       DXY, NASDAQ, DOW, Russell 2000 not yet confirmed present). If a series is absent
       from read_file_content output, fall back to the registered fallback source — do
       not assume the data simply was not surfaced. Distinguish: (a) tab exists but
       content not visible in flattened output vs (b) tab does not exist yet."

    maintain_instruments_json_manually:
      "instruments.json is written by advisory session WriteBack (M12 PATTERN_B).
       Do not edit it by hand between sessions. The advisory session is authoritative
       for active instrument list (§11.3). instruments.json syncs the MCP server."
  }

}
```
