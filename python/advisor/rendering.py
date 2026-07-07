"""
rendering.py — Shared §8 entry and Portfolio_State.md rendering (ENG-3).

Single canonical implementation used by BOTH session pipelines:
  - mcp_server.py (Pattern B — Claude orchestrates via 3 MCP tools, active path)
  - orchestrator/session.py (Pattern A — Python orchestrates, Stage 5 target)

Before this module existed, each path reimplemented §8 entry construction and
Portfolio_State.md rendering independently. ENG-1 was direct proof of the cost:
the identical §8-format bug (missing '---' separator, rounded probabilities
breaking sum-to-100) existed independently in both files and had to be fixed
twice. This module is the fix for that pattern recurring — there is now
exactly one place that knows the §8 schema and the Portfolio_State.md format.

ENG-52 (2026-07-06): §8 entries are now rendered as real YAML (via PyYAML's
safe_dump, not hand-formatted strings) — see config/session_log.py's parser
docstring for why. Output here MUST stay parseable by that module: a '---'
document separator before each entry, then a YAML mapping with at least
'date' and 'scenario_probabilities' keys.
"""
from __future__ import annotations

import datetime as _datetime
import re
from typing import Any, List, Optional

import yaml

_SCENARIOS = ("A", "B", "C", "D", "E", "F")


class _FlowDict(dict):
    """Marker type: render this one mapping in YAML flow style
    ('{ A: 14.92, B: 37.31, ... }' on one line) while every other mapping
    in the same document uses block style. scenario_probabilities is the
    field most worth keeping scannable at a glance — everything else
    (lists, driver narrative) benefits more from block style."""


class _SessionLogDumper(yaml.SafeDumper):
    """Isolated Dumper subclass so the flow-style representer below only
    affects §8 rendering, not any other PyYAML usage in this codebase."""


def _represent_flow_dict(dumper: yaml.Dumper, data: "_FlowDict"):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)


_SessionLogDumper.add_representer(_FlowDict, _represent_flow_dict)


def format_scenario_probs(p: Any) -> str:
    """Legacy helper retained for any caller still wanting a display string
    (e.g. briefing text) — NOT used for §8 persistence anymore (ENG-52
    writes real YAML via build_session_log_entry() below)."""
    return (f"{{ A: {p.A:g}%, B: {p.B:g}%, C: {p.C:g}%, "
            f"D: {p.D:g}%, E: {p.E:g}%, F: {p.F:g}% }}")


def format_bullet_list(items: List[str]) -> str:
    """Display-only helper (briefing text etc.) — §8 persistence uses real
    YAML sequences now, not hand-formatted bullet lines."""
    return "\n".join(f"- {item}" for item in items) if items else "_None this session._"


def format_numbered_list(items: List[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) if items else "_None this session._"


def build_session_log_entry(
    session_date: str,
    session_type_label: str,
    probs: Any,
    primary_driver: str,
    open_triggers: List[str],
    open_decisions: List[str],
    next_session_flags: List[str],
    calibration_changes: Optional[List[str]] = None,
    entry_id: Optional[str] = None,
) -> str:
    """
    Canonical §8 Session_Log.md entry — used by both mcp_server._tool_write_back
    (Pattern B) and orchestrator/session.py._step8_write_back (Pattern A).

    Returns ONLY the new entry text (including its own leading '---' document
    separator). Caller appends it: `log_text.rstrip() + build_session_log_entry(...)`
    — same convention as before ENG-52, just YAML content now instead of
    hand-formatted key:value lines. Callers should normally call
    mark_prior_entries_superseded(log_text, session_date) FIRST, so a same-day
    restart-continuation entry doesn't leave a stale 'status: current' behind it.

    entry_id: real wall-clock timestamp ('YYYY-MM-DDTHH:MM', local machine
      time, minute granularity) identifying exactly when this entry was
      written — the field that disambiguates two same-day entries without
      reading the primary_driver prose. Defaults to datetime.now() at call
      time; the parameter exists so tests can pin a deterministic value.

    session_type_label: free-text session descriptor — e.g. "full M05
    session", "ad-hoc", "audit" (Pattern B, Claude-supplied) or a
    SessionType.value like "FULL_DESKTOP" (Pattern A). Both are valid —
    config/session_log.py does not constrain this field's content.
    """
    if entry_id is None:
        entry_id = _datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")

    doc = {
        "entry_id": entry_id,
        "date": session_date,
        "session_type": session_type_label,
        "status": "current",
        "scenario_probabilities": _FlowDict(
            {s: getattr(probs, s) for s in _SCENARIOS}
        ),
        "primary_driver": primary_driver,
        "open_triggers": list(open_triggers),
        "open_decisions": list(open_decisions),
        "next_session_flags": list(next_session_flags),
    }
    if calibration_changes:
        doc["calibration_changes_this_session"] = list(calibration_changes)

    yaml_text = yaml.dump(
        doc, Dumper=_SessionLogDumper, sort_keys=False,
        allow_unicode=True, default_flow_style=False,
    )
    return f"\n\n---\n{yaml_text}"


def mark_prior_entries_superseded(session_log_text: str, new_date: str) -> str:
    """Before appending a new §8 entry, flip any existing entry with the same
    calendar `new_date` and `status: current` to `status: superseded`.

    Targeted text patch, not a full re-parse-and-re-dump — only the specific
    'status: current' line in a matching block is touched, so entries not
    being superseded keep their exact original formatting/diff footprint.
    Safe no-op if §8 isn't found or nothing matches (e.g. first entry ever,
    or the new entry is a genuinely new calendar day).
    """
    idx8 = session_log_text.find("## Section 8")
    if idx8 == -1:
        return session_log_text
    head, s8 = session_log_text[:idx8], session_log_text[idx8:]

    first_sep = re.search(r"(?m)^---\s*$", s8)
    if not first_sep:
        return session_log_text
    pre, region = s8[:first_sep.start()], s8[first_sep.start():]

    # Split into per-entry chunks, keeping each entry's leading '---' attached
    # (lookahead split — doesn't consume the separator, so nothing is lost).
    chunks = re.split(r"(?m)^(?=---\s*$)", region)

    # PyYAML quotes date-shaped scalars on dump (to keep them str, not
    # !!timestamp, on reload) — e.g. "date: '2026-07-06'" — so the match
    # needs to tolerate an optional quote character either side.
    date_re = re.compile(rf"(?m)^date:\s*['\"]?{re.escape(new_date)}['\"]?\b")
    status_re = re.compile(r"(?m)^status:\s*current\s*$")

    patched = []
    for chunk in chunks:
        if date_re.search(chunk) and status_re.search(chunk):
            chunk = status_re.sub("status: superseded", chunk, count=1)
        patched.append(chunk)

    return head + pre + "".join(patched)


def render_portfolio_state(
    cal_version: str,
    probs: Any,
    session_date: str,
    primary_driver: str,
    open_triggers: List[str],
    open_decisions: List[str],
    generator_label: str,
) -> str:
    """
    Canonical Portfolio_State.md renderer — used by both mcp_server
    (Pattern B) and orchestrator/session.py (Pattern A). Untouched by ENG-52
    (Portfolio_State.md is a plain advisory snapshot, not parsed back in —
    no parseability problem existed here).

    generator_label: identifies which pipeline produced this snapshot —
    e.g. "MCP (Pattern B — Claude app)" or "SessionPipeline (Pattern A)".
    Never use for execution decisions — advisory context snapshot only.
    """
    p = probs
    prob_str = (f"A={p.A:.0f}% / B={p.B:.0f}% / C={p.C:.0f}% / "
                f"D={p.D:.0f}% / E={p.E:.0f}% / F={p.F:.0f}%")
    lines = [
        f"# Portfolio State \u2014 {session_date}",
        "",
        f"**Calibration State:** {cal_version}",
        f"**Scenario probabilities:** {prob_str}",
        f"**Primary driver:** {primary_driver}",
        "",
        "## Open Triggers",
    ]
    for t in open_triggers:
        lines.append(f"- {t}")
    if not open_triggers:
        lines.append("_None this session._")
    lines += ["", "## Open Decisions"]
    for d in open_decisions:
        lines.append(f"- {d}")
    if not open_decisions:
        lines.append("_None this session._")
    lines += ["", f"_Generated via {generator_label}._"]
    return "\n".join(lines)
