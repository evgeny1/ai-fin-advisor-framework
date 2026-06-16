"""
advisor/mcp_server.py — MCP server for Claude Desktop integration.

Exposes the advisor framework as three MCP tools so Claude in the
Claude app can run the full M05 session pipeline without separate
API calls.  Zero additional cost vs CLI mode (no ANTHROPIC_API_KEY
needed here — Claude in the conversation IS the AI).

Three tools:
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

import dataclasses
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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


# ── Tool 1: advisor_run_computation() ─────────────────────────────────────────

def _tool_run_computation(floor_account_weights_json: Optional[str] = None) -> str:
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
    import yfinance as _yf

    from .config import parse_calibration_state, parse_session_log
    from .data.fetch_registry import FetchRegistry
    from .data.file_protocol import read_calibration_state, read_session_log
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
    )
    from .types import DataSource

    result: Dict[str, Any] = {
        "status": "OK",
        "session_date": datetime.date.today().isoformat(),
        "flags": [],
    }

    # ── Step 1: Load config ────────────────────────────────────────────────
    cal_text = read_calibration_state()
    log_text = read_session_log()
    cal = parse_calibration_state(cal_text)
    log = parse_session_log(log_text)

    _cache.update({"cal": cal, "log": log,
                   "cal_text": cal_text, "log_text": log_text})

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
        import datetime as _dt
        end_dt   = _dt.date.today()
        start_dt = end_dt - _dt.timedelta(days=50)  # 50 cal days ≈ 35 trading days
        hist = _yf.download(
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
        _cache["holdings_30d"] = holdings_30d
        result["holdings_30d_returns"] = {
            t: round(v * 100, 2) for t, v in holdings_30d.items() if v is not None
        }
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
            floor_accounts = json.loads(floor_account_weights_json)
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


# ── Tool 3: advisor_write_back() ──────────────────────────────────────────────

def _render_portfolio_state(cal: Any, probs: Any, session_date: str,
                            primary_driver: str, open_triggers: List[str],
                            open_decisions: List[str]) -> str:
    p = probs
    prob_str = (f"A={p.A:.0f}% / B={p.B:.0f}% / C={p.C:.0f}% / "
                f"D={p.D:.0f}% / E={p.E:.0f}% / F={p.F:.0f}%")
    lines = [
        f"# Portfolio State — {session_date}",
        "",
        f"**Calibration State:** {cal.version}",
        f"**Scenario probabilities:** {prob_str}",
        f"**Primary driver:** {primary_driver}",
        "",
        "## Open Triggers",
    ]
    for t in open_triggers:
        lines.append(f"- {t}")
    if not open_triggers:
        lines.append("_None this session._")
    lines += ["", "## Open Decisions"]
    for d in open_decisions:
        lines.append(f"- {d}")
    if not open_decisions:
        lines.append("_None this session._")
    lines += ["", "_Generated via MCP (Pattern B — Claude app)._"]
    return "\n".join(lines)


def _tool_write_back(
    primary_driver: str,
    open_triggers: List[str],
    open_decisions: List[str],
    next_session_flags: List[str],
    dry_run: bool,
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
    prob_str = (f"A={p.A:.0f} / B={p.B:.0f} / C={p.C:.0f} / "
                f"D={p.D:.0f} / E={p.E:.0f} / F={p.F:.0f}")
    flags_str = "; ".join(next_session_flags) if next_session_flags else "none"

    new_entry = (
        f"\n\n### §8 Entry — {today}\n"
        f"**Probabilities:** {prob_str}\n"
        f"**Primary driver:** {primary_driver}\n"
        f"**Open triggers:** {'; '.join(open_triggers) or 'none'}\n"
        f"**Open decisions:** {'; '.join(open_decisions) or 'none'}\n"
        f"**Next session flags:** {flags_str}\n"
    )

    log_text = _cache.get("log_text") or read_session_log()
    updated_log = log_text.rstrip() + new_entry

    portfolio_state = _render_portfolio_state(
        cal, probs, today, primary_driver, open_triggers, open_decisions
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
        floor_account_weights_json: Optional[str] = None,
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
        """
        return _tool_run_computation(floor_account_weights_json)

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
    def advisor_write_back(
        primary_driver: str,
        open_triggers: List[str],
        open_decisions: List[str],
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
        next_session_flags: items to surface at next session start
                            (default empty)
        dry_run: if true, writes files locally but skips git commit

        Returns commit hash on success.
        """
        return _tool_write_back(
            primary_driver=primary_driver,
            open_triggers=open_triggers,
            open_decisions=open_decisions,
            next_session_flags=next_session_flags or [],
            dry_run=dry_run,
        )

    return srv


# Singleton — imported by __main__.py
mcp = build_server()
