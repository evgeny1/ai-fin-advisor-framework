"""
orchestrator/ — ORCHESTRATION: SessionPipeline + AIClient (Stage 5).

Public API:

  from advisor.orchestrator import SessionPipeline, AIClient, StubAIClient, SessionContext
  from advisor.orchestrator.scoring_questions import QUALITATIVE_TARGETS, generate_questions

Usage:
    # Live session (requires ANTHROPIC_API_KEY):
    ctx = SessionPipeline(ai=AIClient()).run()
    print(ctx.briefing)

    # Offline / test:
    ctx = SessionPipeline(ai=StubAIClient(), dry_run=True).run()

    # Dry-run (no write-back):
    ctx = SessionPipeline(ai=AIClient(), dry_run=True).run()
"""
from .context import SessionContext
from .ai_client import AIClient, StubAIClient
from .session import SessionPipeline
from .scoring_questions import QUALITATIVE_TARGETS, generate_questions, aggregate_raw_scores

__all__ = [
    "SessionContext",
    "AIClient",
    "StubAIClient",
    "SessionPipeline",
    "QUALITATIVE_TARGETS",
    "generate_questions",
    "aggregate_raw_scores",
]
