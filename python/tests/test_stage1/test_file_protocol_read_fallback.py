"""
tests/test_stage1/test_file_protocol_read_fallback.py — ENG-21

Coverage for read_framework_file()'s local→Drive fallback chain. This path
had zero test coverage before ENG-21 investigated whether it had ever
actually fired in practice.

Finding (2026-06-20): it hasn't, and currently can't succeed even if
triggered — _get_drive_service() (reused from allocation_sheet.py) requires
either a service-account JSON or an OAuth token file under ~/.advisor/,
and per the framework owner neither is configured: the Python-native
Google Drive integration is a possible future feature, not an active one.
The Allocation spreadsheet itself is read by Claude directly via the
Google Drive MCP connector, not by this code path at all.

These tests don't assert anything about real credentials (CI/dev machines
won't have ~/.advisor/ configured, and shouldn't need to be for this
suite to pass). They confirm the *shape* of the fallback chain: local
file wins when present, Drive is attempted when it's not, and a Drive
failure (the expected outcome with no credentials configured) surfaces
as a clean HardStopException rather than an unhandled exception.
"""
from __future__ import annotations

import pytest

from advisor.data import file_protocol
from advisor.exceptions import HardStopException


@pytest.fixture
def isolated_framework_path(tmp_path, monkeypatch):
    monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))
    return tmp_path


class TestReadFrameworkFileLocalPrimary:

    def test_reads_local_file_when_present(self, isolated_framework_path, monkeypatch):
        (isolated_framework_path / "Calibration_State.md").write_text(
            "local content", encoding="utf-8"
        )
        # If this calls _read_from_drive at all, it's a bug — fail loudly.
        monkeypatch.setattr(
            file_protocol, "_read_from_drive",
            lambda filename: (_ for _ in ()).throw(
                AssertionError("Drive fallback must not be attempted when local file exists")
            ),
        )
        result = file_protocol.read_framework_file("Calibration_State.md")
        assert result == "local content"

    def test_falls_back_to_drive_when_local_missing(self, isolated_framework_path, monkeypatch):
        """Local file absent → Drive fallback is attempted and its result used."""
        monkeypatch.setattr(
            file_protocol, "_read_from_drive",
            lambda filename: f"drive content for {filename}",
        )
        result = file_protocol.read_framework_file("Session_Log.md")
        assert result == "drive content for Session_Log.md"

    def test_hard_stops_with_clear_message_when_both_local_and_drive_fail(
        self, isolated_framework_path, monkeypatch
    ):
        """
        This is the realistic current-state outcome: local file missing AND
        Drive fails (no credentials configured) → clean HardStopException,
        not an unhandled exception bubbling out of the MCP tool call.
        """
        monkeypatch.setattr(
            file_protocol, "_read_from_drive",
            lambda filename: (_ for _ in ()).throw(EnvironmentError("Google credentials not found")),
        )
        with pytest.raises(HardStopException) as exc_info:
            file_protocol.read_framework_file("Calibration_State.md")
        msg = str(exc_info.value)
        assert "Calibration_State.md" in msg
        assert "Google credentials not found" in msg


class TestGetDriveServiceWithoutCredentials:
    """
    _get_drive_service() (allocation_sheet.py, reused by file_protocol's
    Drive fallback) must fail cleanly — not with an import error or an
    opaque googleapiclient traceback — when no credentials are configured.
    This is the expected state on this framework today (ENG-21).
    """

    def test_raises_environment_error_when_no_credentials_configured(
        self, tmp_path, monkeypatch
    ):
        from advisor.data.fetchers import allocation_sheet

        monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", str(tmp_path / "nonexistent_sa.json"))
        monkeypatch.setenv("GOOGLE_OAUTH_TOKEN", str(tmp_path / "nonexistent_token.json"))

        with pytest.raises(EnvironmentError, match="Google credentials not found"):
            allocation_sheet._get_drive_service()
