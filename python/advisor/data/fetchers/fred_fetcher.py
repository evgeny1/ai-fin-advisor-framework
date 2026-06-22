"""
fred_fetcher.py — FRED REST API dispatcher for all FRED_SPREADSHEET_TAB specs.

Handles:
  YIELD_CURVE         — full Treasury curve (DGS3MO, DGS2, DGS5, DGS10, DGS30)
  SOFR                — Secured Overnight Financing Rate (SOFR)
  DFF                 — Effective Federal Funds Rate (DFF)
  THREEFYTP10         — 10Y Term Premium ACM model (THREEFYTP10)
  THREEFYTP10_TREND   — THREEFYTP10, 10 weekly closes
  REAL_YIELD_10Y_TREND — DGS10 minus T10YIE, 8 weekly closes (GAP-16 follow-up,
                          2026-06-21 — see m18_registry.py for why this is
                          distinct from THREEFYTP10/THREEFYTP10_TREND)
  HY_OAS              — ICE BofA US HY OAS (BAMLH0A0HYM2)
  IG_OAS              — ICE BofA US IG OAS (BAMLC0A0CM)
  CCC_OAS             — ICE BofA CCC & Lower OAS (BAMLH0A3HYC)
  BBB_OAS             — ICE BofA BBB Corporate OAS (BAMLC0A4CBBB)

FRED API is free. Get a key at: https://fred.stlouisfed.org/docs/api/api_key.html
Add to .env: FRED_API_KEY=your_key_here
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import requests

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

_BASE    = "https://api.stlouisfed.org/fred/series/observations"
_TIMEOUT = 10

# GAP-16 follow-up (2026-06-21): weekly window for the computed real-yield
# trend series. Matches DXY_TREND's 8-week window (yfinance_fetcher.py)
# since range_position.py pairs the two as IHP's sub-condition drivers and
# directional_trend()'s materiality threshold should mean the same thing
# across both windows.
_REAL_YIELD_WEEKS = 8

# ── FRED series IDs per M18 spec.id ───────────────────────────────────────────

# Yield curve tenors (YIELD_CURVE spec)
_YIELD_SERIES: Dict[str, str] = {
    "month3": "DGS3MO",
    "year2":  "DGS2",
    "year5":  "DGS5",
    "year10": "DGS10",
    "year30": "DGS30",
}

# Single-series specs: spec.id → (fred_series_id, value_key, multiply_100)
# multiply_100=True: FRED returns percentage points (e.g. 2.78%) → convert to bps (278bps)
# multiply_100=False: FRED returns value in native unit (rate %, term premium %)
_SINGLE_SERIES: Dict[str, tuple] = {
    "SOFR":         ("SOFR",         "sofr",              False),
    "DFF":          ("DFF",          "dff",               False),
    "THREEFYTP10":  ("THREEFYTP10",  "term_premium_bps",  False),
    "HY_OAS":       ("BAMLH0A0HYM2", "current",           True),   # FRED: percent → bps
    "IG_OAS":       ("BAMLC0A0CM",   "current",           True),   # FRED: percent → bps
    "CCC_OAS":      ("BAMLH0A3HYC",  "current",           True),   # FRED: percent → bps
    "BBB_OAS":      ("BAMLC0A4CBBB", "current",           True),   # FRED: percent → bps
}


def _api_key() -> Optional[str]:
    return os.environ.get("FRED_API_KEY")


def _fetch_latest(series_id: str) -> Optional[float]:
    """Fetch most recent non-missing observation from FRED."""
    key = _api_key()
    if not key:
        return None
    params = {
        "series_id":         series_id,
        "api_key":           key,
        "file_type":         "json",
        "sort_order":        "desc",
        "limit":             5,
        "observation_start": (datetime.date.today() - datetime.timedelta(days=14)).isoformat(),
    }
    resp = requests.get(_BASE, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    for obs in resp.json().get("observations", []):
        val = obs.get("value", ".")
        if val not in (".", ""):
            try:
                return float(val)
            except ValueError:
                continue
    return None


def _fetch_history(series_id: str, weeks: int) -> List[float]:
    """
    Fetch up to `weeks` most-recent non-missing observations, oldest-first.
    Added to close ENG-13: THREEFYTP10's §13 sustaining/failure conditions
    ("sustained >= N weeks") need a short trailing window, not just the
    latest print — _fetch_latest() alone can't evaluate those.
    """
    key = _api_key()
    if not key:
        return []
    params = {
        "series_id":         series_id,
        "api_key":           key,
        "file_type":         "json",
        "sort_order":        "asc",
        "observation_start": (datetime.date.today() - datetime.timedelta(weeks=weeks + 2)).isoformat(),
    }
    resp = requests.get(_BASE, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    vals: List[float] = []
    for obs in resp.json().get("observations", []):
        v = obs.get("value", ".")
        if v not in (".", ""):
            try:
                vals.append(float(v))
            except ValueError:
                continue
    return vals[-weeks:] if vals else []


def _fetch_history_with_dates(series_id: str, days: int) -> List[tuple]:
    """
    Fetch up to `days` calendar days of non-missing (date_str, value)
    observations, oldest-first. Added for REAL_YIELD_10Y_TREND (GAP-16
    follow-up, 2026-06-21): unlike _fetch_history() above, computing
    real_yield = DGS10 - T10YIE requires aligning two daily series by
    date before subtracting — a bare value list isn't enough.
    """
    key = _api_key()
    if not key:
        return []
    params = {
        "series_id":         series_id,
        "api_key":           key,
        "file_type":         "json",
        "sort_order":        "asc",
        "observation_start": (datetime.date.today() - datetime.timedelta(days=days)).isoformat(),
    }
    resp = requests.get(_BASE, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    out: List[tuple] = []
    for obs in resp.json().get("observations", []):
        v = obs.get("value", ".")
        if v not in (".", ""):
            try:
                out.append((obs["date"], float(v)))
            except ValueError:
                continue
    return out


def _resample_weekly(daily: List[tuple], weeks: int) -> List[float]:
    """
    Collapse a daily (date_str, value) series — sorted oldest-first — to one
    value per ISO calendar week (the last available observation in each
    week), capped to the most recent `weeks` weeks. Mirrors the implicit
    weekly resampling yfinance_fetcher.py gets from
    yf.download(..., interval="1wk") for the YFINANCE *_TREND specs, so
    directional_trend()'s materiality threshold means the same thing
    regardless of which data source a *_TREND spec happens to use.
    """
    by_week: Dict[tuple, float] = {}
    for date_str, value in daily:
        d = datetime.date.fromisoformat(date_str)
        iso_year, iso_week, _ = d.isocalendar()
        by_week[(iso_year, iso_week)] = value  # ascending input -> later date in the same week wins
    ordered = [by_week[k] for k in sorted(by_week.keys())]
    return ordered[-weeks:] if ordered else []


# ── Public dispatcher ──────────────────────────────────────────────────────────

def fetch_yield_curve_fred(spec: FetchSpec) -> List[DataReading]:
    """
    Dispatcher for all FRED_SPREADSHEET_TAB specs. Routes by spec.id.
    Falls back gracefully to None values if FRED_API_KEY is absent.
    """
    if not _api_key():
        return [DataReading(
            spec_id=spec.id, value=None,
            source=DataSource.FRED_SPREADSHEET_TAB,
            fetched_at=datetime.datetime.utcnow(),
            quality_flags=["UNAVAILABLE: FRED_API_KEY not set — "
                           "get a free key at fred.stlouisfed.org/docs/api/api_key.html"],
        )]

    if spec.id == "YIELD_CURVE":
        return _fetch_yield_curve(spec)

    if spec.id == "THREEFYTP10_TREND":
        return _fetch_trend_series(spec, "THREEFYTP10", weeks=10)

    if spec.id == "REAL_YIELD_10Y_TREND":
        return _fetch_real_yield_trend(spec, weeks=_REAL_YIELD_WEEKS)

    if spec.id in _SINGLE_SERIES:
        return _fetch_single_series(spec)

    # Unknown spec — return unavailable
    return [DataReading(
        spec_id=spec.id, value=None,
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=[f"UNHANDLED: no FRED series mapping for spec.id='{spec.id}'"],
    )]


def _fetch_yield_curve(spec: FetchSpec) -> List[DataReading]:
    """Fetch full US Treasury yield curve from FRED."""
    values: Dict[str, Any] = {}
    flags: List[str] = []

    for key_name, series_id in _YIELD_SERIES.items():
        try:
            values[key_name] = _fetch_latest(series_id)
        except Exception as e:
            logger.warning(f"FRED {series_id} failed: {e}")
            values[key_name] = None

    y2  = values.get("year2")
    y10 = values.get("year10")
    y3m = values.get("month3")

    if any(v is None for v in values.values()):
        missing = [k for k, v in values.items() if v is None]
        flags.append(f"PARTIAL: {missing} returned None from FRED")

    return [DataReading(
        spec_id=spec.id,
        value={
            **{k: round(v, 4) if v is not None else None for k, v in values.items()},
            "spread_10y_2y": round(y10 - y2, 4)  if (y10 and y2)  else None,
            "spread_10y_3m": round(y10 - y3m, 4) if (y10 and y3m) else None,
            "source_note":   "FRED REST API (DGS3MO/DGS2/DGS5/DGS10/DGS30)",
        },
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=flags,
    )]


def _fetch_single_series(spec: FetchSpec) -> List[DataReading]:
    """Fetch a single-value FRED series (credit spreads, rates, term premium)."""
    fred_series, value_key, multiply_100 = _SINGLE_SERIES[spec.id]

    try:
        val = _fetch_latest(fred_series)
    except Exception as e:
        logger.warning(f"FRED {fred_series} ({spec.id}) failed: {e}")
        val = None

    flags = []
    if val is None:
        flags.append(f"UNAVAILABLE: FRED series {fred_series} returned no data")

    # Convert percent → bps for OAS series (FRED stores in percentage points)
    if val is not None and multiply_100:
        val = round(val * 100, 2)

    # Return value as {"current": float} so get_scalar() can extract it
    value = {"current": round(val, 4) if val is not None else val} if val is not None else None

    return [DataReading(
        spec_id=spec.id,
        value=value,
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=flags,
    )]


def _fetch_trend_series(spec: FetchSpec, series_id: str, weeks: int) -> List[DataReading]:
    """THREEFYTP10_TREND dispatcher target — see _fetch_history() above."""
    try:
        vals = _fetch_history(series_id, weeks)
    except Exception as e:
        logger.warning(f"FRED {series_id} trend fetch failed: {e}")
        return [DataReading(spec_id=spec.id, value=None,
                            source=DataSource.FRED_SPREADSHEET_TAB,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"FETCH_FAILED: {e}"])]
    if not vals:
        return [DataReading(spec_id=spec.id, value=None,
                            source=DataSource.FRED_SPREADSHEET_TAB,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"UNAVAILABLE: no observations for {series_id} "
                                          "(FRED_API_KEY missing or series empty)"])]
    return [DataReading(
        spec_id=spec.id,
        value={"closes": vals, "n_weeks": len(vals)},
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=([] if len(vals) >= weeks else
                       [f"PARTIAL: only {len(vals)}/{weeks} weeks available"]),
    )]


def _fetch_real_yield_trend(spec: FetchSpec, weeks: int) -> List[DataReading]:
    """
    REAL_YIELD_10Y_TREND dispatcher target (GAP-16 follow-up, 2026-06-21).

    Computes real_yield = DGS10 (10Y nominal Treasury yield) - T10YIE (10Y
    breakeven inflation), both daily FRED series, then resamples to `weeks`
    weekly closes for analysis/trend.py's directional_trend(). This is the
    textbook Fisher-equation real yield -- distinct from THREEFYTP10 (10Y
    *term premium*, the Adrian-Crump-Moench compensation bond investors
    demand for duration risk). The two are not interchangeable: term
    premium can rise or fall independent of the Fed's policy path, while
    real yield is exactly the variable that drives precious metals'
    opportunity cost. Replaces THREEFYTP10 as the real-yield driver in
    analysis/range_position.py's IHP advisory.
    """
    try:
        nominal   = _fetch_history_with_dates("DGS10",  days=weeks * 7 + 21)
        breakeven = _fetch_history_with_dates("T10YIE", days=weeks * 7 + 21)
    except Exception as e:
        logger.warning(f"FRED DGS10/T10YIE real-yield fetch failed: {e}")
        return [DataReading(spec_id=spec.id, value=None,
                            source=DataSource.FRED_SPREADSHEET_TAB,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"FETCH_FAILED: {e}"])]

    if not nominal or not breakeven:
        missing = []
        if not nominal:   missing.append("DGS10")
        if not breakeven: missing.append("T10YIE")
        return [DataReading(spec_id=spec.id, value=None,
                            source=DataSource.FRED_SPREADSHEET_TAB,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"UNAVAILABLE: no observations for {', '.join(missing)} "
                                          "(FRED_API_KEY missing or series empty)"])]

    breakeven_by_date = dict(breakeven)
    daily_real_yield: List[tuple] = [
        (date, value - breakeven_by_date[date])
        for date, value in nominal
        if date in breakeven_by_date
    ]
    if not daily_real_yield:
        return [DataReading(spec_id=spec.id, value=None,
                            source=DataSource.FRED_SPREADSHEET_TAB,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=["UNAVAILABLE: DGS10 and T10YIE observation dates "
                                          "did not overlap on any day in the window"])]

    closes = _resample_weekly(daily_real_yield, weeks)
    if not closes:
        return [DataReading(spec_id=spec.id, value=None,
                            source=DataSource.FRED_SPREADSHEET_TAB,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=["UNAVAILABLE: weekly resample produced no points"])]

    flags = []
    if len(closes) < weeks:
        flags.append(f"PARTIAL: only {len(closes)}/{weeks} weeks available")
    return [DataReading(
        spec_id=spec.id,
        value={"closes": [round(c, 4) for c in closes], "n_weeks": len(closes)},
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=flags,
    )]
