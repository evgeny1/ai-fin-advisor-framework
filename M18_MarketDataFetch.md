# M18 — Market Data Fetch
<!-- Version: 1.2 | Updated: June 4, 2026 -->
<!-- Sub-project: DATA_INTELLIGENCE -->
<!-- Reason to change: new data series needed, source changes, or lag tolerance changes.
     NEVER register DATA_REGISTRY_ENTRIES in any other module — add here only.
     Full change history: git log M18_MarketDataFetch.md -->

<!-- MODULE MANIFEST
  ID:              M18_MarketDataFetch
  Version:         1.2
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
      source:              FMP_COMMODITY
      description:         "Brent crude futures — FMP:commodity commodities-quote BZUSD.
                            Confirmed working free tier June 4, 2026 ($95.24).
                            BZ=F is canonical Brent reference per Calibration_State §2.1 (v1.17).
                            Fallback: YFINANCE_MCP market_get_quotes [BZ=F].
                            NOT Trading Economics CFD (confirmed $3-4 discrepancy May 13, 2026).
                            DEPRECATED source: WEBSEARCH_T1 — removed by HARD_GATE v1.2."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M03, M17]
    }

    REGISTER FetchSpec {
      id:                  "WTI"
      source:              WEBSEARCH_T1
      description:         "WTI crude futures CL=F — EIA weekly or CME Group settlement data.
                            CPI_YOY-class exception: EIA.gov is an official government source.
                            Fallback: YFINANCE_MCP market_get_quotes [CL=F].
                            Note: WTI is secondary to Brent in this framework — used for
                            cross-referencing only; Brent is the primary C-trigger series."
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
      source:              FMP_COMMODITY
      description:         "Gold futures — FMP:commodity commodities-quote GCUSD.
                            Confirmed working free tier June 4, 2026 ($4,504.20).
                            Fallback: YFINANCE_MCP market_get_quotes [GC=F].
                            Crosscheck: GOOGLEFINANCE CURRENCY:XAUUSD via allocation sheet.
                            DEPRECATED source: GOOGLEFINANCE as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "SILVER"
      source:              FMP_COMMODITY
      description:         "Silver futures — FMP:commodity commodities-quote SIUSD.
                            Confirmed working free tier June 4, 2026 ($74.16).
                            Fallback: YFINANCE_MCP market_get_quotes [SI=F].
                            Crosscheck: GOOGLEFINANCE CURRENCY:XAGUSD via allocation sheet.
                            DEPRECATED source: GOOGLEFINANCE as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── BROAD EQUITIES ────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "SP500"
      source:              FMP_INDEXES
      description:         "S&P 500 Index — FMP:indexes index-quote ^GSPC.
                            Confirmed working free tier June 4, 2026 ($7,584.82).
                            ⚠ ^SPX remains ACCESS DENIED — use ^GSPC (same index).
                            Fallback: YFINANCE_MCP market_get_macro [SP500 key].
                            Crosscheck: GOOGLEFINANCE INDEXSP:.INX via allocation sheet.
                            DEPRECATED source: GOOGLEFINANCE as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M14]
    }

    REGISTER FetchSpec {
      id:                  "NASDAQ_COMP"
      source:              YFINANCE_MCP
      description:         "NASDAQ Composite — YFINANCE_MCP market_get_quotes [^IXIC].
                            DEPRECATED source: WEBSEARCH_T1."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "DOW"
      source:              YFINANCE_MCP
      description:         "Dow Jones Industrial Average — YFINANCE_MCP market_get_quotes [^DJI].
                            DEPRECATED source: WEBSEARCH_T1."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "RUSSELL2000"
      source:              YFINANCE_MCP
      description:         "Russell 2000 — YFINANCE_MCP market_get_quotes [^RUT].
                            DEPRECATED source: WEBSEARCH_T1."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }


    // ── VOLATILITY ────────────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "VIX"
      source:              FMP_INDEXES
      description:         "VIX current daily close — FMP:indexes index-quote ^VIX.
                            Confirmed working free tier June 4, 2026 ($15.40).
                            Fallback: YFINANCE_MCP market_get_macro [VIX key].
                            Crosscheck: GOOGLEFINANCE INDEXCBOE:VIX via allocation sheet.
                            DEPRECATED source: ALLOCATION_SPREADSHEET_OTHER as primary."
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
                            Fallback: YFINANCE_MCP market_get_history [^VIX, period=3m]
                            (count back 30 trading days from returned array).
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
                            Also derives VIX_change_90d_pts for M14 divergence signal:
                            VIX_change_90d_pts = close[0] − close[last_index].
                            Fallback: YFINANCE_MCP market_get_history [^VIX, period=6m]
                            (count back 62 trading days from returned array).
                            Session result (May 26): VIX_90D_AVG = 21.24;
                            VIX_change_90d_pts = 16.70 − 17.93 = −1.23 pts."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

    REGISTER FetchSpec {
      id:                  "MOVE"
      source:              YFINANCE_MCP
      description:         "ICE BofA MOVE Index — YFINANCE_MCP market_get_macro [MOVE key].
                            Symbol: ^MOVE. Confirmed working June 4, 2026 (73.58).
                            FMP:indexes index-quote ^MOVE → ACCESS DENIED free tier — do not retry.
                            Fallback: ALLOCATION_SPREADSHEET_OTHER GOOGLEFINANCE(INDEXNYSEGIS:MOVE).
                            DEPRECATED source: ALLOCATION_SPREADSHEET_OTHER as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M11, M02]
      calibration_use:     "Watch level 80. Alert level 100. Formal threshold TBD at Q2 audit."
    }


    // ── REGIONAL BANKS / CASCADE CHAIN EQUITIES ────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "KRE"
      source:              YFINANCE_MCP
      description:         "SPDR S&P Regional Banking ETF — YFINANCE_MCP market_get_macro [KRE key].
                            Symbol: KRE. Confirmed working June 4, 2026.
                            Fallback: ALLOCATION_SPREADSHEET_OTHER GOOGLEFINANCE(KRE).
                            DEPRECATED source: ALLOCATION_SPREADSHEET_OTHER as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M17]
      calibration_use:     "CHAIN_2 §12.2: KRE vs SPX 90d underperformance ≥ −15pp"
    }

    REGISTER FetchSpec {
      id:                  "KBE"
      source:              YFINANCE_MCP
      description:         "SPDR S&P Bank ETF — YFINANCE_MCP market_get_macro [KBE key].
                            Symbol: KBE. Confirmed working June 4, 2026.
                            Fallback: ALLOCATION_SPREADSHEET_OTHER GOOGLEFINANCE(KBE).
                            DEPRECATED source: ALLOCATION_SPREADSHEET_OTHER as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M17]
    }


    // ── RATES & YIELD CURVE ────────────────────────────────────────────────────────
    REGISTER FetchSpec {
      id:                  "TREASURY_10Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "DGS10 — 10-year Treasury yield — FRED tab in allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26, 2026).
                            Add DGS10 at Q2 audit. Until confirmed: obtain from YIELD_CURVE
                            FMP fetch (10Y tenor from FMP:economics treasury-rates).
                            Do NOT use web search as fallback — YIELD_CURVE fetch covers this."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "TREASURY_2Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "DGS2 — 2-year Treasury yield — FRED tab in allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26, 2026).
                            Add at Q2 audit. Until confirmed: obtain from YIELD_CURVE FMP fetch
                            (2Y tenor from FMP:economics treasury-rates).
                            Do NOT use web search as fallback."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02]
    }

    REGISTER FetchSpec {
      id:                  "YIELD_CURVE"
      source:              FMP_ECONOMICS_TREASURY_RATES
      description:         "Full US Treasury par yield curve — FMP:economics treasury-rates
                            endpoint. All tenors: 1M, 2M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y,
                            20Y, 30Y. Confirmed working at current FMP plan tier.
                            Returns array newest-first; use index [0] for current session.
                            Fallback: treasury.gov Daily Par Yield Curve Rates.
                            Derives: TREASURY_10Y, TREASURY_2Y, TREASURY_30Y, 10Y-2Y spread,
                            10Y-3M spread (all readable from this single fetch — no separate
                            TREASURY_10Y or TREASURY_2Y fetch needed when this is available).
                            June 4, 2026: 10Y=4.47%, 2Y=4.05%, 10Y-2Y=+42bp, 30Y=4.97%."
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
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26, 2026).
                            Add at Q2 audit. Until confirmed: FRED T10YIE series page (web search
                            of fred.stlouisfed.org is an approved official-statistics exception;
                            this is not a price series — the HARD_GATE does not apply here)."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M02, M03]
    }

    REGISTER FetchSpec {
      id:                  "BREAKEVEN_5Y"
      source:              FRED_SPREADSHEET_TAB
      description:         "T5YIE — 5-year breakeven inflation rate — FRED tab in
                            allocation sheet.
                            ⚠ NOT YET CONFIRMED in allocation spreadsheet (as of May 26, 2026).
                            Add at Q2 audit. Until confirmed: FRED T5YIE series page (same
                            official-statistics exception as BREAKEVEN_10Y — not a price series)."
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
      source:              YFINANCE_MCP
      description:         "US Dollar Index — YFINANCE_MCP market_get_macro [DXY key].
                            Symbol: DX-Y.NYB. Confirmed working June 4, 2026 (99.46).
                            FMP forex endpoint → all symbols ACCESS DENIED free tier.
                            FMP indexes DX-Y.NYB → ACCESS DENIED free tier.
                            Add GOOGLEFINANCE formula to allocation sheet at Q2 audit.
                            DEPRECATED source: WEBSEARCH_T1."
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
                            HARD_GATE EXCEPTION: CPI is an official government statistical
                            publication (BLS.gov), not a market price or aggregator narrative.
                            Web search targeting the BLS release is permitted; the number
                            appears in the official press release as a primary statistic.
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
      source:              YFINANCE_MCP
      description:         "All active portfolio instrument prices — YFINANCE_MCP market_get_quotes.
                            Instrument list driven by instruments.json (same dir as server.py).
                            instruments.json is written by advisory session WriteBack (M12 PATTERN_B)
                            from §11.3 active positions — replaces manually maintained portfolio.json.
                            Fallback list is hardcoded in server.py for pre-first-session resilience.
                            ⚠ CROSSCHECK REQUIRED: after fetching via YFINANCE_MCP, compare
                            against GOOGLEFINANCE prices in allocation sheet (already loaded at
                            session Step 1). If discrepancy > 5% on any instrument → HALT and
                            apply ALLOCATION_PRICE_CROSSCHECK protocol.
                            Allocation sheet prices are ~20-min delayed but T1 (live exchange feed).
                            DEPRECATED source: GOOGLEFINANCE as primary."
      update_frequency:    DAILY
      acceptable_lag_days: 0
      consumer:            [M02, M06, M13]
    }

    REGISTER FetchSpec {
      id:                  "BROAD_EQUITY_TRAILING"
      source:              FMP_INDEXES
      description:         "S&P 500 (^GSPC) 30-day and 90-day trailing pct-change —
                            computed from FMP:indexes index-historical-price-eod-light ^GSPC
                            with from_date = 90 calendar days prior to session date.
                            Confirmed working: ^GSPC via FMP:indexes June 4, 2026.
                            NOTE: ^GSPC replaces SPY proxy (used in v1.1 because ^SPX
                            was ACCESS DENIED). SPY remains a valid fallback if ^GSPC
                            historical endpoint fails.
                            Computation:
                              30d_return = (close[0] − close[30_trading_days_back]) / close[30_trading_days_back]
                              90d_return = (close[0] − close[last_index]) / close[last_index]
                            Index 0 in FMP response = most recent close (array newest-first).
                            Fallback: YFINANCE_MCP market_get_history [^GSPC, period=6m].
                            Session result (May 26, SPY proxy): 30-trading-day return = +8.68%."
      update_frequency:    DAILY
      acceptable_lag_days: 1
      consumer:            [M14]
    }

    REGISTER FetchSpec {
      id:                  "HISTORICAL_INSTRUMENT_PRICES"
      source:              YFINANCE_MCP
      description:         "Daily adjusted close prices for any portfolio instrument over any
                            date range — YFINANCE_MCP market_get_history.
                            Supports: period shorthands (ytd, 1m, 3m, 6m, 1y, 2y, 5y) or
                            explicit start/end dates (YYYY-MM-DD). Returns adjusted closes
                            (splits + dividends) with total_return_pct computed.
                            ⚠ ON-DEMAND ONLY — NOT a standard session fetch.
                            Fetch only when explicitly needed for a specific analytical task.
                            Use cases:
                              1. Return table validation (M16): compare instrument performance
                                 in historical scenario-equivalent periods vs return table values.
                                 E.g., MLPX during 2022 (B-proxy), DBMF during 2022 (B).
                              2. Thesis performance tracking: is an instrument tracking its
                                 EV trajectory given current scenario probabilities?
                              3. Stress period analysis: drawdown, max daily loss.
                              4. Correlation cross-check: do uncorrelated instruments actually
                                 diverge in practice during this regime?
                            Session capacity: use for Q2 audit calibration tasks; avoid during
                            standard M05 sessions unless a specific decision requires it."
      update_frequency:    ON_DEMAND
      acceptable_lag_days: 1
      consumer:            [M16, M13, M07]
    }

  }  // end DATA_REGISTRY_ENTRIES


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
  //   Written by: advisory session M12 PATTERN_B WriteBack (via Desktop Commander)
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
