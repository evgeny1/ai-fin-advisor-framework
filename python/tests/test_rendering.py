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
    mark_prior_entries_superseded,
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


def test_format_scenario_probs_is_display_only(probs):
    """ENG-52: format_scenario_probs() is retained only as a display/briefing
    helper — §8 persistence goes through build_session_log_entry()'s real
    YAML now, not this string. No parser round-trip claim anymore; just
    confirm it still renders sensibly."""
    result = format_scenario_probs(probs)
    assert "14.3%" in result
    assert "42.9%" in result


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


# ── build_session_log_entry (ENG-52: real YAML) ──────────────────────────────────────

def test_build_session_log_entry_has_separator(probs):
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver", [], [], [],
        entry_id="2026-06-18T09:00",
    )
    assert entry.startswith("\n\n---\n")


def test_build_session_log_entry_default_entry_id_is_generated(probs):
    """entry_id defaults to datetime.now() when not supplied — callers
    normally leave this to the default; only tests pin it."""
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver", [], [], [],
    )
    assert "entry_id:" in entry


def test_build_session_log_entry_parseable_as_new_block(probs):
    seed = (
        "## Section 8 - Session State Log\n\n---\n"
        "entry_id: 2026-06-01T09:00\n"
        "date: 2026-06-01\n"
        "session_type: full M05 session\n"
        "status: current\n"
        "scenario_probabilities: {A: 10, B: 40, C: 30, D: 10, E: 5, F: 5}\n"
        "primary_driver: seed\n"
    )
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver", [], [], [],
        entry_id="2026-06-18T09:00",
    )
    state = parse_session_log(seed.rstrip("\n") + entry)
    assert len(state.scenario_states) == 2


def test_build_session_log_entry_triggers_and_decisions_round_trip(probs):
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver",
        ["trigger A", "trigger B"], ["decision A"], ["flag A"],
        entry_id="2026-06-18T09:00",
    )
    seed = (
        "## Section 8 - Session State Log\n\n---\n"
        "entry_id: 2026-06-01T09:00\ndate: 2026-06-01\nstatus: current\n"
        "scenario_probabilities: {A: 50, B: 50, C: 0, D: 0, E: 0, F: 0}\n"
        "primary_driver: seed\n"
    )
    state = parse_session_log(seed.rstrip("\n") + entry)
    assert state.latest_open_triggers == ["trigger A", "trigger B"]
    assert state.latest_open_decisions == ["decision A"]
    assert state.latest_next_flags == ["flag A"]


def test_build_session_log_entry_entry_id_and_status_round_trip(probs):
    """The fields ENG-52 exists to add — confirm they actually round-trip,
    not just render."""
    entry = build_session_log_entry(
        "2026-06-18", "ad-hoc", probs, "test driver", [], [], [],
        entry_id="2026-06-18T09:00",
    )
    seed = "## Section 8 - Session State Log\n\n"
    state = parse_session_log(seed + entry)
    assert state.scenario_states[-1].entry_id == "2026-06-18T09:00"
    assert state.scenario_states[-1].status == "current"


# ── mark_prior_entries_superseded (ENG-52) ───────────────────────────────────────────

def test_mark_prior_entries_superseded_flips_same_day_current(probs):
    entry = build_session_log_entry(
        "2026-07-06", "ad-hoc", probs, "first", [], [], [],
        entry_id="2026-07-06T10:00",
    )
    text = "## Section 8 - Session State Log" + entry
    patched = mark_prior_entries_superseded(text, "2026-07-06")
    state = parse_session_log(patched)
    assert state.scenario_states[0].status == "superseded"


def test_mark_prior_entries_superseded_ignores_other_dates(probs):
    entry = build_session_log_entry(
        "2026-07-05", "ad-hoc", probs, "first", [], [], [],
        entry_id="2026-07-05T10:00",
    )
    text = "## Section 8 - Session State Log" + entry
    patched = mark_prior_entries_superseded(text, "2026-07-06")
    state = parse_session_log(patched)
    assert state.scenario_states[0].status == "current"


def test_mark_prior_entries_superseded_no_op_when_no_section_8():
    text = "no section 8 heading here"
    assert mark_prior_entries_superseded(text, "2026-07-06") == text


def test_mark_prior_entries_superseded_already_superseded_untouched(probs):
    """Don't accidentally touch entries that are already superseded from a
    prior write — count() shouldn't need to guess at idempotency, the regex
    just never matches a line that already says 'superseded'."""
    entry = build_session_log_entry(
        "2026-07-06", "ad-hoc", probs, "first", [], [], [],
        entry_id="2026-07-06T10:00",
    )
    text = "## Section 8 - Session State Log" + entry
    once = mark_prior_entries_superseded(text, "2026-07-06")
    twice = mark_prior_entries_superseded(once, "2026-07-06")
    assert once == twice


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
