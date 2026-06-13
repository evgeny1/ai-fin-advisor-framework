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

Commands (Stage 5):
  session              Run full SessionPipeline → briefing to stdout
  session --dry-run    Run pipeline without write-back
  validate             Run ValidateClassifications only (fast session-start check)
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env from the python/ directory if present (no dependency required)."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:   # don't override existing env vars
            os.environ[key] = value


_load_dotenv()   # must run before logging / any imports that read env vars

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
    from .data.fetchers import fred_fetcher as fred
    from .data.fetchers import allocation_sheet as sheet
    from .types import DataSource

    registry = FetchRegistry()
    register_all(registry)

    # ── yfinance: single dispatcher handles all YFINANCE specs by spec.id ─────
    registry.register_fetcher(DataSource.YFINANCE, yf.yfinance_dispatcher)

    # ── FRED REST: full yield curve including 2Y (required for 10Y-2Y spread) ──
    # FRED_API_KEY is free from fred.stlouisfed.org. Without the key the fetcher
    # returns a graceful UNAVAILABLE reading and yfinance fills in partial data.
    # FRED_SPREADSHEET_TAB is shared with the allocation-sheet fetcher below;
    # FRED REST is registered first and handles YIELD_CURVE specifically via
    # the dispatcher in yfinance_fetcher for the YFINANCE specs. The FRED fetcher
    # here handles the FRED_SPREADSHEET_TAB source specs not covered by yfinance.
    registry.register_fetcher(DataSource.FRED_SPREADSHEET_TAB, fred.fetch_yield_curve_fred)

    # ── FMP: registered for future use when plan tier is upgraded ─────────────
    # Currently no active FetchSpecs use FMP sources (all moved to yfinance after
    # shadow session June 10 confirmed 403 with standalone key). These become
    # active automatically if specs are moved back to FMP_* sources.
    registry.register_fetcher(DataSource.FMP_COMMODITY,            fmp.fetch_commodity)
    registry.register_fetcher(DataSource.FMP_INDEXES,              fmp.fetch_index)
    registry.register_fetcher(DataSource.FMP_CHART,                fmp.fetch_vix_history_fmp)

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


def cmd_session() -> None:
    """
    Run full SessionPipeline (Stage 5 Pattern A).
    Outputs the M04 briefing to stdout.
    Pass --dry-run to skip write-back.
    """
    import os
    from .orchestrator import SessionPipeline, AIClient, StubAIClient
    from .types import SessionType

    dry_run = "--dry-run" in sys.argv
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    ai = AIClient(api_key=api_key) if api_key else StubAIClient()
    if not api_key:
        print("ℹ ANTHROPIC_API_KEY not set — running with StubAIClient (offline mode)", file=sys.stderr)

    pipeline = SessionPipeline(
        session_type=SessionType.FULL_DESKTOP,
        ai=ai,
        dry_run=dry_run,
    )
    ctx = pipeline.run()

    print("\n" + "=" * 70)
    print("INTELLIGENCE BRIEFING")
    print("=" * 70 + "\n")
    print(ctx.briefing or "[No briefing generated]")

    if ctx.scenario_probs:
        p = ctx.scenario_probs
        print(
            f"\nPROBABILITIES: A={p.A:.0f}% B={p.B:.0f}% C={p.C:.0f}% "
            f"D={p.D:.0f}% E={p.E:.0f}% F={p.F:.0f}%"
        )

    if ctx.write_back_commit:
        print(f"\n✅ Write-back committed: {ctx.write_back_commit}", file=sys.stderr)
    elif dry_run:
        print("\nℹ Dry-run — no write-back.", file=sys.stderr)

    if ctx.all_flags:
        print("\n--- SESSION FLAGS ---", file=sys.stderr)
        for flag in ctx.all_flags:
            print(f"  {flag}", file=sys.stderr)


def cmd_validate() -> None:
    """Run ValidateClassifications against current §11. Fast session-start check."""
    from .data.file_protocol import read_calibration_state
    from .config import parse_calibration_state
    from .analysis import validate_classifications

    cal_text = read_calibration_state()
    cal = parse_calibration_state(cal_text)

    allocation_tickers = [t for t, e in cal.instruments.items() if not e.is_candidate]
    try:
        warnings = validate_classifications(allocation_tickers, cal)
        print(f"✅ ValidateClassifications PASSED — {len(allocation_tickers)} instruments checked")
        if warnings:
            for w in warnings:
                print(f"  ⚠ {w}")
    except Exception as e:
        print(f"HARD_STOP: {e}")
        sys.exit(1)


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
        "session":            cmd_session,
        "validate":           cmd_validate,
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
