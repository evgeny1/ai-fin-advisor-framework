"""
fred_fetcher.py — FRED REST API fetcher for Treasury yield tenors not
available via yfinance (specifically DGS2, the 2-Year yield).

FRED API is free. Get a key at: https://fred.stlouisfed.org/docs/api/api_key.html
Add to .env: FRED_API_KEY=your_key_here

This fills the gap left by yfinance's partial yield curve (yfinance provides
10Y via ^TNX, 30Y via ^TYX, 13W via ^IRX, but NOT 2Y). The 10Y-2Y spread
is required by M17.computeYieldCurveSignal().
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import requests

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

_BASE = "https://api.stlouisfed.org/fred/series/observations"
_TIMEOUT = 10

# FRED series codes for each yield tenor
_FRED_YIELD_SERIES: Dict[str, str] = {
    "year2":   "DGS2",    # 2-Year Treasury Constant Maturity Rate
    "year5":   "DGS5",    # 5-Year
    "year10":  "DGS10",   # 10-Year
    "year30":  "DGS30",   # 30-Year
    "month3":  "DGS3MO",  # 3-Month
}


def _fred_api_key() -> Optional[str]:
    return os.environ.get("FRED_API_KEY")


def _fetch_latest(series_id: str) -> Optional[float]:
    """Fetch the most recent observation for a FRED series. Returns None if unavailable."""
    key = _fred_api_key()
    if not key:
        return None
    params = {
        "series_id":    series_id,
        "api_key":      key,
        "file_type":    "json",
        "sort_order":   "desc",
        "limit":        5,           # last 5 to skip any trailing "." (missing) values
        "observation_start": (datetime.date.today() - datetime.timedelta(days=10)).isoformat(),
    }
    resp = requests.get(_BASE, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    observations = resp.json().get("observations", [])
    for obs in observations:
        val = obs.get("value", ".")
        if val != ".":
            try:
                return float(val)
            except ValueError:
                continue
    return None


def fetch_yield_curve_fred(spec: FetchSpec) -> List[DataReading]:
    """
    Full yield curve from FRED REST API.
    Provides: 3M, 2Y, 5Y, 10Y, 30Y and all derived spreads.
    Requires FRED_API_KEY in environment (free key from fred.stlouisfed.org).
    Falls back gracefully to None values if key is absent.
    """
    key = _fred_api_key()
    if not key:
        return [DataReading(
            spec_id=spec.id, value=None,
            source=DataSource.FRED_SPREADSHEET_TAB,
            fetched_at=datetime.datetime.utcnow(),
            quality_flags=["UNAVAILABLE: FRED_API_KEY not set — "
                           "get a free key at fred.stlouisfed.org/docs/api/api_key.html"],
        )]

    values: Dict[str, Any] = {}
    for key_name, series_id in _FRED_YIELD_SERIES.items():
        try:
            values[key_name] = _fetch_latest(series_id)
        except Exception as e:
            logger.warning(f"FRED {series_id} failed: {e}")
            values[key_name] = None

    y2  = values.get("year2")
    y10 = values.get("year10")
    y3m = values.get("month3")

    flags = []
    if any(v is None for v in values.values()):
        missing = [k for k, v in values.items() if v is None]
        flags.append(f"PARTIAL: {missing} returned None from FRED")

    return [DataReading(
        spec_id=spec.id,
        value={
            **{k: round(v, 4) if v is not None else None for k, v in values.items()},
            "spread_10y_2y":  round(y10 - y2,  4) if (y10 and y2)  else None,
            "spread_10y_3m":  round(y10 - y3m, 4) if (y10 and y3m) else None,
            "source_note":    "FRED REST API (DGS2/DGS5/DGS10/DGS30/DGS3MO)",
        },
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=flags,
    )]
