"""
advisor/mcp_server.py — MCP server for Claude Desktop integration.

Exposes the advisor framework as MCP tools so Claude in the Claude app
can run the full M05 session pipeline without separate API calls.
Zero additional cost vs CLI mode (no ANTHROPIC_API_KEY needed here —
Claude in the conversation IS the AI).

Five tools:
  advisor_run_computation(floor_account_weights_json?)
                                M05 Steps 1–4+3b: load config, fetch
                                market data, compute all signals,
                                CurrentHoldingsFloorCheck, RoleRepricingDivergence,
                                PassiveMandateAbsentWarning, scoring questions.
                                Pass floor account weights (from allocation sheet)
                                to enable floor monitoring.
  advisor_apply_scoring()       M05 Step 5: scoring answers →
                                ScenarioProbabilities (Python math).
                                Auto-runs FloorCheck Step 6b if probs shift >= 5pp.
  advisor_evaluate_allocation() M13/M15/M08: scenarioWeightedAllocation(),
                                FeasibilityCheck(), classifyInstrument(),
                                dominantDirective(), DualRoleConflict() — for
                                one account. Requires advisor_run_computation
                                and advisor_apply_scoring to have run this
                                session (added 2026-06-17 closing ENG-16 — this
                                math previously had no MCP tool and was
                                re-derived by hand from the M13/M15 .md spec
                                every session).
  advisor_check_instrument_candidate()
                                M07.AutoDisqualify() for a candidate
                                instrument not yet in §11. Pure on supplied
                                metrics — no session precondition.
  advisor_write_back()          M05 Step 10: §8 entry + Portfolio_State
                                → git commit.

Usage:
  python -m advisor mcp-server        # start stdio MCP server

Claude Desktop config (~/.config/Claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "financial-advisor": {
        "command": "/usr/bin/python3",
        "args": ["-m", "advisor", "mcp-server"],
        "cwd": "/Users/evgeny/.../python"
      }
    }
  }
"""
from __future__ import annotations

import concurrent.futures
import dataclasses
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


# ENG-33 history: advisor_evaluate_allocation's account_profile parameter
# was originally Dict[str, Any], then briefly an AccountProfileInput
# Pydantic model (2026-06-22 attempt, removed 2026-06-24) to see if a
# precisely-typed nested object would clear a transport-layer hang where
# the request never reached this server's stdio log at all. It didn't --
# the model still generates a $ref/$defs nested JSON schema, same shape
# family as the dict it replaced. advisor_evaluate_allocation now takes
# account_id/planning_horizon_years/objective_type/etc. as flat top-level
# parameters instead (see its @srv.tool() definition below) -- the same
# flat-scalar shape advisor_write_back and advisor_check_instrument_candidate
# already use without issue. See that tool's docstring for the full
# diagnostic trail.


# ENG-33: advisor_evaluate_allocation and advisor_write_back both hung at
# the MCP client's ~4-minute call ceiling this session with no diagnostic
# output. Both proved sub-second when run in-process bypassing the MCP
# transport, so the hang is not in this module's own logic -- but its
# exact cause (transport/serialization layer, per investigation notes in
# FRAMEWORK_BACKLOG.md ENG-33) could not be confirmed without server-side
# stderr access. _with_timeout() is a defensive second line of fix: it
# bounds how long any wrapped tool call can make the MCP client wait,
# converting a silent multi-minute hang into a fast, clear, diagnostic
# error. The timeouts below are well above every observed real runtime
# for these tools (sub-second) -- if one ever actually fires, that is
# itself useful information (something is genuinely stuck), not a false
# positive on legitimately slow data.
_TOOL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="advisor_mcp_tool"
)


def _with_timeout(fn, timeout_s: float, *args, **kwargs) -> str:
    """
    Run fn(*args, **kwargs) in a worker thread with a hard wall-clock
    timeout. Returns fn's normal result if it completes in time;
    otherwise returns a clear TIMEOUT error string instead of letting
    the caller (and the MCP client) hang indefinitely.

    Caveat: a Python thread that is truly stuck (blocked on I/O or a
    lock) cannot be force-killed from here. This bounds how long the
    MCP response takes, not whether the background thread eventually
    finishes. For write_back specifically, the real fix is the git-push
    hardening in file_protocol.py's _git_commit() -- this is a second,
    independent line of defense, not a substitute for it.
    """
    future = _TOOL_EXECUTOR.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError:
        return _err(
            f"{fn.__name__} exceeded its {timeout_s:.0f}s safety timeout "
            f"without returning. This function is proven sub-second under "
            f"normal data (FRAMEWORK_BACKLOG.md ENG-33) -- this timeout "
            f"firing is itself the diagnostic signal that something is "
            f"genuinely stuck, not just slow under heavy load. The call "
            f"may still be running in the background; if it has side "
            f"effects (write_back), check `git log` for a new commit "
            f"before retrying rather than assuming it failed.",
            status="TIMEOUT",
        )


logger = logging.getLogger(__name__)


def _fetch_holdings_30d_raw(alloc_tickers: List[str]) -> Dict[str, Optional[float]]:
    """
    Direct yfinance batch download for RoleRepricingDivergence's 30d
    returns. This bypasses FetchRegistry/yfinance_fetcher.py's
    _yf_lock_guard on purpose -- it runs once, synchronously, after
    fetch_all() has already finished, so there's no concurrent lock
    contention here to guard against. The risk is the same underlying one
    ENG-40 fixed elsewhere though: yfinance/Yahoo Finance can retry without
    an overall bound. Found 2026-06-24: this call site was the second,
    separate place that bug lived -- fetch_registry.py and
    yfinance_fetcher.py's per-fetch timeouts don't cover it because it
    never goes through either of them. Caller wraps this in a hard
    wall-clock bound (see Step 4b below); this function itself stays
    unbounded so the bound lives in one place (_TOOL_EXECUTOR), not two.
    """
    import datetime as _dt
    import yfinance as _yf_local

    holdings_30d: Dict[str, Optional[float]] = {}
    end_dt   = _dt.date.today()
    start_dt = end_dt - _dt.timedelta(days=50)  # 50 cal days ≈ 35 trading days
    hist = _yf_local.download(
        alloc_tickers, start=start_dt.isoformat(),
        end=end_dt.isoformat(), progress=False, auto_adjust=True,
    )
    if not hist.empty:
        closes = hist["Close"] if "Close" in hist.columns else hist
        for ticker in alloc_tickers:
            col = closes.get(ticker) if hasattr(closes, "get") else (
                closes[ticker] if ticker in closes.columns else None
            )
            if col is not None:
                series = col.dropna()
                if len(series) >= 2:
                    holdings_30d[ticker] = float(
                        series.iloc[-1] / series.iloc[0] - 1
                    )
    return holdings_30d


# ── .env load (FMP_API_KEY, etc.) ─────────────────────────────────────────────

def _load_dotenv() -> None:
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
        if key and key not in os.environ:
            os.environ[key] = value

_load_dotenv()

# ── Session cache (per-process, one session) ───────────────────────────────────

_cache: Dict[str, Any] = {}


# ── JSON helpers ──────────────────────────────────────────────────────────────

def _json_default(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, 'value'):        # Enum
        return obj.value
    raise TypeError(f"Not serializable: {type(obj)}")


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=_json_default, indent=2)


def _err(msg: str, status: str = "ERROR") -> str:
    return _dumps({"status": status, "error": msg})


def _parse_floor_accounts(value: Any) -> List[Dict[str, Any]]:
    """
    Coerce floor_account_weights_json into a list of
    {"account_id": str, "weights": {ticker: float}} dicts.

    Defensive against the calling layer sending either a native list
    (the param is typed Optional[Any] below precisely so a list is
    accepted without a pydantic string-type rejection) or a JSON
    string -- including a DOUBLE-encoded JSON string. Some MCP bridges
    re-stringify a string-typed param that already looks like JSON, so
    the value this function receives can itself be the JSON encoding
    of a JSON string. One json.loads() then yields a str, not a list,
    and the caller silently cached that str as floor_accounts -- which
    is what produced "string indices must be integers, not 'str'" when
    check_all_floor_accounts() iterated it character by character.

    Loops json.loads() while the result is still a str, capped at 3
    attempts so a malformed value fails fast with a clear error rather
    than looping forever or silently miscaching.

    Found: 2026-06-20 session, Step 3b / Step 6b both failing.
    """
    if value is None or value == "":
        return []

    parsed: Any = value
    attempts = 0
    while isinstance(parsed, str) and attempts < 3:
        parsed = json.loads(parsed)
        attempts += 1

    if not isinstance(parsed, list):
        raise ValueError(
            "floor_account_weights_json must decode to a list of "
            f"{{account_id, weights}} dicts; got {type(parsed).__name__}"
        )
    for i, entry in enumerate(parsed):
        if not isinstance(entry, dict) or "account_id" not in entry or "weights" not in entry:
            raise ValueError(
                f"floor_account_weights_json[{i}] must be a dict with "
                f"'account_id' and 'weights' keys; got {entry!r}"
            )
    return parsed


def _parse_account_profile(data: Dict[str, Any]) -> Any:
    """
    Build an AccountProfile from the dict Claude constructs after reading
    the allocation sheet's "Objectives" tab. No parser exists for that tab
    in Python (M13's account profiles have always been Claude-read,
    Claude-constructed) — this only validates/converts the dict into the
    typed dataclass M13/M15 functions require.
    """
    from .types import AccountProfile, ObjectiveType

    raw_obj_type = data.get("objective_type")
    try:
        obj_type = ObjectiveType(raw_obj_type)
    except (KeyError, ValueError) as e:
        valid = [o.value for o in ObjectiveType]
        raise ValueError(
            f"objective_type must be one of {valid}, got {raw_obj_type!r}"
        ) from e

    if "account_id" not in data:
        raise ValueError("account_profile missing required field 'account_id'")
    if "planning_horizon_years" not in data:
        raise ValueError("account_profile missing required field 'planning_horizon_years'")

    return AccountProfile(
        account_id=data["account_id"],
        owner=data.get("owner", "primary"),
        planning_horizon_years=int(data["planning_horizon_years"]),
        objective_type=obj_type,
        floor_nominal_loss=bool(data.get("floor_nominal_loss", False)),
        concentration_cap=float(data.get("concentration_cap", 0.40)),
        drawdown_tolerance=float(data.get("drawdown_tolerance", 0.30)),
    )


# ── Tool 1: advisor_run_computation() ─────────────────────────────────────────

def _tool_run_computation(floor_account_weights_json: Optional[Any] = None) -> str:
    """
    M05 Steps 1+2+4+3b: load config, fetch market data, compute signals,
    build M03 scoring questions, run CurrentHoldingsFloorCheck (Step 3b).

    floor_account_weights_json: optional JSON string — list of dicts, each:
      {"account_id": str, "weights": {ticker: float, ...}}
    Only FLOOR_THEN_RETURN accounts. Derive from allocation sheet current
    values / account total BEFORE calling this tool:
      e.g. [{"account_id": "Relative_IRA_469",
              "weights": {"MLPX": 0.24, "SGOV": 0.21, ...}}]
    If omitted: CurrentHoldingsFloorCheck and PassiveMandateAbsentWarning
    are skipped with advisory flags in output.

    The qualitative research (M02 QUALITATIVE_GATHER_LIST) is NOT done
    here — Claude does it after this call using web_search.  The
    qualitative_targets list tells Claude which topics to research.
    """
    from .config import parse_calibration_state, parse_session_log
    from .data.fetch_registry import FetchRegistry
    from .data.file_protocol import (
        read_calibration_state,
        read_instrument_classification,
        read_session_log,
    )
    from .data.m18_registry import register_all
    from .data.fetchers import yfinance_fetcher as yf
    from .analysis import (
        assess_cascade_level,
        compute_credit_signal,
        compute_divergence_signal,
        validate_classifications,
        role_repricing_divergence,
        check_all_floor_accounts,
        passive_mandate_absent_warnings,
    )
    from .orchestrator.scoring_questions import (
        QUALITATIVE_TARGETS,
        generate_questions,
        generate_m19_judgment_questions,
    )
    from .types import DataSource

    result: Dict[str, Any] = {
        "status": "OK",
        "session_date": datetime.date.today().isoformat(),
        "flags": [],
    }

    # ── Step 1: Load config ────────────────────────────────────────────────
    cal_text = read_calibration_state()
    instrument_text = read_instrument_classification()
    log_text = read_session_log()
    cal = parse_calibration_state(cal_text, instrument_text)
    log = parse_session_log(log_text)

    _cache.update({"cal": cal, "log": log,
                   "cal_text": cal_text, "instrument_text": instrument_text,
                   "log_text": log_text})

    result["calibration_version"] = cal.version
    result["calibration_last_updated"] = cal.last_updated

    prior = log.latest_probs
    if prior:
        result["prior_probs"] = {
            "A": prior.A, "B": prior.B, "C": prior.C,
            "D": prior.D, "E": prior.E, "F": prior.F,
        }

    # Validate classifications — HARD_STOP surface
    alloc_tickers = [t for t, e in cal.instruments.items()
                     if not e.is_candidate]

    # Write instruments.json (ENG-25) — local-only, never committed to git.
    # Source is THIS session's §11.3 parse, never memory. A failure here is
    # non-fatal: yfinance_fetcher.load_instruments() falls back to its
    # hardcoded list, so this is flagged, not a HARD_STOP.
    try:
        yf.write_instruments_json(alloc_tickers)
    except Exception as e:
        result["flags"].append(f"⚠ instruments.json write failed: {e}")

    # ENG-43: opportunistically merge today's FRED credit-history window into
    # CreditHistoryStore.json (self-healing local history, client-chosen path
    # (c)). Gated to once/day inside the function itself; never fatal.
    try:
        from .data.credit_history_store import update_credit_history_store
        hist_summary = update_credit_history_store()
        if hist_summary.get("error"):
            result["flags"].append(
                f"⚠ CreditHistoryStore update failed (non-fatal): {hist_summary['error']}"
            )
        elif hist_summary.get("updated") and any(hist_summary.get("added", {}).values()):
            added_str = ", ".join(f"{k}:+{v}" for k, v in hist_summary["added"].items() if v)
            result["flags"].append(f"CreditHistoryStore updated ({added_str})")
    except Exception as e:
        result["flags"].append(f"⚠ CreditHistoryStore update failed (non-fatal): {e}")

    try:
        warns = validate_classifications(alloc_tickers, cal)
        if warns:
            result["flags"].extend(warns)
            result["validate_warnings"] = warns
        else:
            result["validate_status"] = "PASS"
    except Exception as e:
        result["flags"].append(f"HARD_STOP: {e}")
        result["status"] = "HARD_STOP"
        return _dumps(result)

    # Open items from Session_Log §8
    if log.scenario_states:
        latest = log.scenario_states[-1]
        result["prior_session_driver"] = getattr(latest, "primary_driver", "")
        result["open_triggers"]  = getattr(latest, "open_triggers",  [])
        result["open_decisions"] = getattr(latest, "open_decisions", [])
        result["next_session_flags"] = getattr(latest, "next_session_flags", [])


    # ── Step 2: Fetch market data ──────────────────────────────────────────
    registry = FetchRegistry()
    register_all(registry)
    registry.register_fetcher(DataSource.YFINANCE, yf.yfinance_dispatcher)

    try:
        from .data.fetchers import fred_fetcher as fred
        registry.register_fetcher(DataSource.FRED_SPREADSHEET_TAB,
                                   fred.fetch_yield_curve_fred)
    except Exception as e:
        result["flags"].append(f"⚠ FRED fetcher unavailable: {e}")

    readings = registry.fetch_all()
    _cache["readings"] = readings
    readings_by_id = {r.spec_id: r for r in readings}

    valid = sum(1 for r in readings if r.is_valid)
    result["market_data_summary"] = f"{valid}/{len(readings)} specs valid"

    # Compact market snapshot (skip internal/history series)
    _SKIP = {"DOW", "KBE", "NASDAQ_COMP", "RUSSELL2000", "WTI",
             "HISTORICAL_INSTRUMENT_PRICES"}
    mkt: Dict[str, Any] = {}
    for r in readings:
        if not r.is_valid or r.spec_id in _SKIP:
            continue
        if r.spec_id.startswith("HOLDINGS_PRICES:"):
            ticker = r.spec_id.split(":", 1)[1]
            mkt[f"PRICE:{ticker}"] = r.value
        else:
            mkt[r.spec_id] = r.value
    result["market_data"] = mkt

    # ── Step 4: Compute signals ────────────────────────────────────────────
    sigs: Dict[str, Any] = {}
    credit_signal = None

    try:
        cs = compute_credit_signal(readings_by_id, cal)
        credit_signal = cs
        _cache["credit_signal"] = cs
        sigs["credit"] = {
            "hy_oas": cs.hy_oas, "ig_oas": cs.ig_oas, "ccc_oas": cs.ccc_oas,
            "hy_stress_beginning":   cs.hy_stress_beginning,
            "hy_recession_pricing":  cs.hy_recession_pricing,
            "ig_transmission_reached": cs.ig_transmission_reached,
            "convergence_text": cs.convergence_text,
        }
    except Exception as e:
        result["flags"].append(f"⚠ CreditSignal failed: {e}")
        _cache["credit_signal"] = None

    try:
        ds = compute_divergence_signal(readings_by_id, cal)
        sigs["regime"] = {
            "commodity_fear":   ds.commodity_fear_divergence.value,
            "equity_scenario":  ds.equity_scenario_divergence.value,
            "composite":        ds.composite.value,
        }
    except Exception as e:
        result["flags"].append(f"⚠ DivergenceSignal failed: {e}")

    try:
        cc = assess_cascade_level(readings_by_id, cal, credit_signal)
        yc = cc.yield_curve
        _cache["cascade_signal"] = cc
        sigs["cascade"] = {
            "level": cc.level.value,
            "sector_stress_score": cc.sector_stress_score,
            "chain_fires": {k: v for k, v in cc.chain_fires.items() if v},
            "chain_watch": {k: v for k, v in cc.chain_watch.items() if v},
        }
        sigs["yield_curve"] = {
            "spread_10y_2y":   yc.spread_10y_2y,
            "spread_10y_3m":   yc.spread_10y_3m,
            "d_timing_signal": yc.d_timing_signal.value,
            "e_watch_flag":    yc.e_watch_flag.value,
            "e_pathway_type":  yc.e_pathway_type.value,
            "term_premium":    yc.term_premium,
            "yield_30y":       yc.yield_30y,
        }
    except Exception as e:
        result["flags"].append(f"⚠ CascadeSignal failed: {e}")

    result["signals"] = sigs

    # ── Step 4b: holdings 30d returns (for RoleRepricingDivergence) ───────
    holdings_30d: Dict[str, Optional[float]] = {}
    alloc_tickers = [t for t, e in cal.instruments.items() if not e.is_candidate]
    try:
        future = _TOOL_EXECUTOR.submit(_fetch_holdings_30d_raw, alloc_tickers)
        holdings_30d = future.result(timeout=20.0)
        _cache["holdings_30d"] = holdings_30d
        result["holdings_30d_returns"] = {
            t: round(v * 100, 2) for t, v in holdings_30d.items() if v is not None
        }
    except concurrent.futures.TimeoutError:
        result["flags"].append(
            "⚠ Holdings30dReturns fetch exceeded 20s safety timeout — "
            "abandoning (ENG-40 follow-up: this batch yfinance call bypassed "
            "both of ENG-40's other guards). RoleRepricingDivergence skipped "
            "this session; the worker thread may still be running in the "
            "background but advisor_run_computation does not wait on it."
        )
    except Exception as e:
        result["flags"].append(f"⚠ Holdings30dReturns fetch failed: {e}")

    # ── Update 1: RoleRepricingDivergence ─────────────────────────────────
    try:
        ds_obj = compute_divergence_signal(readings_by_id, cal)
        broad_30d = ds_obj.broad_equity_30d
        if broad_30d is not None and holdings_30d:
            repricing_warnings = role_repricing_divergence(
                holdings_30d_returns=holdings_30d,
                broad_market_30d=broad_30d,
                cal=cal,
            )
            _cache["repricing_warnings"] = repricing_warnings
            if repricing_warnings:
                result["role_repricing_warnings"] = [
                    {
                        "ticker":              w.ticker,
                        "primary_role_id":     w.primary_role_id,
                        "instrument_30d_pct":  round(w.instrument_30d * 100, 2),
                        "broad_market_30d_pct":round(w.broad_market_30d * 100, 2),
                        "underperformance_pp": round(w.underperformance_pp, 2),
                        "threshold_pp":        w.threshold_pp,
                    }
                    for w in repricing_warnings
                ]
                result["flags"].append(
                    f"⚠ RoleRepricingDivergence: {len(repricing_warnings)} instrument(s) "
                    "underperforming role thesis vs broad market (§9.5). See role_repricing_warnings."
                )
            else:
                result["role_repricing_warnings"] = []
        else:
            result["flags"].append(
                "⚠ RoleRepricingDivergence skipped — broad_market_30d unavailable "
                "or no holdings 30d data fetched."
            )
    except Exception as e:
        result["flags"].append(f"⚠ RoleRepricingDivergence failed: {e}")

    # ── Update 2: CurrentHoldingsFloorCheck (M05 Step 3b) ─────────────────
    floor_accounts: List[Dict] = []
    if floor_account_weights_json:
        try:
            floor_accounts = _parse_floor_accounts(floor_account_weights_json)
            _cache["floor_accounts"] = floor_accounts
        except Exception as e:
            result["flags"].append(f"⚠ floor_account_weights_json parse error: {e}")

    if floor_accounts:
        prior = log.latest_probs
        if prior is not None:
            try:
                floor_alerts = check_all_floor_accounts(
                    floor_accounts=floor_accounts,
                    probabilities=prior,
                    cal=cal,
                    check_step="3b",
                )
                _cache["floor_alerts_3b"] = floor_alerts
                if floor_alerts:
                    result["floor_breach_alerts"] = [
                        {
                            "step":            a.check_step,
                            "account_id":      a.account_id,
                            "worst_scenario":  a.worst_scenario,
                            "worst_return_pct":round(a.worst_return_pct, 2),
                            "priority":        a.priority,
                        }
                        for a in floor_alerts
                    ]
                    result["status"] = "FLOOR_BREACH"
                    result["flags"].append(
                        f"⚠⚠ FLOOR_BREACH_ALERT [3b]: {len(floor_alerts)} account(s). "
                        "RecalibrationSequence required before allocation recommendations."
                    )
                else:
                    result["floor_breach_alerts"] = []
            except Exception as e:
                result["flags"].append(f"⚠ CurrentHoldingsFloorCheck [3b] failed: {e}")
        else:
            result["flags"].append(
                "⚠ CurrentHoldingsFloorCheck [3b] skipped — no prior probs in §8."
            )
    else:
        result["flags"].append(
            "ℹ CurrentHoldingsFloorCheck skipped — floor_account_weights_json not provided. "
            "Pass current market weights for FLOOR_THEN_RETURN accounts to enable floor monitoring."
        )
        result["floor_breach_alerts"] = []

    # ── Update 3: PassiveMandateAbsentWarning ─────────────────────────────
    if floor_accounts and log.latest_probs is not None:
        try:
            passive_warns = passive_mandate_absent_warnings(
                floor_accounts=floor_accounts,
                cal=cal,
                probs=log.latest_probs,
                holdings_30d_returns=holdings_30d or None,
            )
            _cache["passive_warns"] = passive_warns
            if passive_warns:
                result["passive_mandate_warnings"] = [
                    {
                        "account_id":       w.account_id,
                        "ticker":           w.ticker,
                        "weight_pct":       round(w.current_weight * 100, 1),
                        "instrument_30d_pct": (
                            round(w.instrument_30d * 100, 2)
                            if w.instrument_30d is not None else None
                        ),
                        "floor_proximity_pp": (
                            round(w.floor_proximity_pp, 2)
                            if w.floor_proximity_pp is not None else None
                        ),
                    }
                    for w in passive_warns
                ]
                result["flags"].append(
                    f"⚠ PassiveMandateAbsent: {len(passive_warns)} holding(s) with no "
                    "passive mandate floor actively repricing in FLOOR_THEN_RETURN account(s). "
                    "See passive_mandate_warnings."
                )
            else:
                result["passive_mandate_warnings"] = []
        except Exception as e:
            result["flags"].append(f"⚠ PassiveMandateAbsentWarning failed: {e}")

    # ── Scoring questions (qualitative dict empty — Claude fills via search) ─
    qs = generate_questions(readings, cal, credit_signal, {})
    qs = qs + generate_m19_judgment_questions(cal)
    _cache["scoring_questions"] = qs

    ai_qs    = [q for q in qs if q.auto_score is None]
    auto_qs  = [q for q in qs if q.auto_score is not None]
    result["scoring_questions"] = [
        {
            "id":          q.id,
            "scenario":    q.scenario,
            "question":    q.question,
            "evidence":    q.evidence,
            "valid_scores": q.valid_scores,
            "auto_score":  q.auto_score,   # None = Claude must answer
            "consumer":    q.consumer,     # "M03" or "M19" — informational only
        }
        for q in qs
    ]
    result["scoring_summary"] = {
        "total": len(qs), "auto_scored": len(auto_qs), "needs_claude": len(ai_qs),
    }
    result["qualitative_targets"] = QUALITATIVE_TARGETS

    return _dumps(result)


# ── Tool 2: advisor_apply_scoring() ───────────────────────────────────────────

def _tool_apply_scoring(answers: Dict[str, int]) -> str:
    """
    M05 Step 5: merge Claude's answers with Python auto-scores,
    run apply_all_rules() → ScenarioProbabilities (25pp cap applied).
    """
    from .analysis.scenario_math import apply_all_rules
    from .orchestrator.scoring_questions import aggregate_raw_scores
    from .types import ScoringAnswers

    if "scoring_questions" not in _cache:
        return _err("No scoring questions cached. Call advisor_run_computation first.")

    sa = ScoringAnswers(answers=answers, reasoning={})
    raw_scores = aggregate_raw_scores(sa, _cache["scoring_questions"])
    _cache["raw_scores"] = raw_scores

    log = _cache.get("log")
    prior = log.latest_probs if log else None
    cs = _cache.get("credit_signal")
    hy_recession = cs.hy_recession_pricing if cs else False

    probs, flags = apply_all_rules(
        raw_scores, prior, hy_recession_pricing_fired=hy_recession
    )
    _cache["scenario_probs"] = probs

    result = {
        "status": "OK",
        "scenario_probs": {
            "A": probs.A, "B": probs.B, "C": probs.C,
            "D": probs.D, "E": probs.E, "F": probs.F,
        },
        "raw_scores": {
            "A": raw_scores.A, "B": raw_scores.B, "C": raw_scores.C,
            "D": raw_scores.D, "E": raw_scores.E, "F": raw_scores.F,
        },
        "flags": list(flags),
    }

    # ── M19 thesis-sustaining condition evaluation ─────────────────────────
    # Runs here (not in advisor_run_computation) because several §13
    # conditions reference B+C/Scenario-X probability, which only exists
    # once scoring has run. cal/readings/regime are recomputed from _cache
    # rather than cached objects, following the same convention already
    # used above for RoleRepricingDivergence's DivergenceSignal recompute.
    cal_for_tsc = _cache.get("cal")
    readings_list = _cache.get("readings", [])
    if cal_for_tsc is not None:
        # Note: readings_list may legitimately be empty (all fetchers failed
        # this session) — evaluate_thesis_conditions() and
        # evaluate_range_position_advisories() are both designed to degrade
        # to UNKNOWN/"inconclusive" with quality_flags on missing data, not
        # crash, so there is no reason to skip the whole block on that case
        # alone (a prior version did `and readings_list`, which silently
        # disabled M19 entirely whenever every fetch failed — found via the
        # no_network test fixture while adding GAP-16 coverage).
        try:
            from .analysis import compute_divergence_signal, evaluate_thesis_conditions

            readings_by_id = {r.spec_id: r for r in readings_list}
            held_tickers = [t for t, e in cal_for_tsc.instruments.items()
                            if not e.is_candidate]
            m19_ids = {q.id for q in _cache.get("scoring_questions", [])
                       if q.consumer == "M19"}
            call2_answers = {qid: answers[qid] for qid in m19_ids if qid in answers}

            regime_signal = None
            try:
                regime_signal = compute_divergence_signal(readings_by_id, cal_for_tsc)
            except Exception as e:
                result["flags"].append(f"⚠ M19: DivergenceSignal recompute failed: {e}")

            tsc = evaluate_thesis_conditions(
                held_tickers=held_tickers,
                readings=readings_by_id,
                probs=probs,
                regime_signal=regime_signal,
                cal=cal_for_tsc,
                call2_answers=call2_answers,
            )
            _cache["tsc_evaluations"] = tsc
            result["tsc_evaluations"] = [
                {
                    "ticker":               t.ticker,
                    "status":               t.status.value,
                    "fired_condition_text": t.fired_condition_text,
                    "missing_dependencies": t.missing_dependencies,
                    "quality_flags":        t.quality_flags,
                }
                for t in tsc
            ]
            unknown = [t.ticker for t in tsc if t.status.value == "UNKNOWN"]
            if unknown:
                result["flags"].append(
                    f"⚠ M19: {len(unknown)} ticker(s) UNKNOWN this session "
                    f"(no evaluable §13 condition — not the same as ACTIVE): {unknown}"
                )

            # ── GAP-16: within-scenario range-position advisory ────────────
            # GAP-16 promotion (v1.46): this advisory now also feeds a bounded
            # EV adjustment, not just the briefing — see analysis/range_position.py
            # apply_range_position_adjustment() and analysis/instruments.py
            # blended_scenario_return() for the mechanism. clean_signal_role_map()
            # drops "mixed"/"inconclusive" so only a clean two-driver agreement
            # ever reaches the EV math; populate BEFORE any blended_scenario_return()
            # call this session (evaluate_allocation reuses this same cached cal
            # object) or the adjustment silently no-ops for the whole session.
            try:
                from .analysis import (
                    clean_signal_role_map,
                    evaluate_range_position_advisories,
                )

                range_advisories = evaluate_range_position_advisories(
                    held_tickers=held_tickers, probs=probs,
                    cal=cal_for_tsc, readings=readings_by_id,
                )
                cal_for_tsc.range_position_signals = clean_signal_role_map(range_advisories)
                if range_advisories:
                    result["range_position_advisories"] = [
                        {
                            "ticker":             a.ticker,
                            "role_id":            a.role_id,
                            "scenario":           a.scenario,
                            "range_pct":          [a.range_conservative, a.range_upside],
                            "range_width_pp":     a.range_width_pp,
                            "signal":             a.signal,
                            "drivers":            a.drivers,
                            "note":               a.note,
                            "quality_flags":      a.quality_flags,
                            "ev_adjustment_applied": a.signal in ("favorable", "unfavorable"),
                        }
                        for a in range_advisories
                    ]
                else:
                    result["range_position_advisories"] = []
            except Exception as e:
                result["flags"].append(f"⚠ GAP-16 range-position advisory failed: {e}")
        except Exception as e:
            result["flags"].append(f"⚠ M19 thesis evaluation failed: {e}")
    else:
        result["flags"].append(
            "ℹ M19 thesis evaluation skipped — no cached calibration/readings "
            "(call advisor_run_computation first)."
        )

    # ── Step 6b: re-run floor check if probs shifted >= 5pp ───────────────
    floor_accounts = _cache.get("floor_accounts", [])
    cal            = _cache.get("cal")
    prior          = log.latest_probs if log else None

    if floor_accounts and cal is not None and prior is not None:
        max_shift = max(
            abs(getattr(probs, s) - getattr(prior, s))
            for s in ["A", "B", "C", "D", "E", "F"]
        )
        if max_shift >= 5.0:
            try:
                from .analysis import check_all_floor_accounts
                floor_alerts_6b = check_all_floor_accounts(
                    floor_accounts=floor_accounts,
                    probabilities=probs,
                    cal=cal,
                    check_step="6b",
                )
                if floor_alerts_6b:
                    result["floor_breach_alerts_6b"] = [
                        {
                            "step":            a.check_step,
                            "account_id":      a.account_id,
                            "worst_scenario":  a.worst_scenario,
                            "worst_return_pct":round(a.worst_return_pct, 2),
                            "priority":        a.priority,
                        }
                        for a in floor_alerts_6b
                    ]
                    result["status"] = "FLOOR_BREACH"
                    result["flags"].append(
                        f"⚠⚠ FLOOR_BREACH_ALERT [6b]: {len(floor_alerts_6b)} account(s) "
                        f"at current probs (max shift {max_shift:.1f}pp). "
                        "RecalibrationSequence required."
                    )
                else:
                    result["floor_breach_alerts_6b"] = []
                    result["flags"].append(
                        f"ℹ FloorCheck [6b]: CLEAR at current probs "
                        f"(prob shift {max_shift:.1f}pp triggered re-check)."
                    )
            except Exception as e:
                result["flags"].append(f"⚠ FloorCheck [6b] failed: {e}")
        else:
            result["flags"].append(
                f"ℹ FloorCheck [6b] skipped — max prob shift {max_shift:.1f}pp < 5pp threshold."
            )

    return _dumps(result)


# ── Tool 3: advisor_evaluate_allocation() ─────────────────────────────────────
# Closes ENG-16: M13.idealAllocation()/scenarioWeightedAllocation()/
# FeasibilityCheck(), M15.classifyInstrument()/dominantDirective(),
# M08.DualRoleConflict() all had faithful, tested Python implementations
# that no MCP tool ever called — Claude re-derived all of this by hand from
# the M13/M15/M08 .md spec every session. This tool wires them in.

def _tool_evaluate_allocation(
    account_profile: Dict[str, Any],
    current_weights: Dict[str, float],
    tickers: Optional[List[str]] = None,
    proposed_allocations: Optional[Dict[str, float]] = None,
    cal: Optional[Any] = None,
    probs: Optional[Any] = None,
) -> str:
    """
    M13/M15/M08 portfolio math for one account.

    Normal path: requires advisor_run_computation() and advisor_apply_scoring()
    to have been called earlier this session (uses cached cal + scenario_probs —
    §8 AUTHORITATIVE probabilities, never recomputed here).

    cal/probs: optional explicit overrides, bypassing the session _cache
    entirely when given. This is the ENG-33 CLI fallback path's hook —
    `python -m advisor evaluate-allocation` (see __main__.py) is a fresh
    process with nothing cached, so it reads Calibration_State.md itself
    and takes scenario_probs as an explicit argument (still §8-sourced —
    whatever advisor_apply_scoring returned earlier in the same MCP
    session, never independently recomputed) and passes both straight
    through here. The @srv.tool()-registered advisor_evaluate_allocation
    below never passes these; cache lookup remains the normal live-session
    path. Kept as plain optional params rather than a separate function so
    both paths share one tested implementation instead of two.
    """
    cal = cal if cal is not None else _cache.get("cal")
    probs = probs if probs is not None else _cache.get("scenario_probs")
    if cal is None:
        return _err("No calibration state cached. Call advisor_run_computation first.")
    if probs is None:
        return _err("No scenario probabilities cached. Call advisor_apply_scoring first.")

    from .exceptions import HardStopException
    from .analysis.instruments import classify_instrument, dominant_directive
    from .portfolio.allocation import scenario_weighted_allocation, feasibility_check, recalibration_sequence
    from .portfolio.directives import DIRECTIVES
    from .portfolio.evaluation import dual_role_conflict

    try:
        account = _parse_account_profile(account_profile)
    except Exception as e:
        return _err(f"account_profile invalid: {e}")

    eval_tickers = tickers if tickers else list(current_weights.keys())
    if not eval_tickers:
        return _err("No tickers to evaluate — current_weights is empty and tickers not given.")

    dominant_scenario = max(("A", "B", "C", "D", "E", "F"), key=lambda s: getattr(probs, s))

    result: Dict[str, Any] = {
        "status": "OK",
        "account_id": account.account_id,
        "objective_type": account.objective_type.value,
        "dominant_scenario": dominant_scenario,
        "instruments": {},
        "flags": [],
    }

    for ticker in eval_tickers:
        entry_result: Dict[str, Any] = {}

        try:
            components = classify_instrument(ticker, cal)
            entry_result["components"] = [
                {"role_id": c.role_id, "weight": c.weight} for c in components
            ]
        except HardStopException as e:
            result["flags"].append(f"⚠ {ticker}: classifyInstrument failed — {e}")
            result["instruments"][ticker] = {"error": str(e)}
            continue  # nothing else can be computed without a classification

        try:
            target = scenario_weighted_allocation(
                ticker=ticker, account=account, probs=probs,
                all_current_weights=current_weights, cal=cal,
            )
            entry_result["scenario_weighted_weight"] = round(target.scenario_weighted_weight, 4)
            entry_result["per_scenario"] = {s: round(w, 4) for s, w in target.per_scenario.items()}
            entry_result["blended_conservative_return_pct"] = round(target.blended_conservative_return, 2)
            entry_result["directive"] = target.directive.value
            entry_result["floor"] = round(target.floor, 4)
            if target.quality_flags:
                entry_result["quality_flags"] = target.quality_flags
        except Exception as e:
            result["flags"].append(f"⚠ {ticker}: scenarioWeightedAllocation failed — {e}")

        try:
            entry_result["dominant_directive_conflict_aware"] = dominant_directive(
                ticker, dominant_scenario, DIRECTIVES, cal
            )
        except Exception as e:
            result["flags"].append(f"⚠ {ticker}: dominantDirective failed — {e}")

        try:
            entry_result["dual_role_conflict"] = dual_role_conflict(ticker, dominant_scenario, cal)
        except Exception as e:
            result["flags"].append(f"⚠ {ticker}: DualRoleConflict check failed — {e}")

        result["instruments"][ticker] = entry_result

    if proposed_allocations:
        try:
            fr = feasibility_check(
                account=account, proposed_allocations=proposed_allocations,
                probs=probs, cal=cal,
            )
            result["feasibility"] = {
                "feasible":             fr.feasible,
                "portfolio_return_pct": round(fr.portfolio_return, 2),
                "objective_type":       fr.objective_type,
                "required_return_pct":  (round(fr.required_return, 2)
                                          if fr.required_return is not None else None),
                "target_multiplier":    fr.target_multiplier,
                "shortfall_pp":         (round(fr.shortfall_pp, 2)
                                          if fr.shortfall_pp is not None else None),
                "drawdown_adjusted_return": fr.drawdown_adjusted_return,
                "target_met":           fr.target_met,
                "floor_breached":       fr.floor_breached,
                "worst_scenario":       fr.worst_scenario,
                "worst_return_pct":     (round(fr.worst_return, 2)
                                          if fr.worst_return is not None else None),
                "quality_flags":        fr.quality_flags,
            }
        except Exception as e:
            result["flags"].append(f"⚠ FeasibilityCheck failed: {e}")
    else:
        result["flags"].append(
            "ℹ FeasibilityCheck skipped — proposed_allocations not provided. "
            "Pass a ticker→weight dict for the full proposed portfolio (should sum "
            "to ~1.0) to run it. NEVER present allocation recommendations without "
            "this check having run."
        )


    # ── RecalibrationSequence (ENG-24) — fires when feasibility check fails ────────────────────
    if proposed_allocations and "feasibility" in result and not result["feasibility"]["feasible"]:
        fr_feasible = result["feasibility"]
        shortfall = (
            fr_feasible.get("shortfall_pp")
            or abs(fr_feasible.get("worst_return_pct") or fr_feasible.get("portfolio_return_pct") or 0.0)
        )
        obj_type = fr_feasible.get("objective_type", "")
        priority = "TARGET" if "TARGET_THEN_RETURN" in obj_type else "FLOOR_PROTECTION"
        try:
            rec = recalibration_sequence(
                account=account,
                proposed_allocations=proposed_allocations,
                probs=probs,
                cal=cal,
                shortfall_pp=round(shortfall or 0.0, 2),
                priority=priority,
            )
            result["recalibration"] = {
                "shortfall_pp":                 rec.shortfall_pp,
                "priority":                     rec.priority,
                "anchor_tickers":               rec.anchor_tickers,
                "anchor_weight":                rec.anchor_weight,
                "anchor_return_pct":            rec.anchor_return_pct,
                "residual_weight":              rec.residual_weight,
                "residual_required_return_pct": rec.residual_required_return_pct,
                "gap_closed_by_reallocation":   rec.gap_closed_by_reallocation,
                "revised_portfolio_return_pct": rec.revised_portfolio_return_pct,
                "revised_gap_pp":               rec.revised_gap_pp,
                "revised_allocations":          rec.revised_allocations,
                "candidate_role":               rec.candidate_role,
                "candidate_role_return_pct":    rec.candidate_role_return_pct,
                "candidate_gap_closure_est_pp": rec.candidate_gap_closure_est_pp,
                "no_candidate_message":         rec.no_candidate_message,
                "quality_flags":                rec.quality_flags,
            }
        except Exception as e:
            result["flags"].append(f"⚠ RecalibrationSequence failed: {e}")

    return _dumps(result)


# ── Tool 4: advisor_check_instrument_candidate() ──────────────────────────────
# Closes the M07 portion of ENG-16. Pure on the supplied metrics — no
# CalibrationState dependency, no precondition on advisor_run_computation
# having run this session. For a candidate instrument not yet in §11.

def _tool_check_instrument_candidate(
    ticker: str,
    aum_millions: Optional[float] = None,
    track_record_years: Optional[float] = None,
    foreign_concentration_pct: Optional[float] = None,
    instrument_type: str = "active_fund",
    revenue_type: str = "fee_based",
    has_contract_backstop: bool = True,
    hold_horizon_years: int = 10,
) -> str:
    """M07.AutoDisqualify() for one candidate instrument."""
    from .portfolio.evaluation import auto_disqualify
    from .types import InstrumentSpec

    spec = InstrumentSpec(
        ticker=ticker,
        aum_millions=aum_millions,
        track_record_years=track_record_years,
        foreign_concentration_pct=foreign_concentration_pct,
        instrument_type=instrument_type,
        revenue_type=revenue_type,
        has_contract_backstop=has_contract_backstop,
        hold_horizon_years=hold_horizon_years,
    )
    r = auto_disqualify(spec)
    return _dumps({
        "status":       "OK",
        "ticker":       r.ticker,
        "disqualified": r.disqualified,
        "reason":       r.reason,
        "quality_flags": r.quality_flags,
    })


# ── Tool 5: advisor_write_back() ──────────────────────────────────────────────

# Section8 entry + Portfolio_State.md rendering: shared with orchestrator/session.py
# (Pattern A) via rendering.py -- see ENG-3 (deduplication of the two session pipelines).
from .rendering import (
    build_session_log_entry as _build_session_log_entry,
    mark_prior_entries_superseded as _mark_prior_entries_superseded,
    render_portfolio_state as _render_portfolio_state,
)


def _tool_write_back(
    primary_driver: str,
    open_triggers: List[str],
    open_decisions: List[str],
    next_session_flags: List[str],
    dry_run: bool,
    session_type: str,
) -> str:
    from .data.file_protocol import read_session_log, write_back
    from .types import SessionType

    probs = _cache.get("scenario_probs")
    if probs is None:
        return _err("No scenario probs cached. Call advisor_apply_scoring first.")
    cal = _cache.get("cal")
    if cal is None:
        return _err("No calibration state cached. Call advisor_run_computation first.")

    today = datetime.date.today().isoformat()
    p = probs

    # Canonical §8 schema — see rendering.build_session_log_entry() (ENG-3:
    # shared with orchestrator/session.py's Pattern A write-back).
    new_entry = _build_session_log_entry(
        today, session_type, p, primary_driver,
        open_triggers, open_decisions, next_session_flags,
    )

    log_text = _cache.get("log_text") or read_session_log()
    log_text = _mark_prior_entries_superseded(log_text, today)
    updated_log = log_text.rstrip() + new_entry

    portfolio_state = _render_portfolio_state(
        cal.version, probs, today, primary_driver, open_triggers, open_decisions,
        generator_label="MCP (Pattern B — Claude app)",
    )

    try:
        sha = write_back(
            calibration_state=None,
            session_log=updated_log,
            portfolio_state=portfolio_state,
            session_type=SessionType.FULL_DESKTOP,
            dry_run=dry_run,
        )
        return _dumps({"status": "OK", "committed": not dry_run,
                       "commit_hash": sha, "dry_run": dry_run})
    except Exception as e:
        return _err(str(e))


# ── MCP server ─────────────────────────────────────────────────────────────────

def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP package not installed.\n"
            "Run:  pip install 'mcp>=1.0.0'\n"
            "Then restart the MCP server."
        )

    srv = FastMCP("financial-advisor")

    @srv.tool()
    def advisor_run_computation(
        floor_account_weights_json: Optional[Any] = None,
    ) -> str:
        """
        M05 Steps 1–4 + 3b: load Calibration_State.md + Session_Log.md,
        fetch all M18 market data, compute M11/M14/M17 signals, run
        CurrentHoldingsFloorCheck (Step 3b), and build M03 scoring questions.

        BEFORE CALLING: Read the allocation sheet via Google Drive MCP.
        For each FLOOR_THEN_RETURN account, compute:
          current_weight[ticker] = holding_current_value / account_total
        Then pass as floor_account_weights_json (JSON string):
          '[{"account_id": "Relative_IRA_469",
             "weights": {"MLPX": 0.24, "SGOV": 0.21, "DBMF": 0.15, ...}},
            {"account_id": "Relative_Roth_466",
             "weights": {"MLPX": 0.18, ...}}]'
        If omitted: floor monitoring steps skipped (advisory flags in output).

        Returns JSON with:
          - prior_probs: prior scenario probabilities from §8
          - market_data: compact snapshot of all live readings
          - holdings_30d_returns: 30-day returns for all holdings (pct)
          - signals: credit / regime / cascade / yield_curve
          - role_repricing_warnings: instruments underperforming role thesis (§9.5)
          - floor_breach_alerts: FLOOR_THEN_RETURN account breach alerts [Step 3b]
          - passive_mandate_warnings: non-passive instruments repricing in floor accounts
          - scoring_questions: list with auto_score (None = you answer)
          - qualitative_targets: list of topics to research via web_search
          - open_triggers / open_decisions from last §8

        After calling this tool:
          1. Use web_search for each item in qualitative_targets
          2. Answer scoring_questions where auto_score is null
          3. Call advisor_apply_scoring with your answers dict
             (will auto-run FloorCheck Step 6b if probs shift >= 5pp)

        Bounded to 180s (ENG-40 follow-up, 2026-06-24): wrapped in
        _with_timeout() like the other two tools below, after this tool
        specifically hung 25+ minutes on an unguarded yfinance call. If
        this fires, the underlying fetch may still be running in the
        background -- it has no side effects worth checking for (unlike
        write_back), so just retry.
        """
        return _with_timeout(
            _tool_run_computation, 180.0,
            floor_account_weights_json=floor_account_weights_json,
        )

    @srv.tool()
    def advisor_apply_scoring(answers: Dict[str, int]) -> str:
        """
        M05 Step 5: apply scoring answers → ScenarioProbabilities.

        answers: dict mapping question_id → integer score.
        Only include questions where auto_score was null in
        advisor_run_computation output.  Auto-scored questions are
        handled by Python automatically.

        Example:
          {"A_check_fed": 1, "B_check_cpi": 2, "B_check_gdp": 1,
           "C_check_chokepoint": 2, "D_check_unemployment": 0,
           "D_check_fed": 1, "E_check_dedollar": 0,
           "E_check_stress": 0, "F_check_gdp": 1, "F_check_noshock": 1}

        Returns ScenarioProbabilities (A+B+C+D+E+F = 100) + flags
        (25pp cap notice if applied).
        """
        return _tool_apply_scoring(answers)

    @srv.tool()
    def advisor_evaluate_allocation(
        account_id: str,
        planning_horizon_years: int,
        objective_type: str,
        current_weights: Dict[str, float],
        owner: str = "primary",
        floor_nominal_loss: bool = False,
        concentration_cap: float = 0.40,
        drawdown_tolerance: float = 0.30,
        tickers: Optional[List[str]] = None,
        proposed_allocations: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        M13/M15/M08 portfolio math for one account: scenarioWeightedAllocation()
        (full per-scenario breakdown + probability-weighted target + blended
        conservative return + floor), FeasibilityCheck(), classifyInstrument()
        (ComponentVector), dominantDirective() (conflict-aware, multi-role),
        and DualRoleConflict() (ADD-vs-REDUCE detection in composites).

        Call AFTER advisor_run_computation() and advisor_apply_scoring() —
        uses their cached calibration state and scenario probabilities
        (§8 AUTHORITATIVE — never recompute probabilities yourself).

        account_id, planning_horizon_years, objective_type, owner,
        floor_nominal_loss, concentration_cap, drawdown_tolerance: the
          allocation sheet's "Objectives" tab fields for this account (no
          Python parser for that tab exists — you read and supply these).
          objective_type is one of "TARGET_THEN_RETURN", "RETURN_THEN_TARGET",
          "FLOOR_THEN_RETURN", "PRESERVATION". owner defaults to "primary".

          ENG-33 (2026-06-24): this used to take a single account_profile
          dict/object parameter. That shape hung completely at the MCP
          client layer — the request never even reached this server's
          stdio transport (confirmed via mcp-server-financial-advisor.log
          showing no incoming tools/call entry at all for the hung call,
          while advisor_run_computation and advisor_apply_scoring's calls
          in the same session both logged normally). The one structural
          difference versus those two: a nested object/model parameter,
          which FastMCP exposes as a $ref/$defs JSON schema rather than a
          flat property list. Flattening account_profile into top-level
          scalar parameters removes that shape entirely. Not a confirmed
          fix in the sense of a reproduced-then-resolved root cause (the
          hang is in Claude Desktop's client, outside this codebase, so it
          can't be unit-tested here) — but it removes the one schema
          feature this tool had that the other two working tools don't.

        current_weights: ticker → current allocation fraction in this account,
          for ALL holdings in the account (used for ranking within bounds).
          e.g. {"MLPX": 0.18, "AIPO": 0.12, "SGOV": 0.30, ...}

        tickers: optional — which tickers to compute the full breakdown for.
          Default: all keys in current_weights. Narrow this to just the
          ticker(s) you're actually making a recommendation about.

        proposed_allocations: optional — ticker → proposed weight for the
          FULL account (should sum to ~1.0). Runs FeasibilityCheck against
          this set. If omitted, FeasibilityCheck is skipped with an advisory
          flag — NEVER present allocation recommendations without it having
          run at least once for the account.

        Returns JSON with per-ticker: components (ComponentVector),
        scenario_weighted_weight, per_scenario (all six), blended_conservative
        _return_pct, directive, dominant_directive_conflict_aware, floor,
        dual_role_conflict (null if none), quality_flags. Plus feasibility
        (if proposed_allocations given).
        """
        return _with_timeout(
            _tool_evaluate_allocation, 30.0,
            account_profile={
                "account_id": account_id,
                "owner": owner,
                "planning_horizon_years": planning_horizon_years,
                "objective_type": objective_type,
                "floor_nominal_loss": floor_nominal_loss,
                "concentration_cap": concentration_cap,
                "drawdown_tolerance": drawdown_tolerance,
            },
            current_weights=current_weights,
            tickers=tickers,
            proposed_allocations=proposed_allocations,
        )

    @srv.tool()
    def advisor_check_instrument_candidate(
        ticker: str,
        aum_millions: Optional[float] = None,
        track_record_years: Optional[float] = None,
        foreign_concentration_pct: Optional[float] = None,
        instrument_type: str = "active_fund",
        revenue_type: str = "fee_based",
        has_contract_backstop: bool = True,
        hold_horizon_years: int = 10,
    ) -> str:
        """
        M07.AutoDisqualify() for a candidate instrument not yet in §11.
        No session precondition — pure on the metrics you supply.

        Four hard guards, any one disqualifies: AUM < $100M with a 10+ year
        hold horizon; foreign concentration > 40% for active_fund/sector_ETF;
        commodity-dependent revenue with no contract backstop; track record
        < 3 years. Unknown metrics (None) skip that guard with a flag rather
        than falsely disqualifying — supply what you have.

        instrument_type: "active_fund" | "sector_ETF" | "passive_broad" | "single_stock"
        revenue_type: "fee_based" | "commodity_dependent" | "mixed"

        Returns {disqualified, reason, quality_flags}.
        """
        return _tool_check_instrument_candidate(
            ticker=ticker,
            aum_millions=aum_millions,
            track_record_years=track_record_years,
            foreign_concentration_pct=foreign_concentration_pct,
            instrument_type=instrument_type,
            revenue_type=revenue_type,
            has_contract_backstop=has_contract_backstop,
            hold_horizon_years=hold_horizon_years,
        )

    @srv.tool()
    def advisor_write_back(
        primary_driver: str,
        open_triggers: List[str],
        open_decisions: List[str],
        session_type: str,
        next_session_flags: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> str:
        """
        M05 Step 10: append §8 session state entry to Session_Log.md,
        render Portfolio_State.md, and commit both files via git.

        Call at the end of the portfolio discussion, after
        advisor_apply_scoring has been called this session.

        primary_driver: concise description of session's main driver
        open_triggers:  list of active trigger strings to carry forward
        open_decisions: list of pending decision strings to carry forward
        session_type:   required — describe what kind of session this was,
                        e.g. "full M05 session", "ad-hoc", "audit". No
                        default on purpose: pick deliberately rather than
                        silently mislabeling an ad-hoc session as full M05.
                        Written verbatim into both the §8 'date:' parenthetical
                        and the 'session_type:' field.
        next_session_flags: items to surface at next session start
                            (default empty)
        dry_run: if true, writes files locally but skips git commit

        Returns commit hash on success.
        """
        return _with_timeout(
            _tool_write_back, 90.0,
            primary_driver=primary_driver,
            open_triggers=open_triggers,
            open_decisions=open_decisions,
            next_session_flags=next_session_flags or [],
            dry_run=dry_run,
            session_type=session_type,
        )

    return srv


# Singleton — imported by __main__.py
mcp = build_server()
