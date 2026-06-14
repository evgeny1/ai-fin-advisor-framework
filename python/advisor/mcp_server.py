"""
advisor/mcp_server.py — MCP server for Claude Desktop integration.

Exposes the advisor framework as three MCP tools so Claude in the
Claude app can run the full M05 session pipeline without separate
API calls.  Zero additional cost vs CLI mode (no ANTHROPIC_API_KEY
needed here — Claude in the conversation IS the AI).

Three tools:
  advisor_run_computation()     M05 Steps 1–4: load config, fetch
                                market data, compute all signals,
                                build M03 scoring questions.
  advisor_apply_scoring()       M05 Step 5: scoring answers →
                                ScenarioProbabilities (Python math).
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

def _tool_run_computation() -> str:
    """
    M05 Steps 1+2+4: load config, fetch market data, compute signals,
    build scoring questions.  Caches results for the other two tools.

    The qualitative research (M02 QUALITATIVE_GATHER_LIST) is NOT done
    here — Claude does it after this call using web_search.  The
    qualitative_targets list tells Claude which topics to research.
    """
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

    return _dumps({
        "status": "OK",
        "scenario_probs": {
            "A": probs.A, "B": probs.B, "C": probs.C,
            "D": probs.D, "E": probs.E, "F": probs.F,
        },
        "raw_scores": {
            "A": raw_scores.A, "B": raw_scores.B, "C": raw_scores.C,
            "D": raw_scores.D, "E": raw_scores.E, "F": raw_scores.F,
        },
        "sum_check": probs.A + probs.B + probs.C + probs.D + probs.E + probs.F,
        "flags": flags,
    })


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
    def advisor_run_computation() -> str:
        """
        M05 Steps 1–4: load Calibration_State.md + Session_Log.md from
        local Drive path, fetch all M18 market data, compute M11/M14/M17
        signals, and build M03 scoring questions.

        Returns JSON with:
          - prior_probs: prior scenario probabilities from §8
          - market_data: compact snapshot of all live readings
          - signals: credit / regime / cascade / yield_curve
          - scoring_questions: list with auto_score (None = you answer)
          - qualitative_targets: list of topics to research via web_search
          - open_triggers / open_decisions from last §8

        After calling this tool:
          1. Use web_search for each item in qualitative_targets
          2. Answer scoring_questions where auto_score is null
             (use the evidence field + your qualitative research)
          3. Call advisor_apply_scoring with your answers dict
        """
        return _tool_run_computation()

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
