"""
AEGIS-DocIntel — Task PH-009: Citation Verification & Provenance Grounding
=========================================================================
Validates:
1. Strict citation validation (validate_citations) ensuring answers refer to actual retrieved chunks.
2. Immediate flagging and rejection of hallucinated chunk IDs or foreign documents.
3. Canonical CitationReference schema and validation constraints.
4. CitationVerifier accuracy, precision, and excerpt matching against source documents.
"""
from __future__ import annotations

import pytest

from src.engines.retrieval.retrieval_engine import (
    CitationValidationResult,
    RetrievedEvidence,
    validate_citations,
)
from src.models.citation import CitationReference
from src.verification.citation_verifier import (
    CitationCheckResult,
    CitationMatchStatus,
    CitationVerifier,
)


def test_validate_citations_with_grounded_evidence():
    """Verify validate_citations confirms citations that match retrieved evidence chunks."""
    evidence = [
        RetrievedEvidence(
            document_id="doc-ph009-01",
            chunk_id="chunk-101",
            text="The architecture delivers 450 TFLOPS of compute throughput.",
            page_number=1,
            section_path=("Specifications",),
            retrieval_score=0.95,
        ),
        RetrievedEvidence(
            document_id="doc-ph009-01",
            chunk_id="chunk-102",
            text="Power dissipation is constrained to 220 Watts.",
            page_number=2,
            section_path=("Thermal",),
            retrieval_score=0.91,
        ),
    ]

    citations = [
        {"chunk_id": "chunk-101", "doc_id": "doc-ph009-01", "snippet": "450 TFLOPS"},
        {"chunk_id": "chunk-102", "doc_id": "doc-ph009-01", "snippet": "220 Watts"},
    ]

    res = validate_citations(citations, evidence, tenant_id="tenant-ph009")
    assert res.is_valid is True
    assert res.total_citations == 2
    assert res.valid_citations == 2
    assert len(res.invalid_citations) == 0


def test_validate_citations_flags_hallucinated_and_foreign_chunks():
    """Verify validate_citations rejects invented chunk IDs and foreign document IDs."""
    evidence = [
        RetrievedEvidence(
            document_id="doc-real-01",
            chunk_id="chunk-valid-1",
            text="Valid verified fact.",
            page_number=1,
            section_path=(),
            retrieval_score=0.89,
        )
    ]

    bad_citations = [
        {"chunk_id": "chunk-valid-1", "doc_id": "doc-real-01"},
        {"chunk_id": "chunk-hallucinated-999", "doc_id": "doc-real-01"},  # Invented chunk
        {"chunk_id": "chunk-valid-1", "doc_id": "doc-foreign-99"},        # Foreign doc
    ]

    res = validate_citations(bad_citations, evidence, tenant_id="tenant-ph009")
    assert res.is_valid is False
    assert res.total_citations == 3
    assert res.valid_citations == 1
    assert len(res.invalid_citations) == 2


def test_canonical_citation_reference_validation():
    """Verify CitationReference validates required non-empty identifiers."""
    cit = CitationReference(
        citation_id="cit-001",
        document_id="doc-spec-01",
        page_number=3,
        chunk_id="chk-p3-01",
        quoted_text="Memory capacity is 128 MB SRAM.",
        claim_id="claim-memory",
    )
    assert cit.citation_id == "cit-001"
    assert cit.page_number == 3
    assert cit.quoted_text == "Memory capacity is 128 MB SRAM."

    with pytest.raises(ValueError):
        CitationReference(citation_id="", document_id="doc-1")

    with pytest.raises(ValueError):
        CitationReference(citation_id="cit-valid", document_id="   ")


def test_citation_verifier_excerpt_verification():
    """Verify CitationVerifier confirms claims against source documents."""
    verifier = CitationVerifier(strict=False, fuzzy_threshold=0.6)

    response_text = "[doc1, p.1] Sustained compute performance reaches 450 TFLOPS."
    source_docs = {
        "doc1": {
            "pages": {
                "1": "The AEGIS neural accelerator reaches 450 TFLOPS of sustained compute performance."
            }
        }
    }

    result = verifier.verify(response_text, source_docs)
    assert result.total_citations == 1
    assert result.matches[0].is_correct is True
    assert result.accuracy == 1.0
