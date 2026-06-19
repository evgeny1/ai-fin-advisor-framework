"""
orchestrator/ai_client.py — Three Claude API calls for the Session Pipeline.

AI Call 1: gather_qualitative()   — M02 QUALITATIVE_GATHER_LIST (web search + summarize)
AI Call 2: answer_scoring()       — M03 scoring question answers (integer scores + reasoning)
AI Call 3: generate_briefing()    — M04 intelligence briefing narrative

All calls use claude-sonnet-4-6 (configurable). API key read from ANTHROPIC_API_KEY env var.
Each call uses a focused system prompt so the model knows exactly what to produce.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from ..types import ScoringAnswers, ScoringQuestion

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"
_API_URL       = "https://api.anthropic.com/v1/messages"
_MAX_TOKENS    = 4096


def _recover_partial_json(raw: str) -> Optional[Dict]:
    """
    Attempt to recover a truncated JSON response from answer_scoring.

    Strategy: if the response was cut mid-string (common with token limits),
    try to salvage the 'answers' dict by finding the integer scores before
    the truncation point using a regex scan.

    Returns a dict with at least {"answers": {...}} on success, None on failure.
    """
    import re

    # Strategy 1: close the open JSON object and retry
    for closing in ('}}', '"}}}', '"}}'):
        try:
            return json.loads(raw + closing)
        except (json.JSONDecodeError, ValueError):
            pass

    # Strategy 2: extract "answers" block only via regex
    answers_block = re.search(r'"answers"\s*:\s*(\{[^}]*\})', raw)
    if answers_block:
        try:
            answers = json.loads(answers_block.group(1))
            return {"answers": answers, "reasoning": {}}
        except (json.JSONDecodeError, ValueError):
            pass

    # Strategy 3: scan for "question_id": integer pairs directly
    pairs = re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*(-?\d+)', raw)
    if pairs:
        return {"answers": {k: int(v) for k, v in pairs}, "reasoning": {}}

    return None


_OPEN_ITEMS_MARKER = "###OPEN_ITEMS###"


def _split_open_items(raw: str) -> Tuple[str, List[str], List[str]]:
    """
    Split the AI Call 3 response into (narrative, open_triggers, open_decisions).

    generate_briefing()'s prompt asks the model to append a machine-parseable
    trailer after the human-readable narrative (ENG-4): a literal marker line,
    then OPEN_TRIGGERS: as a bullet list and OPEN_DECISIONS: as a numbered list.
    This keeps the existing 3-AI-call budget — no separate extraction call —
    since the model already has full session context in this same call.

    If the marker is absent (malformed response, or StubAIClient bypassing
    this entirely), returns (raw.strip(), [], []) — caller is responsible for
    flagging the empty result rather than fabricating placeholder content.
    """
    import re

    if _OPEN_ITEMS_MARKER not in raw:
        return raw.strip(), [], []

    narrative, _, trailer = raw.partition(_OPEN_ITEMS_MARKER)

    triggers: List[str] = []
    decisions: List[str] = []

    trig_match = re.search(r"OPEN_TRIGGERS:\s*(.*?)(?:OPEN_DECISIONS:|\Z)", trailer, re.S)
    dec_match  = re.search(r"OPEN_DECISIONS:\s*(.*)", trailer, re.S)

    if trig_match:
        block = trig_match.group(1).strip()
        if block and "_None this session._" not in block:
            triggers = [
                line.lstrip("-* ").strip()
                for line in block.splitlines()
                if line.strip().startswith(("-", "*"))
            ]

    if dec_match:
        block = dec_match.group(1).strip()
        if block and "_None this session._" not in block:
            decisions = [
                re.sub(r"^\d+\.\s*", "", line).strip()
                for line in block.splitlines()
                if re.match(r"^\d+\.", line.strip())
            ]

    return narrative.strip(), triggers, decisions


class AIClient:
    """
    Thin wrapper around the Anthropic messages API.
    Provides the three structured calls used by SessionPipeline.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        api_key: Optional[str] = None,
    ) -> None:
        self.model   = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "ANTHROPIC_API_KEY not set. AI calls will fail. "
                "Set the env var or pass api_key= to AIClient()."
            )

    # ── Call 1: Qualitative Gather ─────────────────────────────────────────────

    def gather_qualitative(
        self,
        targets: List[str],
        market_summary: str = "",
    ) -> Dict[str, str]:
        """
        AI Call 1 — M02 QUALITATIVE_GATHER_LIST.

        Ask the model to research and summarize each qualitative target topic.
        Returns dict[topic → one-paragraph summary].

        Parameters
        ----------
        targets:
            List of topic strings from QUALITATIVE_TARGETS.
        market_summary:
            Short pre-rendered market data context (Brent price, HY OAS, etc.)
            to anchor the model's research queries.
        """
        prompt = (
            "You are an intelligence analyst for a macro investment framework. "
            "Provide a concise, factual 2-3 sentence summary for each topic below, "
            "using your knowledge of current macroeconomic conditions as of today. "
            "For each topic, include the most relevant recent data point or policy signal. "
            "Be specific: cite actual numbers, dates, and sources where known.\n\n"
            f"Market context: {market_summary}\n\n"
            "Topics to research:\n"
            + "\n".join(f"- {t}" for t in targets)
            + "\n\nRespond ONLY with a JSON object where each key is a topic name "
            "and each value is a concise factual summary string. "
            "No preamble, no markdown fences."
        )

        raw = self._call(prompt, max_tokens=1500)
        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return {t: result.get(t, f"{t}: summary unavailable") for t in targets}
        except (json.JSONDecodeError, ValueError):
            logger.warning("gather_qualitative: response was not valid JSON — using raw text")
        # Fallback: return the raw text under each target key
        return {t: raw[:500] for t in targets}

    # ── Call 2: Scenario Scoring ───────────────────────────────────────────────

    def answer_scoring(
        self,
        questions: List[ScoringQuestion],
    ) -> ScoringAnswers:
        """
        AI Call 2 — M03 DeriveScenarioProbabilities (AI side of boundary).

        Receives questions where auto_score is None (qualitative checks).
        Returns ScoringAnswers with integer scores and one-sentence reasoning.

        Parameters
        ----------
        questions:
            Questions from scoring_questions.questions_for_ai() — only the
            non-auto-scored subset.
        """
        if not questions:
            return ScoringAnswers(answers={}, reasoning={})

        # Build compact prompt — keep evidence brief to leave room for response
        question_blocks = []
        for q in questions:
            valid_str = "/".join(str(s) for s in q.valid_scores)
            # Truncate long evidence strings to keep prompt manageable
            evidence = q.evidence[:300] if len(q.evidence) > 300 else q.evidence
            question_blocks.append(
                f"ID: {q.id} | Scenario: {q.scenario} | Scores: [{valid_str}]\n"
                f"Q: {q.question}\n"
                f"Evidence: {evidence}"
            )

        prompt = (
            "You are scoring macro scenario checks for an investment framework (M03).\n"
            "For each question return the integer score from the valid_scores list.\n"
            "Score only from the evidence + current macro knowledge. Conservative if uncertain.\n\n"
            "Questions:\n\n"
            + "\n\n".join(question_blocks)
            + '\n\nReturn ONLY valid JSON — no preamble, no markdown:\n'
            '{"answers":{"ID":score,...},"reasoning":{"ID":"brief rationale",...}}'
        )

        raw = self._call(prompt, max_tokens=_MAX_TOKENS)

        # Primary parse
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            # Truncated response — attempt recovery
            data = _recover_partial_json(raw)
            if data is None:
                logger.error(
                    "answer_scoring: JSON parse failed and recovery unsuccessful — "
                    f"returning zero scores. Raw[:200]: {raw[:200]}"
                )
                return ScoringAnswers(
                    answers={q.id: 0 for q in questions},
                    reasoning={q.id: "parse error — conservative default" for q in questions},
                )

        answers_raw = data.get("answers", {})
        reasoning   = data.get("reasoning", {})
        answers: Dict[str, int] = {}

        for q in questions:
            raw_val = answers_raw.get(q.id)
            if raw_val is not None:
                try:
                    score = int(raw_val)
                    if score in q.valid_scores:
                        answers[q.id] = score
                    else:
                        nearest = min(q.valid_scores, key=lambda x: abs(x - score))
                        logger.warning(
                            f"answer_scoring: {q.id} score {score} not in "
                            f"{q.valid_scores} — clamped to {nearest}"
                        )
                        answers[q.id] = nearest
                except (ValueError, TypeError):
                    logger.warning(f"answer_scoring: {q.id} non-integer — defaulting to 0")
                    answers[q.id] = 0
            else:
                logger.warning(f"answer_scoring: {q.id} missing from response — defaulting to 0")
                answers[q.id] = 0

        return ScoringAnswers(
            answers=answers,
            reasoning={k: str(v) for k, v in reasoning.items()},
        )

    # ── Call 3: Briefing Generation ────────────────────────────────────────────

    def generate_briefing(self, context_summary: str) -> Tuple[str, List[str], List[str]]:
        """
        AI Call 3 — M04 Intelligence Briefing narrative, PLUS open_triggers /
        open_decisions extraction (ENG-4). Same single API call as before —
        the model already has full session context, so the structured trailer
        adds no extra AI-call cost.

        Receives a pre-rendered context summary (all signals, probabilities,
        qualitative findings, portfolio state) and produces the M04 briefing.

        Returns
        -------
        (briefing_narrative, open_triggers, open_decisions)
        """
        prompt = (
            "You are producing an M04 Intelligence Briefing for a structured macro "
            "investment advisory session. Using only the data provided below, "
            "produce a concise briefing. Sections must appear in this order: "
            "PRIMARY_DRIVER → SCENARIO_PROBABILITIES → ENERGY_AND_COMMODITIES → "
            "EQUITY_MARKETS → MARKET_REGIME_SIGNAL → FIXED_INCOME_AND_RATES → "
            "CREDIT_SIGNALS → CASCADE_EARLY_WARNING → CURRENCY → CURRENT_HOLDINGS → "
            "GEOPOLITICAL_SIGNAL → PENDING_TRIGGERS → NET_ASSESSMENT.\n\n"
            "Rules:\n"
            "- Every claim must come from the data below — no inference or embellishment.\n"
            "- SCENARIO_PROBABILITIES must show all 6 probabilities summing to 100%.\n"
            "- NET_ASSESSMENT: 3-5 sentences identifying the dominant risk and recommended posture.\n"
            "- Use concise prose, no bullet lists within sections.\n\n"
            "After NET_ASSESSMENT, append exactly one more block in this literal "
            "machine-readable format (no extra commentary before or after it):\n"
            "###OPEN_ITEMS###\n"
            "OPEN_TRIGGERS:\n"
            "- trigger description\n"
            "(one bullet per open trigger worth tracking into next session; "
            "write '_None this session._' instead of a list if there are none)\n"
            "OPEN_DECISIONS:\n"
            "1. decision description\n"
            "(one numbered item per open decision the client needs to make; "
            "write '_None this session._' instead of a list if there are none)\n\n"
            f"DATA:\n{context_summary}"
        )
        raw = self._call(prompt, max_tokens=_MAX_TOKENS, timeout=180)
        return _split_open_items(raw)

    # ── Low-level HTTP call ────────────────────────────────────────────────────

    def _call(self, user_prompt: str, max_tokens: int = _MAX_TOKENS, timeout: int = 120) -> str:
        """POST one message to the Anthropic API and return the text response."""
        import ssl
        import urllib.request

        try:
            import certifi
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_ctx = ssl.create_default_context()

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        body = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user_prompt}],
        }).encode("utf-8")

        req = urllib.request.Request(_API_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content = data.get("content", [])
        for block in content:
            if block.get("type") == "text":
                return block["text"]
        raise RuntimeError(f"Unexpected API response structure: {data}")


class StubAIClient(AIClient):
    """
    Offline stub — returns deterministic canned responses.
    Used in tests and dry-run without API key.
    """

    def gather_qualitative(self, targets: List[str], market_summary: str = "") -> Dict[str, str]:
        return {t: f"[STUB] {t}: qualitative data not fetched (stub mode)" for t in targets}

    def answer_scoring(self, questions: List[ScoringQuestion]) -> ScoringAnswers:
        # Return midpoint score for each question as a conservative stub
        answers = {}
        reasoning = {}
        for q in questions:
            scores = sorted(q.valid_scores)
            # Pick the lowest non-negative score (conservative)
            stub = next((s for s in scores if s >= 0), scores[0])
            answers[q.id] = stub
            reasoning[q.id] = "[STUB] scored conservatively — no live AI available"
        return ScoringAnswers(answers=answers, reasoning=reasoning)

    def generate_briefing(self, context_summary: str) -> Tuple[str, List[str], List[str]]:
        narrative = (
            "[STUB BRIEFING — AI client in offline mode]\n\n"
            "Pipeline completed with stub AI responses. "
            "Run with ANTHROPIC_API_KEY set for a live briefing.\n\n"
            + context_summary[:2000]
        )
        return (
            narrative,
            ["[STUB] open_triggers not extracted — offline mode, no live AI call"],
            ["[STUB] open_decisions not extracted — offline mode, no live AI call"],
        )
