"""
file_protocol.py — M12 file access via local filesystem (primary) and Google Drive (fallback).
Local path syncs bidirectionally with Google Drive via the desktop client — files are always
current when the Drive client is running (which it is on FULL_DESKTOP sessions).
M12 write-back (git) is also wired here but guarded by SessionType.FULL_DESKTOP.
"""
from __future__ import annotations

import subprocess
import datetime
import logging
import os
from pathlib import Path
from typing import Optional

from ..types import SessionType
from ..exceptions import HardStopException, WriteBackGuardViolation

logger = logging.getLogger(__name__)

# Default local path — override via ADVISOR_FRAMEWORK_PATH env var
_DEFAULT_PATH = Path(
    os.path.expanduser(
        "~/Library/CloudStorage/"
        "GoogleDrive-evgeny.shatalov@gmail.com/"
        "My Drive/dev/AI Financial Advisor Framework"
    )
)


def framework_path() -> Path:
    custom = os.environ.get("ADVISOR_FRAMEWORK_PATH")
    return Path(custom) if custom else _DEFAULT_PATH


# ── Framework file reads ──────────────────────────────────────────────────────

def read_framework_file(filename: str) -> str:
    """
    Read any file from the local framework folder.
    Local filesystem is primary (Drive desktop client keeps it current).
    Raises HardStopException if file not found after fallback.
    """
    local = framework_path() / filename
    if local.exists():
        logger.debug(f"Reading {filename} from local filesystem")
        return local.read_text(encoding="utf-8")

    logger.warning(f"{filename} not found locally — attempting Drive download")
    try:
        return _read_from_drive(filename)
    except Exception as e:
        raise HardStopException(
            f"Cannot read {filename}: not found locally and Drive fallback failed: {e}",
            stage="file_protocol.read_framework_file",
        )


def read_calibration_state() -> str:
    """Fetch Calibration_State.md. HARD_STOP if unavailable."""
    return read_framework_file("Calibration_State.md")


def read_session_log() -> str:
    """Fetch Session_Log.md. HARD_STOP if unavailable."""
    return read_framework_file("Session_Log.md")


# ── Write-back (FULL_DESKTOP only) ────────────────────────────────────────────

def write_back(
    calibration_state: Optional[str],
    session_log: str,
    portfolio_state: str,
    session_type: SessionType,
    dry_run: bool = False,
) -> str:
    """
    M12 PATTERN_B: atomic write-back of three files in a single git commit.
    NEVER execute in READONLY_MOBILE session.
    NEVER commit if §8 probabilities are absent (caller must validate first).
    Returns git commit hash on success.
    """
    if session_type != SessionType.FULL_DESKTOP:
        raise WriteBackGuardViolation(
            "WriteBack blocked: session_type is READONLY_MOBILE",
            stage="file_protocol.write_back",
        )

    base = framework_path()
    today = datetime.date.today().isoformat()
    files_written = []

    if calibration_state is not None:
        _safe_write(base / "Calibration_State.md", calibration_state)
        files_written.append("Calibration_State.md")

    _safe_write(base / "Session_Log.md", session_log)
    files_written.append("Session_Log.md")

    _safe_write(base / "Portfolio_State.md", portfolio_state)
    files_written.append("Portfolio_State.md")

    if dry_run:
        logger.info(f"[DRY RUN] Would commit: {files_written}")
        return "dry-run"

    return _git_commit(base, files_written, f"Session write-back: {today} — §8 scenario state + Portfolio_State")


def _safe_write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    logger.debug(f"Written: {path.name}")


def _git_commit(repo: Path, files: list[str], message: str) -> str:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()

    git("add", *files)
    git("commit", "-m", message)
    git("push", "origin", "master")
    sha = git("rev-parse", "--short", "HEAD")
    logger.info(f"Write-back committed: {sha} — {message}")
    return sha


# ── Drive fallback ────────────────────────────────────────────────────────────

def _read_from_drive(filename: str) -> str:
    """
    Fallback: download file from Google Drive framework folder.
    Uses google-api-python-client. Only called when local file is missing.
    """
    import base64
    from googleapiclient.discovery import build

    # Reuse same auth as allocation_sheet module
    from .fetchers.allocation_sheet import _get_drive_service
    service = _get_drive_service()

    folder_id = "1xGHBLw-wzsJOxzm0rFpuHsBhx0PFhZzQ"
    result = service.files().list(
        q=f"name = '{filename}' and '{folder_id}' in parents",
        spaces="drive",
        fields="files(id, name)",
        pageSize=2,
    ).execute()
    files = result.get("files", [])
    if not files:
        raise FileNotFoundError(f"{filename} not found in Drive framework folder")
    if len(files) > 1:
        raise RuntimeError(f"Duplicate files named {filename} in Drive — resolve manually")

    content = service.files().get_media(fileId=files[0]["id"]).execute()
    # .md files are returned as bytes
    if isinstance(content, bytes):
        return content.decode("utf-8")
    return str(content)
