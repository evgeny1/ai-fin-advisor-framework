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
from typing import Dict, List, Optional

from ..analysis import (
    assess_cascade_level,
    compute_credit_signal,
    compute_divergence_signal,
    validate_classifications,
    blended_scenario_return,
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
    SessionType,
)
from .ai_client import AIClient, StubAIClient
from .context import SessionContext
from .scoring_questions import (
    QUALITATIVE_TARGETS,
    aggregate_raw_scores,
    generate_questions,
    questions_for_ai,
)

logger = logging.getLogger(__name__)


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

    def run(self) -> SessionContext:
        """Execute full M05 pipeline. Returns populated SessionContext."""
        ctx = SessionContext(
            session_type=self.session_type,
            session_date=datetime.date.today().isoformat(),
            dry_run=self.dry_run,
        )

        self._step1_load_config(ctx)
        self._step2_fetch_market_data(ctx)
        self._step3_gather_qualitative(ctx)
        self._step4_compute_signals(ctx)
        self._step5_derive_probabilities(ctx)
        self._step6_portfolio_math(ctx)
        self._step7_generate_briefing(ctx)
        self._step8_write_back(ctx)

        return ctx

    # ── Step 1: Load config ────────────────────────────────────────────────────

    def _step1_load_config(self, ctx: SessionContext) -> None:
        """
        M05 Steps 1+3: Read Calibration_State.md + Session_Log.md.
        Parse into typed CalibrationState + SessionLogState.
        Run ValidateClassifications — HARD_STOP if any allocation ticker absent.
        """
        logger.info("Step 1: Loading framework config")

        cal_text = read_calibration_state()
        log_text = read_session_log()

        ctx.cal = parse_calibration_state(cal_text)
        ctx.log = parse_session_log(log_text)

        logger.info(
            f"Calibration_State v{ctx.cal.version} loaded | "
            f"Session_Log loaded ({len(ctx.log.scenario_states)} §8 entries)"
        )

        # ValidateClassifications — check §11 coverage for all active instruments
        allocation_tickers = [
            t for t, e in ctx.cal.instruments.items()
            if not e.is_candidate
        ]
        try:
            warnings = validate_classifications(allocation_tickers, ctx.cal)
            ctx.validate_flags.extend(warnings)
        except HardStopException as e:
            raise  # propagate hard-stop — session cannot proceed

    # ── Step 2: Fetch market data ──────────────────────────────────────────────

    def _step2_fetch_market_data(self, ctx: SessionContext) -> None:
        """
        M05 Step 4: FetchRegistry.fetch_all() — all M18 registered FetchSpecs.
        """
        logger.info("Step 2: Fetching market data")

        registry = FetchRegistry()
        register_all(registry)

        # Register yfinance fetcher (always available)
        from ..data.fetchers import yfinance_fetcher as yf
        registry.register_fetcher(DataSource.YFINANCE, yf.yfinance_dispatcher)

        # Register FRED REST fetcher (requires FRED_API_KEY — free from fred.stlouisfed.org)
        # Handles: YIELD_CURVE, SOFR, DFF, THREEFYTP10, HY_OAS, IG_OAS, CCC_OAS, BBB_OAS
        try:
            from ..data.fetchers import fred_fetcher as fred
            registry.register_fetcher(DataSource.FRED_SPREADSHEET_TAB, fred.fetch_yield_curve_fred)
        except Exception as e:
            ctx.fetch_flags.append(f"⚠ FRED fetcher not registered: {e} — credit spreads unavailable")

        ctx.readings = registry.fetch_all()

        valid   = sum(1 for r in ctx.readings if r.is_valid)
        flagged = len(ctx.readings) - valid
        logger.info(f"Fetched {len(ctx.readings)} readings: {valid} valid, {flagged} flagged")

        if flagged:
            ctx.fetch_flags.append(
                f"⚠ {flagged} data readings flagged — review quality_flags in readings."
            )

    # ── Step 3: AI Call 1 — Qualitative gather ────────────────────────────────

    def _step3_gather_qualitative(self, ctx: SessionContext) -> None:
        """
        AI Call 1 — M02 QUALITATIVE_GATHER_LIST.
        AI researches geopolitical, Fed guidance, CPI, GDP, labor, dollar reserve.
        """
        logger.info("Step 3: AI Call 1 — qualitative gather")

        # Build brief market summary for context
        brent_reading = next(
            (r for r in ctx.readings if r.spec_id == "BRENT_CRUDE" and r.is_valid), None
        )
        hy_reading = next(
            (r for r in ctx.readings if r.spec_id == "HY_OAS" and r.is_valid), None
        )
        summary_parts = []
        if brent_reading:
            b = brent_reading.value
            price = b.get("current") if isinstance(b, dict) else b
            if price:
                summary_parts.append(f"Brent ${price:.1f}/bbl")
        if hy_reading:
            h = hy_reading.value
            hy_val = h.get("current") if isinstance(h, dict) else h
            if hy_val:
                summary_parts.append(f"HY OAS {hy_val:.0f}bps")
        market_summary = "; ".join(summary_parts) if summary_parts else "market data fetched"

        ctx.qualitative = self.ai.gather_qualitative(QUALITATIVE_TARGETS, market_summary)
        logger.info(f"Qualitative gather complete: {len(ctx.qualitative)} topics")

    # ── Step 4: Compute analysis signals ──────────────────────────────────────

    def _step4_compute_signals(self, ctx: SessionContext) -> None:
        """
        Stage 3 signals: CreditSignal, DivergenceSignal, CascadeSignal, YieldCurveSignal.
        All pure Python — zero AI tokens.
        """
        logger.info("Step 4: Computing analysis signals")
        cal = ctx.cal

        # Analysis functions expect Dict[spec_id, DataReading]; convert from list.
        # HOLDINGS_PRICES:TICKER readings are included under their full key.
        readings = {r.spec_id: r for r in ctx.readings}

        try:
            ctx.credit_signal = compute_credit_signal(readings, cal)
        except Exception as e:
            ctx.signal_flags.append(f"⚠ CreditSignal failed: {e}")
            logger.warning(f"CreditSignal failed: {e}")

        try:
            ctx.divergence_signal = compute_divergence_signal(readings, cal)
        except Exception as e:
            ctx.signal_flags.append(f"⚠ DivergenceSignal failed: {e}")

        try:
            ctx.cascade_signal = assess_cascade_level(
                readings, cal, ctx.credit_signal
            )
            ctx.yield_curve_signal = ctx.cascade_signal.yield_curve
        except Exception as e:
            ctx.signal_flags.append(f"⚠ CascadeSignal/YieldCurve failed: {e}")

        logger.info("Signals computed")

    # ── Step 5: AI Call 2 — Scenario scoring → probabilities ─────────────────

    def _step5_derive_probabilities(self, ctx: SessionContext) -> None:
        """
        Generates ScoringQuestions, calls AI for qualitative answers,
        aggregates raw scores, runs apply_all_rules() → ScenarioProbabilities.
        """
        logger.info("Step 5: AI Call 2 — scenario scoring")

        # Generate all questions (some auto-scored by Python)
        ctx.scoring_questions = generate_questions(
            ctx.readings, ctx.cal, ctx.credit_signal, ctx.qualitative
        )

        ai_qs = questions_for_ai(ctx.scoring_questions)
        auto_count = len(ctx.scoring_questions) - len(ai_qs)
        logger.info(f"Scoring: {len(ctx.scoring_questions)} checks total "
                    f"({auto_count} auto-scored, {len(ai_qs)} to AI)")

        if ai_qs:
            ai_answers = self.ai.answer_scoring(ai_qs)
        else:
            from ..types import ScoringAnswers
            ai_answers = ScoringAnswers(answers={}, reasoning={})

        ctx.scoring_answers = ai_answers

        # Aggregate auto + AI scores → RawScores
        ctx.raw_scores = aggregate_raw_scores(ai_answers, ctx.scoring_questions)

        # Run M03 arithmetic pipeline
        prior = ctx.log.latest_probs if ctx.log else None
        hy_recession = (
            ctx.credit_signal.hy_recession_pricing
            if ctx.credit_signal else False
        )
        ctx.scenario_probs, ctx.prob_flags = apply_all_rules(
            ctx.raw_scores, prior,
            hy_recession_pricing_fired=hy_recession,
        )

        p = ctx.scenario_probs
        logger.info(
            f"Probabilities: A={p.A:.0f}% B={p.B:.0f}% C={p.C:.0f}% "
            f"D={p.D:.0f}% E={p.E:.0f}% F={p.F:.0f}%"
        )

    # ── Step 6: Portfolio math ─────────────────────────────────────────────────

    def _step6_portfolio_math(self, ctx: SessionContext) -> None:
        """
        Stage 4 portfolio math: scenarioWeightedAllocation + FeasibilityCheck
        for each active account in Calibration_State §11.
        Skipped when probs are unavailable.
        """
        if not ctx.has_probs or ctx.cal is None:
            ctx.portfolio_flags.append(
                "Portfolio math skipped — probabilities or calibration not available."
            )
            return

        logger.info("Step 6: Portfolio math")

        # Build account profiles from Calibration_State
        # In Pattern A, account profiles come from the allocation sheet.
        # For now, emit a flag and skip — full portfolio math requires live sheet data.
        ctx.portfolio_flags.append(
            "ℹ Portfolio math: AllocationTarget computation requires account profiles "
            "from Allocation sheet 'Objectives' tab. Run `advisor session --with-allocation` "
            "when Google credentials are available for full Stage 4 integration."
        )

    # ── Step 7: AI Call 3 — Briefing generation ────────────────────────────────

    def _step7_generate_briefing(self, ctx: SessionContext) -> None:
        """
        AI Call 3 — M04 Intelligence Briefing narrative.
        Pre-renders all computed signals/probabilities into a context block,
        then calls AI to produce the M04-ordered briefing text.
        """
        logger.info("Step 7: AI Call 3 — briefing generation")
        context_summary = self._render_briefing_context(ctx)
        ctx.briefing = self.ai.generate_briefing(context_summary)
        logger.info("Briefing generated")

    def _render_briefing_context(self, ctx: SessionContext) -> str:
        """Serialize all computed state into a briefing context string for AI Call 3."""
        lines: List[str] = []

        lines.append(f"SESSION DATE: {ctx.session_date}")
        if ctx.cal:
            lines.append(f"CALIBRATION STATE: v{ctx.cal.version} last updated {ctx.cal.last_updated}")
        if ctx.log and ctx.log.latest_probs:
            p = ctx.log.latest_probs
            lines.append(f"PRIOR PROBABILITIES (§8): A={p.A} B={p.B} C={p.C} D={p.D} E={p.E} F={p.F}")

        lines.append("\n--- MARKET DATA ---")
        for r in ctx.readings:
            if r.is_valid and r.spec_id not in ("HISTORICAL_INSTRUMENT_PRICES",):
                val = r.value
                if isinstance(val, dict):
                    val = {k: round(v, 4) if isinstance(v, float) else v
                           for k, v in list(val.items())[:5]}
                lines.append(f"  {r.spec_id}: {val}")

        lines.append("\n--- QUALITATIVE INTEL ---")
        for topic, summary in ctx.qualitative.items():
            lines.append(f"  {topic.upper()}: {summary}")

        if ctx.credit_signal:
            cs = ctx.credit_signal
            lines.append("\n--- CREDIT SIGNAL ---")
            lines.append(f"  HY OAS: {cs.hy_oas} | IG OAS: {cs.ig_oas} | CCC OAS: {cs.ccc_oas}")
            lines.append(f"  HY_stress: {cs.hy_stress_beginning} | HY_recession: {cs.hy_recession_pricing}")
            lines.append(f"  IG_transmission: {cs.ig_transmission_reached}")
            lines.append(f"  Convergence: {cs.convergence_text}")

        if ctx.divergence_signal:
            ds = ctx.divergence_signal
            lines.append("\n--- MARKET REGIME (M14) ---")
            lines.append(f"  Commodity fear: {ds.commodity_fear_divergence.value}")
            lines.append(f"  Equity divergence: {ds.equity_scenario_divergence.value}")
            lines.append(f"  Composite: {ds.composite.value}")

        if ctx.yield_curve_signal:
            yc = ctx.yield_curve_signal
            lines.append("\n--- YIELD CURVE / SCENARIO E WATCH ---")
            lines.append(f"  10Y-2Y: {yc.spread_10y_2y}bps | 10Y-3M: {yc.spread_10y_3m}bps")
            lines.append(f"  D_timing: {yc.d_timing_signal.value} | E_watch: {yc.e_watch_flag.value}")
            lines.append(f"  e_pathway_type: {yc.e_pathway_type.value}")

        if ctx.cascade_signal:
            cc = ctx.cascade_signal
            lines.append("\n--- CASCADE EARLY WARNING (M17) ---")
            lines.append(f"  Level: {cc.level.value} | SectorStressScore: {cc.sector_stress_score}")
            fires = [k for k, v in cc.chain_fires.items() if v]
            watch = [k for k, v in cc.chain_watch.items() if v]
            if fires:
                lines.append(f"  Fired chains: {fires}")
            if watch:
                lines.append(f"  Watch chains: {watch}")

        if ctx.scenario_probs:
            p = ctx.scenario_probs
            lines.append("\n--- SCENARIO PROBABILITIES ---")
            lines.append(f"  A={p.A:.1f}% B={p.B:.1f}% C={p.C:.1f}% D={p.D:.1f}% E={p.E:.1f}% F={p.F:.1f}%")

        if ctx.raw_scores:
            rs = ctx.raw_scores
            lines.append(f"  Raw scores: A={rs.A} B={rs.B} C={rs.C} D={rs.D} E={rs.E} F={rs.F}")

        if ctx.scoring_answers and ctx.scoring_answers.reasoning:
            lines.append("\n--- SCORING REASONING ---")
            for qid, reason in ctx.scoring_answers.reasoning.items():
                lines.append(f"  {qid}: {reason}")

        if ctx.prob_flags:
            lines.append("\n--- PROBABILITY FLAGS ---")
            for f in ctx.prob_flags:
                lines.append(f"  {f}")

        if ctx.log and ctx.log.scenario_states:
            latest = ctx.log.scenario_states[-1]
            lines.append("\n--- PRIOR SESSION STATE ---")
            lines.append(f"  Primary driver: {latest.primary_driver}")
            if latest.open_triggers:
                lines.append(f"  Open triggers: {latest.open_triggers}")
            if latest.open_decisions:
                lines.append(f"  Open decisions: {latest.open_decisions}")
            if latest.next_session_flags:
                lines.append(f"  Next-session flags: {latest.next_session_flags}")

        if ctx.all_flags:
            lines.append("\n--- SESSION FLAGS ---")
            for f in ctx.all_flags:
                lines.append(f"  {f}")

        return "\n".join(lines)

    # ── Step 8: Write-back ────────────────────────────────────────────────────

    def _step8_write_back(self, ctx: SessionContext) -> None:
        """
        M05 Step 10: Write-back Calibration_State.md, Session_Log.md, Portfolio_State.md.
        Only executes in FULL_DESKTOP mode and when dry_run=False.
        """
        if self.dry_run:
            ctx.write_back_flags.append("Write-back skipped: dry_run=True")
            return
        if self.session_type != SessionType.FULL_DESKTOP:
            ctx.write_back_flags.append("Write-back skipped: READONLY_MOBILE session")
            return
        if not ctx.has_probs:
            ctx.write_back_flags.append(
                "Write-back skipped: scenario probabilities not derived — "
                "cannot write §8 without valid probability vector."
            )
            return

        logger.info("Step 8: Write-back")

        # Read current file texts to modify §8
        cal_text    = read_calibration_state()
        log_text    = read_session_log()
        portfolio_state = self._render_portfolio_state(ctx)

        # Append new §8 entry to Session_Log.md
        updated_log = self._append_session_log_entry(log_text, ctx)

        try:
            sha = write_back(
                calibration_state=None,   # unchanged this session
                session_log=updated_log,
                portfolio_state=portfolio_state,
                session_type=self.session_type,
                dry_run=False,
            )
            ctx.write_back_commit = sha
            logger.info(f"Write-back complete: {sha}")
        except Exception as e:
            ctx.write_back_flags.append(f"⚠ Write-back failed: {e}")
            logger.error(f"Write-back failed: {e}")

    def _render_portfolio_state(self, ctx: SessionContext) -> str:
        """Render Portfolio_State.md content for write-back."""
        p = ctx.scenario_probs
        prob_str = (
            f"A={p.A:.0f}% / B={p.B:.0f}% / C={p.C:.0f}% / "
            f"D={p.D:.0f}% / E={p.E:.0f}% / F={p.F:.0f}%"
            if p else "pending"
        )
        lines = [
            f"# Portfolio State — {ctx.session_date}",
            "",
            f"**Session type:** {ctx.session_type.value}",
            f"**Calibration State:** {ctx.cal.version if ctx.cal else 'N/A'}",
            f"**Scenario probabilities:** {prob_str}",
            "",
            "## Session flags",
            "",
        ]
        for flag in ctx.all_flags:
            lines.append(f"- {flag}")
        if not ctx.all_flags:
            lines.append("_No flags this session._")
        lines += ["", "_Generated by SessionPipeline (Pattern A)._"]
        return "\n".join(lines)

    def _append_session_log_entry(self, log_text: str, ctx: SessionContext) -> str:
        """Append §8 session state block to Session_Log.md content."""
        p = ctx.scenario_probs
        if p is None:
            return log_text  # safety guard — caller already checked

        prob_str = (
            f"A={p.A:.0f} / B={p.B:.0f} / C={p.C:.0f} / "
            f"D={p.D:.0f} / E={p.E:.0f} / F={p.F:.0f}"
        )

        # Identify primary driver from qualitative or signals
        primary_driver = "derived via SessionPipeline (Pattern A)"
        if ctx.divergence_signal:
            primary_driver = f"composite regime: {ctx.divergence_signal.composite.value}"

        new_entry = (
            f"\n\n### §8 Entry — {ctx.session_date}\n"
            f"**Probabilities:** {prob_str}\n"
            f"**Primary driver:** {primary_driver}\n"
            f"**Open triggers:** [review session briefing]\n"
            f"**Open decisions:** [review session briefing]\n"
            f"**Next session flags:** {ctx.prob_flags}\n"
        )
        return log_text + new_entry
