"""
tests/test_mcp/test_evaluate_trend_signal_cli.py — ENG-33 (fourth occurrence)

Tests for `python -m advisor evaluate-trend-signal`, the standing fallback
for advisor_evaluate_trend_signal() when that MCP tool hangs (2026-07-08:
fourth tool confirmed showing ENG-33's client-side transport symptom —
zero tools/call log entries, request never reaches the server; see
FRAMEWORK_BACKLOG.md ENG-33). Mirrors test_evaluate_allocation_cli.py:
this command is what makes the fallback a real, tested, documented part
of the framework rather than a script re-derived from memory each time.

The shadow-mode trial (ENG-50) depends on the trend signal actually
running every FULL_DESKTOP session — the happy-path test here asserts
TrendSignalStore.json is written by the CLI path too, since that's the
entire reason this fallback exists.
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime

import pandas as pd
import pytest

from advisor import __main__ as advisor_main
from advisor.__main__ import cmd_evaluate_trend_signal
from advisor.data.file_protocol import framework_path
from advisor.types import DataReading, DataSource

_FW = framework_path()
_CAL = _FW / "Calibration_State.md"

skip_if_missing = pytest.mark.skipif(
    not _CAL.exists(),
    reason="Framework files not present — skipping trend-signal CLI fallback tests",
)

_PROBS = {"A": 8.39, "B": 50.34, "C": 25.17, "D": 2.95, "E": 8.39, "F": 4.76}

SEED_LOG = """# Session Log

## Section 7 - Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-06-01 | 280 | 80 | 920 | Test fixture | t1 |

## Section 8 - Session State Log

---
entry_id: 2026-06-01T09:00
date: 2026-06-01
session_type: full M05 session
status: current
scenario_probabilities: {A: 10, B: 40, C: 25, D: 10, E: 10, F: 5}
primary_driver: seed entry for trend-signal CLI test
open_triggers:
- seed trigger
open_decisions:
- seed decision
next_session_flags:
- seed flag
"""


class _StubRegistry:
    """fetch_one() degrades to a flagged reading — same contract as the real
    FetchRegistry._safe_fetch() on failure; the tool must turn missing Mode-2
    confirmation series into per-instrument INCONCLUSIVE, not crash."""

    def fetch_one(self, spec_id):
        return [DataReading(
            spec_id=spec_id, value=None, source=DataSource.YFINANCE,
            fetched_at=datetime.utcnow(),
            quality_flags=["FETCH_FAILED: stubbed out in CLI test"],
        )]


@pytest.fixture
def isolated_framework(tmp_path, monkeypatch):
    """Same isolation pattern as test_pattern_b_pipeline.py's pipeline_dir:
    real Calibration_State.md + Instrument_Classification.md content, seeded
    Session_Log.md, ADVISOR_FRAMEWORK_PATH redirected so the CLI reads config
    from tmp_path and TrendSignalStore.json is written there — never the real
    framework files. The store's git commit fails inside tmp_path (not a git
    repo) and must be caught, per trend_signal_store.py's own contract."""
    real_cal = (_FW / "Calibration_State.md").read_text(encoding="utf-8")
    real_instruments = (_FW / "Instrument_Classification.md").read_text(encoding="utf-8")
    (tmp_path / "Calibration_State.md").write_text(real_cal, encoding="utf-8")
    (tmp_path / "Instrument_Classification.md").write_text(real_instruments, encoding="utf-8")
    (tmp_path / "Session_Log.md").write_text(SEED_LOG, encoding="utf-8")
    monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))
    return tmp_path


@pytest.fixture
def no_network(monkeypatch):
    """Empty-DataFrame yf.download (module singleton — covers the batched
    TREND_SIGNAL_HISTORY fetcher) + stubbed registry for the five weekly
    Mode-2 confirmation series the CLI fetches itself."""
    import yfinance as _yf
    monkeypatch.setattr(_yf, "download", lambda *args, **kwargs: pd.DataFrame())
    monkeypatch.setattr(advisor_main, "_build_registry", lambda: _StubRegistry())


@skip_if_missing
def test_json_file_input_runs_end_to_end(tmp_path, isolated_framework,
                                         no_network, monkeypatch, capsys):
    """Real Calibration_State.md, --json-file input, no network — every
    signal must degrade to INCONCLUSIVE with a quality_flag rather than
    crash, and TrendSignalStore.json must be written on the CLI path too
    (the shadow trial's data accumulation is the point of this fallback)."""
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps({"scenario_probs": _PROBS}))

    monkeypatch.setattr(sys, "argv", [
        "__main__.py", "evaluate-trend-signal", "--json-file", str(input_path),
    ])
    cmd_evaluate_trend_signal()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "OK", f"CLI fallback failed: {out}"
    tickers = {s["ticker"] for s in out["trend_signals"]}
    assert tickers == {"MLPX", "DBMF", "XAR", "AIPO", "COPX", "SGOL", "SIVR", "MAGS"}
    for s in out["trend_signals"]:
        assert s["rs_signal"] == "INCONCLUSIVE"
        assert s["quality_flags"], f"{s['ticker']}: expected a flag explaining INCONCLUSIVE"

    # The store update ran on the CLI path — the reason this fallback exists.
    assert (isolated_framework / "TrendSignalStore.json").exists()


@skip_if_missing
def test_stdin_input_works_without_json_file_flag(isolated_framework,
                                                  no_network, monkeypatch, capsys):
    """No --json-file → reads stdin instead."""
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-trend-signal"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"scenario_probs": _PROBS})))
    cmd_evaluate_trend_signal()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "OK"


def test_missing_scenario_probs_is_a_clean_error(monkeypatch, capsys):
    """No live MCP session to read probs from — must fail clearly, not
    silently recompute or default to anything (§8 stays authoritative)."""
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-trend-signal"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({})))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_trend_signal()
    assert exc_info.value.code == 1
    assert "scenario_probs is required" in capsys.readouterr().err


def test_invalid_json_input_is_a_clean_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-trend-signal"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("{not valid json"))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_trend_signal()
    assert exc_info.value.code == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_malformed_scenario_probs_is_a_clean_error(monkeypatch, capsys):
    """Missing scenario keys must fail with a clear message, not an
    unhandled KeyError traceback."""
    payload = {"scenario_probs": {"A": 50, "B": 50}}  # missing C-F
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-trend-signal"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_trend_signal()
    assert exc_info.value.code == 1
    assert "scenario_probs invalid" in capsys.readouterr().err
