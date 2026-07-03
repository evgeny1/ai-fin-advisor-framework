"""
Tests for credit_history_store.py (FRAMEWORK_BACKLOG ENG-43) -- self-healing
local history for the ICE BofA OAS credit series (HY/IG/CCC), since FRED
truncates these to a rolling 3y window and ALFRED does not carry them.
"""
from __future__ import annotations

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from advisor.data import credit_history_store as m


@pytest.fixture(autouse=True)
def _point_at_tmp(tmp_path, monkeypatch):
    """Every test gets its own isolated 'framework root' -- never touches
    the real repo or the real CreditHistoryStore.json."""
    monkeypatch.setattr(m, "framework_path", lambda: tmp_path)
    return tmp_path


class TestLoadStore:
    def test_no_file_returns_empty_series_dicts(self):
        store = m._load_store()
        assert set(store.keys()) == {"HY_OAS", "IG_OAS", "CCC_OAS"}
        assert store["HY_OAS"] == {}

    def test_malformed_json_returns_fresh_store_not_exception(self, tmp_path):
        (tmp_path / m.STORE_FILENAME).write_text("{not valid json", encoding="utf-8")
        store = m._load_store()
        assert store["CCC_OAS"] == {}

    def test_missing_series_key_backfilled(self, tmp_path):
        (tmp_path / m.STORE_FILENAME).write_text(
            json.dumps({"HY_OAS": {"2026-01-01": 280.0}}), encoding="utf-8"
        )
        store = m._load_store()
        assert store["HY_OAS"] == {"2026-01-01": 280.0}
        assert store["IG_OAS"] == {}
        assert store["CCC_OAS"] == {}


class TestAlreadyUpdatedToday:
    def test_true_when_stamp_matches_today(self):
        import datetime
        store = {"last_updated": datetime.date.today().isoformat()}
        assert m.already_updated_today(store)

    def test_false_when_stamp_is_stale_or_absent(self):
        assert not m.already_updated_today({"last_updated": "2020-01-01"})
        assert not m.already_updated_today({})


class TestUpdateCreditHistoryStore:
    def test_skips_when_already_updated_today(self, tmp_path):
        import datetime
        (tmp_path / m.STORE_FILENAME).write_text(
            json.dumps({"last_updated": datetime.date.today().isoformat()}),
            encoding="utf-8",
        )
        with patch.object(m, "fetch_history_with_dates") as fake_fetch:
            summary = m.update_credit_history_store()
        fake_fetch.assert_not_called()
        assert summary["skipped_reason"] == "already updated today"

    def test_merges_and_converts_percent_to_bps(self, tmp_path):
        def fake_fetch(series_id, days):
            return [("2026-06-01", 2.80), ("2026-06-02", 2.90)]

        with patch.object(m, "fetch_history_with_dates", side_effect=fake_fetch), \
             patch.object(m, "_commit"):
            summary = m.update_credit_history_store()

        assert summary["error"] is None
        assert summary["updated"] is True
        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert stored["HY_OAS"]["2026-06-01"] == 280.0
        assert stored["HY_OAS"]["2026-06-02"] == 290.0
        assert summary["added"]["HY_OAS"] == 2

    def test_preserves_dates_that_age_out_of_latest_fetch(self, tmp_path):
        """The whole point of the store: a date FRED no longer returns (aged
        out of its rolling window) must survive a merge, not get dropped."""
        (tmp_path / m.STORE_FILENAME).write_text(json.dumps({
            "HY_OAS": {"2023-01-01": 350.0},
            "IG_OAS": {}, "CCC_OAS": {},
        }), encoding="utf-8")

        def fake_fetch(series_id, days):
            return [("2026-06-01", 2.80)]  # FRED's window no longer includes 2023-01-01

        with patch.object(m, "fetch_history_with_dates", side_effect=fake_fetch):
            m.update_credit_history_store()

        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert stored["HY_OAS"]["2023-01-01"] == 350.0  # preserved
        assert stored["HY_OAS"]["2026-06-01"] == 280.0  # newly added

    def test_no_new_data_reports_zero_added_and_no_commit(self, tmp_path):
        (tmp_path / m.STORE_FILENAME).write_text(json.dumps({
            "HY_OAS": {"2026-06-01": 280.0}, "IG_OAS": {}, "CCC_OAS": {},
        }), encoding="utf-8")

        def fake_fetch(series_id, days):
            return [("2026-06-01", 2.80)] if series_id == "BAMLH0A0HYM2" else []

        with patch.object(m, "fetch_history_with_dates", side_effect=fake_fetch), \
             patch.object(m, "_commit") as fake_commit:
            summary = m.update_credit_history_store()

        assert summary["added"]["HY_OAS"] == 0
        assert summary["committed"] is False
        fake_commit.assert_not_called()

    def test_new_data_triggers_commit(self, tmp_path):
        def fake_fetch(series_id, days):
            return [("2026-06-01", 2.80)]

        with patch.object(m, "fetch_history_with_dates", side_effect=fake_fetch), \
             patch.object(m, "_commit") as fake_commit:
            summary = m.update_credit_history_store()

        assert summary["committed"] is True
        fake_commit.assert_called_once()

    def test_fetch_exception_is_caught_not_raised(self, tmp_path):
        with patch.object(m, "fetch_history_with_dates", side_effect=RuntimeError("boom")):
            summary = m.update_credit_history_store()  # must not raise
        assert summary["error"] == "boom"
        assert summary["updated"] is False

    def test_git_failure_is_caught_not_raised(self, tmp_path):
        def fake_fetch(series_id, days):
            return [("2026-06-01", 2.80)]

        with patch.object(m, "fetch_history_with_dates", side_effect=fake_fetch), \
             patch.object(m.subprocess, "run",
                          side_effect=subprocess.CalledProcessError(1, "git")):
            summary = m.update_credit_history_store()  # must not raise
        assert summary["error"] is not None

    def test_span_reports_full_date_range_and_count(self, tmp_path):
        def fake_fetch(series_id, days):
            return [("2026-06-01", 2.80), ("2026-06-02", 2.85), ("2026-06-03", 2.90)]

        with patch.object(m, "fetch_history_with_dates", side_effect=fake_fetch), \
             patch.object(m, "_commit"):
            summary = m.update_credit_history_store()

        assert summary["span"]["HY_OAS"] == ["2026-06-01", "2026-06-03", 3]
