"""
tests/test_rendering.py — ENG-3: shared §8 entry + Portfolio_State.md rendering.

advisor/rendering.py is the single implementation used by both session
pipelines (mcp_server.py Pattern B and orchestrator/session.py Pattern A).
This file tests it directly so the regression coverage that used to be
duplicated (once per pipeline, see test_mcp/test_write_back_format.py's
docstring for the bug history) lives in exactly one place too.
"""
from __future__ import annotations

import pytest

from advisor.config.session_log import parse_session_log
from advisor.rendering import (
    build_session_log_entry,
    format_bullet_list,
    format_numbered_list,
    format_scenario_probs,
    render_portfolio_state,
)
from advisor.types import ScenarioProbabilities


@pytest.fixture
def probs():
    return ScenarioProbabilities(A=14.3, B=42.9, C=14.3, D=7.1, E=14.3, F=7.1)


# ── format_scenario_probs ────────────────────────────────────────────────────────────────────────────────────────

def test_format_scenario_probs_preserves_decimals(probs):
    """The ':g' format must not round 14.3 to 14 — that rounding is the
    exact bug this format replaced (two June 14, 2026 entries summed to
    99 or 101 because of forced whole-number rounding)."""
    result = format_scenario_probs(probs)
    assert "14.3%" in result
    assert "42.9%" in result


def test_format_scenario_probs_matches_parser_regex(probs):
    """Round-trip through the real parser."""
    text = f"scenario_probabilities: {format_scenario_probs(probs)}"
    fake_entry = "date: 2026-06-18 (ad-hoc)\n" + text + "\nprimary_driver: test\n"
    log = "## Section 8 - Session State Log\n\n---\n\n" + fake_entry
    state = parse_session_log(log)
    p = state.latest_probs
    assert p is not None
    assert p.A == pytest.approx(14.3)


# ── format_bullet_list / format_numbered_list ────────────────────────────────────────────────────────

def test_format_bullet_list_empty_returns_placeholder():
    assert format_bullet_list([]) == "_None this session._"


def test_format_bullet_list_renders_dashes():
    result = format_bullet_list(["item 1", "item 2"])
    assert result == "- item 1\n- item 2"


def test_format_numbered_list_empty_returns_placeholder():
    assert format_numbered_list([]) == "_None this session._"


def test_format_numbered_list_renders_numbers():
    result = format_numbered_list(["first", "second"])
    assert result == "1. first\n2. second"


def test_format_numbered_list_never_a_python_repr():
    """Regression: a List[str] interpolated directly into an f-string
    (the bug independently present in the old Pattern-A code before
    ENG-3) renders as \"['a\', \'b\']\" \u2014 confirm that never happens here."""
    result = format_numbered_list(["a", "b"])
    assert "[" not in result
    assert "]" not in result


# ── build_session_log_entry ───────────────────────────────────────────────────────────

def test_build_session_log_entry_has_separator(probs):
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver", [], [], [],
    )
    assert entry.startswith("\n\n---\n\n")


def test_build_session_log_entry_parseable_as_new_block(probs):
    seed = (
        "## Section 8 - Session State Log\n\n---\n\n"
        "date: 2026-06-01 (full M05 session)\n"
        "scenario_probabilities: { A: 10%, B: 40%, C: 30%, D: 10%, E: 5%, F: 5% }\n"
        "primary_driver: seed\n"
    )
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver", [], [], [],
    )
    state = parse_session_log(seed.rstrip() + entry)
    assert len(state.scenario_states) == 2


def test_build_session_log_entry_triggers_and_decisions_round_trip(probs):
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver",
        ["trigger A", "trigger B"], ["decision A"], ["flag A"],
    )
    seed = "## Section 8 - Session State Log\n\n---\n\ndate: 2026-06-01 (x)\nscenario_probabilities: { A: 50%, B: 50% }\nprimary_driver: seed\n"
    state = parse_session_log(seed.rstrip() + entry)
    assert state.latest_open_triggers == ["trigger A", "trigger B"]
    assert state.latest_open_decisions == ["decision A"]
    assert state.latest_next_flags == ["flag A"]


# ── render_portfolio_state ───────────────────────────────────────────────────────────

def test_render_portfolio_state_has_header(probs):
    out = render_portfolio_state(
        "1.36", probs, "2026-06-18", "test driver", [], [], "TEST",
    )
    assert out.startswith("# Portfolio State")
    assert "2026-06-18" in out


def test_render_portfolio_state_has_calibration_version(probs):
    out = render_portfolio_state(
        "1.36", probs, "2026-06-18", "test driver", [], [], "TEST",
    )
    assert "**Calibration State:** 1.36" in out


def test_render_portfolio_state_probabilities_formatted(probs):
    out = render_portfolio_state(
        "1.0", probs, "2026-06-18", "test driver", [], [], "TEST",
    )
    assert "A=14%" in out  # :.0f rounds for display only, not the §8 entry
    assert "B=43%" in out


def test_render_portfolio_state_open_triggers_section(probs):
    out = render_portfolio_state(
        "1.0", probs, "2026-06-18", "test driver",
        ["trigger A"], [], "TEST",
    )
    assert "## Open Triggers" in out
    assert "- trigger A" in out


def test_render_portfolio_state_empty_triggers_shows_placeholder(probs):
    out = render_portfolio_state(
        "1.0", probs, "2026-06-18", "test driver", [], [], "TEST",
    )
    triggers_section = out.split("## Open Triggers")[1].split("## Open Decisions")[0]
    assert "_None this session._" in triggers_section


def test_render_portfolio_state_generator_label_appears(probs):
    out_a = render_portfolio_state(
        "1.0", probs, "2026-06-18", "x", [], [], "SessionPipeline (Pattern A)",
    )
    out_b = render_portfolio_state(
        "1.0", probs, "2026-06-18", "x", [], [], "MCP (Pattern B — Claude app)",
    )
    assert "Pattern A" in out_a
    assert "Pattern B" in out_b


def test_render_portfolio_state_both_patterns_use_same_structure(probs):
    """The core regression this module exists to prevent: both pipelines
    must produce structurally identical output (same sections, same
    formatting) — only the generator_label trailer should differ."""
    out_a = render_portfolio_state(
        "1.0", probs, "2026-06-18", "driver", ["t1"], ["d1"], "Pattern A",
    )
    out_b = render_portfolio_state(
        "1.0", probs, "2026-06-18", "driver", ["t1"], ["d1"], "Pattern B",
    )
    # Strip the one line that's allowed to differ, compare the rest
    lines_a = [l for l in out_a.split("\n") if "_Generated via" not in l]
    lines_b = [l for l in out_b.split("\n") if "_Generated via" not in l]
    assert lines_a == lines_b
