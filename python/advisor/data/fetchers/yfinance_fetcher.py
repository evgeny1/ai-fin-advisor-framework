"""
yfinance_fetcher.py — Direct yfinance calls for all YFINANCE-sourced specs.
A single dispatcher (yfinance_dispatcher) handles all spec.id routing — one
registration in FetchRegistry covers every YFINANCE spec.
"""
from __future__ import annotations

import concurrent.futures
import contextlib
import datetime
import json
import logging
import os
import threading
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

# yfinance's underlying session/cache is not safe under concurrent calls
# from multiple threads. FetchRegistry.fetch_all() (data/fetch_registry.py)
# runs every registered spec in a ThreadPoolExecutor(max_workers=8), and
# several *_TREND specs (DXY_TREND, BRENT_TREND, GOLD_TREND, SP500_TREND,
# COPPER_TREND, URANIUM_TREND, COPX_PRICE_TREND) plus the point-quote
# fetchers below all call yf.download()/yf.Ticker() concurrently.
#
# Found 2026-06-20: under concurrent load, yf.download() calls for
# different symbols returned identical (wrong-symbol) closes arrays
# across multiple *_TREND readings -- e.g. DXY_TREND and BRENT_TREND came
# back with the exact same array, and COPPER_TREND/GOLD_TREND/
# URANIUM_TREND/SP500_TREND/COPX_PRICE_TREND another shared array. This is
# a known yfinance thread-safety issue (shared session/cache state), not a
# FetchRegistry or _SYMBOL_MAP/_TREND_SPECS bug -- each call site here
# already passes the correct symbol.
#
# Serializing all yfinance network calls behind one lock fixes it.
# fred_fetcher.py's FRED-sourced fetches are unaffected (different client)
# and keep running concurrently in the same ThreadPoolExecutor batch.
_YF_LOCK = threading.Lock()

# Found 2026-06-24: an illiquid/rate-limited symbol can make the underlying
# Yahoo Finance HTTP call retry for many minutes without raising — and
# because _YF_LOCK is a single process-wide lock, that one stuck call blocks
# every other yfinance-sourced spec too, for the rest of the MCP server
# process's life (acquire() with no timeout blocks forever). fetch_registry's
# per-spec timeout bounds fetch_all() for THIS session, but a future yfinance
# call would still hang forever re-acquiring a lock the stuck thread never
# releases. _yf_lock_guard() makes acquisition itself bounded: a spec that
# can't get the lock in time fails fast with a clear error instead of
# joining the pile-up.
_YF_LOCK_TIMEOUT_SECONDS = 20.0


@contextlib.contextmanager
def _yf_lock_guard(timeout: float = _YF_LOCK_TIMEOUT_SECONDS):
    acquired = _YF_LOCK.acquire(timeout=timeout)
    if not acquired:
        raise TimeoutError(
            f"yfinance lock busy for >{timeout}s — another fetch is likely hung"
        )
    try:
        yield
    finally:
        _YF_LOCK.release()


# ENG-69 (2026-07-22): yfinance 0.2.58's threaded download() path waits on a
# COUNT of entries in its shared results dict (see yfinance/multi.py:
# `while len(shared._DFS) < len(tickers): sleep(...)`), not a KEY check --
# even for a single requested ticker. A straggler worker thread left over
# from an earlier, unrelated yf.download() call (e.g. TREND_SIGNAL_HISTORY's
# 16-symbol batch) can satisfy that count with a DIFFERENT ticker's data
# after THIS call's own shared._DFS reset. Confirmed live: NASDAQ_30D_RETURN
# (^IXIC) returned SIVR's series this way -- the old "Close" in df.columns
# check only verified the price-TYPE level was present, never that the
# requested symbol specifically was among the ticker-level columns actually
# returned. _yf_lock_guard() serializes this codebase's OWN call sites but
# cannot stop a straggler thread from a PRIOR call outliving the lock hold
# that spawned it -- this check is the backstop: fail loud instead of
# silently computing a real-looking result from the wrong ticker.
def _extract_closes(df: "pd.DataFrame", symbol: str, context: str) -> List[float]:
    """Verify `symbol` is present in a yf.download() response and return its
    dropna'd, flattened Close values. Raises RuntimeError on mismatch rather
    than returning another ticker's data. `context` (usually spec.id) is
    included in the error for log/flag readability.

    Real yf.download() calls in this file always keep the ticker level in
    df["Close"]'s columns (multi_level_index defaults True and is never
    overridden here), so `close_block` is expected to be a DataFrame with
    `.columns`. If it's a bare Series instead (only reachable via a test
    mock that doesn't model the ticker level, or a future yfinance version
    that behaves differently) there's no ticker information to check against
    -- fall back to trusting it rather than failing on a shape our own real
    call sites never actually produce.
    """
    close_block = df["Close"]
    if not hasattr(close_block, "columns"):
        return close_block.dropna().values.flatten().tolist()
    cols = list(close_block.columns)
    if symbol not in cols:
        raise RuntimeError(
            f"{context}: expected {symbol!r} in yfinance response, got "
            f"{cols!r} instead -- likely cross-ticker contamination "
            f"(ENG-69), not genuine data unavailability. Treating as a "
            f"failed fetch rather than trusting the wrong ticker's numbers."
        )
    return close_block[symbol].dropna().values.flatten().tolist()


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
    # Industrial metals (§13 M19)
    "COPPER_SPOT":  "HG=F",
    "URANIUM_SPOT": "UX=F",  # ⚠ unconfirmed/illiquid — see m18_registry.py note
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

# Weekly trend specs: spec.id -> (yfinance ticker, weeks of history) ───────
# Added to close ENG-13: trailing-window §13 conditions need N weeks of
# history, fetchable in one call — same single-request pattern as
# VIX_30D_AVG/BROAD_EQUITY_TRAILING below. See analysis/trend.py for the
# pure evaluation logic these feed.
_TREND_SPECS: Dict[str, tuple] = {
    "DXY_TREND":        ("DX-Y.NYB", 8),
    "BRENT_TREND":      ("BZ=F",     8),
    "GOLD_TREND":       ("GC=F",     8),
    "SP500_TREND":      ("^GSPC",    8),
    "COPPER_TREND":     ("HG=F",    12),
    "URANIUM_TREND":    ("UX=F",    12),
    "COPX_PRICE_TREND": ("COPX",     8),
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
    if spec.id == "NASDAQ_30D_RETURN":
        return fetch_nasdaq_trailing(spec)
    if spec.id in _TREND_SPECS:
        symbol, weeks = _TREND_SPECS[spec.id]
        return fetch_weekly_trend(spec, symbol, weeks)
    if spec.id == "YIELD_CURVE":
        return fetch_yield_curve_partial(spec)
    if spec.id == "HISTORICAL_INSTRUMENT_PRICES":
        raise ValueError("HISTORICAL_INSTRUMENT_PRICES is ON_DEMAND — call fetch_one() explicitly")
    if spec.id == "TREND_SIGNAL_HISTORY":
        return fetch_trend_signal_histories(spec)
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


def write_instruments_json(tickers: List[str]) -> Path:
    """
    Write the active §11.3 instrument list to instruments.json (ENG-25).

    Called once per session from _tool_run_computation() right after
    Calibration_State.md §11.3 is parsed — never from memory. Local-only:
    instruments.json lives outside the framework git repo (sibling
    market_data_mcp/ folder) and is NEVER committed (@see M12 STEP 4b).

    Raises on failure (caller wraps in try/except and flags rather than
    hard-stopping the session — see mcp_server.py _tool_run_computation).
    """
    payload = {
        "instruments": list(tickers),
        "last_updated": datetime.date.today().isoformat(),
        "session": f"{datetime.date.today().isoformat()} advisory",
    }
    _MCP_DIR.mkdir(parents=True, exist_ok=True)
    _INSTRUMENTS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"Wrote {len(tickers)} instruments to {_INSTRUMENTS_FILE}")
    return _INSTRUMENTS_FILE


def fetch_holdings_prices(spec: FetchSpec) -> List[DataReading]:
    """Current price + day-change for all portfolio instruments."""
    symbols = load_instruments()
    now = datetime.datetime.utcnow()
    readings = []
    with _yf_lock_guard():
        tickers = yf.Tickers(" ".join(symbols))
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
    with _yf_lock_guard():
        df = yf.download("^VIX", start=start.isoformat(), progress=False, auto_adjust=True)
    if df.empty or "Close" not in df.columns:
        raise RuntimeError("^VIX history returned empty")
    closes = _extract_closes(df, "^VIX", spec.id)
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
    with _yf_lock_guard():
        df = yf.download("^GSPC", start=start.isoformat(), progress=False, auto_adjust=True)
    if df.empty or "Close" not in df.columns:
        raise RuntimeError("^GSPC history returned empty")
    closes = _extract_closes(df, "^GSPC", spec.id)
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


# ── NASDAQ 30d trailing return (MAGS §13 failure signal) ──────────────────────

def fetch_nasdaq_trailing(spec: FetchSpec) -> List[DataReading]:
    """NASDAQ_30D_RETURN: ^IXIC 30-trading-day pct-change. Same pattern as
    fetch_broad_equity_trailing — added so MAGS's "Nasdaq 30d return <= -10%"
    failure_signal (analysis/thesis.py) has data to evaluate against; it
    previously had no FetchSpec or regex pattern at all (fell through to
    "no evaluator recognizes condition" every session)."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=60)
    with _yf_lock_guard():
        df = yf.download("^IXIC", start=start.isoformat(), progress=False, auto_adjust=True)
    if df.empty or "Close" not in df.columns:
        raise RuntimeError("^IXIC history returned empty")
    closes = _extract_closes(df, "^IXIC", spec.id)
    if not closes:
        raise RuntimeError("^IXIC history returned empty")
    n = min(22, len(closes))
    pct30 = round((closes[-1] / closes[-n] - 1) * 100, 2)
    return [DataReading(
        spec_id=spec.id,
        value={"return_30d_pct": pct30, "current": round(closes[-1], 2)},
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]


# ── Generic N-week trend history (ENG-13) ─────────────────────────────────────

def fetch_weekly_trend(spec: FetchSpec, symbol: str, weeks: int) -> List[DataReading]:
    """
    Generic weekly-resampled closes for analysis/trend.py's pure functions.
    One request covers the whole window — no cross-session persistence needed.
    Gracefully degrades (quality_flag, no exception) on an empty/illiquid
    series — same contract as the rest of this file (e.g. URANIUM_SPOT).
    """
    today = datetime.date.today()
    start = today - datetime.timedelta(weeks=weeks + 3)
    try:
        with _yf_lock_guard():
            df = yf.download(symbol, start=start.isoformat(), interval="1wk",
                             progress=False, auto_adjust=True)
    except Exception as e:
        return [DataReading(spec_id=spec.id, value=None, source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"FETCH_FAILED: {e}"])]
    if df.empty or "Close" not in df.columns:
        return [DataReading(spec_id=spec.id, value=None, source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"UNAVAILABLE: {symbol} weekly history empty "
                                          "(illiquid contract or delisted)"])]
    try:
        closes = [round(float(c), 4) for c in _extract_closes(df, symbol, spec.id)]
    except RuntimeError as e:
        return [DataReading(spec_id=spec.id, value=None, source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"FETCH_FAILED: {e}"])]
    if not closes:
        return [DataReading(spec_id=spec.id, value=None, source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"UNAVAILABLE: {symbol} weekly history empty"])]
    n = min(weeks, len(closes))
    recent = closes[-n:]
    flags = []
    if n < weeks:
        flags.append(f"PARTIAL: only {n}/{weeks} weeks of {symbol} history available")
    return [DataReading(
        spec_id=spec.id,
        value={"closes": recent, "n_weeks": n, "symbol": symbol},
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
        quality_flags=flags,
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
    with _yf_lock_guard():
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


# ── ENG-55 batched trend-signal history ──────────────────────────────────────
# ONE yf.download() call for all 16 symbols (8 held instruments' own prices +
# 8 comparator tickers) rather than 16 separate registry entries -- ENG-35
# already flagged advisor_run_computation() running close to the MCP call
# ceiling; the existing per-symbol _TREND_SPECS pattern (7 separate calls)
# would make that materially worse if repeated at this scale. Daily
# resolution, ~100 calendar days back (comfortably covers the 63-trading-day
# medium window with margin for holidays/gaps). Mode 2's macro-confirmation
# inputs (DXY_TREND, BRENT_TREND, GOLD_TREND, SP500_TREND,
# REAL_YIELD_10Y_TREND) are NOT included here -- all five already exist as
# separate FetchSpecs and are reused as-is by analysis/trend_signal.py.

_TREND_SIGNAL_SYMBOLS: List[str] = [
    # 8 held instruments (ENG-55's own scope)
    "MLPX", "DBMF", "XAR", "AIPO", "COPX", "SGOL", "SIVR", "MAGS",
    # 8 comparator tickers (ENG-55 design, client-confirmed 2026-07-07)
    "BZ=F", "HG=F", "ITA", "PPA", "PAVE", "QQQM", "URA", "VEA",
]

_TREND_SIGNAL_LOOKBACK_DAYS = 100


def fetch_trend_signal_histories(spec: FetchSpec) -> List[DataReading]:
    """
    TREND_SIGNAL_HISTORY: daily closes for all _TREND_SIGNAL_SYMBOLS,
    batched into one request. Mirrors mcp_server._fetch_holdings_30d_raw's
    multi-symbol yf.download() + column-lookup pattern. Per-symbol
    failures degrade to a FETCH_FAILED reading for that symbol only --
    never raises for the whole batch.
    """
    end_dt = datetime.date.today()
    start_dt = end_dt - datetime.timedelta(days=_TREND_SIGNAL_LOOKBACK_DAYS)
    now = datetime.datetime.utcnow()

    try:
        with _yf_lock_guard():
            hist = yf.download(
                _TREND_SIGNAL_SYMBOLS, start=start_dt.isoformat(),
                end=end_dt.isoformat(), progress=False, auto_adjust=True,
            )
    except Exception as e:
        return [
            DataReading(spec_id=f"{spec.id}:{sym}", value=None,
                        source=DataSource.YFINANCE, fetched_at=now,
                        quality_flags=[f"FETCH_FAILED: batch download error: {e}"])
            for sym in _TREND_SIGNAL_SYMBOLS
        ]

    if hist.empty:
        return [
            DataReading(spec_id=f"{spec.id}:{sym}", value=None,
                        source=DataSource.YFINANCE, fetched_at=now,
                        quality_flags=["FETCH_FAILED: batch download returned empty"])
            for sym in _TREND_SIGNAL_SYMBOLS
        ]

    closes_block = hist["Close"] if "Close" in hist.columns else hist
    readings: List[DataReading] = []
    for sym in _TREND_SIGNAL_SYMBOLS:
        col = (closes_block.get(sym) if hasattr(closes_block, "get")
               else (closes_block[sym] if sym in closes_block.columns else None))
        if col is None:
            readings.append(DataReading(
                spec_id=f"{spec.id}:{sym}", value=None,
                source=DataSource.YFINANCE, fetched_at=now,
                quality_flags=[f"FETCH_FAILED: {sym} not present in batch response"],
            ))
            continue
        series = col.dropna()
        closes = [round(float(c), 4) for c in series.values.flatten().tolist()]
        if not closes:
            readings.append(DataReading(
                spec_id=f"{spec.id}:{sym}", value=None,
                source=DataSource.YFINANCE, fetched_at=now,
                quality_flags=[f"UNAVAILABLE: {sym} history empty"],
            ))
            continue
        readings.append(DataReading(
            spec_id=f"{spec.id}:{sym}",
            value={"symbol": sym, "closes": closes, "n_days": len(closes)},
            source=DataSource.YFINANCE, fetched_at=now,
        ))
    return readings


# ── ON_DEMAND: single instrument history ─────────────────────────────────────

def fetch_instrument_history(spec: FetchSpec, symbol: str,
                             start: str, end: Optional[str] = None) -> List[DataReading]:
    """HISTORICAL_INSTRUMENT_PRICES: ON_DEMAND. Call via registry.fetch_one()."""
    end = end or datetime.date.today().isoformat()
    with _yf_lock_guard():
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty or "Close" not in df.columns:
        return [DataReading(spec_id=f"{spec.id}:{symbol}", value=None,
                            source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=["FETCH_FAILED: empty history"])]
    try:
        closes = _extract_closes(df, symbol, spec.id)
    except RuntimeError as e:
        return [DataReading(spec_id=f"{spec.id}:{symbol}", value=None,
                            source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=[f"FETCH_FAILED: {e}"])]
    if not closes:
        return [DataReading(spec_id=f"{spec.id}:{symbol}", value=None,
                            source=DataSource.YFINANCE,
                            fetched_at=datetime.datetime.utcnow(),
                            quality_flags=["FETCH_FAILED: empty history"])]
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
#
# ENG-58 (2026-07-08): _fetch_single() was the one yfinance call site in this
# file with NO exception handling and NO independent timeout — unlike its
# two siblings (fetch_weekly_trend, fetch_trend_signal_histories), which both
# degrade gracefully. Confirmed live via mcp-server-financial-advisor.log:
# URANIUM_SPOT (UX=F — already flagged "unconfirmed/illiquid" in _SYMBOL_MAP
# and m18_registry.py) is now genuinely delisted on Yahoo Finance. Once
# yf.Ticker(...).fast_info hangs/retries internally against a delisted
# symbol, it can run for ~4 minutes — well past fetch_registry.py's own
# _FETCH_TIMEOUT_SECONDS=25s per-future bound. Worse, that outer bound only
# abandons *waiting* on the future; the underlying thread keeps running and
# keeps holding _YF_LOCK (the single global lock ENG-27 added to prevent
# cross-symbol data corruption under concurrent yfinance calls), so every
# OTHER yfinance-sourced spec in the same fetch_all() batch then also queues
# behind that still-held lock — this is what compounded one bad symbol into
# an aggregate ~240s delay landing right on Claude Desktop's own ~4-minute
# MCP client-side cancellation window (see FRAMEWORK_BACKLOG.md ENG-58).
#
# Fix: bound the actual blocking call to _SINGLE_FETCH_TIMEOUT_SECONDS using
# the same worker-thread + future.result(timeout=...) pattern already used
# in mcp_server.py's _with_timeout(). This guarantees _fetch_single() exits
# (and releases _YF_LOCK) well within fetch_all()'s own 25s budget even if
# the abandoned inner thread keeps running in the background — same accepted
# caveat _with_timeout() already documents ("a truly stuck thread cannot be
# force-killed from here"), just applied one layer deeper so the *lock*
# specifically can never be held past our own bound.

_SINGLE_FETCH_TIMEOUT_SECONDS = 12.0
_SINGLE_FETCH_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="yf_single_fetch"
)


def _fetch_single_raw(symbol: str) -> Dict[str, float]:
    """The actual blocking yfinance call — runs inside _SINGLE_FETCH_EXECUTOR
    so _fetch_single() can bound how long it waits without needing to (and
    without being able to) kill this thread if the symbol is truly stuck."""
    info = yf.Ticker(symbol).fast_info
    price = round(float(info.last_price), 4)
    previous_close = info.previous_close
    if previous_close is None:
        # The exact TypeError this used to raise uncaught (float - NoneType)
        # when a delisted/illiquid symbol has a price but no previous_close.
        raise ValueError(
            f"{symbol}: previous_close unavailable (delisted/illiquid contract?)"
        )
    day_change_pct = round((price - previous_close) / previous_close * 100, 2)
    return {"price": price, "day_change_pct": day_change_pct}


def _fetch_single(spec: FetchSpec) -> List[DataReading]:
    symbol = _SYMBOL_MAP.get(spec.id)
    if not symbol:
        raise ValueError(
            f"No yfinance symbol for spec.id='{spec.id}'. "
            f"Add it to _SYMBOL_MAP in yfinance_fetcher.py."
        )
    with _yf_lock_guard():
        future = _SINGLE_FETCH_EXECUTOR.submit(_fetch_single_raw, symbol)
        try:
            result = future.result(timeout=_SINGLE_FETCH_TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            return [DataReading(
                spec_id=spec.id, value=None, source=DataSource.YFINANCE,
                fetched_at=datetime.datetime.utcnow(),
                quality_flags=[
                    f"FETCH_TIMEOUT: {symbol} exceeded "
                    f"{_SINGLE_FETCH_TIMEOUT_SECONDS:.0f}s bound ─ likely "
                    f"delisted/illiquid (see ENG-58). _YF_LOCK is released "
                    f"now regardless, so this does not stall other yfinance "
                    f"fetches in the same fetch_all() batch."
                ],
            )]
        except Exception as e:
            return [DataReading(
                spec_id=spec.id, value=None, source=DataSource.YFINANCE,
                fetched_at=datetime.datetime.utcnow(),
                quality_flags=[f"FETCH_FAILED: {e}"],
            )]
    return [DataReading(
        spec_id=spec.id,
        value={
            "symbol":         symbol,
            "price":          result["price"],
            "day_change_pct": result["day_change_pct"],
        },
        source=DataSource.YFINANCE, fetched_at=datetime.datetime.utcnow(),
    )]
