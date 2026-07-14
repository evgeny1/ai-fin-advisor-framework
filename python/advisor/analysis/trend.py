"""
analysis/trend.py — generic rolling-window trend primitives.

Built to close FRAMEWORK_BACKLOG.md ENG-13's core blocker: §13 conditions
containing "sustained"/"consecutive"/"rolling"/"trend"/"reversal" previously
had no infrastructure at all and were unconditionally skipped with a
quality_flag in analysis/thesis.py, regardless of whether the underlying
data was actually fetchable.

Key insight that makes this cheap: yfinance and FRED both serve arbitrary
historical lookback windows in a single request (already proven by the
existing VIX_30D_AVG/VIX_90D_AVG/BROAD_EQUITY_TRAILING fetchers in
data/fetchers/yfinance_fetcher.py). Multi-week price/series trend conditions
do NOT require persisting data across sessions — one fetch per session,
covering the full window, is sufficient. This module supplies the pure
evaluation logic; data/fetchers/yfinance_fetcher.py and fred_fetcher.py
supply the weekly-closes history via new *_TREND FetchSpecs registered in
data/m18_registry.py.

Cross-session SIGNAL history (e.g. "M14 equity_scenario_divergence stayed
MODERATE for >= 2 consecutive SESSIONS") is a genuinely different problem —
it requires persisting a computed signal's value session-over-session, not
a raw price series fetchable on demand. That is NOT solved here — see
FRAMEWORK_BACKLOG.md ENG-26.

All functions are pure on a List[float] of weekly closes, oldest-first.
No CalibrationState dependency, no I/O — easy to unit test directly.
"""
from __future__ import annotations

from typing import List, Optional


def net_change_pct(weekly_closes: List[float]) -> Optional[float]:
    """(last/first - 1) * 100. None if fewer than 2 points or first == 0."""
    if len(weekly_closes) < 2 or weekly_closes[0] == 0:
        return None
    return (weekly_closes[-1] / weekly_closes[0] - 1.0) * 100.0


def directional_trend(
    weekly_closes: List[float],
    threshold_pct: float,
    require_no_reversal: bool = False,
) -> Optional[str]:
    """
    "up" | "down" | None.

    Default (require_no_reversal=False): standard time-series-momentum
    trend read — the sign of the net change over the window
    (net_change_pct), gated by a materiality floor
    (|net_change_pct| >= threshold_pct). This is a plain, industry-
    standard measure (the same baseline "sign of trailing return"
    definition systematic trend-following strategies use) and is what
    every caller should use for an instrument's own price, a macro
    series, or any other general-purpose trend read. It does not care
    whether the path to get there was smooth — only the net outcome over
    the window (FRAMEWORK_BACKLOG.md ENG-65).

    require_no_reversal=True additionally requires that no later close in
    the window ever crossed back through the window's *starting* value —
    i.e. the move never fully gave itself back at any point along the
    way. This is NOT a general trend-detection requirement. It exists
    solely to implement Calibration_State.md 13's own documented text for
    DBMF's macro-breadth sustaining/failure conditions ("directional =
    net move >= 8% in one direction without full reversal"), which check
    whether OTHER markets (BZUSD/GCUSD/DXY/^GSPC) are trending as a proxy
    for whether DBMF's trend-following STRATEGY has a supportive
    backdrop — a strategy-level condition, not a property of any
    instrument's own price. Do not set this for an instrument's own price
    trend or any other module's trend read — doing so will silently and
    materially suppress a real, sustained move that merely had one early
    wobble (the exact failure mode found live on 2026-07-13, see ENG-65).
    """
    net = net_change_pct(weekly_closes)
    if net is None or abs(net) < threshold_pct:
        return None
    if not require_no_reversal:
        return "up" if net > 0 else "down"

    base = weekly_closes[0]
    if net > 0:
        if any(c < base for c in weekly_closes[1:]):
            return None  # gave back the entire move at some point — reversed
        return "up"
    if any(c > base for c in weekly_closes[1:]):
        return None
    return "down"


def all_weeks_meet(weekly_closes: List[float], comparator: str, threshold: float) -> Optional[bool]:
    """
    True iff EVERY supplied weekly close satisfies `close <comparator> threshold`.
    comparator: ">" | ">=" | "<" | "<="
    None if weekly_closes is empty (caller should flag, not assume False).
    """
    if not weekly_closes:
        return None
    ops = {
        ">":  lambda c: c > threshold,
        ">=": lambda c: c >= threshold,
        "<":  lambda c: c < threshold,
        "<=": lambda c: c <= threshold,
    }
    if comparator not in ops:
        raise ValueError(f"Unsupported comparator: {comparator!r}")
    f = ops[comparator]
    return all(f(c) for c in weekly_closes)


def decline_from_high_pct(weekly_closes: List[float]) -> Optional[float]:
    """
    (max - last) / max * 100. Always >= 0. None if empty or the window's
    high is <= 0 (degenerate — never expected for the series this is used on).
    """
    if not weekly_closes:
        return None
    peak = max(weekly_closes)
    if peak <= 0:
        return None
    return (peak - weekly_closes[-1]) / peak * 100.0


def mean_reversion_mode(
    weekly_closes: List[float],
    threshold_pct: float,
    trailing_weeks: Optional[int] = None,
    require_no_reversal: bool = False,
) -> Optional[bool]:
    """
    True if the trailing `trailing_weeks` closes (or the full window, when
    trailing_weeks is None — the default and recommended usage) show no
    directional_trend — i.e. the series is range-bound/choppy rather than
    trending. Using the SAME window and threshold as the directional check
    keeps this a clean logical negation of "trending"; an earlier draft
    defaulted to a short trailing sub-window evaluated against the SAME
    materiality threshold as the full window, which systematically
    misclassified an ongoing longer trend as "mean-reversion" — a steady
    trend typically moves less than the materiality threshold within almost
    any short sub-window of itself. None if insufficient history.

    require_no_reversal is threaded straight through to directional_trend()
    — see that function's docstring. DBMF's own §13 failure condition
    ("all 4 markets in mean-reversion mode") is this module's sole real
    caller and passes True, since it's checking the same trend-following-
    strategy-backdrop concept as DBMF's sustaining condition.
    """
    window = weekly_closes if trailing_weeks is None else weekly_closes[-trailing_weeks:]
    if len(window) < 2 or (trailing_weeks is not None and len(weekly_closes) < trailing_weeks):
        return None
    return directional_trend(window, threshold_pct, require_no_reversal=require_no_reversal) is None
