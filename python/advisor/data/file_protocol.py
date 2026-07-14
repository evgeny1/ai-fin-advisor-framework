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
import threading
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


def read_instrument_classification() -> str:
    """Fetch Instrument_Classification.md (ENG-51, 2026-07-06 — §11 split
    out of Calibration_State.md into its own file). HARD_STOP if unavailable
    — same failure mode as any other required framework file; there is no
    reason a session should proceed with a stale/missing role registry."""
    return read_framework_file("Instrument_Classification.md")


def read_session_log() -> str:
    """Fetch Session_Log.md. HARD_STOP if unavailable."""
    return read_framework_file("Session_Log.md")


# ── Write-back (FULL_DESKTOP only) ────────────────────────────────────────────


import re
from typing import Dict, List, Tuple

_SEC7_ROW_RE = re.compile(r"^\| \d{4}-\d{2}-\d{2}[^\n]*", re.M)
_SEC7_TABLE_HEADER = (
    "| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
)

# ENG-53 (2026-07-06): calendar-age archival threshold, client-confirmed.
# Replaces the entry-count based rule (ENG-5) entirely -- client's explicit
# stated preference was "rotate by calendar age, not entry count or file
# size", so there is deliberately no count-based fallback limit either.
_ARCHIVE_AGE_DAYS = 90


def _quarter_label(d: datetime.date) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}Q{q}"


def _parse_date_prefix(s: str):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _row_date(row_text: str):
    """§7 row's own date, e.g. '| 2026-05-22 (full) | ...' -> date(2026,5,22)."""
    m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})", row_text)
    return _parse_date_prefix(m.group(1)) if m else None


def _entry_date(block_text: str):
    """§8 entry's own `date:` field (ENG-52 YAML format). Tolerates the
    quote PyYAML adds around date-shaped scalars on dump."""
    m = re.search(r"(?m)^date:\s*['\"]?(\d{4}-\d{2}-\d{2})", block_text)
    return _parse_date_prefix(m.group(1)) if m else None


def _compact_session_log(session_log: str, base: Path) -> Tuple[str, Dict[str, str]]:
    """
    M12 CompactSessionLog (ENG-53, 2026-07-06): calendar-age based archival,
    replacing the entry-count based rule (ENG-5) entirely. Any §7 row or §8
    entry whose own date is more than _ARCHIVE_AGE_DAYS calendar days before
    today moves to the archive file for ITS OWN quarter (not today's
    quarter) — a single write-back whose archived items span more than one
    quarter can touch more than one archive file in one call. There is
    deliberately no count-based fallback limit — client's stated preference
    (2026-07-06) was calendar age only, not entry count or file size; a
    quiet stretch with few sessions just keeps everything live.

    Returns (compacted_log, {archive_filename: archive_content, ...}).
    The dict is empty when nothing needed archiving this call — caller
    should skip writing any archive file in that case.
    """
    sec7_idx = session_log.find("## Section 7")
    sec8_idx = session_log.find("## Section 8")
    if sec7_idx == -1 or sec8_idx == -1:
        return session_log, {}

    sec7 = session_log[sec7_idx:sec8_idx]
    sec8 = session_log[sec8_idx:]

    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=_ARCHIVE_AGE_DAYS)
    today_iso = today.isoformat()

    # ── §7 rows: split, classify by age ──────────────────────────────────
    row_matches = [(m.start(), m.group()) for m in _SEC7_ROW_RE.finditer(sec7)]
    ends7 = [s for s, _ in row_matches[1:]] + [len(sec7)]
    rows = [sec7[s:e].rstrip() for (s, _), e in zip(row_matches, ends7)]

    archived_rows: List[Tuple[str, datetime.date]] = []
    kept_rows: List[str] = []
    for row in rows:
        d = _row_date(row)
        (archived_rows.append((row, d)) if d is not None and d < cutoff
         else kept_rows.append(row))

    # ── §8 entries: lookahead-split on '---' so each chunk keeps its own
    # leading separator (ENG-52 convention — same technique as
    # rendering.mark_prior_entries_superseded()), then classify by age ────
    first_sep = re.search(r"(?m)^---\s*$", sec8)
    if first_sep:
        header_block = sec8[:first_sep.start()]
        region = sec8[first_sep.start():]
        entry_chunks = re.split(r"(?m)^(?=---\s*$)", region)
    else:
        header_block = sec8
        entry_chunks = []

    archived_entries: List[Tuple[str, datetime.date]] = []
    kept_entries: List[str] = []
    for chunk in entry_chunks:
        d = _entry_date(chunk)
        (archived_entries.append((chunk, d)) if d is not None and d < cutoff
         else kept_entries.append(chunk))

    if not archived_rows and not archived_entries:
        return session_log, {}

    # ── Rebuild §7 ──────────────────────────────────────────────────────────
    if archived_rows:
        title_line_end = sec7.find("\n")
        title_line = sec7[:title_line_end]
        quarters7 = sorted({_quarter_label(d) for _, d in archived_rows})
        dest7 = ", ".join(f"Archive_{q}.md" for q in quarters7)
        note7 = (
            f"\n\n// COMPACTED: {today_iso} — {len(archived_rows)} row(s) older than "
            f"{_ARCHIVE_AGE_DAYS} calendar days archived to {dest7} "
            f"(FRAMEWORK_BACKLOG.md ENG-53)"
        )
        new_sec7 = (
            title_line + note7 + "\n\n" + _SEC7_TABLE_HEADER
            + "\n".join(kept_rows) + "\n\n"
        )
    else:
        new_sec7 = sec7

    # ── Rebuild §8 ──────────────────────────────────────────────────────────
    if archived_entries:
        quarters8 = sorted({_quarter_label(d) for _, d in archived_entries})
        dest8 = ", ".join(f"Archive_{q}.md" for q in quarters8)
        note8 = (
            f"\n\n// COMPACTED: {today_iso} — {len(archived_entries)} entry(ies) older "
            f"than {_ARCHIVE_AGE_DAYS} calendar days archived to {dest8} "
            f"(FRAMEWORK_BACKLOG.md ENG-53)"
        )
        new_header_block = header_block.rstrip("\n") + note8 + "\n"
        new_sec8 = new_header_block + "".join(kept_entries)
    else:
        new_sec8 = sec8

    compacted_log = session_log[:sec7_idx] + new_sec7 + new_sec8

    # ── Distribute archived items into their own quarter's archive file ────
    archives: Dict[str, str] = {}

    def _get_archive(quarter: str) -> str:
        if quarter in archives:
            return archives[quarter]
        path = base / f"Archive_{quarter}.md"
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            content = (
                f"# Archive — {quarter[:4]} {quarter[4:]}\n"
                f"<!-- Created: {today_iso} — Session_Log.md compaction per M12 CompactSessionLog -->\n"
                f"<!-- Purpose: append-only archive of displaced §7 rows / §8 entries -->\n\n---\n\n"
            )
        archives[quarter] = content
        return content

    rows_by_quarter: Dict[str, List[str]] = {}
    for row, d in archived_rows:
        rows_by_quarter.setdefault(_quarter_label(d), []).append(row)

    for quarter, quarter_rows in rows_by_quarter.items():
        content = _get_archive(quarter)
        marker = "## Archived §7 Credit Readings"
        idx = content.find(marker)
        insertion_text = "\n".join(quarter_rows) + "\n"
        if idx == -1:
            content = (
                content.rstrip() + "\n\n" + marker
                + f" (displaced by {_ARCHIVE_AGE_DAYS}-day retention)\n\n"
                + _SEC7_TABLE_HEADER + insertion_text
            )
        else:
            next_heading = content.find("\n## ", idx + len(marker))
            insert_at = next_heading if next_heading != -1 else len(content)
            content = (
                content[:insert_at].rstrip() + "\n" + insertion_text
                + content[insert_at:]
            )
        archives[quarter] = content

    entries_by_quarter: Dict[str, List[str]] = {}
    for chunk, d in archived_entries:
        entries_by_quarter.setdefault(_quarter_label(d), []).append(chunk)

    for quarter, quarter_entries in entries_by_quarter.items():
        content = _get_archive(quarter)
        marker8 = "## Archived §8 Session States"
        idx8 = content.find(marker8)
        insertion_text8 = "".join(quarter_entries)
        if idx8 == -1:
            content = (
                content.rstrip() + "\n\n" + marker8
                + f" (displaced by {_ARCHIVE_AGE_DAYS}-day retention)\n"
                + insertion_text8
            )
        else:
            next_heading8 = content.find("\n## ", idx8 + len(marker8))
            insert_at8 = next_heading8 if next_heading8 != -1 else len(content)
            content = (
                content[:insert_at8].rstrip() + "\n" + insertion_text8
                + content[insert_at8:]
            )
        archives[quarter] = content

    archive_files = {f"Archive_{q}.md": content for q, content in archives.items()}
    return compacted_log, archive_files




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

    §7/§8 compaction (ENG-53, 2026-07-06): calendar-age based (90 days),
    enforced on every call — see _compact_session_log(). A single call can
    touch more than one Archive_[Year]Q[N].md file if archived items span
    a quarter boundary.
    """
    if session_type != SessionType.FULL_DESKTOP:
        raise WriteBackGuardViolation(
            "WriteBack blocked: session_type is READONLY_MOBILE",
            stage="file_protocol.write_back",
        )

    base = framework_path()
    today = datetime.date.today().isoformat()
    files_written = []

    session_log, archive_files = _compact_session_log(session_log, base)

    if calibration_state is not None:
        _safe_write(base / "Calibration_State.md", calibration_state)
        files_written.append("Calibration_State.md")

    _safe_write(base / "Session_Log.md", session_log)
    files_written.append("Session_Log.md")

    _safe_write(base / "Portfolio_State.md", portfolio_state)
    files_written.append("Portfolio_State.md")

    for archive_filename, archive_content in archive_files.items():
        _safe_write(base / archive_filename, archive_content)
        files_written.append(archive_filename)

    if dry_run:
        logger.info(f"[DRY RUN] Would commit: {files_written}")
        return "dry-run"

    commit_msg = f"Session write-back: {today} — §8 scenario state + Portfolio_State"
    if archive_files:
        commit_msg += f" (+ §7/§8 compaction to {', '.join(sorted(archive_files))})"

    return _git_commit(base, files_written, commit_msg)


def _safe_write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    logger.debug(f"Written: {path.name}")


def _git_commit(repo: Path, files: list[str], message: str) -> str:
    """
    Found 2026-06-20 (ENG-33): the original version of this function
    called `git push` with no timeout and no guard against an
    interactive credential prompt. If the MCP server process does not
    have the same cached git credentials an interactive shell session
    has, `git push` can block indefinitely waiting for input that will
    never arrive (no TTY) -- this manifested as advisor_write_back
    hanging at the MCP client's ~4-minute timeout ceiling, even though
    the operation eventually completed and committed successfully once
    it cleared (proving it was a slow/stuck push, not a crash).

    Fix: GIT_TERMINAL_PROMPT=0 makes git fail fast instead of prompting
    when run non-interactively; an explicit timeout on the push step
    bounds the worst case; and a failed/timed-out push is treated as
    non-fatal -- the local commit (the part that matters for
    Session_Log.md/Portfolio_State.md integrity) has already succeeded
    by that point, so this still returns the commit sha rather than
    losing that information by raising.
    """
    git_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

    def git(*args: str, timeout: float = 60.0) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            capture_output=True, text=True, check=True,
            env=git_env, timeout=timeout,
        )
        return result.stdout.strip()

    git("add", *files)
    git("commit", "-m", message)
    sha = git("rev-parse", "--short", "HEAD")

    def _push_in_background() -> None:
        try:
            git("push", "origin", "master", timeout=30.0)
            logger.info(f"Write-back pushed: {sha} — {message}")
        except subprocess.TimeoutExpired:
            logger.warning(
                f"Write-back committed locally ({sha}) but `git push` did not "
                f"complete within 30s -- likely no non-interactive git "
                f"credentials available to this process. The commit is safe; "
                f"push manually: git -C {repo} push origin master"
            )
        except subprocess.CalledProcessError as e:
            logger.warning(
                f"Write-back committed locally ({sha}) but `git push` failed: "
                f"{e.stderr.strip()}"
            )

    # ENG-48 fix: push used to run synchronously here, taking up to 30s
    # inside the 90s _with_timeout() budget it shares with render/compact/
    # file-write/commit above -- both confirmed ENG-48 TIMEOUTs landed at
    # ~90.02s, right at the edge, strongly suggesting push's own up-to-30s
    # allowance was eating most of the margin. Push failures have been
    # non-fatal since ENG-38 (the local commit is what matters for session
    # continuity) -- backgrounding it changes no write guarantee, it only
    # removes its duration from the synchronous critical path the caller's
    # own timeout is racing against.
    threading.Thread(
        target=_push_in_background, name="advisor_git_push", daemon=True
    ).start()

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
