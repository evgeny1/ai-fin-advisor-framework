"""
tests/test_mcp/test_pattern_b_pipeline.py — ENG-11

End-to-end test for the Pattern-B MCP pipeline:
  advisor_run_computation() → advisor_apply_scoring() → advisor_write_back()

Pattern A has test_stage5/test_session.py which runs SessionPipeline end-to-end
with StubAIClient. Pattern B — the actually active path — had no equivalent.
This file is that equivalent.

The three tool functions are called in sequence the way a real Claude session
does, against an isolated tmp framework dir (real Calibration_State.md content,
seeded Session_Log.md). Network calls are mocked. The final write_back uses
dry_run=True to avoid git operations.

Assertions confirm:
  - The full sequence completes without error
  - The cache is correctly populated at each step (sequential dependency)
  - Session_Log.md has a new, parseable §8 entry after write_back
  - The new entry's probabilities sum to 100%
  - Dates are monotonically non-decreasing
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from advisor import mcp_server
from advisor.config.session_log import parse_session_log
from advisor.data.fetch_registry import FetchRegistry
from advisor.data.file_protocol import framework_path
from advisor.types import ScenarioProbabilities


_FW = framework_path()
_CAL = _FW / "Calibration_State.md"

skip_if_missing = pytest.mark.skipif(
    not _CAL.exists(),
    reason="Framework files not present — skipping Pattern-B e2e pipeline test",
)

SEED_LOG = """# Session Log

## Section 7 - Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-06-01 | 280 | 80 | 920 | Test fixture | t1 |

## Section 8 - Session State Log

---

date: 2026-06-01 (full M05 session)
scenario_probabilities: { A: 10%, B: 40%, C: 25%, D: 10%, E: 10%, F: 5% }
primary_driver: seed entry for Pattern-B e2e test
session_type: full M05 session

open_triggers:
- seed trigger

open_decisions:
1. seed decision

next_session_flags:
- seed flag
"""


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def pipeline_dir(tmp_path, monkeypatch):
    """
    Isolated tmp framework dir with real Calibration_State.md content and a
    seeded Session_Log.md. Redirects ADVISOR_FRAMEWORK_PATH to tmp_path so
    run_computation reads config from there and write_back writes there.
    Never touches the real framework files.
    """
    real_cal = (_FW / "Calibration_State.md").read_text(encoding="utf-8")
    (tmp_path / "Calibration_State.md").write_text(real_cal, encoding="utf-8")
    (tmp_path / "Session_Log.md").write_text(SEED_LOG, encoding="utf-8")
    monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))
    mcp_server._cache.clear()
    yield tmp_path
    mcp_server._cache.clear()


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(FetchRegistry, "fetch_all", lambda self: [])
    try:
        import yfinance as _yf
        monkeypatch.setattr(_yf, "download", lambda *args, **kwargs: pd.DataFrame())
    except ImportError:
        pass


def _make_stub_answers(cache):
    qs = cache.get("scoring_questions", [])
    return {
        q.id: (q.auto_score if q.auto_score is not None else min(q.valid_scores))
        for q in qs
    }


# ── Sequential dependency tests ────────────────────────────────────────────────

def test_write_back_fails_without_run_computation():
    """Confirms the tool enforces the sequential dependency."""
    mcp_server._cache.clear()
    result = json.loads(mcp_server._tool_write_back(
        primary_driver="test", open_triggers=[], open_decisions=[],
        next_session_flags=[], dry_run=True, session_type="ad-hoc",
    ))
    assert result["status"] == "ERROR"


def test_write_back_fails_without_apply_scoring():
    """write_back must fail if apply_scoring has not set scenario_probs."""
    from types import SimpleNamespace
    mcp_server._cache.clear()
    mcp_server._cache["cal"] = SimpleNamespace(version="test")
    # scenario_probs deliberately NOT in cache
    result = json.loads(mcp_server._tool_write_back(
        primary_driver="test", open_triggers=[], open_decisions=[],
        next_session_flags=[], dry_run=True, session_type="ad-hoc",
    ))
    assert result["status"] == "ERROR"


# ── Full pipeline test (ENG-11 core case) ─────────────────────────────────────

@skip_if_missing
def test_full_pipeline_completes_without_error(pipeline_dir, no_network):
    """run_computation → apply_scoring → write_back (dry_run) must all return OK."""
    r1 = json.loads(mcp_server._tool_run_computation())
    assert r1["status"] == "OK", f"run_computation failed: {r1}"

    answers = _make_stub_answers(mcp_server._cache)
    r2 = json.loads(mcp_server._tool_apply_scoring(answers))
    assert r2["status"] == "OK", f"apply_scoring failed: {r2}"

    r3 = json.loads(mcp_server._tool_write_back(
        primary_driver="Pattern-B e2e test driver",
        open_triggers=["trigger A"],
        open_decisions=["decision A"],
        next_session_flags=["flag A"],
        dry_run=True,
        session_type="ad-hoc",
    ))
    assert r3["status"] == "OK", f"write_back failed: {r3}"


@skip_if_missing
def test_full_pipeline_session_log_has_new_entry(pipeline_dir, no_network):
    """After write_back, Session_Log.md must contain a new parseable §8 entry."""
    mcp_server._tool_run_computation()
    mcp_server._tool_apply_scoring(_make_stub_answers(mcp_server._cache))
    mcp_server._tool_write_back(
        primary_driver="Pattern-B e2e test driver",
        open_triggers=[], open_decisions=[], next_session_flags=[],
        dry_run=True, session_type="ad-hoc",
    )
    written = (pipeline_dir / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)

    assert len(state.scenario_states) == 2, (
        f"Expected seed entry + new entry as 2 distinct §8 blocks, "
        f"got {len(state.scenario_states)}. "
        "If 1, the new entry was merged into the seed block (missing '---' separator)."
    )


@skip_if_missing
def test_full_pipeline_new_entry_probs_sum_to_100(pipeline_dir, no_network):
    mcp_server._tool_run_computation()
    mcp_server._tool_apply_scoring(_make_stub_answers(mcp_server._cache))
    mcp_server._tool_write_back(
        primary_driver="test", open_triggers=[], open_decisions=[],
        next_session_flags=[], dry_run=True, session_type="ad-hoc",
    )
    written = (pipeline_dir / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    p = state.latest_probs
    assert p is not None, "latest_probs is None — new entry may not have parsed"
    total = p.A + p.B + p.C + p.D + p.E + p.F
    assert abs(total - 100.0) < 0.01, f"New entry probs sum to {total:.4f}"


@skip_if_missing
def test_full_pipeline_new_entry_all_probs_at_floor(pipeline_dir, no_network):
    mcp_server._tool_run_computation()
    mcp_server._tool_apply_scoring(_make_stub_answers(mcp_server._cache))
    mcp_server._tool_write_back(
        primary_driver="test", open_triggers=[], open_decisions=[],
        next_session_flags=[], dry_run=True, session_type="ad-hoc",
    )
    written = (pipeline_dir / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    p = state.latest_probs
    assert p is not None
    for s in ("A", "B", "C", "D", "E", "F"):
        val = getattr(p, s)
        assert val >= 3.0, f"Scenario {s}={val}% below 3% floor in written entry"


@skip_if_missing
def test_full_pipeline_seed_entry_unchanged(pipeline_dir, no_network):
    """Prior session entry (seed) must be preserved exactly after write_back."""
    mcp_server._tool_run_computation()
    mcp_server._tool_apply_scoring(_make_stub_answers(mcp_server._cache))
    mcp_server._tool_write_back(
        primary_driver="test", open_triggers=[], open_decisions=[],
        next_session_flags=[], dry_run=True, session_type="ad-hoc",
    )
    written = (pipeline_dir / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    prior = state.prior_probs
    assert prior is not None, "Seed entry not parsed as prior_probs"
    assert prior.A == pytest.approx(10.0), f"Seed A changed: {prior.A}"
    assert prior.B == pytest.approx(40.0), f"Seed B changed: {prior.B}"


@skip_if_missing
def test_full_pipeline_dates_monotonic(pipeline_dir, no_network):
    mcp_server._tool_run_computation()
    mcp_server._tool_apply_scoring(_make_stub_answers(mcp_server._cache))
    mcp_server._tool_write_back(
        primary_driver="test", open_triggers=[], open_decisions=[],
        next_session_flags=[], dry_run=True, session_type="ad-hoc",
    )
    written = (pipeline_dir / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    dates = [e.date[:10] for e in state.scenario_states]
    assert dates == sorted(dates), f"Session entries not chronological: {dates}"


@skip_if_missing
def test_full_pipeline_open_triggers_round_trip(pipeline_dir, no_network):
    """Triggers written to Session_Log.md by write_back must be retrievable."""
    mcp_server._tool_run_computation()
    mcp_server._tool_apply_scoring(_make_stub_answers(mcp_server._cache))
    mcp_server._tool_write_back(
        primary_driver="test",
        open_triggers=["trigger A", "trigger B"],
        open_decisions=["decision A"],
        next_session_flags=["flag A"],
        dry_run=True,
        session_type="ad-hoc",
    )
    written = (pipeline_dir / "Session_Log.md").read_text(encoding="utf-8")
    state = parse_session_log(written)
    assert state.latest_open_triggers == ["trigger A", "trigger B"]
    assert state.latest_open_decisions == ["decision A"]
    assert state.latest_next_flags == ["flag A"]
