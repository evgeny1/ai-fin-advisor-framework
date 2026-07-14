"""
analysis/signal_history.py — consecutive-period streak logic for §13 thesis
conditions that need cross-session/cross-period persistence of a computed
value or Call-2 judgment (ENG-26/31/66's shared problem), as opposed to a
raw price series (analysis/trend.py already handles those from data
yfinance/FRED can serve on demand for any historical window).

Pure functions only — no I/O. Callers fetch history via
data/signal_history_store.get_history() and pass it in; this module never
reads or writes the store itself.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, Sequence


def next_month_period(period: str) -> str:
    """'2026-07' -> '2026-08'; '2026-12' -> '2027-01'."""
    year, month = (int(x) for x in period.split("-"))
    month += 1
    if month > 12:
        month = 1
        year += 1
    return f"{year:04d}-{month:02d}"


def next_quarter_period(period: str) -> str:
    """'2026-Q3' -> '2026-Q4'; '2026-Q4' -> '2027-Q1'."""
    year_str, q_str = period.split("-Q")
    year, q = int(year_str), int(q_str)
    q += 1
    if q > 4:
        q = 1
        year += 1
    return f"{year:04d}-Q{q}"


def consecutive_session_streak(
    history: Sequence[dict], predicate: Callable[[Any], bool], min_count: int,
) -> Optional[bool]:
    """
    Session-granularity streak (MAGS's "shifts to MODERATE for >= 2
    consecutive sessions"): 'consecutive' means the last min_count
    RECORDED entries in a row, regardless of calendar gaps between
    sessions — each entry IS one session by construction (one record per
    advisory session), so "2 consecutive sessions" is just the last 2
    entries in history.

    Returns None if fewer than min_count entries exist yet — genuinely
    not enough history to judge, not a false negative.
    """
    if len(history) < min_count:
        return None
    tail = history[-min_count:]
    return all(predicate(e["value"]) for e in tail)


def consecutive_calendar_streak(
    history: Sequence[dict], predicate: Callable[[Any], bool], min_count: int,
    step: Callable[[str], str],
) -> Optional[bool]:
    """
    Calendar-granularity streak (COPX's PMI months, AIPO's capex quarters):
    the last min_count DISTINCT periods must not only all satisfy
    predicate, they must be genuinely back-to-back per step() — no
    skipped period. A gap (e.g. no reading recorded for an intervening
    month) means the condition's continuity can't be confirmed, so this
    returns None (inconclusive) rather than a false True or False.
    """
    if len(history) < min_count:
        return None
    tail = history[-min_count:]
    for i in range(len(tail) - 1):
        if step(tail[i]["period"]) != tail[i + 1]["period"]:
            return None  # gap — contiguity can't be confirmed
    return all(predicate(e["value"]) for e in tail)
