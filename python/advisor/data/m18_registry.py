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
]
