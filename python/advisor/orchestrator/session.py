"""
orchestrator/session.py — SessionPipeline: M05.SessionStartSequence as executable Python.

Usage:
    from advisor.orchestrator import SessionPipeline, StubAIClient
    ctx = SessionPipeline(ai=StubAIClient()).run()
    print(ctx.briefing)

Three AI calls (Pattern A — Python orchestrates, Claude as service):
    1. gather_qualitative   → qualitative context for scoring
    2. answer_scoring       → integer scores for qualitative M03 checks
    3. generate_briefing    → M04 narrative briefing

All arithmetic (normalize, floors, session cap, EV math) is Python.
"""
from __future__ import annotations

import datetime
import logging
import sys
from typing import Dict, List, Optional

from ..analysis import (
    assess_cascade_level,
    compute_credit_signal,
    compute_divergence_signal,
    validate_classifications,
    blended_scenario_return,
    check_all_floor_accounts,
    role_repricing_divergence,
    passive_mandate_absent_warnings,
)
from ..analysis.scenario_math import apply_all_rules
from ..config import parse_calibration_state, parse_session_log
from ..data.fetch_registry import FetchRegistry
from ..data.file_protocol import framework_path, write_back, read_calibration_state, read_session_log
from ..data.m18_registry import register_all
from ..exceptions import HardStopException
from ..portfolio import (
    feasibility_check,
    scenario_weighted_allocation,
)
from ..types import (
    DataReading,
    DataSource,
    ScoringAnswers,
    SessionType,
)
from .ai_client import AIClient, StubAIClient
from .context import SessionContext
from ..rendering import build_session_log_entry, mark_prior_entries_superseded, render_portfolio_state
from .scoring_questions import (
    QUALITATIVE_TARGETS,
    aggregate_raw_scores,
    generate_questions,
    questions_for_ai,
)

logger = logging.getLogger(__name__)


def _fmt_bps(value: "float | None") -> str:
    """Format a bps value for a progress/summary line, degrading to "n/a"
    when unavailable (ENG-47) rather than crashing the f-string that reads
    it. A transient FRED read-timeout is enough to leave e.g.
    YieldCurveSignal.spread_10y_2y as None -- not rare enough to treat as
    it-basically-never-happens. This is a log/progress line, not a
    computation result, so "n/a" is a safe degrade -- no downstream signal
    math depends on this string."""
    return "n/a" if value is None else f"{value:.0f}bps"


class SessionPipeline:
    """
    Implements M05.SessionStartSequence Steps 1–10 as a single runnable pipeline.

    Parameters
    ----------
    session_type : SessionType
        FULL_DESKTOP (write-back enabled) or READONLY_MOBILE (no write-back).
    ai : AIClient or None
        AI client for the 3 API calls. Defaults to StubAIClient (offline).
    dry_run : bool
        When True: skip write-back even in FULL_DESKTOP mode.
    """

    def __init__(
        self,
        session_type: SessionType = SessionType.FULL_DESKTOP,
        ai: Optional[AIClient] = None,
        dry_run: bool = False,
    ) -> None:
        self.session_type = session_type
        self.ai = ai or StubAIClient()
        self.dry_run = dry_run

    # ── Progress reporter ──────────────────────────────────────────────────────

    @staticmethod
    def _prog(message: str, done: bool = False) -> None:
        """Print a timestamped progress line to stderr."""
        ts  = datetime.datetime.now().strftime("%H:%M:%S")
        pfx = "✓" if done else "→"
        print(f"[{ts}] {pfx} {message}", file=sys.stderr, flush=True)

    def run(self) -> SessionContext:
        """Execute full M05 pipeline. Returns populated SessionContext."""
        self._prog("SessionPipeline starting")
        ctx = SessionContext(
            session_type=self.session_type,
            session_date=datetime.date.today().isoformat(),
            dry_run=self.dry_run,
        )

        self._step1_load_config(ctx)
        self._step2_fetch_market_data(ctx)
        self._step2b_floor_check(ctx, check_step="3b")   # M05 Step 3b
        self._step3_gather_qualitative(ctx)
        self._step4_compute_signals(ctx)
        self._step5_derive_probabilities(ctx)
        self._step5b_floor_check_rerun(ctx)              # M05 Step 6b
        self._step6_portfolio_math(ctx)
        self._step7_generate_briefing(ctx)
        self._step8_write_back(ctx)

        self._prog("Pipeline complete", done=True)
        return ctx

    # ── Step 1: Load config ────────────────────────────────────────────────────

    def _step1_load_config(self, ctx: SessionContext) -> None:
        """
        M05 Steps 1+3: Read Calibration_State.md + Session_Log.md.
        Parse into typed CalibrationState + SessionLogState.
        Run ValidateClassifications — HARD_STOP if any allocation ticker absent.
        """
        self._prog("Step 1/8  Loading Calibration_State.md + Session_Log.md ...")
        logger.info("Step 1: Loading framework config")

        cal_text = read_calibration_state()
        log_text = read_session_log()

        ctx.cal = parse_calibration_state(cal_text)
        ctx.log = parse_session_log(log_text)

        n_entries = len(ctx.log.scenario_states)
        self._prog(
            f"Step 1/8  Config: Calibration_State v{ctx.cal.version} | "
            f"Session_Log: {n_entries} §8 entries",
            done=True,
        )

        # ValidateClassifications
        allocation_tickers = [t for t, e in ctx.cal.instruments.items() if not e.is_candidate]
        try:
            warnings = validate_classifications(allocation_tickers, ctx.cal)
            ctx.validate_flags.extend(warnings)
            if warnings:
                for w in warnings:
                    self._prog(f"  ⚠ {w[:120]}")
        except HardStopException as e:
            raise

    # ── Step 2: Fetch market data ──────────────────────────────────────────────

    def _step2_fetch_market_data(self, ctx: SessionContext) -> None:
        """M05 Step 4: FetchRegistry.fetch_all() — all M18 registered FetchSpecs."""
        self._prog("Step 2/8  Fetching market data (M18 registry) ...")
        logger.info("Step 2: Fetching market data")

        registry = FetchRegistry()
        register_all(registry)

        from ..data.fetchers import yfinance_fetcher as yf
        registry.register_fetcher(DataSource.YFINANCE, yf.yfinance_dispatcher)

        try:
            from ..data.fetchers import fred_fetcher as fred
            registry.register_fetcher(DataSource.FRED_SPREADSHEET_TAB, fred.fetch_yield_curve_fred)
        except Exception as e:
            ctx.fetch_flags.append(f"⚠ FRED fetcher not registered: {e} — credit spreads unavailable")

        ctx.readings = registry.fetch_all()

        valid   = sum(1 for r in ctx.readings if r.is_valid)
        flagged = len(ctx.readings) - valid
        self._prog(
            f"Step 2/8  Market data: {valid} valid, {flagged} unavailable "
            f"({len(ctx.readings)} specs total)",
            done=True,
        )
        if flagged:
            ctx.fetch_flags.append(f"⚠ {flagged} data readings flagged — review quality_flags in readings.")

    # ── Step 2b: M05 Step 3b — CurrentHoldingsFloorCheck (prior probs) ──────

    def _step2b_floor_check(self, ctx: SessionContext, check_step: str = "3b") -> None:
        """
        M05 Step 3b: CurrentHoldingsFloorCheck for FLOOR_THEN_RETURN accounts.

        Uses prior session probabilities (§8) — best available before scoring.
        Allocation sheet current weights must be pre-loaded into ctx.floor_account_weights
        by the caller when Google credentials are available. If not loaded, step is skipped
        with a flag — the Claude orchestrator path handles this via MCP sheet fetch.
        """
        self._prog(f"Step 2b  M05.{check_step}: CurrentHoldingsFloorCheck ...")

        if not ctx.floor_account_weights:
            ctx.floor_alerts.append(
                f"⚠ FloorCheck Step {check_step} skipped — no allocation sheet weights loaded. "
                "Run with Google credentials or provide floor_account_weights to SessionContext."
            )
            self._prog(f"Step 2b  FloorCheck skipped (no sheet data)", done=True)
            return

        probs = ctx.log.latest_probs if ctx.log else None
        if probs is None:
            ctx.floor_alerts.append(
                f"⚠ FloorCheck Step {check_step} skipped — no prior probabilities in §8."
            )
            self._prog(f"Step 2b  FloorCheck skipped (no prior probs)", done=True)
            return

        alerts = check_all_floor_accounts(
            floor_accounts=ctx.floor_account_weights,
            probabilities=probs,
            cal=ctx.cal,
            check_step=check_step,
        )

        for alert in alerts:
            msg = (
                f"⚠ FLOOR_BREACH_ALERT [{check_step}] — {alert.account_id}: "
                f"scenario {alert.worst_scenario} returns {alert.worst_return_pct:.2f}% "
                f"at {'prior' if check_step == '3b' else 'current'} probability vector. "
                "Floor constraint breached on current holdings. "
                "RecalibrationSequence required before allocation recommendations."
            )
            ctx.floor_alerts.append(msg)
            self._prog(f"  !! {msg[:140]}")

        if not alerts:
            self._prog(f"Step 2b  FloorCheck {check_step}: all FLOOR accounts CLEAR", done=True)
        else:
            self._prog(
                f"Step 2b  FloorCheck {check_step}: {len(alerts)} BREACH(ES) detected — "
                "client acknowledgment required",
                done=True,
            )

        # Update 3: passive mandate absent warnings — runs alongside floor check
        if ctx.floor_account_weights and ctx.cal is not None:
            try:
                probs = ctx.log.latest_probs if ctx.log else None
                if probs is not None:
                    ctx.passive_mandate_warnings = passive_mandate_absent_warnings(
                        floor_accounts=ctx.floor_account_weights,
                        cal=ctx.cal,
                        probs=probs,
                        holdings_30d_returns=ctx.holdings_30d_returns or None,
                    )
                    if ctx.passive_mandate_warnings:
                        n = len(ctx.passive_mandate_warnings)
                        self._prog(f"  ⚠ PassiveMandateAbsent: {n} warning(s) — see briefing")
            except Exception as e:
                ctx.signal_flags.append(f"⚠ PassiveMandateAbsentWarning failed: {e}")

    # ── Step 5b: M05 Step 6b — FloorCheck re-run at current probabilities ────

    def _step5b_floor_check_rerun(self, ctx: SessionContext) -> None:
        """
        M05 Step 6b: Re-run CurrentHoldingsFloorCheck with newly derived probabilities.
        Only runs if any scenario shifted >= 5pp vs prior session.
        """
        if not ctx.has_probs or not ctx.log or not ctx.log.latest_probs:
            return  # can't compare — skip silently

        prior = ctx.log.latest_probs
        current = ctx.scenario_probs
        max_shift = max(
            abs(getattr(current, s) - getattr(prior, s)) for s in ["A","B","C","D","E","F"]
        )
        if max_shift < 5.0:
            self._prog("Step 5b  FloorCheck 6b: prob shift < 5pp — skip re-run", done=True)
            return

        self._prog(f"Step 5b  FloorCheck 6b: prob shift {max_shift:.1f}pp — re-running ...")
        self._step2b_floor_check(ctx, check_step="6b")

    # ── Step 3: AI Call 1 — Qualitative gather ────────────────────────────────

    def _step3_gather_qualitative(self, ctx: SessionContext) -> None:
        """AI Call 1 — M02 QUALITATIVE_GATHER_LIST."""
        self._prog(f"Step 3/8  AI Call 1: gathering qualitative context ({len(QUALITATIVE_TARGETS)} topics) ...")
        logger.info("Step 3: AI Call 1 — qualitative gather")

        brent_reading = next((r for r in ctx.readings if r.spec_id == "BRENT_CRUDE" and r.is_valid), None)
        hy_reading    = next((r for r in ctx.readings if r.spec_id == "HY_OAS"       and r.is_valid), None)
        summary_parts = []
        if brent_reading:
            b = brent_reading.value
            price = b.get("current") if isinstance(b, dict) else (b.get("price") if isinstance(b, dict) else b)
            if price:
                summary_parts.append(f"Brent ${price:.1f}/bbl")
        if hy_reading:
            h = hy_reading.value
            hy_val = h.get("current") if isinstance(h, dict) else h
            if hy_val:
                summary_parts.append(f"HY OAS {hy_val:.0f}bps")
        market_summary = "; ".join(summary_parts) if summary_parts else "market data fetched"

        ctx.qualitative = self.ai.gather_qualitative(QUALITATIVE_TARGETS, market_summary)
        self._prog(f"Step 3/8  Qualitative context ready ({len(ctx.qualitative)} topics)", done=True)

    # ── Step 4: Compute analysis signals ──────────────────────────────────────

    def _step4_compute_signals(self, ctx: SessionContext) -> None:
        """Stage 3 signals: CreditSignal, DivergenceSignal, CascadeSignal, YieldCurveSignal."""
        self._prog("Step 4/8  Computing signals (credit, regime, cascade) ...")
        logger.info("Step 4: Computing analysis signals")
        cal = ctx.cal

        readings = {r.spec_id: r for r in ctx.readings}

        try:
            ctx.credit_signal = compute_credit_signal(readings, cal)
        except Exception as e:
            ctx.signal_flags.append(f"⚠ CreditSignal failed: {e}")

        try:
            ctx.divergence_signal = compute_divergence_signal(readings, cal)
        except Exception as e:
            ctx.signal_flags.append(f"⚠ DivergenceSignal failed: {e}")

        # Update 1: role repricing divergence — uses holdings_30d_returns if available
        if ctx.divergence_signal is not None and ctx.holdings_30d_returns:
            broad_30d = ctx.divergence_signal.broad_equity_30d
            try:
                ctx.divergence_signal.role_repricing_warnings = role_repricing_divergence(
                    holdings_30d_returns=ctx.holdings_30d_returns,
                    broad_market_30d=broad_30d,
                    cal=cal,
                )
                if ctx.divergence_signal.role_repricing_warnings:
                    n = len(ctx.divergence_signal.role_repricing_warnings)
                    self._prog(f"  ⚠ RoleRepricingDivergence: {n} instrument(s) flagged")
            except Exception as e:
                ctx.signal_flags.append(f"⚠ RoleRepricingDivergence failed: {e}")
        elif not ctx.holdings_30d_returns:
            ctx.signal_flags.append(
                "⚠ RoleRepricingDivergence skipped — no holdings_30d_returns provided. "
                "In the Claude orchestrator path, populate ctx.holdings_30d_returns "
                "from the allocation sheet (GOOGLEFINANCE period returns) before Step 4."
            )

        try:
            ctx.cascade_signal     = assess_cascade_level(readings, cal, ctx.credit_signal)
            ctx.yield_curve_signal = ctx.cascade_signal.yield_curve
        except Exception as e:
            ctx.signal_flags.append(f"⚠ CascadeSignal/YieldCurve failed: {e}")

        # Build summary line
        cs_summary = "n/a"
        if ctx.credit_signal:
            cs = ctx.credit_signal
            cs_summary = f"HY={cs.hy_oas}bps IG={cs.ig_oas}bps"
        yc_summary = "n/a"
        if ctx.yield_curve_signal:
            yc = ctx.yield_curve_signal
            yc_summary = f"10Y-2Y={_fmt_bps(yc.spread_10y_2y)} {yc.e_pathway_type.value}"
        cc_summary = f"Cascade={ctx.cascade_signal.level.value}" if ctx.cascade_signal else "n/a"
        self._prog(f"Step 4/8  Credit: {cs_summary} | {yc_summary} | {cc_summary}", done=True)

    # ── Step 5: AI Call 2 — Scenario scoring → probabilities ─────────────────

    def _step5_derive_probabilities(self, ctx: SessionContext) -> None:
        """Scoring questions → AI Call 2 → raw scores → apply_all_rules() → ScenarioProbabilities."""
        logger.info("Step 5: AI Call 2 — scenario scoring")

        ctx.scoring_questions = generate_questions(
            ctx.readings, ctx.cal, ctx.credit_signal, ctx.qualitative
        )
        ai_qs     = questions_for_ai(ctx.scoring_questions)
        auto_count = len(ctx.scoring_questions) - len(ai_qs)

        self._prog(
            f"Step 5/8  AI Call 2: scoring {len(ai_qs)} qualitative checks "
            f"({auto_count} auto-scored by Python) ..."
        )

        ctx.scoring_answers = self.ai.answer_scoring(ai_qs) if ai_qs else \
            ScoringAnswers(answers={}, reasoning={})

        ctx.raw_scores = aggregate_raw_scores(ctx.scoring_answers, ctx.scoring_questions)

        prior = ctx.log.latest_probs if ctx.log else None
        hy_recession = ctx.credit_signal.hy_recession_pricing if ctx.credit_signal else False
        ctx.scenario_probs, ctx.prob_flags = apply_all_rules(
            ctx.raw_scores, prior, hy_recession_pricing_fired=hy_recession
        )

        p = ctx.scenario_probs
        self._prog(
            f"Step 5/8  Probabilities: "
            f"A={p.A:.0f}% B={p.B:.0f}% C={p.C:.0f}% D={p.D:.0f}% E={p.E:.0f}% F={p.F:.0f}%",
            done=True,
        )
        for flag in ctx.prob_flags:
            if "cap applied" in flag:
                self._prog(f"  ⚑ {flag[:120]}")

    # ── Step 6: Portfolio math ─────────────────────────────────────────────────

    def _step6_portfolio_math(self, ctx: SessionContext) -> None:
        """Stage 4 portfolio math (requires allocation sheet account profiles)."""
        if not ctx.has_probs or ctx.cal is None:
            self._prog("Step 6/8  Portfolio math skipped (no probabilities)", done=True)
            ctx.portfolio_flags.append("Portfolio math skipped — probabilities unavailable.")
            return

        self._prog("Step 6/8  Portfolio math ...")
        logger.info("Step 6: Portfolio math")
        ctx.portfolio_flags.append(
            "ℹ Portfolio math: AllocationTarget computation requires account profiles "
            "from Allocation sheet 'Objectives' tab. Run `advisor session --with-allocation` "
            "when Google credentials are available for full Stage 4 integration."
        )
        self._prog("Step 6/8  Portfolio math: allocation sheet not loaded (needs Google creds)", done=True)

    # ── Step 7: AI Call 3 — Briefing generation ────────────────────────────────

    def _step7_generate_briefing(self, ctx: SessionContext) -> None:
        """AI Call 3 — M04 Intelligence Briefing narrative."""
        self._prog("Step 7/8  AI Call 3: generating M04 briefing (may take 30-60s) ...")
        logger.info("Step 7: AI Call 3 — briefing generation")
        context_summary = self._render_briefing_context(ctx)
        self._prog(f"  Context: {len(context_summary)} chars (~{len(context_summary)//4} tokens)")
        ctx.briefing, ctx.open_triggers, ctx.open_decisions = (
            self.ai.generate_briefing(context_summary)
        )
        if not ctx.open_triggers and not ctx.open_decisions:
            ctx.write_back_flags.append(
                "⚠ AI Call 3 did not return a parseable OPEN_ITEMS trailer — "
                "open_triggers/open_decisions empty this session (ENG-4)."
            )
        self._prog("Step 7/8  Briefing ready", done=True)

    def _render_briefing_context(self, ctx: SessionContext) -> str:
        """Serialize all computed state into a compact briefing context for AI Call 3."""
        lines: List[str] = []

        lines.append(f"SESSION DATE: {ctx.session_date}")
        if ctx.cal:
            lines.append(f"CALIBRATION: v{ctx.cal.version} ({ctx.cal.last_updated})")
        if ctx.log and ctx.log.latest_probs:
            p = ctx.log.latest_probs
            lines.append(f"PRIOR PROBS: A={p.A} B={p.B} C={p.C} D={p.D} E={p.E} F={p.F}")

        # ── Market data — only briefing-relevant series ────────────────────────
        _SKIP = {"DOW", "KBE", "NASDAQ_COMP", "RUSSELL2000", "WTI", "HISTORICAL_INSTRUMENT_PRICES"}
        lines.append("\nMARKET DATA:")
        holdings_lines: List[str] = []
        for r in ctx.readings:
            if not r.is_valid:
                continue
            spec = r.spec_id
            if spec in _SKIP:
                continue
            v = r.value
            if spec.startswith("HOLDINGS_PRICES:"):
                ticker = spec.split(":", 1)[1]
                if isinstance(v, dict):
                    holdings_lines.append(
                        f"  {ticker}: ${v.get('price','?')} ({v.get('day_change_pct','?'):+.2f}%)"
                        if isinstance(v.get('day_change_pct'), (int, float))
                        else f"  {ticker}: {v.get('price','?')}"
                    )
            else:
                if isinstance(v, dict):
                    # Compact: drop prev_close and symbol noise
                    compact = {k: (round(val, 2) if isinstance(val, float) else val)
                               for k, val in v.items()
                               if k not in ("symbol", "source_note", "prev_close")}
                    lines.append(f"  {spec}: {compact}")
                elif v is not None:
                    lines.append(f"  {spec}: {v}")
        if holdings_lines:
            lines.append("  HOLDINGS (price, day%chg):")
            lines.extend(holdings_lines)

        # ── Qualitative intel — capped per topic ──────────────────────────────
        if ctx.qualitative:
            lines.append("\nQUALITATIVE INTEL:")
            for topic, summary in ctx.qualitative.items():
                text = summary[:300] if len(summary) > 300 else summary
                lines.append(f"  {topic.upper()}: {text}")

        # ── Signals ────────────────────────────────────────────────────────────
        if ctx.credit_signal:
            cs = ctx.credit_signal
            lines.append(f"\nCREDIT: HY={cs.hy_oas}bps IG={cs.ig_oas}bps CCC={cs.ccc_oas}bps "
                         f"| stress={cs.hy_stress_beginning} recession={cs.hy_recession_pricing} "
                         f"ig_tx={cs.ig_transmission_reached}")
            lines.append(f"  → {cs.convergence_text}")

        if ctx.divergence_signal:
            ds = ctx.divergence_signal
            lines.append(f"\nREGIME: commodity_fear={ds.commodity_fear_divergence.value} "
                         f"equity={ds.equity_scenario_divergence.value} "
                         f"composite={ds.composite.value}")

        if ctx.yield_curve_signal:
            yc = ctx.yield_curve_signal
            lines.append(f"\nYIELD CURVE: 10Y-2Y={_fmt_bps(yc.spread_10y_2y)} "
                         f"10Y-3M={_fmt_bps(yc.spread_10y_3m)} "
                         f"D_timing={yc.d_timing_signal.value} "
                         f"E_watch={yc.e_watch_flag.value} "
                         f"e_pathway={yc.e_pathway_type.value}")

        if ctx.cascade_signal:
            cc = ctx.cascade_signal
            fires = [k for k, v in cc.chain_fires.items() if v]
            watch = [k for k, v in cc.chain_watch.items() if v]
            lines.append(f"\nCASCADE: {cc.level.value} | score={cc.sector_stress_score}"
                         + (f" | fires={fires}" if fires else "")
                         + (f" | watch={watch}" if watch else ""))

        # ── Scenario probabilities ─────────────────────────────────────────────
        if ctx.scenario_probs:
            p = ctx.scenario_probs
            lines.append(f"\nSCENARIO PROBS: A={p.A:.1f}% B={p.B:.1f}% C={p.C:.1f}% "
                         f"D={p.D:.1f}% E={p.E:.1f}% F={p.F:.1f}%")
        if ctx.raw_scores:
            rs = ctx.raw_scores
            lines.append(f"RAW SCORES: A={rs.A} B={rs.B} C={rs.C} D={rs.D} E={rs.E} F={rs.F}")
        if ctx.scoring_answers and ctx.scoring_answers.reasoning:
            lines.append("SCORING REASONING:")
            for qid, reason in ctx.scoring_answers.reasoning.items():
                lines.append(f"  {qid}: {reason[:120]}")

        # ── Prior session state ────────────────────────────────────────────────
        if ctx.log and ctx.log.scenario_states:
            latest = ctx.log.scenario_states[-1]
            lines.append(f"\nPRIOR SESSION: driver={latest.primary_driver}")
            if latest.open_triggers:
                lines.append(f"  Open triggers: {latest.open_triggers}")
            if latest.open_decisions:
                lines.append(f"  Open decisions: {latest.open_decisions}")

        # ── Flags ──────────────────────────────────────────────────────────────
        notable = [f for f in ctx.prob_flags + ctx.signal_flags
                   if "cap applied" in f or "HARD_STOP" in f]
        if notable:
            lines.append("\nKEY FLAGS:")
            for f in notable[:6]:
                lines.append(f"  {f[:150]}")

        return "\n".join(lines)

    # ── Step 8: Write-back ────────────────────────────────────────────────────

    def _step8_write_back(self, ctx: SessionContext) -> None:
        """M05 Step 10: Write-back (FULL_DESKTOP only, dry_run=False only)."""
        if self.dry_run:
            ctx.write_back_flags.append("Write-back skipped: dry_run=True")
            self._prog("Step 8/8  Write-back skipped (dry_run)", done=True)
            return
        if self.session_type != SessionType.FULL_DESKTOP:
            ctx.write_back_flags.append("Write-back skipped: READONLY_MOBILE session")
            self._prog("Step 8/8  Write-back skipped (READONLY_MOBILE)", done=True)
            return
        if not ctx.has_probs:
            ctx.write_back_flags.append(
                "Write-back skipped: scenario probabilities not derived."
            )
            self._prog("Step 8/8  Write-back skipped (no probabilities)", done=True)
            return

        self._prog("Step 8/8  Writing back to git ...")
        logger.info("Step 8: Write-back")

        # §8 entry + Portfolio_State.md rendering: shared with mcp_server.py
        # (Pattern B) via rendering.py -- see ENG-3 (deduplication of the two
        # session pipelines). Primary driver derivation below is Pattern-A-only
        # (Pattern B gets primary_driver directly from Claude as a parameter).
        primary_driver = "derived via SessionPipeline (Pattern A)"
        if ctx.divergence_signal:
            primary_driver = f"composite regime: {ctx.divergence_signal.composite.value}"

        log_text = read_session_log()
        cal_version = ctx.cal.version if ctx.cal else "N/A"

        portfolio_state = render_portfolio_state(
            cal_version, ctx.scenario_probs, ctx.session_date, primary_driver,
            ctx.open_triggers, ctx.open_decisions,
            generator_label="SessionPipeline (Pattern A)",
        )

        # ENG-4: open_triggers/open_decisions now come from generate_briefing()'s
        # OPEN_ITEMS trailer (ctx.open_triggers/open_decisions) -- no more
        # hardcoded "[review session briefing]" placeholders. next_session_flags
        # uses ctx.prob_flags, matching this pipeline's pre-existing choice of
        # what belongs in that field.
        new_entry = build_session_log_entry(
            ctx.session_date, ctx.session_type.value, ctx.scenario_probs,
            primary_driver, ctx.open_triggers, ctx.open_decisions, ctx.prob_flags,
        )
        log_text = mark_prior_entries_superseded(log_text, ctx.session_date)
        updated_log = log_text.rstrip() + new_entry

        try:
            sha = write_back(
                calibration_state=None,
                session_log=updated_log,
                portfolio_state=portfolio_state,
                session_type=self.session_type,
                dry_run=False,
            )
            ctx.write_back_commit = sha
            self._prog(f"Step 8/8  Write-back committed: {sha}", done=True)
            logger.info(f"Write-back complete: {sha}")
        except Exception as e:
            ctx.write_back_flags.append(f"⚠ Write-back failed: {e}")
            self._prog(f"Step 8/8  Write-back FAILED: {e}")
            logger.error(f"Write-back failed: {e}")
