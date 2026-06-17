"""
tests/test_mcp/test_write_back_format.py

Regression test for the §8 write-back format bug (fixed 2026-06-17):
advisor_write_back() was generating §8 entries in a format
('### §8 Entry — DATE', '**Probabilities:** A=N / B=N', no '---'
separator) that config/session_log.py's parser could not read. Two
real entries (June 14, 2026) were silently invisible to
SessionLogState.latest_probs / prior_probs as a result — the system
loaded a stale prior probability vector with no error.

This exercises the real _tool_write_back() code path end-to-end
(dry_run=True, so no git operations) against an isolated temp
framework directory, then re-parses the result with the real
parse_session_log() to confirm the new entry is recognized as its
own block with correct values.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from advisor import mcp_server
from advisor.config.session_log import parse_session_log
from advisor.types import ScenarioProbabilities

SEED_LOG = """# Session Log

## Section 7 - Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-06-01 | 280 | 80 | 920 | Test fixture | t1 |

## Section 8 - Session State Log

---

date: 2026-06-01 (full M05 session — seed entry)
scenario_probabilities: { A: 10%, B: 40%, C: 30%, D: 10%, E: 5%, F: 5% }
primary_driver: seed entry for round-trip test
session_type: full M05 session

open_triggers:
- seed trigger

open_decisions:
1. seed decision

next_session_flags:
- seed flag
"""


@pytest.fixture
def isolated_framework(tmp_path, monkeypatch):
    """Point file_protocol.framework_path() at a throwaway directory and
    seed it with a minimal, correctly-formatted Session_Log.md. Never
    touches the real framework files or git."""
    monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))
    (tmp_path / "Session_Log.md").write_text(SEED_LOG, encoding="utf-8")
    mcp_server._cache["scenario_probs"] = ScenarioProbabilities(
        A=12.5, B=37.5, C=20.0, D=10.0, E=12.5, F=7.5
    )
    mcp_server._cache["cal"] = SimpleNamespace(version="vTEST")
    mcp_server._cache.pop("log_text", None)
    yield tmp_path
    for key in ("scenario_probs", "cal", "log_text"):
        mcp_server._cache.pop(key, None)


def test_write_back_entry_is_parseable(isolated_framework):
    """The new §8 entry must be a distinct, parseable block — not merged
    into the prior block (the original bug's actual failure mode: no
    '---' separator meant the appended text was swallowed by the
    previous block instead of standing alone)."""
    result = mcp_server._tool_write_back(
        primary_driver="round-trip test driver",
        open_triggers=["trigger A", "trigger B"],
        open_decisions=["decision A"],
        next_session_flags=["flag A"],
        dry_run=True,
        session_type="ad-hoc",
    )
    assert '"status": "OK"' in result

    written = (isolated_framework / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)

    assert len(state.scenario_states) == 2, (
        "Expected seed entry + new entry as two distinct blocks. If this "
        "is 1, the new entry was merged into the prior block."
    )


def test_write_back_latest_probs_match(isolated_framework):
    mcp_server._tool_write_back(
        primary_driver="round-trip test driver",
        open_triggers=["trigger A"],
        open_decisions=["decision A"],
        next_session_flags=["flag A"],
        dry_run=True,
        session_type="ad-hoc",
    )
    written = (isolated_framework / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)

    latest = state.latest_probs
    assert latest is not None, "New entry's probabilities did not parse"
    assert latest.A == pytest.approx(12.5)
    assert latest.B == pytest.approx(37.5)
    assert latest.C == pytest.approx(20.0)
    assert latest.D == pytest.approx(10.0)
    assert latest.E == pytest.approx(12.5)
    assert latest.F == pytest.approx(7.5)

    prior = state.prior_probs
    assert prior is not None
    assert prior.A == pytest.approx(10.0)  # seed entry, unchanged


def test_write_back_lists_round_trip(isolated_framework):
    mcp_server._tool_write_back(
        primary_driver="round-trip test driver",
        open_triggers=["trigger A", "trigger B", "trigger C"],
        open_decisions=["decision A", "decision B"],
        next_session_flags=["flag A"],
        dry_run=True,
        session_type="ad-hoc",
    )
    written = (isolated_framework / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)

    assert state.latest_open_triggers == ["trigger A", "trigger B", "trigger C"]
    assert state.latest_open_decisions == ["decision A", "decision B"]
    assert state.latest_next_flags == ["flag A"]


def test_write_back_sum_to_100(isolated_framework):
    """Guards against the exact failure mode in the original bug: a
    rounded headline probability string that summed to 99 or 101
    instead of 100."""
    mcp_server._tool_write_back(
        primary_driver="round-trip test driver",
        open_triggers=[], open_decisions=[], next_session_flags=[],
        dry_run=True, session_type="ad-hoc",
    )
    written = (isolated_framework / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    p = state.latest_probs
    total = p.A + p.B + p.C + p.D + p.E + p.F
    assert abs(total - 100.0) < 0.01


def test_write_back_empty_lists_render_as_none(isolated_framework):
    """Empty open_triggers/decisions/flags must not break parsing —
    confirms the '_None this session._' placeholder path is safe."""
    mcp_server._tool_write_back(
        primary_driver="round-trip test driver",
        open_triggers=[], open_decisions=[], next_session_flags=[],
        dry_run=True, session_type="ad-hoc",
    )
    written = (isolated_framework / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    assert len(state.scenario_states) == 2
    assert state.latest_open_triggers == []
    assert state.latest_open_decisions == []
