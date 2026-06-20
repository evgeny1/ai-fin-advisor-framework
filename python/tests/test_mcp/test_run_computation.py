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

    Also patches write_instruments_json (ENG-25) to a no-op — without this,
    every test in this file would overwrite the REAL instruments.json on
    disk (it lives outside the framework git repo and outside any tmp_path
    sandbox, so there is nothing else isolating it). Tests that want to
    assert on the write itself patch it again locally with their own stub.
    """
    monkeypatch.setattr(FetchRegistry, "fetch_all", lambda self: [])
    try:
        import yfinance as _yf
        monkeypatch.setattr(_yf, "download", lambda *args, **kwargs: pd.DataFrame())
    except ImportError:
        pass  # yfinance unavailable in this env
    from advisor.data.fetchers import yfinance_fetcher as _yfm
    monkeypatch.setattr(_yfm, "write_instruments_json", lambda tickers: None)

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
def test_calibration_state_has_section_12_header(fresh_cache, no_network):
    """
    Regression guard (ENG-18): _parse_cascade() in calibration.py anchors on
    the literal string "## Section 12" to locate §12.1-12.4. That header
    went missing from the live file for an unknown period with no test
    catching it — every cascade threshold silently fell back to
    _parse_cascade()'s hardcoded Python defaults instead of ever reading
    Calibration_State.md. This doesn't assert specific threshold values
    (those are expected to change at calibration, e.g. the June 30 audit) —
    just that the structural anchor the parser depends on still exists.
    """
    mcp_server._tool_run_computation()
    cal_text = mcp_server._cache["cal_text"]
    assert "## Section 12" in cal_text, (
        "Calibration_State.md is missing the '## Section 12' header — "
        "calibration.py._parse_cascade() will silently fall back to "
        "hardcoded defaults instead of reading live cascade thresholds."
    )
    cal = mcp_server._cache["cal"]
    assert cal.cascade is not None


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


# ── run_computation: instruments.json write (ENG-25) ───────────────────────────

@skip_if_missing
def test_run_computation_writes_instruments_json_with_active_tickers(fresh_cache, no_network, monkeypatch):
    """
    _tool_run_computation() must call write_instruments_json() with exactly
    the §11.3 active tickers (is_candidate == False) parsed from THIS
    session's Calibration_State.md — not §11.4 candidates, not memory.
    """
    from advisor.data.fetchers import yfinance_fetcher as yfm
    calls = []
    monkeypatch.setattr(yfm, "write_instruments_json", lambda tickers: calls.append(tickers))

    mcp_server._tool_run_computation()

    assert len(calls) == 1, "write_instruments_json should be called exactly once per session"
    written = calls[0]
    cal = mcp_server._cache["cal"]
    expected = {t for t, e in cal.instruments.items() if not e.is_candidate}
    assert set(written) == expected
    candidates = {t for t, e in cal.instruments.items() if e.is_candidate}
    assert not (set(written) & candidates), (
        "§11.4 candidate instruments must never appear in instruments.json"
    )


@skip_if_missing
def test_run_computation_survives_instruments_json_write_failure(fresh_cache, no_network, monkeypatch):
    """
    A write failure (e.g. unwritable ADVISOR_MCP_DIR) must be flagged, not
    HARD_STOP the whole session — yfinance_fetcher.load_instruments() has
    its own fallback, so a session can proceed without a fresh write.
    """
    from advisor.data.fetchers import yfinance_fetcher as yfm

    def _boom(tickers):
        raise OSError("disk full")
    monkeypatch.setattr(yfm, "write_instruments_json", _boom)

    result = json.loads(mcp_server._tool_run_computation())

    assert result["status"] == "OK", "A non-fatal instruments.json write failure must not HARD_STOP"
    assert any("instruments.json" in f for f in result["flags"]), (
        "Write failure must be surfaced as a flag in the output"
    )


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


# ── apply_scoring: GAP-16 range_position_advisories ───────────────────────────

@skip_if_missing
def test_apply_scoring_has_range_position_advisories_key(fresh_cache, no_network):
    """Key must always be present (possibly empty) — Claude should never
    have to special-case its absence when building the briefing."""
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    assert "range_position_advisories" in result
    assert isinstance(result["range_position_advisories"], list)


@skip_if_missing
def test_range_position_advisory_shape_when_present(fresh_cache, no_network):
    """With no_network (empty readings), any emitted advisory must still
    be 'inconclusive' with two quality_flags — never a guessed signal."""
    mcp_server._tool_run_computation()
    answers = _make_stub_answers(mcp_server._cache)
    result = json.loads(mcp_server._tool_apply_scoring(answers))
    for adv in result["range_position_advisories"]:
        assert adv["role_id"] == "inflation_hedge_precious_metals"
        assert adv["range_width_pp"] >= 6.0
        assert adv["signal"] == "inconclusive"
        assert len(adv["quality_flags"]) == 2
