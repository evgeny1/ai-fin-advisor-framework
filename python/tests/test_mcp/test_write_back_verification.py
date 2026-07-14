"""
tests/test_mcp/test_write_back_verification.py — ENG-48

Coverage for _write_back_with_verification() (mcp_server.py): the
git-HEAD-based check that tells a genuinely-late-but-successful
advisor_write_back() apart from a genuinely-stuck one, instead of
trusting whichever side of the 90s _with_timeout() race the response
happens to land on.

Confirmed race (FRAMEWORK_BACKLOG.md ENG-48): both observed TIMEOUTs
landed at ~90.02s against the 90.0s budget -- the underlying call had
actually finished, including the git commit, a beat after
future.result() gave up waiting.

These tests mock both _with_timeout() and _git_head_short() directly --
no real MCP call, no real git repo, no real 90s wait.
"""
from __future__ import annotations

import json

from advisor import mcp_server


class TestWriteBackVerification:

    def test_ok_result_passes_through_unchanged(self, monkeypatch):
        """A normal, on-time success must not be touched by the
        verification wrapper at all."""
        ok_result = json.dumps({"status": "OK", "committed": True, "commit_hash": "abc1234"})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: ok_result)
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: "HEAD1")

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=False,
        )
        assert result == ok_result

    def test_dry_run_skips_verification_entirely(self, monkeypatch):
        """dry_run=True never writes a commit, so there's nothing to
        verify -- _git_head_short() must not even be called."""
        timeout_result = json.dumps({"status": "TIMEOUT", "error": "..."})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)

        def _fail_if_called():
            raise AssertionError("_git_head_short() must not be called when dry_run=True")
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: _fail_if_called())

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=True,
        )
        assert result == timeout_result

    def test_ok_delayed_when_commit_lands_during_grace_poll(self, monkeypatch):
        """The actual ENG-48 race: _with_timeout() reports TIMEOUT, but a
        new commit lands (HEAD changes) within the grace-poll window --
        must be reported as a real success, not a false failure."""
        timeout_result = json.dumps({"status": "TIMEOUT", "error": "exceeded its 90s..."})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)
        monkeypatch.setattr(mcp_server.time, "sleep", lambda s: None)

        heads = iter(["HEAD_BEFORE", "HEAD_BEFORE", "HEAD_BEFORE", "HEAD_AFTER"] + ["HEAD_AFTER"] * 10)
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: next(heads))

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=False,
        )
        parsed = json.loads(result)
        assert parsed["status"] == "OK_DELAYED"
        assert parsed["committed"] is True
        assert parsed["commit_hash"] == "HEAD_AF"  # first 7 chars

    def test_timeout_stands_when_no_commit_ever_lands(self, monkeypatch):
        """Genuinely stuck (ENG-49): HEAD never changes across the whole
        grace-poll window -- the original TIMEOUT result must be returned
        unchanged, not silently upgraded."""
        timeout_result = json.dumps({"status": "TIMEOUT", "error": "exceeded its 90s..."})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)
        monkeypatch.setattr(mcp_server.time, "sleep", lambda s: None)
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: "SAME_HEAD")

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=False,
        )
        assert result == timeout_result

    def test_head_before_unavailable_skips_verification(self, monkeypatch):
        """If HEAD can't be read before the call even starts (repo
        missing, git unavailable), there is nothing to compare against --
        must fall back to whatever _with_timeout() returned, not crash."""
        timeout_result = json.dumps({"status": "TIMEOUT", "error": "..."})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: None)

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=False,
        )
        assert result == timeout_result
