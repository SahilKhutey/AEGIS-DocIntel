"""
src/engines/generation/contracts.py
===================================
Data contracts for evidence-grounded answer generation, claims, and citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Tuple


@dataclass(frozen=True, slots=True)
class Evidence:
    """A source passage returned by the trusted retrieval layer."""

    chunk_id: str
    document_id: str
    tenant_id: str
    text: str
    score: float
    page_number: int | None = None
    section_path: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Claim:
    """One factual statement and the evidence IDs offered to support it."""

    text: str
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Citation:
    """A validated reference to a retrieved evidence passage."""

    evidence_id: str
    document_id: str
    page_number: int | None = None
    section_path: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GenerationPolicy:
    """Configuration constraints and safety limits for generation."""

    max_question_chars: int = 4000
    max_evidence_items: int = 50
    min_evidence_items: int = 1
    max_answer_chars: int = 10000
    max_output_tokens: int = 1500
    temperature: float = 0.0
    require_citations: bool = True
    allow_inferences: bool = True


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Request payload for evidence-grounded answer generation."""

    question: str
    tenant_id: str
    evidence: Tuple[Evidence, ...] = ()
    policy: GenerationPolicy = field(default_factory=GenerationPolicy)


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Structured result returned by the generation engine."""

    status: Literal["answered", "insufficient_evidence", "conflicting_evidence"]
    answer: str
    claims: Tuple[Claim, ...] = ()
    citations: Tuple[Citation, ...] = ()
    warnings: Tuple[str, ...] = ()
