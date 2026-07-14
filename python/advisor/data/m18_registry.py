"""
M18 DATA_REGISTRY_ENTRIES — Python translation of M18_MarketDataFetch.md.
This is the ONLY file where FetchSpecs are registered. Never add series elsewhere.
To add a new series: add one FetchSpec block here. Nothing else changes.
"""
from __future__ import annotations
from ..types import DataSource, FetchSpec, UpdateFrequency
from .fetch_registry import FetchRegistry


def register_all(registry: FetchRegistry) -> None:
    """Register every M18 DATA_REGISTRY_ENTRY into the given FetchRegistry."""
    for spec in _ALL_SPECS:
        registry.register(spec)


# ── ENERGY ────────────────────────────────────────────────────────────────────

_ALL_SPECS: list[FetchSpec] = [

    FetchSpec(
        id="BRENT_CRUDE",
        source=DataSource.YFINANCE,
        description="Brent crude BZ=F via yfinance. FMP BZUSD returns 403 with standalone API key "
                    "(FMP MCP uses a higher-tier account). Confirmed yfinance path works.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02", "M03", "M17"],
    ),

    FetchSpec(
        id="WTI",
        source=DataSource.YFINANCE,
        description="WTI crude CL=F. Secondary to Brent; cross-reference only.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
    ),

    FetchSpec(
        id="NATURAL_GAS",
        source=DataSource.FRED_OR_WEBSEARCH,
        description="Henry Hub front-month. MANDATORY when FARM_FILINGS_YOY within "
                    "10pp of +50%. Currently +46% — fetch every session.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=3,
        consumer=["M02", "M17"],
        calibration_use="CHAIN_1 §12.1: >=6.00/mmBtu sustained 30 days",
    ),

    # ── PRECIOUS METALS ───────────────────────────────────────────────────────

    FetchSpec(
        id="GOLD_SPOT",
        source=DataSource.YFINANCE,
        description="Gold futures GC=F via yfinance. FMP GCUSD returns 403 with standalone API key.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
    ),

    FetchSpec(
        id="SILVER",
        source=DataSource.YFINANCE,
        description="Silver futures SI=F via yfinance. FMP SIUSD returns 403 with standalone API key.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
    ),

    FetchSpec(
        id="COPPER_SPOT",
        source=DataSource.YFINANCE,
        description="Copper futures HG=F via yfinance. Same liquid-contract pattern as GOLD_SPOT/SILVER "
                    "(COMEX High Grade Copper, heavily traded). Added for §13 M19 COPX thesis monitoring "
                    "(data_dependency: COPPER_SPOT — corrected from a prior draft that mistakenly listed SIUSD).",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M19"],
    ),

    FetchSpec(
        id="URANIUM_SPOT",
        source=DataSource.YFINANCE,
        description="⚠ UNCONFIRMED — CME UxC U3O8 futures (ticker UX, yfinance convention UX=F). "
                    "Real but illiquid contract (CME-quoted volume frequently 0; wide bid/ask). "
                    "Verify against live yfinance before relying on it — sandbox has no network path "
                    "to Yahoo Finance to test this ticker directly. If FETCH_FAILED or implausible, "
                    "M19 falls back to the URA ETF price (already fetched via HOLDINGS_PRICES) as a proxy, "
                    "flagged as a proxy substitution, never silently treated as the true spot price.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M19"],
    ),

    # ── BROAD EQUITIES ────────────────────────────────────────────────────────

    FetchSpec(
        id="SP500",
        source=DataSource.YFINANCE,
        description="S&P 500 ^GSPC via yfinance. FMP indexes ^VIX/^GSPC return 403 with standalone key.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02", "M14"],
    ),

    FetchSpec(
        id="NASDAQ_COMP",
        source=DataSource.YFINANCE,
        description="NASDAQ Composite ^IXIC.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
    ),

    FetchSpec(
        id="DOW",
        source=DataSource.YFINANCE,
        description="Dow Jones Industrial Average ^DJI.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
    ),

    FetchSpec(
        id="RUSSELL2000",
        source=DataSource.YFINANCE,
        description="Russell 2000 ^RUT.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
    ),

    # ── VOLATILITY ────────────────────────────────────────────────────────────

    FetchSpec(
        id="VIX",
        source=DataSource.YFINANCE,
        description="VIX daily close ^VIX via yfinance. FMP ^VIX returns 403 with standalone key.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02", "M14"],
    ),

    FetchSpec(
        id="VIX_30D_AVG",
        source=DataSource.YFINANCE,
        description="VIX 30-day rolling average from yfinance ^VIX history.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M14"],
    ),

    FetchSpec(
        id="VIX_90D_AVG",
        source=DataSource.YFINANCE,
        description="VIX 90-day rolling avg from yfinance ^VIX history. Also derives VIX_change_90d_pts.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M14"],
    ),

    FetchSpec(
        id="MOVE",
        source=DataSource.YFINANCE,
        description="ICE BofA MOVE Index ^MOVE. FMP ^MOVE ACCESS DENIED.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M11", "M02"],
        calibration_use="Watch 80. Alert 100. Formal threshold TBD Q2.",
    ),

    # ── REGIONAL BANKS ────────────────────────────────────────────────────────

    FetchSpec(
        id="KRE",
        source=DataSource.YFINANCE,
        description="SPDR S&P Regional Banking ETF KRE.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M17"],
        calibration_use="CHAIN_2 §12.2: KRE vs SPX 90d underperformance >= -15pp",
    ),

    FetchSpec(
        id="KBE",
        source=DataSource.YFINANCE,
        description="SPDR S&P Bank ETF KBE.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M17"],
    ),

    # ── RATES & YIELD CURVE ───────────────────────────────────────────────────

    FetchSpec(
        id="YIELD_CURVE",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="Full US Treasury yield curve. FRED REST preferred (DGS2/DGS5/DGS10/DGS30/DGS3MO "
                    "— requires FRED_API_KEY, free from fred.stlouisfed.org). "
                    "Fallback: yfinance ^TNX/^TYX/^IRX (partial — year2=None, spread_10y_2y=None). "
                    "FMP:economics treasury-rates works via FMP MCP but returns 403 with standalone key.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=2,
        consumer=["M17", "M02"],
    ),

    FetchSpec(
        id="SOFR",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="SOFR — Secured Overnight Financing Rate.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=2,
        consumer=["M17", "M11"],
    ),

    FetchSpec(
        id="DFF",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="DFF — Effective Federal Funds Rate.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=2,
        consumer=["M17", "M11", "M02"],
    ),

    FetchSpec(
        id="THREEFYTP10",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="THREEFYTP10 — 10Y Treasury term premium (ACM). Weekly cadence.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M17", "M02"],
        calibration_use="§12.5 E_term_premium_warning=100bp; alert=150bp",
    ),

    # ── CREDIT SPREADS ────────────────────────────────────────────────────────

    FetchSpec(
        id="HY_OAS",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="ICE BofA US HY OAS — BAMLH0A0HYM2.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M11"],
        calibration_use="M11 §1.1 HY_STRESS_DELTA and HY_RECESSION_DELTA",
    ),

    FetchSpec(
        id="IG_OAS",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="ICE BofA US IG OAS — BAMLC0A0CM.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M11"],
        calibration_use="M11 §1.2 IG_TRANSMISSION_DELTA",
    ),

    FetchSpec(
        id="CCC_OAS",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="ICE BofA CCC & Lower OAS — BAMLH0A3HYC.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M11"],
    ),

    FetchSpec(
        id="BBB_OAS",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="ICE BofA BBB US Corporate OAS — BAMLC0A4CBBB.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M11"],
    ),

    # ── FX ────────────────────────────────────────────────────────────────────

    FetchSpec(
        id="DXY",
        source=DataSource.YFINANCE,
        description="US Dollar Index DX-Y.NYB. FMP forex/indexes both ACCESS DENIED.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M02"],
        calibration_use="§2.2: DXY >= 105 sustained → SGOL invalidation risk",
    ),

    # ── INFLATION & MONETARY POLICY ───────────────────────────────────────────

    FetchSpec(
        id="CPI_YOY",
        source=DataSource.WEBSEARCH_T1,
        description="Latest BLS CPI YoY print. BLS.gov official stats exception "
                    "(not a price series — HARD_GATE does not apply). "
                    "Current: Apr 2026 = 3.8% YoY. Next: mid-June 2026.",
        update_frequency=UpdateFrequency.MONTHLY,
        acceptable_lag_days=35,
        consumer=["M02", "M03"],
        calibration_use="§2.3 B-trigger: >= 4.0% YoY, 3+ consecutive prints",
    ),

    FetchSpec(
        id="CHINA_PMI_MANUFACTURING",
        source=DataSource.WEBSEARCH_T1,
        description="NBS (National Bureau of Statistics of China) official Manufacturing PMI, "
                    "same official-statistics exception pattern as CPI_YOY (BLS). Not a price series — "
                    "HARD_GATE does not apply. Added for §13 M19 SIVR/COPX industrial-demand monitoring.",
        update_frequency=UpdateFrequency.MONTHLY,
        acceptable_lag_days=35,
        consumer=["M19"],
    ),

    # ── CASCADE CHAIN STRUCTURAL INPUTS ───────────────────────────────────────

    FetchSpec(
        id="FINRA_MARGIN_DEBT",
        source=DataSource.ALLOCATION_SPREADSHEET_FINRA,
        description="FINRA monthly margin debit balances. Current: $1.304T Apr 2026 "
                    "(all-time nominal record). CHAIN_3_WATCH=TRUE.",
        update_frequency=UpdateFrequency.MONTHLY,
        acceptable_lag_days=30,
        consumer=["M17"],
        calibration_use="CHAIN_3 §12.3: WATCH on record; FIRES on -5% MoM or gate_count>=3",
    ),

    FetchSpec(
        id="NATGAS_HENRY_HUB",
        source=DataSource.FRED_OR_WEBSEARCH,
        description="Henry Hub natgas. MANDATORY when FARM_FILINGS within 10pp of +50%.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=3,
        consumer=["M17"],
        calibration_use="CHAIN_1 §12.1: >=6.00/mmBtu sustained 30 days",
    ),

    FetchSpec(
        id="FARM_FILINGS_YOY",
        source=DataSource.USDA_OR_AFBF,
        description="Chapter 12 farm bankruptcy YoY change. Current: +46% (2025 data). "
                    "Quarterly cadence. Next USDA update may cross +50% threshold.",
        update_frequency=UpdateFrequency.QUARTERLY,
        acceptable_lag_days=90,
        consumer=["M17"],
        calibration_use="CHAIN_1 §12.1: >=+50% YoY",
    ),

    # ── HOLDINGS & PORTFOLIO PRICES ───────────────────────────────────────────

    FetchSpec(
        id="HOLDINGS_PRICES",
        source=DataSource.YFINANCE,
        description="All active portfolio instrument prices. List from instruments.json. "
                    "Crosscheck against allocation sheet (5% discrepancy = HALT).",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=0,
        consumer=["M02", "M06", "M13"],
    ),

    FetchSpec(
        id="BROAD_EQUITY_TRAILING",
        source=DataSource.YFINANCE,
        description="S&P 500 ^GSPC 30d and 90d trailing pct-change via yfinance history.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M14"],
    ),

    FetchSpec(
        id="HISTORICAL_INSTRUMENT_PRICES",
        source=DataSource.YFINANCE,
        description="Daily adjusted closes for any instrument, any date range. "
                    "ON_DEMAND only — not a standard session fetch.",
        update_frequency=UpdateFrequency.ON_DEMAND,
        acceptable_lag_days=1,
        consumer=["M16", "M13", "M07"],
    ),

    # ── TREND SERIES (ENG-13) ─────────────────────────────────────────────────
    # §13 conditions containing "sustained"/"consecutive"/"rolling"/"trend"/
    # "reversal" were previously always skipped (analysis/thesis.py) — no
    # FetchSpec existed for the multi-week history they need. One call per
    # series per session covers the whole lookback window; see analysis/trend.py.

    FetchSpec(
        id="DXY_TREND",
        source=DataSource.YFINANCE,
        description="DX-Y.NYB, 8 weekly closes. Feeds SGOL/SIVR DXY sustaining/"
                    "failure conditions (§13) and DBMF's 4-market directional check. "
                    "Also feeds GAP-16 IHP range-position advisory (analysis/range_position.py).",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19", "M15"],
    ),

    FetchSpec(
        id="BRENT_TREND",
        source=DataSource.YFINANCE,
        description="BZ=F, 8 weekly closes. Feeds DBMF's directional check and "
                    "MLPX's 'BZUSD sustained < 65 for >= 6 consecutive weeks' failure signal.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19"],
    ),

    FetchSpec(
        id="GOLD_TREND",
        source=DataSource.YFINANCE,
        description="GC=F, 8 weekly closes. Feeds DBMF's directional check.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19"],
    ),

    FetchSpec(
        id="SP500_TREND",
        source=DataSource.YFINANCE,
        description="^GSPC, 8 weekly closes. Feeds DBMF's directional check.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19"],
    ),

    FetchSpec(
        id="COPPER_TREND",
        source=DataSource.YFINANCE,
        description="HG=F, 12 weekly closes. Feeds COPX/URA 'stable or upward trend' "
                    "sustaining conditions and SIVR/COPX 'sustained decline' failure signals.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19"],
    ),

    FetchSpec(
        id="URANIUM_TREND",
        source=DataSource.YFINANCE,
        description="⚠ Same illiquid-contract caveat as URANIUM_SPOT (UX=F). Feeds "
                    "URA's 'stable or upward trend' / '20% decline from high' §13 conditions. "
                    "Falls back to FETCH_FAILED gracefully — never silently treated as data.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19"],
    ),

    FetchSpec(
        id="COPX_PRICE_TREND",
        source=DataSource.YFINANCE,
        description="COPX ETF price, 8 weekly closes. Feeds SIVR's "
                    "'COPX sustained decline > 15% over 8 weeks' failure signal.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=7,
        consumer=["M19"],
    ),

    FetchSpec(
        id="THREEFYTP10_TREND",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="THREEFYTP10, 10 weekly observations. Feeds SGOL/SIVR's "
                    "'real yield sustained > 2.0% for >= 4 weeks' M19 §13 failure "
                    "signal text (that condition still names THREEFYTP10 explicitly; "
                    "relabeling it is a separate Calibration_State.md §13 text change, "
                    "not done this session). No longer used by the GAP-16 IHP "
                    "range-position advisory as of 2026-06-21 — see REAL_YIELD_10Y_TREND.",
        update_frequency=UpdateFrequency.WEEKLY,
        acceptable_lag_days=10,
        consumer=["M19"],
    ),

    FetchSpec(
        id="REAL_YIELD_10Y_TREND",
        source=DataSource.FRED_SPREADSHEET_TAB,
        description="10Y real yield = DGS10 (nominal Treasury yield) minus T10YIE "
                    "(10Y breakeven inflation), both daily FRED series, resampled to "
                    "8 weekly closes (Fisher-equation real yield). GAP-16 follow-up "
                    "(identified 2026-06-21): THREEFYTP10 -- the 10Y *term premium* -- "
                    "was being used as the real-yield sub-condition driver in IHP's "
                    "range-position advisory, but term premium is bond-supply/demand "
                    "duration compensation, not the Fed-path-driven real rate that "
                    "actually sets precious metals' opportunity cost; the two series "
                    "can and do diverge. This spec replaces THREEFYTP10 as that driver "
                    "in analysis/range_position.py.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=2,
        consumer=["M15"],
        calibration_use="GAP-16 follow-up: IHP range-position real-yield sub-condition",
    ),

    FetchSpec(
        id="NASDAQ_30D_RETURN",
        source=DataSource.YFINANCE,
        description="^IXIC 30-trading-day pct-change. Feeds MAGS's "
                    "'Nasdaq 30d return <= -10%' failure signal — previously had "
                    "no FetchSpec or regex pattern at all (silently unevaluable).",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M19"],
    ),

    FetchSpec(
        id="DBMF_3M_RETURN",
        source=DataSource.YFINANCE,
        description="DBMF's own ~64-trading-day (3-month) pct-change. Feeds "
                    "DBMF's 'DBMF_3M_return < -3% while B+C >= 55%' failure "
                    "signal (ENG-30) — previously had no FetchSpec or regex "
                    "pattern at all (silently unevaluable). Own-performance, "
                    "not a generic market-index trend — distinct from the "
                    "*_TREND specs below, which ENG-13 already covers.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["M19"],
    ),

    # ── TREND/ROTATION SIGNAL (ENG-50/ENG-55) ─────────────────────────────────
    # New module, no M-number — explicitly NOT part of the M01-M19 spec
    # sequence (FRAMEWORK_BACKLOG.md ENG-50). Additive, shadow-mode only;
    # NEVER feeds M03.DeriveScenarioProbabilities().

    FetchSpec(
        id="TREND_SIGNAL_HISTORY",
        source=DataSource.YFINANCE,
        description="Daily closes (~100 calendar days) for the 8 held instruments "
                    "(MLPX/DBMF/XAR/AIPO/COPX/SGOL/SIVR/MAGS) plus ENG-55's comparator "
                    "tickers (BZ=F, HG=F, ITA, PPA, PAVE, QQQM, URA, VEA) — 16 symbols, "
                    "ONE batched yf.download() call rather than 16 separate registry "
                    "entries. ENG-35 already flagged advisor_run_computation() running "
                    "close to the MCP call ceiling; the existing per-symbol weekly-trend "
                    "pattern (7 separate calls) would make that materially worse at this "
                    "scale. Feeds analysis/trend_signal.py's Mode 1 return-spread math "
                    "and the own_short/own_medium legs of Mode 2. Mode 2's macro-"
                    "confirmation inputs (DXY_TREND, BRENT_TREND, GOLD_TREND, "
                    "SP500_TREND, REAL_YIELD_10Y_TREND) are NOT refetched here — all "
                    "five already exist above and are reused as-is.",
        update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
        consumer=["TREND_SIGNAL"],
    ),
]
