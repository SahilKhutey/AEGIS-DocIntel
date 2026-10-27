"""tests/test_mvp3_validation.py
===============================
MVP 3 tests for model output parsing, schema enforcement, and claim reference validation.
"""

from __future__ import annotations

import pytest

from src.engines.generation.contracts import (
    Claim,
    Evidence,
    GenerationResult,
)
from src.engines.generation.validation import (
    CitationValidationError,
    ModelOutputError,
    parse_model_output,
    resolve_citations,
    validate_claim_references,
)


def make_evidence_pool() -> tuple[Evidence, ...]:
    return (
        Evidence(
            chunk_id="chunk-1",
            document_id="doc-1",
            tenant_id="tenant-a",
            text="Revenue grew by 14% to $120M.",
            score=0.95,
            page_number=2,
            section_path=("Financials",),
        ),
        Evidence(
            chunk_id="chunk-2",
            document_id="doc-1",
            tenant_id="tenant-a",
            text="Operating margins expanded by 200 bps.",
            score=0.90,
            page_number=3,
            section_path=("Financials",),
        ),
    )


def test_invalid_json_is_rejected():
    with pytest.raises(ModelOutputError, match="not valid JSON"):
        parse_model_output("invalid-json{missing_bracket")


def test_non_dict_json_is_rejected():
    with pytest.raises(ModelOutputError, match="must be a JSON object"):
        parse_model_output('["array", "not", "object"]')


def test_unknown_status_is_rejected():
    with pytest.raises(ModelOutputError, match="invalid generation status"):
        parse_model_output('{"status": "hallucinated", "answer": "text", "claims": []}')


def test_missing_answer_is_rejected():
    with pytest.raises(ModelOutputError, match="must contain a string 'answer'"):
        parse_model_output('{"status": "answered", "claims": []}')


def test_malformed_claims_rejected():
    with pytest.raises(ModelOutputError, match="'claims' field must be a list"):
        parse_model_output('{"status": "answered", "answer": "txt", "claims": "not-a-list"}')


def test_claim_without_evidence_ids_is_rejected():
    result = GenerationResult(
        status="answered",
        answer="Ungrounded claim with no evidence.",
        claims=(Claim(text="Ungrounded claim", evidence_ids=()),),
    )
    with pytest.raises(CitationValidationError, match="has no evidence reference"):
        validate_claim_references(result, make_evidence_pool())


def test_claim_referencing_unknown_evidence_is_rejected():
    result = GenerationResult(
        status="answered",
        answer="Fabricated citation.",
        claims=(Claim(text="Fabricated fact", evidence_ids=("chunk-fake-999",)),),
    )
    with pytest.raises(CitationValidationError, match="claim references unknown evidence"):
        validate_claim_references(result, make_evidence_pool())


def test_answered_status_with_empty_claims_is_rejected():
    result = GenerationResult(
        status="answered",
        answer="Answer claiming success with no claims.",
        claims=(),
    )
    with pytest.raises(CitationValidationError, match="must contain at least one claim"):
        validate_claim_references(result, make_evidence_pool())


def test_resolve_citations_maps_provenance():
    evidence = make_evidence_pool()
    result = GenerationResult(
        status="answered",
        answer="Revenue and margins both improved.",
        claims=(
            Claim(text="Revenue grew by 14%.", evidence_ids=("chunk-1",)),
            Claim(text="Operating margins expanded.", evidence_ids=("chunk-2", "chunk-1")),
        ),
    )

    validate_claim_references(result, evidence)
    citations = resolve_citations(result, evidence)

    assert len(citations) == 2
    assert citations[0].evidence_id == "chunk-1"
    assert citations[0].document_id == "doc-1"
    assert citations[0].page_number == 2
    assert citations[0].section_path == ("Financials",)

    assert citations[1].evidence_id == "chunk-2"
    assert citations[1].page_number == 3
