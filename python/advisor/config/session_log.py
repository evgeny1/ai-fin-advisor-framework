"""
advisor/config/session_log.py

Markdown parser: Session_Log.md → SessionLogState dataclass.
§7 credit readings table + §8 scenario state blocks.

§8 is the AUTHORITATIVE source for prior scenario probabilities (M05 rule).
Never use memory or Calibration_State.md for prior probabilities.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..types import (
    CreditReading,
    ScenarioProbabilities,
    SessionLogState,
    SessionStateEntry,
)

_SCENARIOS = ("A", "B", "C", "D", "E", "F")

# Top-level §8 field names that signal the start of a new section.
# Used as stop-markers when extracting list sections.
_SECTION_KEYS = frozenset({
    "scenario_probabilities", "primary_driver", "session_type",
    "open_triggers", "open_decisions", "next_session_flags",
    "calibration_changes_this_session", "work_completed",
    "credit_readings", "cascade_signals", "trades_executed",
    "m14_recomputation_results", "b_watch_level_3",
    "calibration_versions_this_session", "calibration_changes",
})


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
    """Parse §7 credit readings pipe table → list of CreditReading."""
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


def _parse_probs(block: str) -> Optional[ScenarioProbabilities]:
    """Extract scenario_probabilities: { A: X%, ... } from a §8 block."""
    m = re.search(
        r"scenario_probabilities:\s*\{\s*"
        r"A:\s*(\d+(?:\.\d+)?)%[^}]*"
        r"B:\s*(\d+(?:\.\d+)?)%[^}]*"
        r"C:\s*(\d+(?:\.\d+)?)%[^}]*"
        r"D:\s*(\d+(?:\.\d+)?)%[^}]*"
        r"E:\s*(\d+(?:\.\d+)?)%[^}]*"
        r"F:\s*(\d+(?:\.\d+)?)%",
        block,
    )
    if not m:
        return None
    try:
        return ScenarioProbabilities(
            A=float(m.group(1)), B=float(m.group(2)), C=float(m.group(3)),
            D=float(m.group(4)), E=float(m.group(5)), F=float(m.group(6)),
        )
    except (ValueError, TypeError):
        return None


def _extract_list(block: str, key: str) -> List[str]:
    """Extract a bullet (- item) or numbered (N. item) list under key within a §8 block.

    Finds the first occurrence of 'key:' at the start of a line, then collects
    subsequent '- ' and 'N. ' items until a blank line terminates the list or
    a new top-level section key is encountered.
    """
    m = re.search(rf"(?m)^{re.escape(key)}:\s*$", block)
    if not m:
        return []
    items: List[str] = []
    for line in block[m.end():].splitlines():
        stripped = line.strip()
        if not stripped:
            if items:
                break          # blank line ends the list
            continue
        # New top-level section header (non-indented word ending with colon)
        if not line.startswith((" ", "\t")):
            kw_m = re.match(r"^([a-z_][a-z_0-9]*):", line)
            if kw_m and kw_m.group(1) in _SECTION_KEYS:
                break
        # Collect list items
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
    return items


def _parse_scenario_states(text: str) -> List[SessionStateEntry]:
    """Parse all §8 session state blocks in chronological order.

    Blocks are separated by '---' horizontal rules.
    Skips:
      - The compacted summary line (starts with '//')
      - The canonical schema template (date: YYYY-MM-DD)
      - Any block without a valid date or parseable probabilities
    """
    idx8 = text.find("## Section 8")
    if idx8 == -1:
        return []
    s8 = text[idx8:]

    blocks = re.split(r"(?m)^---\s*$", s8)
    entries: List[SessionStateEntry] = []

    for block in blocks:
        # Must have a concrete date line (YYYY-MM-DD not literal template)
        date_m = re.search(r"(?m)^date:\s*(\d{4}-\d{2}-\d{2}[^\n]*)", block)
        if not date_m:
            continue
        date_str = date_m.group(1).strip()
        if date_str.upper().startswith("YYYY"):
            continue   # template sentinel — skip

        probs = _parse_probs(block)
        if probs is None:
            continue   # malformed block

        drv_m  = re.search(r"(?m)^primary_driver:\s*(.+)", block)
        driver = drv_m.group(1).strip() if drv_m else ""

        entries.append(SessionStateEntry(
            date             = date_str,
            probabilities    = probs,
            primary_driver   = driver,
            open_triggers    = _extract_list(block, "open_triggers"),
            open_decisions   = _extract_list(block, "open_decisions"),
            next_session_flags = _extract_list(block, "next_session_flags"),
            calibration_changes = _extract_list(block, "calibration_changes_this_session"),
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
