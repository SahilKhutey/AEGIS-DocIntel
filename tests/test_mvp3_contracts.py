"""tests/test_mvp3_contracts.py
==============================
MVP 3 tests for generation contracts and input boundary validation.
"""

from __future__ import annotations

import pytest

from src.engines.generation.contracts import (
    Evidence,
    GenerationPolicy,
    GenerationRequest,
)
from src.engines.generation.validation import (
    GenerationInputError,
    validate_generation_request,
)


def make_evidence(
    *,
    chunk_id: str = "chunk-1",
    document_id: str = "doc-1",
    tenant_id: str = "tenant-a",
    text: str = "Annual revenue was 10 million.",
    score: float = 0.95,
    page_number: int = 1,
) -> Evidence:
    return Evidence(
        chunk_id=chunk_id,
        document_id=document_id,
        tenant_id=tenant_id,
        text=text,
        score=score,
        page_number=page_number,
    )


def test_valid_request_is_accepted():
    request = GenerationRequest(
        question="What was the annual revenue?",
        tenant_id="tenant-a",
        evidence=(make_evidence(),),
    )
    policy = GenerationPolicy()
    validate_generation_request(request, policy)


@pytest.mark.parametrize("empty_q", ["", "   ", "\n\t"])
def test_empty_question_is_rejected(empty_q: str):
    request = GenerationRequest(
        question=empty_q,
        tenant_id="tenant-a",
        evidence=(make_evidence(),),
    )
    with pytest.raises(GenerationInputError, match="question must not be empty"):
        validate_generation_request(request, GenerationPolicy())


def test_question_exceeding_max_chars_is_rejected():
    long_q = "x" * 4001
    request = GenerationRequest(
        question=long_q,
        tenant_id="tenant-a",
        evidence=(make_evidence(),),
    )
    with pytest.raises(GenerationInputError, match="question exceeds maximum length"):
        validate_generation_request(request, GenerationPolicy(max_question_chars=4000))


@pytest.mark.parametrize("empty_t", ["", "  ", "\t"])
def test_empty_tenant_id_is_rejected(empty_t: str):
    request = GenerationRequest(
        question="What was revenue?",
        tenant_id=empty_t,
        evidence=(make_evidence(),),
    )
    with pytest.raises(GenerationInputError, match="tenant_id must not be empty"):
        validate_generation_request(request, GenerationPolicy())


def test_evidence_exceeding_max_items_is_rejected():
    evidence_items = tuple(
        make_evidence(chunk_id=f"chunk-{i}") for i in range(11)
    )
    request = GenerationRequest(
        question="What was revenue?",
        tenant_id="tenant-a",
        evidence=evidence_items,
    )
    with pytest.raises(GenerationInputError, match="evidence count"):
        validate_generation_request(request, GenerationPolicy(max_evidence_items=10))


def test_cross_tenant_evidence_is_rejected_at_boundary():
    """Evidence belonging to another tenant must not enter the generation pipeline."""
    evidence_items = (
        make_evidence(chunk_id="chunk-1", tenant_id="tenant-a"),
        make_evidence(chunk_id="chunk-2", tenant_id="tenant-b_infiltrator"),
    )
    request = GenerationRequest(
        question="What was revenue?",
        tenant_id="tenant-a",
        evidence=evidence_items,
    )
    with pytest.raises(GenerationInputError, match="unauthorized for request tenant"):
        validate_generation_request(request, GenerationPolicy())
