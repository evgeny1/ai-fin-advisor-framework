"""
tests/test_mcp/test_run_computation.py — ENG-10

Tests for _tool_run_computation() and _tool_apply_scoring() MCP tool wrappers.

The underlying analysis functions (analysis/*.py, portfolio/*.py) each have
their own unit tests. What was missing was any test of the MCP tool wrappers
themselves: that they correctly call the underlying functions, populate
_cache for subsequent tools, and return JSON with the shape the session
protocol depends on.

These tests require the real framework files (Calibration_State.md,
Session_Log.md) for config parsing, but mock out all network fetchers —
the fetcher unit tests in test_stage1/ cover those separately.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from advisor import mcp_server
from advisor.data.fetch_registry import FetchRegistry
from advisor.data.file_protocol import framework_path


_FW = framework_path()
_CAL = _FW / "Calibration_State.md"
_LOG = _FW / "Session_Log.md"

skip_if_missing = pytest.mark.skipif(
    not _CAL.exists() or not _LOG.exists(),
    reason="Framework files not present — skipping MCP run_computation tests",
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_cache():
    """Clear _cache before and after each test to isolate state."""
    mcp_server._cache.clear()
    yield
    mcp_server._cache.clear()


@pytest.fixture
def no_network(monkeypatch):
    """
    Patch FetchRegistry.fetch_all and yfinance.download to avoid real
    network calls. All DataReadings will be missing (FETCH_FAILED), but
    downstream analysis handles this gracefully via quality_flags.
    """
    monkeypatch.setattr(FetchRegistry, "fetch_all", lambda self: [])
    try:
        import yfinance as _yf
        monkeypatch.setattr(_yf, "download", lambda *args, **kwargs: pd.DataFrame())
    except ImportError:
        pass  # yfinance unavailable in this env

def _make_stub_answers(cache):
    """Build minimal scoring answers: use auto_score if set, else min(valid_scores)."""
    qs = cache.get("scoring_questions", [])
    return {
        q.id: (q.auto_score if q.auto_score is not None else min(q.valid_scores))
        for q in qs
    }


# ── run_computation: basic shape ───────────────────────────────────────────────

@skip_if_missing
def test_run_computation_returns_ok(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    assert result["status"] == "OK", f"Expected OK, got: {result}"


@skip_if_missing
def test_run_computation_has_prior_probs(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    assert "prior_probs" in result
    probs = result["prior_probs"]
    assert set(probs.keys()) == {"A", "B", "C", "D", "E", "F"}


@skip_if_missing
def test_run_computation_prior_probs_sum_to_100(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    probs = result["prior_probs"]
    total = sum(probs.values())
    assert abs(total - 100.0) < 0.1, f"prior_probs sum to {total:.2f}"


@skip_if_missing
def test_run_computation_has_scoring_questions(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    assert "scoring_questions" in result
    qs = result["scoring_questions"]
    assert isinstance(qs, list)
    assert len(qs) > 0, "Expected at least one scoring question"


@skip_if_missing
def test_run_computation_scoring_questions_have_required_fields(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    for q in result["scoring_questions"]:
        assert "id" in q
        assert "scenario" in q
        assert "valid_scores" in q
        # M03 questions use A-F; M19 judgment questions use "N/A"
        assert q["scenario"] in ("A", "B", "C", "D", "E", "F", "N/A")


@skip_if_missing
def test_run_computation_has_signals(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    assert "signals" in result


@skip_if_missing
def test_run_computation_has_calibration_version(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    assert "calibration_version" in result
    assert result["calibration_version"] != ""


@skip_if_missing
def test_run_computation_floor_alerts_present(fresh_cache, no_network):
    """floor_breach_alerts key must always be present in output."""
    result = json.loads(mcp_server._tool_run_computation())
    assert "floor_breach_alerts" in result

@skip_if_missing
def test_run_computation_has_market_data_summary(fresh_cache, no_network):
    result = json.loads(mcp_server._tool_run_computation())
    assert "market_data_summary" in result
    assert "/" in result["market_data_summary"]  # e.g. "0/30 specs valid"


# ── run_computation: _cache population ────────────────────────────────────────

@skip_if_missing
def test_run_computation_caches_cal(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    assert "cal" in mcp_server._cache
    assert mcp_server._cache["cal"] is not None


@skip_if_missing
def test_run_computation_caches_log(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    assert "log" in mcp_server._cache


@skip_if_missing
def test_run_computation_caches_scoring_questions(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    assert "scoring_questions" in mcp_server._cache
    assert len(mcp_server._cache["scoring_questions"]) > 0


@skip_if_missing
def test_run_computation_caches_readings(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    assert "readings" in mcp_server._cache
    assert isinstance(mcp_server._cache["readings"], list)


# ── apply_scoring: preconditions ──────────────────────────────────────────────

def test_apply_scoring_errors_without_run_computation(fresh_cache):
    """apply_scoring without prior run_computation → clear error, not crash."""
    result = json.loads(mcp_server._tool_apply_scoring({}))
    assert result["status"] == "ERROR"


# ── apply_scoring: output shape ───────────────────────────────────────────────

@skip_if_missing
def test_apply_scoring_returns_ok(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    assert result["status"] == "OK", f"Expected OK: {result}"


@skip_if_missing
def test_apply_scoring_probs_sum_to_100(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    probs = result["scenario_probs"]
    total = sum(probs.values())
    assert abs(total - 100.0) < 0.01, f"Probs sum to {total:.4f}"


@skip_if_missing
def test_apply_scoring_has_all_scenarios(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    assert set(result["scenario_probs"].keys()) == {"A", "B", "C", "D", "E", "F"}


@skip_if_missing
def test_apply_scoring_all_probs_at_or_above_floor(fresh_cache, no_network):
    """No scenario should fall below the 3% floor."""
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    for s, v in result["scenario_probs"].items():
        assert v >= 3.0, f"Scenario {s}={v}% below 3% floor"


@skip_if_missing
def test_apply_scoring_caches_scenario_probs(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    mcp_server._tool_apply_scoring(answers)
    assert "scenario_probs" in mcp_server._cache
    p = mcp_server._cache["scenario_probs"]
    total = p.A + p.B + p.C + p.D + p.E + p.F
    assert abs(total - 100.0) < 0.01


@skip_if_missing
def test_apply_scoring_has_raw_scores(fresh_cache, no_network):
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    assert "raw_scores" in result
    assert set(result["raw_scores"].keys()) == {"A", "B", "C", "D", "E", "F"}


@skip_if_missing
def test_apply_scoring_enables_write_back(fresh_cache, no_network):
    """After run_computation + apply_scoring, write_back prereqs are in cache."""
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    mcp_server._tool_apply_scoring(answers)
    assert "scenario_probs" in mcp_server._cache
    assert "cal" in mcp_server._cache
