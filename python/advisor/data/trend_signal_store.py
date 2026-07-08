"""
data/trend_signal_store.py -- ENG-50/ENG-55: persistent shadow-mode log for
the trend/rotation signal, mirroring credit_history_store.py's pattern
(FRAMEWORK_BACKLOG.md ENG-43): accumulate readings over time, JSON (not
markdown -- this is computational data, not client-facing narrative),
git-committed via local add+commit with NO push (push rides along with
whatever session write-back happens next -- same low-risk posture,
avoids the ENG-33/38 git-push-hang class of bug entirely).

Store format: TrendSignalStore.json at the framework repo root --
  { "MLPX": {"2026-07-10": {...}, "2026-07-24": {...}}, ...,
    "last_updated": "2026-07-24" }

Forward-outcome fill (client-confirmed 2026-07-07: fixed ~21-trading-day
lookback, approximated as ~29 calendar days -- same trading-day/calendar-day
conversion convention EntryExtensionGuard already uses elsewhere, e.g.
"90 calendar days ~= 62-63 trading days"): every call to
update_trend_signal_store() scans EVERY existing entry across ALL tickers
for one whose forward_outcome is still null and whose date is old enough,
and fills it in using that entry's own stored price_at_signal (never
re-derived from a fetch window that may no longer cover that date) plus
the CURRENT session's price. This runs opportunistically on every call,
not just checking "yesterday's" entry -- catches up on anything overdue
regardless of session cadence gaps.

Known limitation (flagged, not silently accepted -- the client noted this
explicitly when confirming the fixed-lookback design): this only runs when
a session actually happens to call it. A genuinely fixed 21-trading-day
schedule independent of session cadence would need a standalone check
outside live advisory sessions (e.g. a scheduled `python -m advisor`
invocation) -- not built here, a natural follow-up if session cadence
proves too irregular for the trial to produce clean data.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_protocol import framework_path
from ..types import TrendSignalReading

logger = logging.getLogger(__name__)

STORE_FILENAME = "TrendSignalStore.json"

TARGET_GAP_TRADING_DAYS = 21
# ~21 trading days -> ~29 calendar days -- same trading/calendar
# conversion convention EntryExtensionGuard already uses elsewhere in this
# framework, not independently derived here.
TARGET_GAP_CALENDAR_DAYS = 29


def _store_path() -> Path:
    return framework_path() / STORE_FILENAME


def _load_store() -> Dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(
            f"TrendSignalStore.json unreadable ({e}) -- starting from an "
            f"empty in-memory store rather than overwriting a possibly-"
            f"salvageable file; git history retains any prior committed "
            f"version regardless."
        )
        return {}


def _save(store: Dict[str, Any]) -> None:
    # default=str: defense in depth — a single non-JSON-native field (e.g. a
    # DirectiveCode enum slipping through, the exact 2026-07-08 bug the CLI
    # fallback's tests caught) must degrade to its string form, not silently
    # lose the entire session's shadow-trial data. Producers should still
    # normalize at the source (mcp_server._tool_evaluate_trend_signal does);
    # this is the backstop, not the fix.
    _store_path().write_text(
        json.dumps(store, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )


def _commit(message: str) -> None:
    """Local commit only (no push) -- same low-risk posture as
    credit_history_store.py's _commit(). Any failure is caught by the
    caller's broad except -- a missed commit just means the next
    successful run's commit picks up the diff."""
    repo = framework_path()
    git_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    subprocess.run(["git", "-C", str(repo), "add", STORE_FILENAME],
                   check=True, capture_output=True, text=True, env=git_env, timeout=30.0)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", message],
                   check=True, capture_output=True, text=True, env=git_env, timeout=30.0)


def _fill_due_forward_outcomes(
    store: Dict[str, Any],
    current_prices: Dict[str, float],
    today: datetime.date,
) -> int:
    """
    Scan every ticker's dated entries for one whose forward_outcome is
    still null and whose date is >= TARGET_GAP_CALENDAR_DAYS old. Fills
    it in using that entry's own stored price_at_signal (never a
    re-derived value) plus current_prices[ticker] (this session's fresh
    close). Returns the count filled.
    """
    filled = 0
    for ticker, entries in store.items():
        if ticker == "last_updated" or not isinstance(entries, dict):
            continue
        current_price = current_prices.get(ticker)
        for date_str, entry in entries.items():
            if not isinstance(entry, dict) or entry.get("forward_outcome") is not None:
                continue
            try:
                entry_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                continue
            age_days = (today - entry_date).days
            if age_days < TARGET_GAP_CALENDAR_DAYS:
                continue

            price_then = entry.get("price_at_signal")
            if price_then is None or current_price is None:
                entry["forward_outcome"] = {
                    "actual_check_date": today.isoformat(),
                    "target_gap_trading_days": TARGET_GAP_TRADING_DAYS,
                    "actual_gap_calendar_days": age_days,
                    "error": "price_at_signal or current price unavailable — outcome not computable",
                }
                filled += 1
                continue

            if current_price > price_then:
                direction = "up"
            elif current_price < price_then:
                direction = "down"
            else:
                direction = "flat"

            rs_signal = entry.get("rs_signal")
            if rs_signal == "STRENGTHENING":
                matched: Optional[bool] = (direction == "up")
            elif rs_signal == "WEAKENING":
                matched = (direction == "down")
            else:
                matched = None  # INCONCLUSIVE — nothing to validate against

            entry["forward_outcome"] = {
                "actual_check_date": today.isoformat(),
                "target_gap_trading_days": TARGET_GAP_TRADING_DAYS,
                "actual_gap_calendar_days": age_days,
                "price_at_check": current_price,
                "price_direction_since_signal": direction,
                "matched_signal": matched,
            }
            filled += 1
    return filled


def update_trend_signal_store(
    readings: List[TrendSignalReading],
    current_prices: Dict[str, float],
) -> Dict[str, Any]:
    """
    Append this session's readings, retroactively fill any due
    forward-outcome checks, save, and commit (local only) if anything
    changed. Returns a summary dict -- never raises. Callers should treat
    this as fire-and-forget, surfacing the summary as an advisory flag,
    same posture as credit_history_store.update_credit_history_store().
    """
    summary: Dict[str, Any] = {
        "attempted": True, "updated": False, "entries_added": 0,
        "forward_outcomes_filled": 0, "committed": False, "error": None,
    }
    try:
        store = _load_store()
        today = datetime.date.today()

        for r in readings:
            ticker_store = store.setdefault(r.ticker, {})
            ticker_store[r.session_date] = r.to_dict()
            summary["entries_added"] += 1

        summary["forward_outcomes_filled"] = _fill_due_forward_outcomes(store, current_prices, today)

        store["last_updated"] = today.isoformat()
        _save(store)

        any_change = summary["entries_added"] > 0 or summary["forward_outcomes_filled"] > 0
        if any_change:
            _commit(
                f"TrendSignalStore.json: {summary['entries_added']} new, "
                f"{summary['forward_outcomes_filled']} forward-outcomes filled, "
                f"{today.isoformat()}"
            )
        summary["updated"] = True
        summary["committed"] = any_change
        return summary

    except Exception as e:
        logger.warning(f"TrendSignalStore update failed (non-fatal): {e}")
        summary["error"] = str(e)
        return summary
