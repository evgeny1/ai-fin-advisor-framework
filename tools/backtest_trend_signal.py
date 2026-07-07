#!/usr/bin/env python3
"""
tools/backtest_trend_signal.py -- ENG-50/ENG-55/ENG-57 historical backtest.

Complementary to (NOT a substitute for) the live shadow-mode trial running
via advisor_evaluate_trend_signal() every FULL_DESKTOP session (Step 6c).
Reuses analysis/trend_signal.py's exact production entry point --
evaluate_all_trend_signals() -- fed sliced historical data at many
non-overlapping as-of points, rather than reimplementing the formula.
This guarantees the backtest tests the SAME code path production uses,
not a parallel reimplementation that could silently drift from it.

Genuine limitations, not silently glossed over (see chat discussion,
2026-07-07, when this script was scoped):
  - NOISE_FLOOR_PCT (2.0) and the 10% materiality threshold were chosen
    TODAY, informed loosely by recent market memory -- backtesting them
    against the recent past carries some circularity risk. This script
    reports hit rates AT the current thresholds as a first read, not a
    recalibration exercise.
  - MLPX's HY OAS confirmation compares readings ~30 calendar days apart,
    approximating the live tool's own Session_Log.md-cadence
    approximation -- deliberately truncated per as-of point here (see
    _hy_oas_window below), since passing the FULL historical HY OAS
    series would compare against the very start of the whole backtest
    window instead of ~30 days back.
  - dominant_directive_conflict_aware is NOT reconstructed historically --
    it depends on Calibration_State/scenario_probs AT each historical
    point, which were different then. Not attempted here; see the
    ENG-57 archive writeup for why.
  - Non-overlapping ~21-trading-day windows means a limited sample size
    (roughly lookback_days/21 windows per instrument) -- treat hit rates
    as an early read, not a statistically definitive verdict.

Usage:
    python tools/backtest_trend_signal.py                # ~18mo, default
    python tools/backtest_trend_signal.py --months 12     # shorter window
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FRAMEWORK_ROOT / "python"))

import yfinance as yf  # noqa: E402

from advisor.analysis.trend_signal import (  # noqa: E402
    TREND_SIGNAL_CONFIG,
    evaluate_all_trend_signals,
    MEDIUM_WINDOW_DAYS,
)
from advisor.data.fetchers.fred_fetcher import fetch_history_with_dates  # noqa: E402
from advisor.types import TrendSignalCode  # noqa: E402

OUTCOME_AFTER_DAYS = 21                    # same ~21 trading day forward-outcome window as live
WINDOW_SPACING_DAYS = 21                   # non-overlapping spacing between as-of points
MIN_HISTORY_BEFORE = MEDIUM_WINDOW_DAYS    # 63 -- own-instrument needs this much lookback

_YF_SYMBOLS = [
    "MLPX", "DBMF", "XAR", "AIPO", "COPX", "SGOL", "SIVR", "MAGS",
    "BZ=F", "HG=F", "ITA", "PPA", "PAVE", "QQQM", "URA", "VEA",
    "DX-Y.NYB", "GC=F", "^GSPC",
]


def _load_dotenv() -> None:
    """FRED_API_KEY lives in python/.env. mcp_server.py loads this at
    import time for the live pipeline; this script is standalone and
    never imports mcp_server.py, so it must load .env itself -- found by
    running this script once and seeing FRED report empty despite the
    live pipeline using FRED successfully moments earlier."""
    env_path = FRAMEWORK_ROOT / "python" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _iso_week_resample_asof(daily_pairs: List[Tuple[str, float]], as_of_date: str, weeks: int) -> List[float]:
    """
    Same ISO-week-resample logic as fred_fetcher._resample_weekly, but
    filtered to dates <= as_of_date FIRST -- so no future data ever leaks
    into a historical as-of snapshot.
    """
    by_week: Dict[Tuple[int, int], float] = {}
    for date_str, value in daily_pairs:
        if date_str > as_of_date:
            continue
        d = datetime.date.fromisoformat(date_str)
        iso_year, iso_week, _ = d.isocalendar()
        by_week[(iso_year, iso_week)] = value
    ordered = [by_week[k] for k in sorted(by_week.keys())]
    return ordered[-weeks:] if ordered else []


def _hy_oas_window(hy_oas_daily: List[Tuple[str, float]], as_of_date: str) -> List[Tuple[str, int]]:
    """
    Truncate to ~35 calendar days before as_of_date, converting FRED's
    native percent to bps (int) -- matches CreditReading.hy_oas's own
    type. NOT the full history: _mlpx_hy_oas_confirms() compares the
    first and last entries of whatever list it's given, so passing the
    whole backtest-window history would compare against the very start
    of the window instead of ~30 days back, which is not what the live
    logic (or its own documented approximation) intends.
    """
    as_of_dt = datetime.date.fromisoformat(as_of_date)
    window_start = (as_of_dt - datetime.timedelta(days=35)).isoformat()
    return [(d, int(round(v * 100))) for d, v in hy_oas_daily
            if window_start <= d <= as_of_date]


def fetch_all_history(lookback_days: int) -> Dict[str, object]:
    """One batched yfinance call (19 symbols) + three FRED series, all with
    `lookback_days` of history."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=lookback_days)
    print(f"Fetching {len(_YF_SYMBOLS)} yfinance symbols, {start} to {end} ...")
    hist = yf.download(_YF_SYMBOLS, start=start.isoformat(), end=end.isoformat(),
                        progress=False, auto_adjust=True)
    closes_block = hist["Close"] if "Close" in hist.columns else hist

    dated_closes: Dict[str, List[Tuple[str, float]]] = {}
    for sym in _YF_SYMBOLS:
        col = (closes_block.get(sym) if hasattr(closes_block, "get")
               else (closes_block[sym] if sym in closes_block.columns else None))
        if col is None:
            print(f"  WARNING: {sym} missing from batch response -- skipped")
            continue
        series = col.dropna()
        pairs = [(idx.strftime("%Y-%m-%d"), round(float(v), 4)) for idx, v in series.items()]
        dated_closes[sym] = pairs
        if abs(len(pairs) - len(dated_closes.get("MLPX", pairs))) > 5:
            print(f"  NOTE: {sym} has {len(pairs)} trading days vs MLPX's "
                  f"{len(dated_closes.get('MLPX', pairs))} -- calendars may not align exactly")

    print("Fetching FRED series (DGS10, T10YIE, HY OAS) ...")
    dgs10 = dict(fetch_history_with_dates("DGS10", days=lookback_days + 20))
    t10yie = dict(fetch_history_with_dates("T10YIE", days=lookback_days + 20))
    hy_oas_raw = fetch_history_with_dates("BAMLH0A0HYM2", days=lookback_days + 20)
    if not dgs10 or not t10yie:
        print("  WARNING: FRED_API_KEY missing or DGS10/T10YIE empty -- "
              "SGOL/SIVR real-yield confirmation will degrade to INCONCLUSIVE")
    if not hy_oas_raw:
        print("  WARNING: HY OAS series empty -- MLPX confirmation gate unavailable")

    real_yield_daily = sorted((d, dgs10[d] - t10yie[d]) for d in dgs10 if d in t10yie)

    return {"closes": dated_closes, "real_yield_daily": real_yield_daily, "hy_oas_daily": hy_oas_raw}


def run_backtest(lookback_days: int) -> Dict[str, list]:
    data = fetch_all_history(lookback_days)
    closes: Dict[str, List[Tuple[str, float]]] = data["closes"]
    real_yield_daily = data["real_yield_daily"]
    hy_oas_daily = data["hy_oas_daily"]

    results: Dict[str, list] = {t: [] for t in TREND_SIGNAL_CONFIG}
    if "MLPX" not in closes:
        print("FATAL: MLPX (master timeline) missing from batch response -- aborting")
        return results

    master_dates = [d for d, _ in closes["MLPX"]]
    n = len(master_dates)
    n_windows = max(0, (n - OUTCOME_AFTER_DAYS - MIN_HISTORY_BEFORE) // WINDOW_SPACING_DAYS)
    print(f"{n} trading days fetched. Usable as-of range: "
          f"[{MIN_HISTORY_BEFORE}, {n - OUTCOME_AFTER_DAYS}) -- {n_windows} non-overlapping windows")

    for idx in range(MIN_HISTORY_BEFORE, n - OUTCOME_AFTER_DAYS, WINDOW_SPACING_DAYS):
        as_of_date = master_dates[idx]

        # "As-of" snapshots -- everything sliced to hide future data.
        daily_histories_asof: Dict[str, List[float]] = {}
        for sym, pairs in closes.items():
            sliced = [v for d, v in pairs if d <= as_of_date]
            if sliced:
                daily_histories_asof[sym] = sliced

        weekly_trend_asof = {
            "DXY_TREND":            _iso_week_resample_asof(closes.get("DX-Y.NYB", []), as_of_date, 8),
            "BRENT_TREND":          _iso_week_resample_asof(closes.get("BZ=F", []), as_of_date, 8),
            "GOLD_TREND":           _iso_week_resample_asof(closes.get("GC=F", []), as_of_date, 8),
            "SP500_TREND":          _iso_week_resample_asof(closes.get("^GSPC", []), as_of_date, 8),
            "REAL_YIELD_10Y_TREND": _iso_week_resample_asof(real_yield_daily, as_of_date, 8),
        }
        hy_oas_asof = _hy_oas_window(hy_oas_daily, as_of_date)
        dominant_directives_asof = {t: None for t in TREND_SIGNAL_CONFIG}  # not reconstructed -- see docstring

        signals = evaluate_all_trend_signals(
            held_tickers=list(TREND_SIGNAL_CONFIG.keys()),
            daily_histories=daily_histories_asof,
            weekly_trend_readings=weekly_trend_asof,
            hy_oas_session_history=hy_oas_asof,
            dominant_directives=dominant_directives_asof,
        )

        check_idx = idx + OUTCOME_AFTER_DAYS
        for sig in signals:
            ticker_pairs = closes.get(sig.ticker)
            if not ticker_pairs or check_idx >= len(ticker_pairs):
                continue
            price_at_signal = daily_histories_asof.get(sig.ticker, [None])[-1]
            price_at_check = ticker_pairs[check_idx][1]
            if price_at_signal is None:
                continue
            if price_at_check > price_at_signal:
                direction = "up"
            elif price_at_check < price_at_signal:
                direction = "down"
            else:
                direction = "flat"

            if sig.rs_signal == TrendSignalCode.STRENGTHENING:
                matched: Optional[bool] = (direction == "up")
            elif sig.rs_signal == TrendSignalCode.WEAKENING:
                matched = (direction == "down")
            else:
                matched = None

            results[sig.ticker].append({
                "as_of": as_of_date, "signal": sig.rs_signal.value,
                "direction": direction, "matched": matched,
            })

    return results


def print_report(results: Dict[str, list]) -> None:
    print("\n" + "=" * 72)
    print("ENG-50/ENG-55 TREND SIGNAL -- HISTORICAL BACKTEST")
    print("(early read against current thresholds -- NOT a substitute for")
    print(" the live shadow-mode trial; see module docstring for limits)")
    print("=" * 72)
    total_calls = total_matched = total_inconclusive = 0
    for ticker, windows in results.items():
        n_windows = len(windows)
        calls = [w for w in windows if w["matched"] is not None]
        matched = [w for w in calls if w["matched"]]
        inconclusive = n_windows - len(calls)
        hit_rate = (len(matched) / len(calls) * 100) if calls else None
        total_calls += len(calls)
        total_matched += len(matched)
        total_inconclusive += inconclusive
        hr_str = f"{hit_rate:.0f}%" if hit_rate is not None else "n/a"
        print(f"{ticker:6s}  windows={n_windows:3d}  calls={len(calls):3d}  "
              f"hit_rate={hr_str:>5s}  inconclusive={inconclusive}")
    overall = (total_matched / total_calls * 100) if total_calls else None
    print("-" * 72)
    overall_str = f"{overall:.0f}%" if overall is not None else "n/a"
    print(f"OVERALL  calls={total_calls}  matched={total_matched}  "
          f"hit_rate={overall_str}  inconclusive={total_inconclusive}")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtest the ENG-55 trend/rotation signal against history.")
    parser.add_argument("--months", type=int, default=18,
                         help="Lookback window in months (default 18)")
    args = parser.parse_args()
    lookback_days = args.months * 30 + 30  # margin for weekends/holidays

    results = run_backtest(lookback_days)
    print_report(results)


if __name__ == "__main__":
    main()
