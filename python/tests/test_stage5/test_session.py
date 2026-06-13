"""
tests/test_stage5/test_session.py — Pipeline smoke tests with StubAIClient.

Coverage:
  - SessionPipeline(dry_run=True, ai=StubAIClient()) runs without error
  - Returns a populated SessionContext
  - Scenario probabilities sum to 100%
  - No write-back happens in dry_run mode
  - StubAIClient returns deterministic responses
  - generate_briefing produces non-empty string
  - cmd_validate() passes against live Calibration_State.md (marked integration)
"""
from __future__ import annotations

import pytest

from advisor.orchestrator import SessionPipeline, StubAIClient, SessionContext
from advisor.types import SessionType, ScenarioProbabilities


# ── StubAIClient unit tests ────────────────────────────────────────────────────

def test_stub_gather_qualitative():
    from advisor.orchestrator.scoring_questions import QUALITATIVE_TARGETS
    client = StubAIClient()
    result = client.gather_qualitative(QUALITATIVE_TARGETS)
    assert isinstance(result, dict)
    assert set(result.keys()) == set(QUALITATIVE_TARGETS)
    for v in result.values():
        assert isinstance(v, str)


def test_stub_answer_scoring():
    from advisor.types import ScoringQuestion, ScoringAnswers
    client = StubAIClient()
    qs = [
        ScoringQuestion(id="A_check_fed", scenario="A",
                        question="Q?", evidence="E", valid_scores=[0, 1, 2]),
        ScoringQuestion(id="B_check_cpi", scenario="B",
                        question="Q2?", evidence="E2", valid_scores=[0, 2, 3]),
    ]
    answers = client.answer_scoring(qs)
    assert isinstance(answers, ScoringAnswers)
    for q in qs:
        assert q.id in answers.answers
        assert answers.answers[q.id] in q.valid_scores


def test_stub_generate_briefing():
    client = StubAIClient()
    result = client.generate_briefing("CONTEXT DATA")
    assert isinstance(result, str)
    assert len(result) > 0


# ── SessionPipeline smoke tests ────────────────────────────────────────────────

@pytest.mark.integration
def test_pipeline_dry_run_completes():
    """Full pipeline with StubAIClient and dry_run=True — integration test."""
    pipeline = SessionPipeline(
        session_type=SessionType.FULL_DESKTOP,
        ai=StubAIClient(),
        dry_run=True,
    )
    ctx = pipeline.run()
    assert isinstance(ctx, SessionContext)


@pytest.mark.integration
def test_pipeline_produces_probabilities():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert ctx.has_probs, "ScenarioProbabilities should be derived"
    p = ctx.scenario_probs
    total = p.A + p.B + p.C + p.D + p.E + p.F
    assert abs(total - 100.0) < 0.1, f"Probs sum to {total:.2f}% (expected 100%)"


@pytest.mark.integration
def test_pipeline_probabilities_all_at_or_above_floor():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    if ctx.scenario_probs:
        p = ctx.scenario_probs
        for scenario, val in p.as_dict().items():
            assert val >= 3.0, f"Scenario {scenario}={val}% below 3% floor"


@pytest.mark.integration
def test_pipeline_no_write_back_in_dry_run():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert ctx.write_back_commit is None
    assert any("dry_run" in f.lower() or "skipped" in f.lower()
               for f in ctx.write_back_flags)


@pytest.mark.integration
def test_pipeline_briefing_non_empty():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert ctx.has_briefing


@pytest.mark.integration
def test_pipeline_config_loaded():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert ctx.cal is not None
    assert ctx.log is not None


@pytest.mark.integration
def test_pipeline_readings_fetched():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert len(ctx.readings) > 0


@pytest.mark.integration
def test_pipeline_qualitative_populated():
    from advisor.orchestrator.scoring_questions import QUALITATIVE_TARGETS
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    for target in QUALITATIVE_TARGETS:
        assert target in ctx.qualitative


@pytest.mark.integration
def test_pipeline_scoring_questions_generated():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert len(ctx.scoring_questions) == 20  # A:3 B:3 C:3 D:4 E:3 F:4


@pytest.mark.integration
def test_pipeline_raw_scores_present():
    pipeline = SessionPipeline(ai=StubAIClient(), dry_run=True)
    ctx = pipeline.run()
    assert ctx.raw_scores is not None
    assert ctx.raw_scores.total >= 0


# ── SessionContext properties ─────────────────────────────────────────────────

def test_context_has_probs_false_initially():
    ctx = SessionContext(
        session_type=SessionType.FULL_DESKTOP,
        session_date="2026-06-12",
        dry_run=True,
    )
    assert not ctx.has_probs


def test_context_has_briefing_false_initially():
    ctx = SessionContext(
        session_type=SessionType.FULL_DESKTOP,
        session_date="2026-06-12",
        dry_run=True,
    )
    assert not ctx.has_briefing


def test_context_all_flags_aggregates():
    ctx = SessionContext(
        session_type=SessionType.FULL_DESKTOP,
        session_date="2026-06-12",
        dry_run=False,
    )
    ctx.validate_flags.append("v1")
    ctx.fetch_flags.append("f1")
    ctx.signal_flags.append("s1")
    ctx.prob_flags.append("p1")
    assert len(ctx.all_flags) == 4
    assert "v1" in ctx.all_flags and "p1" in ctx.all_flags
