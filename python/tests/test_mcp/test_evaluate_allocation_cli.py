"""
tests/test_mcp/test_evaluate_allocation_cli.py — ENG-33

Tests for `python -m advisor evaluate-allocation`, the standing fallback
for advisor_evaluate_allocation() when that MCP tool hangs (confirmed
2026-06-25 to be a Claude Desktop client-side issue, not in this
codebase -- see FRAMEWORK_BACKLOG.md ENG-33). This command is what makes
the fallback a real, tested, documented part of the framework rather
than a script re-derived from memory each time it's needed.

Uses the real Calibration_State.md (skipped if absent, same convention
as test_mcp/test_run_computation.py) since cmd_evaluate_allocation()
reads it fresh -- that's the whole point of this path: a brand-new
process with nothing cached.
"""
from __future__ import annotations

import io
import json
import sys

import pytest

from advisor.__main__ import cmd_evaluate_allocation
from advisor.data.file_protocol import framework_path

_CAL = framework_path() / "Calibration_State.md"

skip_if_missing = pytest.mark.skipif(
    not _CAL.exists(),
    reason="Calibration_State.md not present — skipping CLI fallback tests",
)

_PROFILE = {
    "account_id": "cli_test_account",
    "owner": "primary",
    "planning_horizon_years": 10,
    "objective_type": "TARGET_THEN_RETURN",
    "concentration_cap": 0.40,
    "drawdown_tolerance": 0.35,
}
_PROBS = {"A": 17.0, "B": 34.0, "C": 23.0, "D": 3.0, "E": 6.0, "F": 17.0}


def _payload(**overrides):
    base = {
        "account_profile": _PROFILE,
        "current_weights": {"NOT_A_REAL_TICKER": 1.0},
        "scenario_probs": _PROBS,
    }
    base.update(overrides)
    return base


@skip_if_missing
def test_json_file_input_runs_end_to_end(tmp_path, monkeypatch, capsys):
    """Real Calibration_State.md, --json-file input, unclassified ticker
    (robust to whatever's actually in §11 today) — must still return
    valid OK-status JSON with a per-ticker error rather than crashing."""
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(_payload()))

    monkeypatch.setattr(sys, "argv", [
        "__main__.py", "evaluate-allocation", "--json-file", str(input_path),
    ])
    cmd_evaluate_allocation()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "OK"
    assert "error" in out["instruments"]["NOT_A_REAL_TICKER"]


@skip_if_missing
def test_stdin_input_works_without_json_file_flag(monkeypatch, capsys):
    """No --json-file → reads stdin instead."""
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-allocation"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_payload())))
    cmd_evaluate_allocation()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "OK"


def test_missing_scenario_probs_is_a_clean_error(monkeypatch, capsys):
    """No live MCP session to read probs from — must fail clearly, not
    silently recompute or default to anything."""
    payload = _payload()
    del payload["scenario_probs"]
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-allocation"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_allocation()
    assert exc_info.value.code == 1
    assert "scenario_probs is required" in capsys.readouterr().err


def test_invalid_json_input_is_a_clean_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-allocation"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("{not valid json"))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_allocation()
    assert exc_info.value.code == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_missing_required_fields_is_a_clean_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-allocation"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"scenario_probs": _PROBS})))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_allocation()
    assert exc_info.value.code == 1
    assert "account_profile" in capsys.readouterr().err


def test_malformed_scenario_probs_is_a_clean_error(monkeypatch, capsys):
    """Missing a required scenario key (e.g. typo'd 'a' instead of 'A')
    must fail with a clear message, not an unhandled KeyError traceback."""
    payload = _payload(scenario_probs={"A": 50, "B": 50})  # missing C-F
    monkeypatch.setattr(sys, "argv", ["__main__.py", "evaluate-allocation"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    with pytest.raises(SystemExit) as exc_info:
        cmd_evaluate_allocation()
    assert exc_info.value.code == 1
    assert "scenario_probs invalid" in capsys.readouterr().err
