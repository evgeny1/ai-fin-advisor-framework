"""
fmp_fetcher.py — Financial Modeling Prep REST API calls.
Covers: commodities (BZUSD/GCUSD/SIUSD), indexes (^VIX/^GSPC),
        treasury rates (full yield curve), historical EOD chart.
FMP plan-tier map: M18_MarketDataFetch.md FMP_PLAN_TIER_MAP.
NEVER retry ACCESS DENIED endpoints (^MOVE, ^SPX, forex, ETF quotes).
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import requests

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

_BASE = "https://financialmodelingprep.com/api"
_STABLE = "https://financialmodelingprep.com/stable"
_TIMEOUT = 10

# FMP commodity symbols confirmed working free tier June 4, 2026
_COMMODITY_SYMBOLS: Dict[str, str] = {
    "BRENT_CRUDE": "BZUSD",
    "GOLD_SPOT":   "GCUSD",
    "SILVER":      "SIUSD",
}

# FMP index symbols confirmed working free tier
_INDEX_SYMBOLS: Dict[str, str] = {
    "VIX":   "%5EVIX",    # ^VIX URL-encoded
    "SP500": "%5EGSPC",   # ^GSPC URL-encoded
}


def _api_key() -> str:
    key = os.environ.get("FMP_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "FMP_API_KEY not set. Export it or add to .env: export FMP_API_KEY=your_key"
        )
    return key


def _get(url: str, params: Optional[Dict] = None) -> Any:
    params = params or {}
    params["apikey"] = _api_key()
    resp = requests.get(url, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── Commodities ───────────────────────────────────────────────────────────────

def fetch_commodity(spec: FetchSpec) -> List[DataReading]:
    """
    Fetch a single commodity quote (BZUSD, GCUSD, SIUSD).
    Endpoint: /api/v3/quote/{symbol}
    """
    symbol = _COMMODITY_SYMBOLS.get(spec.id)
    if not symbol:
        raise ValueError(f"No FMP commodity symbol for spec.id={spec.id}")
    data   = _get(f"{_BASE}/v3/quote/{symbol}")
    if not data:
        raise RuntimeError(f"Empty response for {symbol}")
    item   = data[0] if isinstance(data, list) else data
    return [DataReading(
        spec_id=spec.id,
        value={"price": round(float(item["price"]), 4),
               "day_change_pct": round(float(item.get("changesPercentage", 0)), 2)},
        source=DataSource.FMP_COMMODITY,
        fetched_at=datetime.datetime.utcnow(),
        raw=item,
    )]


# ── Indexes ───────────────────────────────────────────────────────────────────

def fetch_index(spec: FetchSpec) -> List[DataReading]:
    """
    Fetch index quote (^VIX, ^GSPC). Never retry ^MOVE, ^SPX, DXY — ACCESS DENIED.
    Endpoint: /api/v3/quote/{encoded_symbol}
    """
    symbol = _INDEX_SYMBOLS.get(spec.id)
    if not symbol:
        raise ValueError(
            f"No FMP index symbol for spec.id={spec.id}. "
            f"If this is ^MOVE or DXY, use yfinance fetcher instead."
        )
    data = _get(f"{_BASE}/v3/quote/{symbol}")
    if not data:
        raise RuntimeError(f"Empty response for {spec.id}")
    item = data[0] if isinstance(data, list) else data
    return [DataReading(
        spec_id=spec.id,
        value={"price": round(float(item["price"]), 4),
               "day_change_pct": round(float(item.get("changesPercentage", 0)), 2)},
        source=DataSource.FMP_INDEXES,
        fetched_at=datetime.datetime.utcnow(),
        raw=item,
    )]


# ── Treasury Rates (Yield Curve) ──────────────────────────────────────────────

def fetch_yield_curve(spec: FetchSpec) -> List[DataReading]:
    """
    Full US Treasury par yield curve via FMP economics treasury-rates endpoint.
    Returns most recent entry. Derives: 10Y, 2Y, 30Y, 10Y-2Y spread, 10Y-3M spread.
    Endpoint: /api/v4/treasury
    """
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=7)).isoformat()
    data  = _get(f"{_BASE}/v4/treasury", {"from": start, "to": today.isoformat()})
    if not data:
        raise RuntimeError("Empty treasury-rates response")
    latest = data[0]  # newest-first
    y2   = float(latest.get("year2",  0))
    y3m  = float(latest.get("month3", 0))
    y10  = float(latest.get("year10", 0))
    y30  = float(latest.get("year30", 0))
    return [DataReading(
        spec_id=spec.id,
        value={
            "date":           latest.get("date"),
            "year2":          round(y2,  4),
            "year10":         round(y10, 4),
            "year30":         round(y30, 4),
            "spread_10y_2y":  round(y10 - y2,  4),
            "spread_10y_3m":  round(y10 - y3m, 4),
            "full_curve":     {k: v for k, v in latest.items() if k != "date"},
        },
        source=DataSource.FMP_ECONOMICS_TREASURY_RATES,
        fetched_at=datetime.datetime.utcnow(),
        raw=latest,
    )]


# ── Historical chart (VIX/equity rolling averages) ────────────────────────────

def fetch_vix_history_fmp(spec: FetchSpec) -> List[DataReading]:
    """
    VIX_30D_AVG / VIX_90D_AVG via FMP chart historical-price-eod-light.
    Confirmed working: ^VIX, SPY at current plan tier.
    """
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=100)).isoformat()
    data  = _get(
        f"{_STABLE}/historical-price-eod-light",
        {"symbol": "%5EVIX", "from": start, "to": today.isoformat()},
    )
    # Response: list newest-first [{date, close, ...}]
    if not data:
        raise RuntimeError("Empty VIX history from FMP chart")
    closes = [float(d["close"]) for d in data if d.get("close") is not None]
    if not closes:
        raise RuntimeError("No valid closes in VIX history")
    closes.reverse()  # now oldest-first

    readings = []
    now = datetime.datetime.utcnow()
    for days, sid in [(30, "VIX_30D_AVG"), (62, "VIX_90D_AVG")]:
        if spec.id != sid:
            continue
        n      = min(days, len(closes))
        recent = closes[-n:]
        avg    = sum(recent) / len(recent)
        change = recent[-1] - recent[0] if len(recent) > 1 else 0.0
        readings.append(DataReading(
            spec_id=spec.id,
            value={"avg": round(avg, 2), "change_pts": round(change, 2), "n_days": n},
            source=DataSource.FMP_CHART, fetched_at=now,
        ))
    return readings


def fetch_broad_equity_trailing(spec: FetchSpec) -> List[DataReading]:
    """
    BROAD_EQUITY_TRAILING: S&P 500 30d and 90d pct-change from ^GSPC history.
    """
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=100)).isoformat()
    data  = _get(
        f"{_STABLE}/historical-price-eod-light",
        {"symbol": "%5EGSPC", "from": start, "to": today.isoformat()},
    )
    if not data:
        raise RuntimeError("Empty ^GSPC history from FMP")
    closes = [float(d["close"]) for d in data if d.get("close") is not None]
    closes.reverse()  # oldest-first
    current = closes[-1]

    def pct(n: int) -> float:
        if len(closes) < n:
            return 0.0
        return round((current / closes[-n] - 1) * 100, 2)

    return [DataReading(
        spec_id=spec.id,
        value={"return_30d_pct": pct(30), "return_90d_pct": pct(62), "current": round(current, 2)},
        source=DataSource.FMP_INDEXES, fetched_at=datetime.datetime.utcnow(),
    )]
