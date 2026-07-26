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
        grace-poll window -- status must remain TIMEOUT (never silently
        upgraded), with the original error text preserved. As of the
        ENG-49 instrumentation fix the payload is additionally ENRICHED
        with last-step triage fields -- asserted in detail by the
        TestTimeoutProgressEnrichment class below."""
        timeout_result = json.dumps({"status": "TIMEOUT", "error": "exceeded its 90s..."})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)
        monkeypatch.setattr(mcp_server.time, "sleep", lambda s: None)
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: "SAME_HEAD")

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=False,
        )
        parsed = json.loads(result)
        assert parsed["status"] == "TIMEOUT"
        assert parsed["error"] == "exceeded its 90s..."
        assert "last_step" in parsed and "triage_note" in parsed

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


# ── ENG-49: TIMEOUT progress enrichment ──────────────────────────────────────

import time as _time

from advisor.data import file_protocol as _fp


def _run_stuck_timeout(monkeypatch, progress):
    """Drive _write_back_with_verification into the genuinely-stuck branch
    (TIMEOUT, HEAD never changes) with read_write_back_progress stubbed to
    return `progress`; returns the parsed response payload."""
    timeout_result = json.dumps({"status": "TIMEOUT", "error": "exceeded its 90s..."})
    monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)
    monkeypatch.setattr(mcp_server.time, "sleep", lambda s: None)
    monkeypatch.setattr(mcp_server, "_git_head_short", lambda: "SAME_HEAD")
    monkeypatch.setattr(_fp, "read_write_back_progress", lambda base=None: progress)

    result = mcp_server._write_back_with_verification(
        primary_driver="d", open_triggers=[], open_decisions=[],
        session_type="ad-hoc", next_session_flags=[], dry_run=False,
    )
    return json.loads(result)


class TestTimeoutProgressEnrichment:
    """ENG-49 (FRAMEWORK_BACKLOG.md): a genuine TIMEOUT response must carry
    the last progress step recorded FOR THIS CALL, so triage happens from
    the response itself instead of a manual git status/git diff pass."""

    def test_fresh_progress_embedded_in_timeout(self, monkeypatch):
        payload = _run_stuck_timeout(monkeypatch, {
            "step": "GIT_ADD", "detail": "Session_Log.md, Portfolio_State.md",
            "ts": _time.time() + 5, "ts_iso": "2026-07-26T12:00:00.000",
        })
        assert payload["status"] == "TIMEOUT"          # never upgraded
        assert payload["last_step"] == "GIT_ADD"
        assert payload["last_step_detail"] == "Session_Log.md, Portfolio_State.md"
        assert payload["last_step_ts"] == "2026-07-26T12:00:00.000"
        assert "GIT_ADD" in payload["triage_note"]

    def test_stale_progress_from_prior_call_not_misattributed(self, monkeypatch):
        """A progress file left by a PRIOR successful call (ts before this
        call started) must not be reported as this call's progress."""
        payload = _run_stuck_timeout(monkeypatch, {
            "step": "PUSH_BACKGROUNDED", "detail": "abc1234",
            "ts": _time.time() - 3600, "ts_iso": "2026-07-26T10:00:00.000",
        })
        assert payload["status"] == "TIMEOUT"
        assert payload["last_step"] is None
        assert "stale" in payload["triage_note"]

    def test_missing_progress_reports_null_with_fallback_note(self, monkeypatch):
        payload = _run_stuck_timeout(monkeypatch, None)
        assert payload["status"] == "TIMEOUT"
        assert payload["last_step"] is None
        assert "git status" in payload["triage_note"]

    def test_original_error_text_preserved_through_enrichment(self, monkeypatch):
        payload = _run_stuck_timeout(monkeypatch, {
            "step": "WRITE_SESSION_LOG", "detail": "",
            "ts": _time.time() + 5, "ts_iso": "x",
        })
        assert payload["error"] == "exceeded its 90s..."

    def test_ok_delayed_path_not_enriched(self, monkeypatch):
        """The ENG-48 OK_DELAYED path (commit lands during grace poll) is a
        success — it must return before enrichment, with no triage fields."""
        timeout_result = json.dumps({"status": "TIMEOUT", "error": "..."})
        monkeypatch.setattr(mcp_server, "_with_timeout", lambda fn, t, **kw: timeout_result)
        monkeypatch.setattr(mcp_server.time, "sleep", lambda s: None)
        heads = iter(["H_BEFORE", "H_AFTER"] + ["H_AFTER"] * 10)
        monkeypatch.setattr(mcp_server, "_git_head_short", lambda: next(heads))

        def _fail(base=None):
            raise AssertionError("read_write_back_progress must not be called on OK_DELAYED")
        monkeypatch.setattr(_fp, "read_write_back_progress", _fail)

        result = mcp_server._write_back_with_verification(
            primary_driver="d", open_triggers=[], open_decisions=[],
            session_type="ad-hoc", next_session_flags=[], dry_run=False,
        )
        parsed = json.loads(result)
        assert parsed["status"] == "OK_DELAYED"
        assert "last_step" not in parsed and "triage_note" not in parsed
