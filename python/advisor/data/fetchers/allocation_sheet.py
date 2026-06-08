"""
allocation_sheet.py — Google Sheets API reader for the Allocation spreadsheet.
Provides: FRED credit series (HY/IG/CCC/BBB OAS, SOFR, DFF, THREEFYTP10, NATGAS),
          FINRA margin debt, Other Indexes tab (VIX/MOVE/KRE/KBE crosscheck).
Authentication: Google service account JSON (preferred) or OAuth2 token file.
Setup: see python/README.md §Google Sheets Authentication.
"""
from __future__ import annotations

import datetime
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

# ── Credentials helpers ───────────────────────────────────────────────────────

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_sheets_service():
    """Build Google Sheets API service. Tries service account, then OAuth token."""
    from googleapiclient.discovery import build

    creds_path = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        str(Path.home() / ".advisor" / "google_service_account.json"),
    )
    oauth_path = os.environ.get(
        "GOOGLE_OAUTH_TOKEN",
        str(Path.home() / ".advisor" / "google_token.json"),
    )

    creds = None
    if Path(creds_path).exists():
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=_SCOPES
        )
        logger.debug("Google auth: service account")
    elif Path(oauth_path).exists():
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials.from_authorized_user_file(oauth_path, _SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        logger.debug("Google auth: OAuth token")
    else:
        raise EnvironmentError(
            "Google credentials not found. "
            "Set GOOGLE_SERVICE_ACCOUNT_JSON or run: python -m advisor setup google"
        )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _read_sheet_range(spreadsheet_id: str, range_: str) -> List[List[Any]]:
    """Read a named range from Google Sheets. Returns list of rows."""
    service = _get_sheets_service()
    result  = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_)
        .execute()
    )
    return result.get("values", [])


# ── FRED Series tab parser ────────────────────────────────────────────────────

# Maps spec_id → (FRED series code, column-header substring to find it)
_FRED_SERIES: Dict[str, Tuple[str, str]] = {
    "HY_OAS":         ("BAMLH0A0HYM2",  "BAMLH0A0HYM2"),
    "IG_OAS":         ("BAMLC0A0CM",    "BAMLC0A0CM"),
    "CCC_OAS":        ("BAMLH0A3HYC",   "BAMLH0A3HYC"),
    "BBB_OAS":        ("BAMLC0A4CBBB",  "BAMLC0A4CBBB"),
    "SOFR":           ("SOFR",          "SOFR"),
    "DFF":            ("DFF",           "DFF"),
    "THREEFYTP10":    ("THREEFYTP10",   "THREEFYTP10"),
    "NATGAS_HENRY_HUB": ("DHHNGSP",     "DHHNGSP"),
    "NATURAL_GAS":    ("DHHNGSP",       "DHHNGSP"),
}


def _parse_float(val: str) -> Optional[float]:
    """Parse a cell value that might be '282', '0.94', '3.51', etc."""
    try:
        cleaned = val.strip().replace(",", "")
        return float(cleaned) if cleaned else None
    except (ValueError, AttributeError):
        return None


def fetch_fred_series(spec: FetchSpec) -> List[DataReading]:
    """
    Fetch one FRED series from the 'FRED Series' tab of the allocation sheet.
    Returns the most recent non-null value.
    """
    series_code, _ = _FRED_SERIES.get(spec.id, (None, None))
    if not series_code:
        raise ValueError(f"No FRED series mapping for spec.id={spec.id}")

    sheet_id = _get_allocation_sheet_id()
    rows     = _read_sheet_range(sheet_id, "FRED Series")
    if not rows:
        raise RuntimeError("FRED Series tab returned empty")

    # Find the column containing this series code
    header_row = rows[0] if rows else []
    col_idx    = None
    for i, cell in enumerate(header_row):
        if series_code in str(cell):
            col_idx = i
            break

    if col_idx is None:
        return [DataReading(
            spec_id=spec.id, value=None,
            source=DataSource.FRED_SPREADSHEET_TAB,
            fetched_at=datetime.datetime.utcnow(),
            quality_flags=[f"UNAVAILABLE: {series_code} not found in FRED Series tab. "
                           f"Not yet added to spreadsheet."],
        )]

    # Walk rows bottom-up to find the most recent value
    value = None
    date_str = None
    for row in reversed(rows[1:]):
        if col_idx < len(row):
            parsed = _parse_float(str(row[col_idx]))
            if parsed is not None:
                value = parsed
                # date typically in first column
                date_str = row[0] if row else None
                break

    flags = [f"STALE: last value from {date_str}"] if date_str else []
    return [DataReading(
        spec_id=spec.id, value=value,
        source=DataSource.FRED_SPREADSHEET_TAB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=flags,
        raw={"series": series_code, "date": date_str},
    )]


def fetch_finra_margin(spec: FetchSpec) -> List[DataReading]:
    """FINRA_MARGIN_DEBT from 'FINRA Statistics' tab."""
    sheet_id = _get_allocation_sheet_id()
    rows     = _read_sheet_range(sheet_id, "FINRA Statistics")
    if not rows:
        return [DataReading(
            spec_id=spec.id, value=None,
            source=DataSource.ALLOCATION_SPREADSHEET_FINRA,
            fetched_at=datetime.datetime.utcnow(),
            quality_flags=["UNAVAILABLE: FINRA Statistics tab empty"],
        )]
    # Find the most recent margin debit balance (typically last row, col 1 or 2)
    value = None
    for row in reversed(rows[1:]):
        for cell in row:
            parsed = _parse_float(str(cell).replace("$", "").replace("T", ""))
            if parsed is not None and parsed > 0:
                value = parsed
                break
        if value is not None:
            break
    return [DataReading(
        spec_id=spec.id, value=value,
        source=DataSource.ALLOCATION_SPREADSHEET_FINRA,
        fetched_at=datetime.datetime.utcnow(),
    )]


# ── Sheet ID resolution ───────────────────────────────────────────────────────

_CACHED_SHEET_ID: Optional[str] = None


def _get_allocation_sheet_id() -> str:
    """Search Drive root for 'Allocation' spreadsheet and return its ID."""
    global _CACHED_SHEET_ID
    if _CACHED_SHEET_ID:
        return _CACHED_SHEET_ID

    from googleapiclient.discovery import build
    service = _get_drive_service()
    result  = service.files().list(
        q="name = 'Allocation' and mimeType = 'application/vnd.google-apps.spreadsheet'",
        spaces="drive",
        fields="files(id, name)",
        pageSize=5,
    ).execute()
    files = result.get("files", [])
    if not files:
        raise RuntimeError("Cannot find 'Allocation' spreadsheet in Drive root")
    if len(files) > 1:
        raise RuntimeError(f"Found {len(files)} files named 'Allocation' — delete duplicates")
    _CACHED_SHEET_ID = files[0]["id"]
    return _CACHED_SHEET_ID


def _get_drive_service():
    """Build Google Drive API service using same credentials as Sheets."""
    from googleapiclient.discovery import build
    creds_path = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        str(Path.home() / ".advisor" / "google_service_account.json"),
    )
    oauth_path = os.environ.get(
        "GOOGLE_OAUTH_TOKEN",
        str(Path.home() / ".advisor" / "google_token.json"),
    )
    _DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    if Path(creds_path).exists():
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=_DRIVE_SCOPES
        )
    elif Path(oauth_path).exists():
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(oauth_path, _DRIVE_SCOPES)
    else:
        raise EnvironmentError("Google credentials not found")
    return build("drive", "v3", credentials=creds, cache_discovery=False)
