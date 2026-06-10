"""
advisor/__main__.py — CLI entry point for the Python advisor framework.
Usage: python -m advisor <command> [options]

Commands (Stage 1):
  fetch market-data    Run FetchRegistry.fetch_all() → JSON to stdout
  fetch allocation     Read allocation sheet (summary) → JSON
  fetch calibration    Read Calibration_State.md → raw text
  fetch session-log    Read Session_Log.md → raw text
  status               Show FetchRegistry summary (registered specs + fetchers)
  setup google         Interactive Google credentials setup wizard
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=os.environ.get("ADVISOR_LOG_LEVEL", "WARNING"),
    format="%(levelname)s %(name)s: %(message)s",
)


def _build_registry():
    """Bootstrap a FetchRegistry with all M18 specs and registered fetchers."""
    from .data.fetch_registry import FetchRegistry
    from .data.m18_registry import register_all
    from .data.fetchers import yfinance_fetcher as yf
    from .data.fetchers import fmp_fetcher as fmp
    from .data.fetchers import allocation_sheet as sheet
    from .types import DataSource

    registry = FetchRegistry()
    register_all(registry)

    # ── yfinance: single dispatcher handles all YFINANCE specs by spec.id ─────
    # One registration — no loop, no overwrite bug.
    registry.register_fetcher(DataSource.YFINANCE, yf.yfinance_dispatcher)

    # ── FMP: only kept for future use when plan tier is upgraded ──────────────
    # All FMP-sourced specs moved to YFINANCE after shadow session (June 10)
    # confirmed FMP REST returns 403 for commodity/indexes/chart endpoints
    # with a standalone API key (FMP MCP uses a higher-tier account).
    # These registrations are harmless (no active specs use these sources now)
    # and will become active when FMP plan is upgraded.
    registry.register_fetcher(DataSource.FMP_COMMODITY,             fmp.fetch_commodity)
    registry.register_fetcher(DataSource.FMP_INDEXES,               fmp.fetch_index)
    registry.register_fetcher(DataSource.FMP_CHART,                 fmp.fetch_vix_history_fmp)

    # ── Allocation sheet fetchers (Stage 5 / Pattern A only) ──────────
    # In Pattern B Claude's Google Drive MCP connector handles the FRED
    # tab and FINRA tab. Register these only when credentials exist.
    from pathlib import Path as _Path
    _cred_paths = (
        _Path.home() / ".advisor" / "google_service_account.json",
        _Path.home() / ".advisor" / "google_token.json",
    )
    if any(p.exists() for p in _cred_paths) or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"):
        registry.register_fetcher(DataSource.FRED_SPREADSHEET_TAB,        sheet.fetch_fred_series)
        registry.register_fetcher(DataSource.ALLOCATION_SPREADSHEET_FINRA, sheet.fetch_finra_margin)

    return registry


def cmd_fetch_market_data() -> None:
    """Run FetchRegistry.fetch_all() and print results as JSON."""
    registry = _build_registry()
    readings = registry.fetch_all()
    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "count": len(readings),
        "readings": [r.to_dict() for r in readings],
        "valid": sum(1 for r in readings if r.is_valid),
        "flagged": sum(1 for r in readings if not r.is_valid),
    }
    print(json.dumps(output, indent=2, default=str))


def cmd_status() -> None:
    """Print FetchRegistry summary to stderr (human-readable)."""
    registry = _build_registry()
    print(registry.summary(), file=sys.stderr)


def cmd_fetch_calibration() -> None:
    from .data.file_protocol import read_calibration_state
    print(read_calibration_state())


def cmd_fetch_session_log() -> None:
    from .data.file_protocol import read_session_log
    print(read_session_log())


def cmd_setup_google() -> None:
    """Interactive Google OAuth2 setup wizard."""
    from pathlib import Path
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_json = input("Path to OAuth2 client_secrets.json (from Google Cloud Console): ").strip()
    if not Path(creds_json).exists():
        print(f"File not found: {creds_json}")
        sys.exit(1)
    flow  = InstalledAppFlow.from_client_secrets_file(creds_json, SCOPES)
    creds = flow.run_local_server(port=0)
    out   = Path.home() / ".advisor" / "google_token.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(creds.to_json())
    print(f"Token saved to {out}")
    print("Set GOOGLE_OAUTH_TOKEN={out} in your .env if needed.")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = " ".join(args[:2]) if len(args) >= 2 else args[0]

    dispatch = {
        "fetch market-data": cmd_fetch_market_data,
        "fetch calibration":  cmd_fetch_calibration,
        "fetch session-log":  cmd_fetch_session_log,
        "status":             cmd_status,
        "setup google":       cmd_setup_google,
    }

    fn = dispatch.get(cmd) or dispatch.get(args[0])
    if fn is None:
        print(f"Unknown command: {cmd}\n{__doc__}")
        sys.exit(1)

    try:
        fn()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
