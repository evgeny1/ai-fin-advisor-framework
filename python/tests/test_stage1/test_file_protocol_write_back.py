"""
tests/test_stage1/test_file_protocol_write_back.py — ENG-48

Coverage for the push-backgrounding half of the ENG-48 fix
(FRAMEWORK_BACKLOG.md): _git_commit() used to run `git push` synchronously,
up to its own 30s timeout, inside the same call the MCP layer's 90s
_with_timeout() budget shares with render/compact/file-write/commit. Both
confirmed ENG-48 TIMEOUTs landed at ~90.02s -- right at the edge -- and
push was the prime suspect for eating that margin (already non-fatal since
ENG-38, so backgrounding it changes no write guarantee).

These tests mock subprocess.run entirely -- no real git repo needed, and
matches this test suite's existing pattern of never exercising real git
operations directly (other write_back tests all use dry_run=True instead).
The commit steps (add/commit/rev-parse) are asserted to run synchronously
and return the real sha; push is asserted to run in the background and to
still complete on its own.
"""
from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from advisor.data import file_protocol


def _fake_git_run_factory(push_delay: float, push_started: threading.Event,
                           push_completed: threading.Event, sha: str = "abc1234"):
    """Builds a fake subprocess.run() standing in for `git -C <repo> <args...>`.
    add/commit/rev-parse return instantly; push sleeps push_delay seconds
    before "completing", signalling both events around the sleep so a test
    can distinguish "started" from "actually finished"."""

    def fake_run(cmd, capture_output=True, text=True, check=True, env=None, timeout=None):
        args = cmd[3:]  # strip ["git", "-C", repo]
        if args and args[0] == "push":
            push_started.set()
            time.sleep(push_delay)
            push_completed.set()
            return SimpleNamespace(stdout="", stderr="")
        if args and args[0] == "rev-parse":
            return SimpleNamespace(stdout=f"{sha}\n", stderr="")
        return SimpleNamespace(stdout="", stderr="")

    return fake_run


class TestGitCommitBackgroundsPush:

    def test_returns_before_push_completes(self, tmp_path, monkeypatch):
        """The whole point of the ENG-48 fix: _git_commit() must not block
        on git push. Push is stubbed to take 0.5s; _git_commit() must
        return well before that."""
        push_started = threading.Event()
        push_completed = threading.Event()
        monkeypatch.setattr(
            file_protocol.subprocess, "run",
            _fake_git_run_factory(0.5, push_started, push_completed),
        )

        start = time.monotonic()
        sha = file_protocol._git_commit(tmp_path, ["Session_Log.md"], "test commit")
        elapsed = time.monotonic() - start

        assert sha == "abc1234"
        assert elapsed < 0.3, (
            f"_git_commit() took {elapsed:.2f}s -- push (0.5s stub) appears "
            "to still be running synchronously, not backgrounded"
        )

    def test_push_still_completes_in_background(self, tmp_path, monkeypatch):
        """Backgrounding push must not mean dropping it -- it should still
        run to completion shortly after _git_commit() returns."""
        push_started = threading.Event()
        push_completed = threading.Event()
        monkeypatch.setattr(
            file_protocol.subprocess, "run",
            _fake_git_run_factory(0.2, push_started, push_completed),
        )

        file_protocol._git_commit(tmp_path, ["Session_Log.md"], "test commit")

        assert push_completed.wait(timeout=2.0), (
            "push never completed in the background within 2s"
        )

    def test_commit_sha_unaffected_by_slow_push(self, tmp_path, monkeypatch):
        """The sha returned comes from `git rev-parse` (runs before push is
        even started), so a slow or hung push must never change it or
        delay it being returned."""
        push_started = threading.Event()
        push_completed = threading.Event()
        monkeypatch.setattr(
            file_protocol.subprocess, "run",
            _fake_git_run_factory(1.5, push_started, push_completed, sha="deadbee"),
        )

        sha = file_protocol._git_commit(tmp_path, ["Portfolio_State.md"], "test commit 2")
        assert sha == "deadbee"

    def test_push_failure_in_background_does_not_raise(self, tmp_path, monkeypatch):
        """A push that fails (CalledProcessError) must not propagate --
        ENG-38 already made push failures non-fatal; backgrounding must
        preserve that, not turn a background failure into a crashed
        daemon thread that silently loses the warning log."""
        import subprocess as _subprocess

        def fake_run(cmd, capture_output=True, text=True, check=True, env=None, timeout=None):
            args = cmd[3:]
            if args and args[0] == "push":
                raise _subprocess.CalledProcessError(1, cmd, stderr="simulated push failure")
            if args and args[0] == "rev-parse":
                return SimpleNamespace(stdout="cafefee\n", stderr="")
            return SimpleNamespace(stdout="", stderr="")

        monkeypatch.setattr(file_protocol.subprocess, "run", fake_run)

        # Must not raise, and must still return the real sha synchronously.
        sha = file_protocol._git_commit(tmp_path, ["Session_Log.md"], "test commit 3")
        assert sha == "cafefee"

        # Give the background thread a moment to hit (and swallow) the
        # simulated failure before the test process moves on.
        time.sleep(0.2)


# ── ENG-49: per-step progress instrumentation ────────────────────────────────

import json


class TestWriteBackProgressInstrumentation:
    """ENG-49 (FRAMEWORK_BACKLOG.md): every write-back step boundary records
    a progress marker to .write_back_progress.json so a TIMEOUT can be
    triaged from the record directly. Instrumentation is best-effort: it
    must never raise, and a broken progress file must never break the
    actual write-back."""

    def test_report_and_read_round_trip(self, tmp_path):
        file_protocol.report_write_back_progress("GIT_ADD", detail="a, b", base=tmp_path)
        entry = file_protocol.read_write_back_progress(base=tmp_path)
        assert entry is not None
        assert entry["step"] == "GIT_ADD"
        assert entry["detail"] == "a, b"
        assert isinstance(entry["ts"], float)
        assert "ts_iso" in entry and "pid" in entry

    def test_report_never_raises_on_unwritable_base(self, tmp_path):
        # Nonexistent nested directory — write_text will fail internally;
        # the reporter must swallow it (instrumentation can never break
        # the write-back it instruments).
        bad_base = tmp_path / "does" / "not" / "exist"
        file_protocol.report_write_back_progress("COMPACT", base=bad_base)  # no raise

    def test_read_returns_none_when_file_missing(self, tmp_path):
        assert file_protocol.read_write_back_progress(base=tmp_path) is None

    def test_read_returns_none_on_corrupt_json(self, tmp_path):
        (tmp_path / file_protocol.PROGRESS_FILE).write_text(
            "{not valid json", encoding="utf-8"
        )
        assert file_protocol.read_write_back_progress(base=tmp_path) is None

    def test_read_returns_none_on_wrong_shape(self, tmp_path):
        # Valid JSON but not a progress entry (no 'step' key) — must be
        # treated as unavailable, not passed through to enrich a TIMEOUT.
        (tmp_path / file_protocol.PROGRESS_FILE).write_text(
            json.dumps(["a", "list"]), encoding="utf-8"
        )
        assert file_protocol.read_write_back_progress(base=tmp_path) is None

    def test_git_commit_records_step_sequence(self, tmp_path, monkeypatch):
        """_git_commit must record GIT_ADD → GIT_COMMIT → COMMIT_DONE(sha)
        → PUSH_BACKGROUNDED(sha), in that order, synchronously."""
        recorded = []
        monkeypatch.setattr(
            file_protocol, "report_write_back_progress",
            lambda step, detail="", base=None: recorded.append((step, detail)),
        )
        push_started = threading.Event()
        push_completed = threading.Event()
        monkeypatch.setattr(
            file_protocol.subprocess, "run",
            _fake_git_run_factory(0.0, push_started, push_completed, sha="fee1dea"),
        )

        sha = file_protocol._git_commit(tmp_path, ["Session_Log.md"], "test")
        steps = [s for s, _ in recorded]
        assert steps == ["GIT_ADD", "GIT_COMMIT", "COMMIT_DONE", "PUSH_BACKGROUNDED"]
        assert recorded[0][1] == "Session_Log.md"     # GIT_ADD detail = files
        assert recorded[2][1] == sha == "fee1dea"     # COMMIT_DONE detail = sha
        assert recorded[3][1] == sha                  # PUSH_BACKGROUNDED detail = sha

    def test_write_back_dry_run_records_expected_sequence(self, tmp_path, monkeypatch):
        """dry_run write-back with no calibration state and no archives:
        COMPACT → WRITE_SESSION_LOG → WRITE_PORTFOLIO_STATE → DRY_RUN_DONE,
        with no calibration step and no git steps."""
        from advisor.types import SessionType

        monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))
        recorded = []
        monkeypatch.setattr(
            file_protocol, "report_write_back_progress",
            lambda step, detail="", base=None: recorded.append(step),
        )

        file_protocol.write_back(
            calibration_state=None,
            session_log="# Session Log\n",
            portfolio_state="# Portfolio State\n",
            session_type=SessionType.FULL_DESKTOP,
            dry_run=True,
        )
        assert recorded == [
            "COMPACT", "WRITE_SESSION_LOG", "WRITE_PORTFOLIO_STATE", "DRY_RUN_DONE",
        ]

    def test_write_back_records_calibration_step_when_given(self, tmp_path, monkeypatch):
        from advisor.types import SessionType

        monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))
        recorded = []
        monkeypatch.setattr(
            file_protocol, "report_write_back_progress",
            lambda step, detail="", base=None: recorded.append(step),
        )

        file_protocol.write_back(
            calibration_state="# Calibration State\n",
            session_log="# Session Log\n",
            portfolio_state="# Portfolio State\n",
            session_type=SessionType.FULL_DESKTOP,
            dry_run=True,
        )
        assert recorded == [
            "COMPACT", "WRITE_CALIBRATION_STATE", "WRITE_SESSION_LOG",
            "WRITE_PORTFOLIO_STATE", "DRY_RUN_DONE",
        ]

    def test_progress_file_final_state_after_real_commit(self, tmp_path, monkeypatch):
        """Un-mocked reporter through _git_commit: the file on disk must
        end at PUSH_BACKGROUNDED with the commit sha as detail."""
        push_started = threading.Event()
        push_completed = threading.Event()
        monkeypatch.setattr(
            file_protocol.subprocess, "run",
            _fake_git_run_factory(0.0, push_started, push_completed, sha="0ddba11"),
        )

        file_protocol._git_commit(tmp_path, ["Session_Log.md"], "test")
        entry = file_protocol.read_write_back_progress(base=tmp_path)
        assert entry is not None
        assert entry["step"] == "PUSH_BACKGROUNDED"
        assert entry["detail"] == "0ddba11"

    def test_progress_file_is_gitignored(self):
        """The progress file is local-only working state (like
        .git-commit-msg.txt) — it must never be committable."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[3]
        gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
        assert file_protocol.PROGRESS_FILE in gitignore
