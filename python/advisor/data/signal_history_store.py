"""
data/signal_history_store.py — local-only, per-period signal-value history
for §13 thesis conditions that need cross-session/cross-period tracking of
a COMPUTED value or Call-2 judgment (not a raw price series, which
yfinance/FRED already serve on demand for any historical window via
analysis/trend.py) — ENG-26/31/66's shared problem, solved once here.

Local-only, mirrors instruments.json's write pattern exactly (ENG-25):
lives in the same sibling market_data_mcp/ folder, NEVER committed to the
framework git repo (@see M12 STEP 4b). A read/write failure here is
non-fatal to the session — callers flag it and the affected condition
evaluates to UNKNOWN for that ticker, same as any other missing dependency.

Schema: {"<ticker>:<signal_name>": [{"period": str, "value": <JSON-safe>}, ...]}
`period` is the signal's own natural cadence key, supplied by the caller —
ISO date for session-level signals (MAGS), "YYYY-MM" for month-level
(COPX), "YYYY-Qn" for quarter-level (AIPO). A second write within the same
period overwrites that period's value rather than appending a duplicate,
so checking a signal more than once in the same period (e.g. two sessions
in the same month) doesn't inflate a streak count.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Same directory instruments.json already lives in (ENG-25) — see
# data/fetchers/yfinance_fetcher.py's _MCP_DIR for the identical layout
# comment. Six levels below dev/ from this file's location.
_MCP_DIR = Path(os.environ.get(
    "ADVISOR_MCP_DIR",
    str(Path(__file__).parent.parent.parent.parent.parent / "market_data_mcp"),
))
_STORE_FILE = _MCP_DIR / "SignalHistoryStore.json"

_DEFAULT_MAX_HISTORY = 12  # plenty for a 2-consecutive-period check with margin


def _load() -> Dict[str, List[Dict[str, Any]]]:
    if not _STORE_FILE.exists():
        return {}
    return json.loads(_STORE_FILE.read_text(encoding="utf-8"))


def _save(data: Dict[str, List[Dict[str, Any]]]) -> None:
    _MCP_DIR.mkdir(parents=True, exist_ok=True)
    _STORE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_signal(
    ticker: str, signal_name: str, period: str, value: Any,
    max_history: int = _DEFAULT_MAX_HISTORY,
) -> None:
    """
    Append one reading, or overwrite the most recent entry if `period`
    matches it exactly (same period read again this session/cycle).

    Raises on a genuine read/parse/write failure — caller wraps in
    try/except and flags rather than hard-stopping the session, the same
    non-fatal posture write_instruments_json() already uses.
    """
    key = f"{ticker}:{signal_name}"
    data = _load()
    history = data.get(key, [])
    if history and history[-1]["period"] == period:
        history[-1]["value"] = value
    else:
        history.append({"period": period, "value": value})
    data[key] = history[-max_history:]
    _save(data)


def get_history(ticker: str, signal_name: str) -> List[Dict[str, Any]]:
    """
    Read-only accessor. Never raises — a missing or corrupt store just
    means no history exists yet, which every caller already treats as
    "not enough data" (None / inconclusive), the same conservative
    default as any other missing dependency.
    """
    try:
        return _load().get(f"{ticker}:{signal_name}", [])
    except Exception as e:
        logger.warning(f"SignalHistoryStore unreadable ({e}) — treating as no history")
        return []
