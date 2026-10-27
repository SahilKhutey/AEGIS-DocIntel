"""
src/engines/generation/__init__.py
==================================
AEGIS-DocIntel Grounded Generation & Citation Verification Engine.
"""

from __future__ import annotations

from .contracts import (
    Citation,
    Claim,
    Evidence,
    GenerationPolicy,
    GenerationRequest,
    GenerationResult,
)
from .generator import AnswerGenerator, ModelGenerationError, TextModel
from .prompts import SYSTEM_INSTRUCTIONS, build_prompt
from .service import GenerationService
from .validation import (
    CitationValidationError,
    GenerationError,
    GenerationInputError,
    ModelOutputError,
    parse_model_output,
    resolve_citations,
    validate_claim_references,
    validate_generation_request,
)

__all__ = [
    "Evidence",
    "Claim",
    "Citation",
    "GenerationPolicy",
    "GenerationRequest",
    "GenerationResult",
    "TextModel",
    "ModelGenerationError",
    "AnswerGenerator",
    "SYSTEM_INSTRUCTIONS",
    "build_prompt",
    "GenerationService",
    "GenerationError",
    "GenerationInputError",
    "CitationValidationError",
    "ModelOutputError",
    "validate_generation_request",
    "parse_model_output",
    "validate_claim_references",
    "resolve_citations",
]
