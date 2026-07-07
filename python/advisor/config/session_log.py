"""
advisor/config/session_log.py

Markdown parser: Session_Log.md → SessionLogState dataclass.
§7 credit readings table (pipe-table, unchanged by ENG-52) + §8 scenario
state entries.

§8 is the AUTHORITATIVE source for prior scenario probabilities (M05 rule).
Never use memory or Calibration_State.md for prior probabilities.

ENG-52 (2026-07-06): §8 entries are now real YAML documents rather than
loosely-structured markdown key:value lines parsed field-by-field via
regex. Each entry is still delimited by the pre-existing '---' separator
convention, but the region is now valid standard YAML multi-document
syntax and is parsed with yaml.safe_load_all(). This was a client-
identified gap: two same-day 2026-07-03 entries were indistinguishable
without reading the full primary_driver prose — no unique id, no way to
tell which one was authoritative. Both `entry_id` (real timestamp) and
`status` (current|superseded) are now mandatory-in-practice YAML keys —
see types.SessionStateEntry.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import yaml

from ..types import (
    CreditReading,
    ScenarioProbabilities,
    SessionLogState,
    SessionStateEntry,
)

_SCENARIOS = ("A", "B", "C", "D", "E", "F")


def _between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i == -1:
        return ""
    i += len(start)
    j = text.find(end, i)
    return text[i:j] if j != -1 else text[i:]


def _table_rows(section: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("|") and "---" not in s:
            cols = [c.strip() for c in s.strip("|").split("|")]
            if len(cols) >= 2 and any(c for c in cols):
                rows.append(cols)
    return rows[1:]  # skip header


def _extract_int(cell: str) -> Optional[int]:
    """Extract first integer from a table cell like '277 (carry)'."""
    m = re.search(r"(\d+)", cell)
    return int(m.group(1)) if m else None


def _parse_credit_readings(text: str) -> List[CreditReading]:
    """Parse §7 credit readings pipe table → list of CreditReading.
    Unchanged by ENG-52 — §7 was already a clean, mechanically-parseable
    markdown table with no disambiguation problem."""
    s7 = _between(text, "## Section 7", "## Section 8")
    readings: List[CreditReading] = []
    for row in _table_rows(s7):
        if len(row) < 5:
            continue
        readings.append(CreditReading(
            date    = row[0],
            hy_oas  = _extract_int(row[1]),
            ig_oas  = _extract_int(row[2]),
            ccc_oas = _extract_int(row[3]),
            source  = row[4],
            t1_flag = row[5] if len(row) > 5 else "",
        ))
    return readings


def _probs_from_doc(doc: Dict[str, Any]) -> Optional[ScenarioProbabilities]:
    """Build ScenarioProbabilities from a parsed §8 doc's
    scenario_probabilities mapping. Values are plain numbers now (no '%'
    suffix) — ENG-52 dropped the string convention since YAML numerics
    round-trip exactly, rather than needing '%'-stripping regex."""
    raw = doc.get("scenario_probabilities")
    if not isinstance(raw, dict):
        return None
    try:
        return ScenarioProbabilities(**{k: float(raw[k]) for k in _SCENARIOS})
    except (KeyError, TypeError, ValueError):
        return None


def _str_list(doc: Dict[str, Any], key: str) -> List[str]:
    val = doc.get(key)
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    return [str(val)]


def _parse_scenario_states(text: str) -> List[SessionStateEntry]:
    """Parse all §8 session state entries in chronological order.

    Entries are delimited by '---' (same convention as before ENG-52), and
    each entry's content between separators is now valid YAML rather than
    hand-parsed key:value lines. Deliberately parsed one chunk at a time
    (yaml.safe_load() per chunk) rather than yaml.safe_load_all() across
    the whole region as one stream: a single malformed or un-migrated
    pre-ENG-52 entry must only drop ITSELF, not silently take down every
    entry after it — the same per-block independence the old regex parser
    had, just applied to YAML parsing instead of regex matching.

    Skips any chunk that fails to parse, isn't a dict, or lacks a real
    date / parseable scenario_probabilities (covers the canonical-schema
    example documented near the top of the file, any malformed entry, and
    any entry still in the pre-ENG-52 prose format).
    """
    idx8 = text.find("## Section 8")
    if idx8 == -1:
        return []
    s8 = text[idx8:]

    first_sep = re.search(r"(?m)^---\s*$", s8)
    if not first_sep:
        return []
    region = s8[first_sep.start():]

    # Split into individual '---'-delimited chunks and parse each one
    # independently (rather than yaml.safe_load_all() across the whole
    # region as a single stream) — a single malformed or pre-migration
    # entry must only drop ITSELF, not silently wipe out every
    # well-formed entry after it in the file. Same per-block independence
    # the old regex parser had; only the per-block parsing method changed.
    chunks = re.split(r"(?m)^---\s*$", region)

    entries: List[SessionStateEntry] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            doc = yaml.safe_load(chunk)
        except yaml.YAMLError:
            continue   # malformed block — skip, don't touch other entries
        if not isinstance(doc, dict):
            continue
        date_val = doc.get("date")
        if not date_val or not re.match(r"^\d{4}-\d{2}-\d{2}", str(date_val)):
            continue
        probs = _probs_from_doc(doc)
        if probs is None:
            continue

        entries.append(SessionStateEntry(
            date                = str(date_val),
            entry_id            = str(doc.get("entry_id", "")),
            status              = str(doc.get("status", "current")),
            probabilities       = probs,
            primary_driver      = str(doc.get("primary_driver", "")),
            open_triggers       = _str_list(doc, "open_triggers"),
            open_decisions      = _str_list(doc, "open_decisions"),
            next_session_flags  = _str_list(doc, "next_session_flags"),
            calibration_changes = _str_list(doc, "calibration_changes_this_session"),
        ))

    return entries


# ── Top-level entry point ──────────────────────────────────────────────────────


def parse_session_log(text: str) -> SessionLogState:
    """Parse the full text of Session_Log.md into a SessionLogState.

    Args:
        text: Raw markdown content of Session_Log.md.

    Returns:
        SessionLogState with .credit_readings (§7) and .scenario_states (§8).
        Entries in .scenario_states are in chronological order.
        Use .latest_probs for the AUTHORITATIVE current probability vector (M05).
        Use .prior_probs for the previous vector (25pp cap enforcement).
    """
    return SessionLogState(
        credit_readings  = _parse_credit_readings(text),
        scenario_states  = _parse_scenario_states(text),
    )
