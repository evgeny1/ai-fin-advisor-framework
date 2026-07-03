"""
credit_history_store.py -- persistent, self-healing local history for the
ICE BofA OAS credit series (HY/IG/CCC), FRAMEWORK_BACKLOG ENG-43.

FRED restricts these series (BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC) to a
rolling ~3-year window as of April 2026. FRED's own ALFRED archival layer
does not carry them either -- confirmed empirically 2026-07-02: querying
with ALFRED's realtime_start/vintage_dates parameters returns FRED's own
error, "the series does not exist in ALFRED but may exist in FRED", and
the series' own notes point elsewhere ("for more data, go to the source",
i.e. ICE directly) rather than at FRED's own archival layer. Client-chosen
path (c), 2026-07-02: accumulate the daily readings FRED DOES currently
provide into a local, git-committed store every time this runs, so the
window self-heals over roughly the next ~2 years (assuming this runs at
least roughly daily going forward; less-frequent runs still self-heal,
just more slowly, since a merge never loses a date it has already seen
even after that date ages out of FRED's own live window).

Store format: CreditHistoryStore.json at the framework repo root --
  { "HY_OAS": {"2023-07-03": 399.0, ...}, "IG_OAS": {...}, "CCC_OAS": {...},
    "last_updated": "2026-07-02" }
Values are in bps (this repo's OAS convention -- Calibration_State.md,
credit.py) -- NOT FRED's native percent. Contrast with market_data_mcp's
fred_get_history tool (ENG-42), which intentionally returns native units
for its own, separate reasons (documented there).

Gated to run at most once per calendar day, checked against the store's
own last_updated field -- FRED data is daily-resolution regardless, so
more frequent runs add FRED API load and local-git-commit noise for zero
additional coverage. Any failure (network, parse, git) is caught here and
returned in the summary dict, never raised -- this is a background
accumulation nice-to-have, not a session-blocking requirement, same
posture as instruments.json's write in mcp_server.py.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

from .file_protocol import framework_path
from .fetchers.fred_fetcher import fetch_history_with_dates

logger = logging.getLogger(__name__)

STORE_FILENAME = "CreditHistoryStore.json"

# spec_id -> FRED series ID. Deliberately duplicated from fred_fetcher.py's
# _SINGLE_SERIES table (just these three rows) rather than imported, to
# keep this module's dependency on fred_fetcher.py limited to the one
# function it actually calls (fetch_history_with_dates) -- importing the
# whole private table would couple this module to fred_fetcher.py's
# internal structure for no real benefit.
_CREDIT_SERIES: Dict[str, str] = {
    "HY_OAS":  "BAMLH0A0HYM2",
    "IG_OAS":  "BAMLC0A0CM",
    "CCC_OAS": "BAMLH0A3HYC",
}

_FETCH_DAYS = 1200  # ~3.3 years -- FRED's current visible window plus margin


def _store_path() -> Path:
    return framework_path() / STORE_FILENAME


def _load_store() -> dict:
    path = _store_path()
    if not path.exists():
        return {sid: {} for sid in _CREDIT_SERIES}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(
            f"CreditHistoryStore.json unreadable ({e}) -- starting from an "
            f"empty in-memory store rather than overwriting a possibly-salvageable "
            f"file; git history retains any prior committed version regardless."
        )
        return {sid: {} for sid in _CREDIT_SERIES}
    for sid in _CREDIT_SERIES:
        data.setdefault(sid, {})
    return data


def already_updated_today(store: dict) -> bool:
    return store.get("last_updated") == datetime.date.today().isoformat()


def update_credit_history_store() -> Dict[str, Any]:
    """
    Fetch each credit series' currently-visible FRED window and merge new
    observations into the local store, then commit (git add + commit, no
    push -- push happens via whatever later write-back naturally pushes)
    if anything actually changed.

    Returns a summary dict -- never raises. Callers (e.g.
    advisor_run_computation) should treat this as fire-and-forget,
    surfacing the summary as an advisory flag, not a blocking step.
    """
    summary: Dict[str, Any] = {
        "attempted": True, "updated": False, "added": {}, "span": {}, "error": None,
    }
    try:
        store = _load_store()
        if already_updated_today(store):
            summary["skipped_reason"] = "already updated today"
            return summary

        any_new = False
        for spec_id, fred_id in _CREDIT_SERIES.items():
            observations = fetch_history_with_dates(fred_id, days=_FETCH_DAYS)
            series_store = store.setdefault(spec_id, {})
            added = 0
            for date_str, pct_value in observations:
                bps_value = round(pct_value * 100, 2)
                if series_store.get(date_str) != bps_value:
                    series_store[date_str] = bps_value
                    added += 1
            summary["added"][spec_id] = added
            if series_store:
                dates = sorted(series_store.keys())
                summary["span"][spec_id] = [dates[0], dates[-1], len(dates)]
            if added:
                any_new = True

        store["last_updated"] = datetime.date.today().isoformat()
        _save(store)
        if any_new:
            _commit(f"CreditHistoryStore.json: daily merge, {datetime.date.today().isoformat()}")
        summary["updated"] = True
        summary["committed"] = any_new
        return summary

    except Exception as e:
        logger.warning(f"CreditHistoryStore update failed (non-fatal): {e}")
        summary["error"] = str(e)
        return summary


def _save(store: dict) -> None:
    _store_path().write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")


def _commit(message: str) -> None:
    """Local commit only (no push) -- deliberately simple and low-risk for a
    background nice-to-have: no interactive-prompt/hang exposure (contrast
    ENG-33/ENG-38, both real git-push hangs elsewhere in this codebase).
    Any failure here is caught by the caller's broad except -- a missed
    commit just means the next successful run's commit picks up the diff."""
    repo = framework_path()
    git_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    subprocess.run(["git", "-C", str(repo), "add", STORE_FILENAME],
                    check=True, capture_output=True, text=True, env=git_env, timeout=30.0)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", message],
                    check=True, capture_output=True, text=True, env=git_env, timeout=30.0)
