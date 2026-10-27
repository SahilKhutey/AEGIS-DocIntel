"""
src/engines/generation/service.py
=================================
Central orchestration service for evidence-grounded answer generation.
"""

from __future__ import annotations

import logging
from typing import Optional

from .contracts import (
    GenerationPolicy,
    GenerationRequest,
    GenerationResult,
)
from .generator import AnswerGenerator
from .prompts import build_prompt
from .validation import (
    ModelOutputError,
    parse_model_output,
    resolve_citations,
    validate_claim_references,
    validate_generation_request,
)

logger = logging.getLogger("aegis.generation.service")


class GenerationService:
    """Orchestrates validation, prompt building, LLM execution, citation verification, and abstention."""

    def __init__(
        self,
        generator: AnswerGenerator,
        policy: Optional[GenerationPolicy] = None,
    ) -> None:
        self._generator = generator
        self._policy = policy or GenerationPolicy()

    def answer(self, request: GenerationRequest) -> GenerationResult:
        """Generate a source-grounded answer from retrieved evidence with full citation verification."""
        policy = request.policy if request.policy is not None else self._policy

        # Step 1: Deterministic request validation
        validate_generation_request(request, policy)

        # Step 2: Safe abstention on insufficient evidence
        if len(request.evidence) < policy.min_evidence_items:
            logger.info(
                "Abstaining from generation: retrieved evidence items (%d) < minimum required (%d)",
                len(request.evidence),
                policy.min_evidence_items,
            )
            return GenerationResult(
                status="insufficient_evidence",
                answer="The provided documents do not contain sufficient evidence to answer this question.",
                claims=(),
                citations=(),
                warnings=("Insufficient evidence available for this query.",),
            )

        # Step 3: Prompt construction with untrusted-data boundary
        system_prompt, user_prompt = build_prompt(request)

        # Step 4: Model execution
        raw_output = self._generator.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=policy.temperature,
        )

        # Step 5: Parse structured output
        parsed = parse_model_output(raw_output)

        # Step 6: Enforce output length limit
        if len(parsed.answer) > policy.max_answer_chars:
            raise ModelOutputError(
                f"Generated answer exceeds maximum length of {policy.max_answer_chars} characters"
            )

        # Step 7: Grounding and citation resolution
        if parsed.status == "answered":
            validate_claim_references(parsed, request.evidence)
            citations = resolve_citations(parsed, request.evidence)
            return GenerationResult(
                status="answered",
                answer=parsed.answer,
                claims=parsed.claims,
                citations=citations,
                warnings=parsed.warnings,
            )

        # For insufficient_evidence or conflicting_evidence, preserve warnings and answer text
        return GenerationResult(
            status=parsed.status,
            answer=parsed.answer,
            claims=parsed.claims,
            citations=(),
            warnings=parsed.warnings,
        )
