"""
tests/evaluation/test_citation_integrity.py
===========================================
Phase 3.4 Evaluation Quality Suite — Citation Integrity:
Verifies cryptographic and identifier matching between returned LLM answer citations
and the retrieved evidence chunks to detect hallucinations and prevent source fabrication.
"""
from __future__ import annotations

import pytest

from src.models.evidence_object import (
    CitationValidationResult,
    RetrievedEvidence,
    validate_citations,
)


def test_valid_citations_pass_integrity_check():
    """Citations referencing chunks in the retrieved evidence pool pass validation."""
    evidence_pool = [
        RetrievedEvidence(
            document_id="doc_alpha",
            chunk_id="chunk_101",
            text="Gross revenue grew 18% in FY2024 to $450 million.",
            page_number=1,
            section_path=("Financial Summary",),
            retrieval_score=0.96,
        ),
        RetrievedEvidence(
            document_id="doc_alpha",
            chunk_id="chunk_102",
            text="Operating margin expanded by 350 basis points.",
            page_number=2,
            section_path=("Operations",),
            retrieval_score=0.88,
        ),
    ]

    valid_citations = [
        {"chunk_id": "chunk_101", "text": "Gross revenue grew 18%"},
        {"chunk_id": "chunk_102", "text": "Operating margin expanded"},
    ]

    result: CitationValidationResult = validate_citations(valid_citations, evidence_pool)
    assert result.is_valid, f"Expected citations to pass: {result}"
    assert result.total_citations == 2
    assert result.valid_citations == 2
    assert len(result.invalid_citations) == 0


def test_fabricated_citations_fail_integrity_check():
    """Citations with ungrounded/hallucinated chunk IDs are rejected."""
    evidence_pool = [
        RetrievedEvidence(
            document_id="doc_alpha",
            chunk_id="chunk_101",
            text="Real retrieved document chunk text.",
            page_number=1,
            section_path=(),
            retrieval_score=0.95,
        ),
    ]

    fake_citations = [
        {"chunk_id": "chunk_101", "text": "Real chunk"},
        {"chunk_id": "chunk_fake_9999", "text": "Hallucinated citation"},
    ]

    result: CitationValidationResult = validate_citations(fake_citations, evidence_pool)
    assert not result.is_valid, "Fabricated citation was falsely accepted"
    assert result.valid_citations == 1
    assert len(result.invalid_citations) == 1
    assert result.invalid_citations[0]["chunk_id"] == "chunk_fake_9999"


def test_empty_citations_and_empty_evidence_behavior():
    """Verify behavior on boundary conditions (empty evidence and empty citations)."""
    # Empty citations with evidence pool is trivially valid (no claims made)
    evidence = [
        RetrievedEvidence(
            document_id="d1",
            chunk_id="c1",
            text="Text",
            page_number=1,
            section_path=(),
            retrieval_score=0.9,
        )
    ]
    res_empty_cit = validate_citations([], evidence)
    assert res_empty_cit.is_valid
    assert res_empty_cit.valid_citations == 0
    assert res_empty_cit.total_citations == 0

    # Non-empty citations with empty evidence pool must fail (cannot cite missing evidence)
    res_no_evidence = validate_citations([{"chunk_id": "c1"}], [])
    assert not res_no_evidence.is_valid
    assert len(res_no_evidence.invalid_citations) == 1
    assert res_no_evidence.valid_citations == 0
