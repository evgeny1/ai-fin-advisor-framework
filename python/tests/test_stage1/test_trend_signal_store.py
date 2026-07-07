"""
Tests for trend_signal_store.py (FRAMEWORK_BACKLOG ENG-50/ENG-55) --
persistent shadow-mode log for the trend/rotation signal, mirroring
credit_history_store.py's pattern with an added retroactive
forward-outcome fill mechanism.
"""
from __future__ import annotations

import datetime
import json
import subprocess
from unittest.mock import patch

import pytest

from advisor.data import trend_signal_store as m
from advisor.types import ComparatorMode, TrendSignalCode, TrendSignalReading


@pytest.fixture(autouse=True)
def _point_at_tmp(tmp_path, monkeypatch):
    """Every test gets its own isolated 'framework root' -- never touches
    the real repo or the real TrendSignalStore.json."""
    monkeypatch.setattr(m, "framework_path", lambda: tmp_path)
    return tmp_path


def _reading(ticker="MLPX", session_date="2026-07-10", rs_signal=TrendSignalCode.STRENGTHENING,
             price_at_signal=78.42):
    return TrendSignalReading(
        ticker=ticker, session_date=session_date, rs_signal=rs_signal,
        own_short_dir="up", own_medium_dir="up",
        comparator_mode=ComparatorMode.HYBRID,
        comparator_detail="BZ=F return-spread, HY_OAS confirmation gate",
        price_at_signal=price_at_signal,
        dominant_directive_conflict_aware="ADD",
    )


class TestLoadStore:
    def test_no_file_returns_empty_dict(self):
        assert m._load_store() == {}

    def test_malformed_json_returns_empty_dict_not_exception(self, tmp_path):
        (tmp_path / m.STORE_FILENAME).write_text("{not valid json", encoding="utf-8")
        assert m._load_store() == {}


class TestUpdateTrendSignalStore:
    def test_new_entry_written_and_committed(self, tmp_path):
        with patch.object(m, "_commit") as fake_commit:
            summary = m.update_trend_signal_store([_reading()], {"MLPX": 78.42})

        assert summary["error"] is None
        assert summary["entries_added"] == 1
        assert summary["committed"] is True
        fake_commit.assert_called_once()

        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert stored["MLPX"]["2026-07-10"]["rs_signal"] == "STRENGTHENING"
        assert stored["MLPX"]["2026-07-10"]["price_at_signal"] == 78.42
        assert stored["MLPX"]["2026-07-10"]["forward_outcome"] is None

    def test_no_new_entries_and_nothing_due_reports_no_commit(self, tmp_path):
        with patch.object(m, "_commit") as fake_commit:
            summary = m.update_trend_signal_store([], {})
        assert summary["entries_added"] == 0
        assert summary["forward_outcomes_filled"] == 0
        assert summary["committed"] is False
        fake_commit.assert_not_called()

    def test_fetch_or_write_exception_is_caught_not_raised(self, tmp_path):
        with patch.object(m, "_save", side_effect=RuntimeError("disk full")):
            summary = m.update_trend_signal_store([_reading()], {"MLPX": 78.42})  # must not raise
        assert summary["error"] == "disk full"
        assert summary["updated"] is False

    def test_git_failure_is_caught_not_raised(self, tmp_path):
        with patch.object(m.subprocess, "run",
                          side_effect=subprocess.CalledProcessError(1, "git")):
            summary = m.update_trend_signal_store([_reading()], {"MLPX": 78.42})  # must not raise
        assert summary["error"] is not None


class TestForwardOutcomeFill:
    """
    These seed the store directly via m._save() to represent an entry
    that already existed from a past session, then make ONE
    update_trend_signal_store([], ...) call to represent the later check.
    (Calling update_trend_signal_store twice with a backdated reading
    does NOT work for this: the fill pass runs on every call, including
    the very first one that adds the backdated entry, so it would fill
    immediately using that same call's current_prices instead of a
    later, different price.)
    """

    def _seed(self, tmp_path, ticker, date, rs_signal, price_at_signal):
        store = {
            ticker: {
                date: {
                    "rs_signal": rs_signal, "own_short_dir": "up", "own_medium_dir": "up",
                    "comparator_mode": "hybrid", "comparator_detail": "test",
                    "price_at_signal": price_at_signal,
                    "dominant_directive_conflict_aware": "ADD",
                    "margin_debt_fragility_flag": None, "quality_flags": [],
                    "forward_outcome": None,
                }
            }
        }
        (tmp_path / m.STORE_FILENAME).write_text(json.dumps(store), encoding="utf-8")

    def test_entry_younger_than_target_gap_not_touched(self, tmp_path):
        """29 calendar days is the fill threshold — a 10-day-old entry
        must NOT get a forward_outcome yet."""
        young_date = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
        self._seed(tmp_path, "MLPX", young_date, "STRENGTHENING", 78.42)

        with patch.object(m, "_commit"):
            summary = m.update_trend_signal_store([], {"MLPX": 82.00})

        assert summary["forward_outcomes_filled"] == 0
        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert stored["MLPX"][young_date]["forward_outcome"] is None

    def test_strengthening_matched_when_price_rose(self, tmp_path):
        old_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self._seed(tmp_path, "MLPX", old_date, "STRENGTHENING", 78.42)

        with patch.object(m, "_commit"):
            summary = m.update_trend_signal_store([], {"MLPX": 85.00})

        assert summary["forward_outcomes_filled"] == 1
        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        outcome = stored["MLPX"][old_date]["forward_outcome"]
        assert outcome["price_direction_since_signal"] == "up"
        assert outcome["matched_signal"] is True
        assert outcome["target_gap_trading_days"] == 21

    def test_strengthening_not_matched_when_price_fell(self, tmp_path):
        old_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self._seed(tmp_path, "MLPX", old_date, "STRENGTHENING", 78.42)

        with patch.object(m, "_commit"):
            m.update_trend_signal_store([], {"MLPX": 70.00})

        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        outcome = stored["MLPX"][old_date]["forward_outcome"]
        assert outcome["price_direction_since_signal"] == "down"
        assert outcome["matched_signal"] is False

    def test_inconclusive_signal_gets_null_matched_not_false(self, tmp_path):
        """INCONCLUSIVE made no directional call — there's nothing to
        validate against, so matched_signal must be null, not a false
        negative."""
        old_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self._seed(tmp_path, "MLPX", old_date, "INCONCLUSIVE", 78.42)

        with patch.object(m, "_commit"):
            m.update_trend_signal_store([], {"MLPX": 85.00})

        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        outcome = stored["MLPX"][old_date]["forward_outcome"]
        assert outcome["matched_signal"] is None
        assert outcome["price_direction_since_signal"] == "up"  # still recorded, informational

    def test_missing_current_price_records_error_not_exception(self, tmp_path):
        old_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self._seed(tmp_path, "MLPX", old_date, "STRENGTHENING", 78.42)

        with patch.object(m, "_commit"):
            summary = m.update_trend_signal_store([], {})  # MLPX price missing this time

        assert summary["forward_outcomes_filled"] == 1
        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert "error" in stored["MLPX"][old_date]["forward_outcome"]

    def test_already_filled_entry_not_recomputed(self, tmp_path):
        """Once forward_outcome is set, a later call must not overwrite it."""
        old_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self._seed(tmp_path, "MLPX", old_date, "STRENGTHENING", 78.42)

        with patch.object(m, "_commit"):
            m.update_trend_signal_store([], {"MLPX": 85.00})
            summary_second_pass = m.update_trend_signal_store([], {"MLPX": 200.00})

        assert summary_second_pass["forward_outcomes_filled"] == 0
        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert stored["MLPX"][old_date]["forward_outcome"]["price_at_check"] == 85.00

    def test_multiple_tickers_independent(self, tmp_path):
        old_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self._seed(tmp_path, "MLPX", old_date, "STRENGTHENING", 78.42)
        store = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        store["XAR"] = {old_date: dict(store["MLPX"][old_date])}
        store["XAR"][old_date]["price_at_signal"] = 250.0
        (tmp_path / m.STORE_FILENAME).write_text(json.dumps(store), encoding="utf-8")

        with patch.object(m, "_commit"):
            summary = m.update_trend_signal_store([], {"MLPX": 85.00, "XAR": 240.00})

        assert summary["forward_outcomes_filled"] == 2
        stored = json.loads((tmp_path / m.STORE_FILENAME).read_text(encoding="utf-8"))
        assert stored["MLPX"][old_date]["forward_outcome"]["price_direction_since_signal"] == "up"
        assert stored["XAR"][old_date]["forward_outcome"]["price_direction_since_signal"] == "down"
