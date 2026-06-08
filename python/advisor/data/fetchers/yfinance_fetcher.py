"""
yfinance_fetcher.py — Direct yfinance calls replacing the YFINANCE_MCP server.
Handles: quotes, YTD, history, macro (DXY/MOVE/VIX/SP500/KRE/KBE).
Source of truth for implementation patterns: dev/market_data_mcp/server.py.
"""
from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yfinance as yf
import pandas as pd

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

# Canonical symbols matching M18 registry descriptions
_MACRO_SYMBOLS: Dict[str, str] = {
    "DXY":   "DX-Y.NYB",
    "MOVE":  "^MOVE",
    "VIX":   "^VIX",
    "SP500": "^GSPC",
    "KRE":   "KRE",
    "KBE":   "KBE",
}

_COMMODITY_FALLBACKS: Dict[str, str] = {
    "BRENT_CRUDE": "BZ=F",
    "WTI":         "CL=F",
    "GOLD_SPOT":   "GC=F",
    "SILVER":      "SI=F",
    "NATURAL_GAS": "NG=F",
}

_EQUITY_SYMBOLS: Dict[str, str] = {
    "NASDAQ_COMP": "^IXIC",
    "DOW":         "^DJI",
    "RUSSELL2000": "^RUT",
    "SP500":       "^GSPC",
}

_SERVER_DIR = Path(__file__).parent.parent.parent.parent.parent / "dev" / "market_data_mcp"
_INSTRUMENTS_FILE = _SERVER_DIR / "instruments.json"
_FALLBACK_INSTRUMENTS = [
    "MAGS", "DBMF", "MLPX", "SGOL", "SIVR", "COPX",
    "XAR", "SGOV", "XLP", "PAVE", "URA", "VTIP", "AIPO",
]


def load_instruments() -> List[str]:
    """Read active instrument list from instruments.json (same file the MCP uses)."""
    try:
        data = json.loads(_INSTRUMENTS_FILE.read_text())
        instruments = data.get("instruments", [])
        if instruments:
            return instruments
    except Exception as e:
        logger.warning(f"Could not load instruments.json: {e} — using fallback list")
    return _FALLBACK_INSTRUMENTS


# ── Public fetcher functions — each matches one or more FetchSpec.source ────────

def fetch_holdings_prices(spec: FetchSpec) -> List[DataReading]:
    """HOLDINGS_PRICES: current price + day-change for all portfolio instruments."""
    symbols = load_instruments()
    now = datetime.datetime.utcnow()
    tickers = yf.Tickers(" ".join(symbols))
    readings = []
    for sym in symbols:
        try:
            info  = tickers.tickers[sym].fast_info
            value = {
                "price":          round(float(info.last_price), 4),
                "prev_close":     round(float(info.previous_close), 4),
                "day_change_pct": round(
                    (info.last_price - info.previous_close) / info.previous_close * 100, 2
                ),
            }
            readings.append(DataReading(
                spec_id=f"{spec.id}:{sym}", value=value,
                source=DataSource.YFINANCE, fetched_at=now,
            ))
        except Exception as e:
            readings.append(DataReading(
                spec_id=f"{spec.id}:{sym}", value=None,
                source=DataSource.YFINANCE, fetched_at=now,
                quality_flags=[f"FETCH_FAILED: {e}"],
            ))
    return readings


def fetch_macro(spec: FetchSpec) -> List[DataReading]:
    """DXY, MOVE, VIX, SP500, KRE, KBE in one call."""
    symbol = _MACRO_SYMBOLS.get(spec.id, "")
    if not symbol:
        symbol = _EQUITY_SYMBOLS.get(spec.id, "")
    if not symbol:
        raise ValueError(f"No yfinance symbol mapping for spec.id={spec.id}")
    return _fetch_single_quote(spec, symbol)


def fetch_commodity_fallback(spec: FetchSpec) -> List[DataReading]:
    """Fallback for commodity specs when FMP fails. Uses futures symbols."""
    symbol = _COMMODITY_FALLBACKS.get(spec.id)
    if not symbol:
        raise ValueError(f"No yfinance fallback symbol for {spec.id}")
    return _fetch_single_quote(spec, symbol)


def fetch_vix_history(spec: FetchSpec) -> List[DataReading]:
    """VIX_30D_AVG and VIX_90D_AVG: download history, compute rolling averages."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=100)  # enough for 90 calendar days
    df    = yf.download("^VIX", start=start.isoformat(), progress=False, auto_adjust=True)
    closes = df["Close"].dropna()
    if closes.empty:
        raise RuntimeError("^VIX history returned empty")

    readings = []
    now = datetime.datetime.utcnow()

    if spec.id in ("VIX_30D_AVG", "VIX_90D_AVG"):
        n = 30 if spec.id == "VIX_30D_AVG" else 62
        if len(closes) < n:
            n = len(closes)
        recent = closes.iloc[-n:]
        avg    = float(recent.mean())
        change = float(closes.iloc[-1]) - float(closes.iloc[-n]) if len(closes) >= n else 0.0
        readings.append(DataReading(
            spec_id=spec.id,
            value={"avg": round(avg, 2), "change_pts": round(change, 2), "n_days": n},
            source=DataSource.YFINANCE, fetched_at=now,
        ))

    return readings


def fetch_instrument_history(spec: FetchSpec, symbol: str,
                              start: str, end: Optional[str] = None) -> List[DataReading]:
    """HISTORICAL_INSTRUMENT_PRICES: ON_DEMAND fetch for a specific symbol + date range."""
    end   = end or datetime.date.today().isoformat()
    df    = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        return [DataReading(
            spec_id=spec.id, value=None,
            source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
            quality_flags=["FETCH_FAILED: empty history"],
        )]
    closes = df["Close"].dropna()
    base   = float(closes.iloc[0])
    last   = float(closes.iloc[-1])
    ret    = (last / base - 1) * 100
    return [DataReading(
        spec_id=f"{spec.id}:{symbol}",
        value={
            "symbol":           symbol,
            "start":            start,
            "end":              end,
            "start_price":      round(base, 4),
            "end_price":        round(last, 4),
            "total_return_pct": round(ret, 2),
            "n_days":           len(closes),
        },
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fetch_single_quote(spec: FetchSpec, symbol: str) -> List[DataReading]:
    info  = yf.Ticker(symbol).fast_info
    value = {
        "price":          round(float(info.last_price), 4),
        "day_change_pct": round(
            (info.last_price - info.previous_close) / info.previous_close * 100, 2
        ),
    }
    return [DataReading(
        spec_id=spec.id, value=value,
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]
