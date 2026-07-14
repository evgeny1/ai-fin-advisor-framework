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
