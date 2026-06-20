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


import re

_SEC7_ROW_RE = re.compile(r"^\| \d{4}-\d{2}-\d{2}[^\n]*", re.M)
_SEC7_TABLE_HEADER = (
    "| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
)


def _quarter_label(d: datetime.date) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}Q{q}"


def _compact_session_log(session_log: str, base: Path):
    """
    M12 CompactSessionLog (ENG-5): enforce §7 (last 10 rows) / §8 (last 3
    entries) retention on every write-back, not just quarterly Q-end audits.

    If either limit is exceeded, archives the overflow into the current
    quarter’s Archive_[Year]Q[N].md (creating it if absent this quarter,
    appending if it already exists), and returns the compacted session_log.

    Returns (compacted_log, archive_filename_or_None, archive_content_or_None).
    archive_filename/content are None when nothing needed archiving — caller
    should skip writing a 4th file in that case.
    """
    sec7_idx = session_log.find("## Section 7")
    sec8_idx = session_log.find("## Section 8")
    if sec7_idx == -1 or sec8_idx == -1:
        return session_log, None, None

    sec7 = session_log[sec7_idx:sec8_idx]
    sec8 = session_log[sec8_idx:]

    row_matches = [(m.start(), m.group()) for m in _SEC7_ROW_RE.finditer(sec7)]
    ends7 = [s for s, _ in row_matches[1:]] + [len(sec7)]
    rows = [sec7[s:e].rstrip() for (s, _), e in zip(row_matches, ends7)]
    sec7_overflow = max(0, len(rows) - 10)
    archived_rows = rows[:sec7_overflow]
    kept_rows = rows[sec7_overflow:]

    blocks = re.split(r"\n\n---\n\n", sec8)
    header_block = blocks[0]
    entry_blocks = blocks[1:]
    sec8_overflow = max(0, len(entry_blocks) - 3)
    archived_entries = entry_blocks[:sec8_overflow]
    kept_entries = entry_blocks[sec8_overflow:]

    if sec7_overflow == 0 and sec8_overflow == 0:
        return session_log, None, None

    today = datetime.date.today()
    today_iso = today.isoformat()
    quarter = _quarter_label(today)
    archive_filename = f"Archive_{quarter}.md"
    archive_path = base / archive_filename

    if sec7_overflow > 0:
        title_line_end = sec7.find("\n")
        title_line = sec7[:title_line_end]
        note7 = (
            f"\n\n// COMPACTED: {today_iso} — {sec7_overflow} oldest row(s) "
            f"archived to {archive_filename}, restoring the last-10 retention rule "
            f"(FRAMEWORK_BACKLOG.md ENG-5)"
        )
        new_sec7 = (
            title_line + note7 + "\n\n" + _SEC7_TABLE_HEADER
            + "\n".join(kept_rows) + "\n\n"
        )
    else:
        new_sec7 = sec7

    if sec8_overflow > 0:
        note8 = (
            f"\n\n// COMPACTED: {today_iso} — {sec8_overflow} oldest entry(ies) "
            f"archived to {archive_filename}, restoring the last-3 retention rule "
            f"(FRAMEWORK_BACKLOG.md ENG-5)"
        )
        new_header_block = header_block.rstrip() + note8
        new_sec8 = (
            new_header_block + "\n\n---\n\n" + "\n\n---\n\n".join(kept_entries) + "\n"
        )
    else:
        new_sec8 = sec8

    compacted_log = session_log[:sec7_idx] + new_sec7 + new_sec8

    if archive_path.exists():
        archive_content = archive_path.read_text(encoding="utf-8")
    else:
        archive_content = (
            f"# Archive — {today.year} Q{(today.month - 1) // 3 + 1}\n"
            f"<!-- Created: {today_iso} — Session_Log.md compaction per M12 CompactSessionLog -->\n"
            f"<!-- Purpose: append-only archive of displaced §7 rows / §8 entries -->\n\n---\n\n"
        )

    if archived_rows:
        marker = "## Archived §7 Credit Readings"
        idx_sec7_arch = archive_content.find(marker)
        insertion_text = "\n".join(archived_rows) + "\n"
        if idx_sec7_arch == -1:
            archive_content = (
                archive_content.rstrip() + "\n\n" + marker
                + " (displaced by last-10 retention)\n\n" + _SEC7_TABLE_HEADER
                + insertion_text
            )
        else:
            next_heading = archive_content.find("\n## ", idx_sec7_arch + len(marker))
            insert_at = next_heading if next_heading != -1 else len(archive_content)
            archive_content = (
                archive_content[:insert_at].rstrip() + "\n" + insertion_text
                + archive_content[insert_at:]
            )

    if archived_entries:
        marker8 = "## Archived §8 Session States"
        idx_sec8_arch = archive_content.find(marker8)
        insertion_text8 = "\n\n---\n\n".join(archived_entries) + "\n"
        if idx_sec8_arch == -1:
            archive_content = (
                archive_content.rstrip() + "\n\n" + marker8
                + " (displaced by last-3 retention)\n\n" + insertion_text8
            )
        else:
            next_heading8 = archive_content.find("\n## ", idx_sec8_arch + len(marker8))
            insert_at8 = next_heading8 if next_heading8 != -1 else len(archive_content)
            archive_content = (
                archive_content[:insert_at8].rstrip() + "\n\n" + insertion_text8
                + archive_content[insert_at8:]
            )

    return compacted_log, archive_filename, archive_content


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

    §7/§8 compaction (ENG-5): enforced on every call, not gated to
    quarterly Q-end audits. See _compact_session_log().
    """
    if session_type != SessionType.FULL_DESKTOP:
        raise WriteBackGuardViolation(
            "WriteBack blocked: session_type is READONLY_MOBILE",
            stage="file_protocol.write_back",
        )

    base = framework_path()
    today = datetime.date.today().isoformat()
    files_written = []

    session_log, archive_filename, archive_content = _compact_session_log(session_log, base)

    if calibration_state is not None:
        _safe_write(base / "Calibration_State.md", calibration_state)
        files_written.append("Calibration_State.md")

    _safe_write(base / "Session_Log.md", session_log)
    files_written.append("Session_Log.md")

    _safe_write(base / "Portfolio_State.md", portfolio_state)
    files_written.append("Portfolio_State.md")

    if archive_filename is not None:
        _safe_write(base / archive_filename, archive_content)
        files_written.append(archive_filename)

    if dry_run:
        logger.info(f"[DRY RUN] Would commit: {files_written}")
        return "dry-run"

    commit_msg = f"Session write-back: {today} — §8 scenario state + Portfolio_State"
    if archive_filename is not None:
        commit_msg += f" (+ §7/§8 compaction to {archive_filename})"

    return _git_commit(base, files_written, commit_msg)


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

    Dormant by design (ENG-21, 2026-06-20): requires a service-account or
    OAuth credential file under ~/.advisor/ that is not currently configured
    — this is a possible future feature, not an active path. The expected
    outcome today, if this is ever reached, is a clean EnvironmentError from
    _get_drive_service(), which read_framework_file() wraps into a
    HardStopException naming both the missing-local and Drive failure. See
    tests/test_stage1/test_file_protocol_read_fallback.py.
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
