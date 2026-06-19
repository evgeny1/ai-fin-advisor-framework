"""
rendering.py — Shared В§8 entry and Portfolio_State.md rendering (ENG-3).

Single canonical implementation used by BOTH session pipelines:
  - mcp_server.py (Pattern B — Claude orchestrates via 3 MCP tools, active path)
  - orchestrator/session.py (Pattern A — Python orchestrates, Stage 5 target)

Before this module existed, each path reimplemented В§8 entry construction and
Portfolio_State.md rendering independently. ENG-1 was direct proof of the cost:
the identical В§8-format bug (missing '---' separator, rounded probabilities
breaking sum-to-100) existed independently in both files and had to be fixed
twice. This module is the fix for that pattern recurring — there is now
exactly one place that knows the В§8 schema and the Portfolio_State.md format.

Output here MUST stay byte-compatible with config/session_log.py's parser:
'---' block separator, a line starting 'date:', and a literal
'scenario_probabilities: { A: X%, ... }' line.
"""
from __future__ import annotations

from typing import Any, List


def format_scenario_probs(p: Any) -> str:
    """Render as 'scenario_probabilities: { A: X%, ... }' — the exact literal
    form config/session_log.py._parse_probs() matches via regex. Uses ':g'
    (no forced rounding to whole numbers) so values like 12.5 are preserved
    exactly rather than rounding inconsistently and breaking the sum-to-100
    invariant (the bug this replaces: rounded headline values summed to 99
    or 101 in two malformed June 14, 2026 Session_Log.md entries)."""
    return (f"{{ A: {p.A:g}%, B: {p.B:g}%, C: {p.C:g}%, "
            f"D: {p.D:g}%, E: {p.E:g}%, F: {p.F:g}% }}")


def format_bullet_list(items: List[str]) -> str:
    """Render as '- item' lines, matching the В§8 canonical-schema list format
    that config/session_log.py._extract_list() parses (bullet items under a
    bare 'key:' line, terminated by a blank line)."""
    return "\n".join(f"- {item}" for item in items) if items else "_None this session._"


def format_numbered_list(items: List[str]) -> str:
    """Render as '1. item' lines — same parser, numbered-list branch."""
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) if items else "_None this session._"


def build_session_log_entry(
    session_date: str,
    session_type_label: str,
    probs: Any,
    primary_driver: str,
    open_triggers: List[str],
    open_decisions: List[str],
    next_session_flags: List[str],
) -> str:
    """
    Canonical В§8 Session_Log.md entry — used by both mcp_server._tool_write_back
    (Pattern B) and orchestrator/session.py._step8_write_back (Pattern A).

    Returns ONLY the new entry text (including its own leading separator).
    Caller appends it: `log_text.rstrip() + build_session_log_entry(...)`.

    session_type_label: free-text session descriptor for the 'date:' line
    parenthetical and the 'session_type:' line — e.g. "full M05 session",
    "ad-hoc", "audit" (Pattern B, Claude-supplied) or a SessionType.value
    like "FULL_DESKTOP" (Pattern A). Both are valid — config/session_log.py
    does not constrain this field's content, only its position.
    """
    return (
        f"\n\n---\n\n"
        f"date: {session_date} ({session_type_label})\n"
        f"scenario_probabilities: {format_scenario_probs(probs)}\n"
        f"primary_driver: {primary_driver}\n"
        f"session_type: {session_type_label}\n\n"
        f"open_triggers:\n{format_bullet_list(open_triggers)}\n\n"
        f"open_decisions:\n{format_numbered_list(open_decisions)}\n\n"
        f"next_session_flags:\n{format_bullet_list(next_session_flags)}\n"
    )


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
    (Pattern B) and orchestrator/session.py (Pattern A). This is the format
    actually in production (see git history of Portfolio_State.md);
    Pattern A previously rendered a structurally different layout
    ("## Session flags" instead of Open Triggers / Open Decisions sections)
    that was never the canonical/shipped format — converged here.

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
