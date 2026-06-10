"""
yfinance_fetcher.py — Direct yfinance calls for all YFINANCE-sourced specs.
A single dispatcher (yfinance_dispatcher) handles all spec.id routing — one
registration in FetchRegistry covers every YFINANCE spec.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

# ── instruments.json path ─────────────────────────────────────────────────────
# Layout: My Drive/dev/
#           AI Financial Advisor Framework/python/advisor/data/fetchers/  ← here (6 levels below dev/)
#           market_data_mcp/instruments.json
_MCP_DIR = Path(os.environ.get(
    "ADVISOR_MCP_DIR",
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "market_data_mcp"),
))
_INSTRUMENTS_FILE = _MCP_DIR / "instruments.json"
_FALLBACK_INSTRUMENTS = [
    "DBMF", "MLPX", "SGOL", "SIVR", "COPX",
    "XAR", "SGOV", "XLP", "VTIP", "AIPO",
]

# ── Symbol map: spec.id → yfinance ticker ─────────────────────────────────────
_SYMBOL_MAP: Dict[str, str] = {
    # Energy
    "BRENT_CRUDE":  "BZ=F",
    "WTI":          "CL=F",
    "NATURAL_GAS":  "NG=F",
    "NATGAS_HENRY_HUB": "NG=F",
    # Precious metals
    "GOLD_SPOT":    "GC=F",
    "SILVER":       "SI=F",
    # Broad equities
    "SP500":        "^GSPC",
    "NASDAQ_COMP":  "^IXIC",
    "DOW":          "^DJI",
    "RUSSELL2000":  "^RUT",
    # Volatility / macro
    "VIX":          "^VIX",
    "MOVE":         "^MOVE",
    "DXY":          "DX-Y.NYB",
    # Banks
    "KRE":          "KRE",
    "KBE":          "KBE",
    # Treasury yield tenors available on yfinance
    "YIELD_CURVE_10Y": "^TNX",
    "YIELD_CURVE_30Y": "^TYX",
    "YIELD_CURVE_3M":  "^IRX",
}


# ── Public dispatcher — register this ONE function for DataSource.YFINANCE ────

def yfinance_dispatcher(spec: FetchSpec) -> List[DataReading]:
    """
    Single entry point for all YFINANCE-sourced specs.
    Routes by spec.id so FetchRegistry needs only one registration.
    """
    if spec.id == "HOLDINGS_PRICES":
        return fetch_holdings_prices(spec)
    if spec.id in ("VIX_30D_AVG", "VIX_90D_AVG"):
        return fetch_vix_history(spec)
    if spec.id == "BROAD_EQUITY_TRAILING":
        return fetch_broad_equity_trailing(spec)
    if spec.id == "YIELD_CURVE":
        return fetch_yield_curve_partial(spec)
    if spec.id == "HISTORICAL_INSTRUMENT_PRICES":
        raise ValueError("HISTORICAL_INSTRUMENT_PRICES is ON_DEMAND — call fetch_one() explicitly")
    # Default: single-quote fetch using _SYMBOL_MAP
    return _fetch_single(spec)


# ── Holdings prices ───────────────────────────────────────────────────────────

def load_instruments() -> List[str]:
    """Read active instrument list from instruments.json (shared with MCP server)."""
    try:
        data = json.loads(_INSTRUMENTS_FILE.read_text())
        instruments = data.get("instruments", [])
        if instruments:
            logger.debug(f"Loaded {len(instruments)} instruments from {_INSTRUMENTS_FILE}")
            return instruments
    except Exception as e:
        logger.warning(f"instruments.json not readable at {_INSTRUMENTS_FILE}: {e} — using fallback")
    return _FALLBACK_INSTRUMENTS


def fetch_holdings_prices(spec: FetchSpec) -> List[DataReading]:
    """Current price + day-change for all portfolio instruments."""
    symbols = load_instruments()
    now = datetime.datetime.utcnow()
    tickers = yf.Tickers(" ".join(symbols))
    readings = []
    for sym in symbols:
        try:
            info = tickers.tickers[sym].fast_info
            readings.append(DataReading(
                spec_id=f"{spec.id}:{sym}",
                value={
                    "symbol":         sym,
                    "price":          round(float(info.last_price), 4),
                    "prev_close":     round(float(info.previous_close), 4),
                    "day_change_pct": round(
                        (info.last_price - info.previous_close) / info.previous_close * 100, 2
                    ),
                },
                source=DataSource.YFINANCE, fetched_at=now,
            ))
        except Exception as e:
            readings.append(DataReading(
                spec_id=f"{spec.id}:{sym}", value=None,
                source=DataSource.YFINANCE, fetched_at=now,
                quality_flags=[f"FETCH_FAILED: {e}"],
            ))
    return readings


# ── VIX rolling averages ──────────────────────────────────────────────────────

def fetch_vix_history(spec: FetchSpec) -> List[DataReading]:
    """VIX_30D_AVG or VIX_90D_AVG: download history, compute rolling average."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=110)
    df = yf.download("^VIX", start=start.isoformat(), progress=False, auto_adjust=True)
    if df.empty or "Close" not in df.columns:
        raise RuntimeError("^VIX history returned empty")
    closes_raw = df["Close"].dropna()
    closes = closes_raw.values.tolist() if hasattr(closes_raw, "values") else list(closes_raw)
    if not closes:
        raise RuntimeError("^VIX history returned empty")
    n = 30 if spec.id == "VIX_30D_AVG" else 62
    n = min(n, len(closes))
    recent = closes[-n:]
    avg    = sum(recent) / len(recent)
    change = recent[-1] - recent[0] if len(recent) > 1 else 0.0
    return [DataReading(
        spec_id=spec.id,
        value={"avg": round(avg, 2), "change_pts": round(change, 2), "n_days": n},
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]


# ── Broad equity trailing returns ─────────────────────────────────────────────

def fetch_broad_equity_trailing(spec: FetchSpec) -> List[DataReading]:
    """BROAD_EQUITY_TRAILING: S&P 500 30d and 90d pct-change from ^GSPC history."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=110)
    df = yf.download("^GSPC", start=start.isoformat(), progress=False, auto_adjust=True)
    if df.empty or "Close" not in df.columns:
        raise RuntimeError("^GSPC history returned empty")
    raw = df["Close"].dropna()
    closes = raw.values.flatten().tolist()
    if not closes:
        raise RuntimeError("^GSPC history returned empty")
    current = closes[-1]

    def pct(n: int) -> float:
        idx = max(len(closes) - n, 0)
        return round((current / closes[idx] - 1) * 100, 2)

    return [DataReading(
        spec_id=spec.id,
        value={"return_30d_pct": pct(22), "return_90d_pct": pct(64),
               "current": round(current, 2)},
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]


# ── Yield curve (partial — 2Y unavailable from yfinance) ─────────────────────

def fetch_yield_curve_partial(spec: FetchSpec) -> List[DataReading]:
    """
    Available tenors via yfinance: 10Y (^TNX), 30Y (^TYX), 13W (^IRX).
    2Y is NOT available — 10Y-2Y spread will be None.
    ⚠ Use FMP MCP for the full curve including 2Y.
    """
    tenor_map = {"^TNX": "year10", "^TYX": "year30", "^IRX": "month3"}
    values: Dict[str, Any] = {}
    for sym, key in tenor_map.items():
        try:
            values[key] = round(float(yf.Ticker(sym).fast_info.last_price), 4)
        except Exception as e:
            values[key] = None
            logger.warning(f"Yield curve {sym} ({key}) failed: {e}")

    y10 = values.get("year10")
    y3m = values.get("month3")
    return [DataReading(
        spec_id=spec.id,
        value={
            "year10":        y10,
            "year30":        values.get("year30"),
            "month3":        y3m,
            "year2":         None,
            "spread_10y_2y": None,
            "spread_10y_3m": round(y10 - y3m, 4) if (y10 and y3m) else None,
            "source_note":   "yfinance ^TNX/^TYX/^IRX. year2 unavailable — FMP MCP has full curve.",
        },
        source=DataSource.YFINANCE,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=["PARTIAL: year2=None, spread_10y_2y=None — use FMP MCP for full curve"],
    )]


# ── ON_DEMAND: single instrument history ─────────────────────────────────────

def fetch_instrument_history(spec: FetchSpec, symbol: str,
                             start: str, end: Optional[str] = None) -> List[DataReading]:
    """HISTORICAL_INSTRUMENT_PRICES: ON_DEMAND. Call via registry.fetch_one()."""
    end = end or datetime.date.today().isoformat()
    df  = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        return [DataReading(spec_id=f"{spec.id}:{symbol}", value=None,
                            source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=["FETCH_FAILED: empty history"])]
    closes = df["Close"].dropna().values.flatten().tolist()
    base, last = closes[0], closes[-1]
    return [DataReading(
        spec_id=f"{spec.id}:{symbol}",
        value={"symbol": symbol, "start": start, "end": end,
               "start_price": round(base, 4), "end_price": round(last, 4),
               "total_return_pct": round((last / base - 1) * 100, 2),
               "n_days": len(closes)},
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]


# ── Internal: single-quote by spec.id via _SYMBOL_MAP ────────────────────────

def _fetch_single(spec: FetchSpec) -> List[DataReading]:
    symbol = _SYMBOL_MAP.get(spec.id)
    if not symbol:
        raise ValueError(
            f"No yfinance symbol for spec.id='{spec.id}'. "
            f"Add it to _SYMBOL_MAP in yfinance_fetcher.py."
        )
    info = yf.Ticker(symbol).fast_info
    return [DataReading(
        spec_id=spec.id,
        value={
            "symbol":         symbol,
            "price":          round(float(info.last_price), 4),
            "day_change_pct": round(
                (info.last_price - info.previous_close) / info.previous_close * 100, 2
            ),
        },
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]
