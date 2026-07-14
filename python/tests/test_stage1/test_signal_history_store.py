"""
tests/test_stage1/test_signal_history_store.py — ENG-26/31/66

Coverage for data/signal_history_store.py: the shared local-only,
per-period signal-value history mechanism for the three §13 conditions
needing cross-session/cross-period persistence (MAGS/session, COPX/month,
AIPO/quarter). Mirrors instruments.json's write pattern (ENG-25) — same
isolation style as test_dispatcher_and_instruments.py's per-test
_INSTRUMENTS_FILE patch (direct module-attribute patch, not the env var,
since _STORE_FILE is computed once at import time).
"""
from __future__ import annotations

import json

import pytest

from advisor.data import signal_history_store as m


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_MCP_DIR", tmp_path)
    monkeypatch.setattr(m, "_STORE_FILE", tmp_path / "SignalHistoryStore.json")
    return tmp_path


class TestRecordAndGetRoundTrip:

    def test_record_then_get_returns_the_value(self, isolated_store):
        m.record_signal("MAGS", "equity_scenario_divergence", "2026-07-14", "MODERATE")
        history = m.get_history("MAGS", "equity_scenario_divergence")
        assert history == [{"period": "2026-07-14", "value": "MODERATE"}]

    def test_get_history_for_unknown_key_is_empty_list(self, isolated_store):
        assert m.get_history("NOTHING", "not_a_signal") == []

    def test_multiple_periods_append_in_order(self, isolated_store):
        m.record_signal("COPX", "china_pmi_below_47", "2026-05", False)
        m.record_signal("COPX", "china_pmi_below_47", "2026-06", True)
        m.record_signal("COPX", "china_pmi_below_47", "2026-07", True)
        history = m.get_history("COPX", "china_pmi_below_47")
        assert [e["period"] for e in history] == ["2026-05", "2026-06", "2026-07"]
        assert [e["value"] for e in history] == [False, True, True]

    def test_same_period_overwrites_not_appends(self, isolated_store):
        """Checking a signal twice in the same period (e.g. two sessions
        in one month) must update that period's entry, not create a
        duplicate — otherwise a streak count could be inflated by
        re-checking the same period multiple times."""
        m.record_signal("AIPO", "capex_guidance_negative", "2026-Q3", False)
        m.record_signal("AIPO", "capex_guidance_negative", "2026-Q3", True)
        history = m.get_history("AIPO", "capex_guidance_negative")
        assert len(history) == 1
        assert history[0] == {"period": "2026-Q3", "value": True}

    def test_different_tickers_and_signals_dont_collide(self, isolated_store):
        m.record_signal("MAGS", "equity_scenario_divergence", "2026-07-14", "HIGH")
        m.record_signal("AIPO", "equity_scenario_divergence", "2026-07-14", "MODERATE")
        assert m.get_history("MAGS", "equity_scenario_divergence")[0]["value"] == "HIGH"
        assert m.get_history("AIPO", "equity_scenario_divergence")[0]["value"] == "MODERATE"

    def test_max_history_caps_length(self, isolated_store):
        for i in range(20):
            m.record_signal("MAGS", "equity_scenario_divergence", f"2026-{i:02d}-01",
                             "MODERATE", max_history=5)
        history = m.get_history("MAGS", "equity_scenario_divergence")
        assert len(history) == 5
        assert history[-1]["period"] == "2026-19-01"  # most recent kept


class TestFileNeverCommittedLocation:

    def test_store_file_lives_outside_git_repo_layout(self, isolated_store):
        assert m._STORE_FILE.name == "SignalHistoryStore.json"
        assert m._STORE_FILE.parent == isolated_store


class TestGracefulDegradation:

    def test_get_history_on_missing_file_is_empty_not_an_exception(self, isolated_store):
        assert not m._STORE_FILE.exists()
        assert m.get_history("MAGS", "equity_scenario_divergence") == []

    def test_get_history_on_corrupt_file_is_empty_not_an_exception(self, isolated_store):
        m._MCP_DIR.mkdir(parents=True, exist_ok=True)
        m._STORE_FILE.write_text("{not valid json", encoding="utf-8")
        assert m.get_history("MAGS", "equity_scenario_divergence") == []

    def test_record_signal_raises_on_corrupt_file(self, isolated_store):
        """Unlike get_history() (read path, safe to degrade), record_signal()
        must NOT silently treat a corrupt store as empty and overwrite it —
        that would silently destroy prior history. Raising lets the caller
        (mcp_server.py) flag it instead, same non-fatal-to-the-session
        posture as write_instruments_json()."""
        m._MCP_DIR.mkdir(parents=True, exist_ok=True)
        m._STORE_FILE.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            m.record_signal("MAGS", "equity_scenario_divergence", "2026-07-14", "MODERATE")
