"""
tests/evaluation/citations/test_citation_precision.py
====================================================
Comprehensive CIT-001 through CIT-012 test suite verifying multi-layer
citation precision, resolution, claim grounding, and quality gate enforcement.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.models.citation import (
    CitationEvaluator,
    CitationGateResult,
    CitationMetrics,
    CitationReference,
    ClaimVerificationItem,
)
from src.models.evidence_object import RetrievedEvidence

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def sample_evidence():
    return [
        RetrievedEvidence(
            document_id="doc_annual_report_2024",
            chunk_id="c1",
            text="In fiscal year 2024, consolidated revenue grew by 18% to $450 million.",
            page_number=1,
            section_path=("Executive Summary", "Financial Highlights"),
            retrieval_score=0.98,
            document_version="v1.0",
        ),
        RetrievedEvidence(
            document_id="doc_annual_report_2024",
            chunk_id="c2",
            text="Operating margin improved from 12% to 15.5% over the same fiscal period.",
            page_number=2,
            section_path=("Financial Review", "Margins"),
            retrieval_score=0.92,
            document_version="v1.0",
        ),
    ]


def test_cit_001_l1_schema_validation():
    """CIT-001: L1 schema validation rejects empty identifiers."""
    with pytest.raises(ValidationError):
        CitationReference(citation_id="", document_id="doc1")

    with pytest.raises(ValidationError):
        CitationReference(citation_id="cit1", document_id="   ")

    valid_cit = CitationReference(citation_id="cit1", document_id="doc1", page_number=1)
    assert valid_cit.citation_id == "cit1"
    assert valid_cit.document_id == "doc1"


def test_cit_002_l2_source_existence_failure(sample_evidence):
    """CIT-002: L2 source existence fails when document_id is missing from evidence pool."""
    with open(FIXTURES_DIR / "wrong_document.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(claims, sample_evidence)
    assert not result.passed
    assert result.metrics.resolution_rate == 0.0
    assert len(result.unresolved_citations) == 1
    assert "not found in evidence pool" in result.unresolved_citations[0]


def test_cit_003_l3_location_chunk_missing(sample_evidence):
    """CIT-003: L3 location precision fails when chunk_id does not exist."""
    claim = ClaimVerificationItem(
        claim_id="CLM-003",
        claim_text="Revenue grew 18%",
        citations=[
            CitationReference(
                citation_id="CIT-003",
                document_id="doc_annual_report_2024",
                chunk_id="chunk_nonexistent_999",
            )
        ],
    )
    result = CitationEvaluator.evaluate([claim], sample_evidence)
    assert not result.passed
    assert result.metrics.resolution_rate == 0.0
    assert len(result.unresolved_citations) == 1


def test_cit_004_l3_location_page_mismatch(sample_evidence):
    """CIT-004: L3 location precision fails when cited page_number mismatches evidence chunk page."""
    with open(FIXTURES_DIR / "wrong_page.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(claims, sample_evidence)
    assert not result.passed
    assert result.metrics.resolution_rate == 0.0
    assert any("Page mismatch" in s for s in result.unresolved_citations)


def test_cit_005_l4_claim_support_success(sample_evidence):
    """CIT-005: L4 claim support succeeds when evidence text supports claim."""
    with open(FIXTURES_DIR / "valid_citations.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(claims, sample_evidence)
    assert result.passed
    assert result.metrics.precision == 1.0
    assert result.metrics.coverage == 1.0
    assert result.metrics.supported_citations == 2


def test_cit_006_l4_claim_support_contradictory_numbers(sample_evidence):
    """CIT-006: L4 claim support fails when claim asserts contradictory numerical values."""
    with open(FIXTURES_DIR / "unsupported_claims.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(claims, sample_evidence)
    assert not result.passed
    assert result.metrics.precision == 0.0
    assert result.metrics.coverage == 0.0
    assert "CLM-ERR-001" in result.unsupported_claims


def test_cit_007_l4_claim_support_ambiguous(sample_evidence):
    """CIT-007: L4 claim support fails on ambiguous/unsupported statements."""
    with open(FIXTURES_DIR / "ambiguous_claims.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(claims, sample_evidence)
    assert not result.passed
    assert result.metrics.precision == 0.0
    assert "CLM-AMB-001" in result.unsupported_claims


def test_cit_008_l5_attribution_version_mismatch(sample_evidence):
    """CIT-008: L5 attribution accuracy detects mismatched document_version."""
    with open(FIXTURES_DIR / "stale_document_version.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(claims, sample_evidence)
    assert not result.passed
    assert result.metrics.attribution_accuracy == 0.0
    assert any("Version mismatch" in s for s in result.attribution_errors)


def test_cit_009_l5_attribution_document_origin_mismatch(sample_evidence):
    """CIT-009: L5 attribution accuracy detects mismatched document origin."""
    claim = ClaimVerificationItem(
        claim_id="CLM-ATTR-01",
        claim_text="Operating margin improved from 12% to 15.5%",
        citations=[
            CitationReference(
                citation_id="CIT-ATTR-01",
                document_id="doc_other_org",
                chunk_id="c2",
            )
        ],
    )
    result = CitationEvaluator.evaluate([claim], sample_evidence)
    assert not result.passed
    assert result.metrics.resolution_rate == 0.0  # doc not in pool


def test_cit_010_metric_calculation_accuracy(sample_evidence):
    """CIT-010: Metric calculation correctly computes P_c, C_c, R_c, A_c."""
    valid_claim = ClaimVerificationItem(
        claim_id="CLM-V",
        claim_text="consolidated revenue grew by 18% to $450 million.",
        citations=[
            CitationReference(citation_id="CIT-1", document_id="doc_annual_report_2024", chunk_id="c1")
        ]
    )
    invalid_claim = ClaimVerificationItem(
        claim_id="CLM-INV",
        claim_text="consolidated revenue fell by 90%",
        citations=[
            CitationReference(citation_id="CIT-2", document_id="doc_annual_report_2024", chunk_id="c1")
        ]
    )
    result = CitationEvaluator.evaluate([valid_claim, invalid_claim], sample_evidence)
    # Total citations: 2, resolved: 2, supported: 1 -> P_c = 0.5
    # Total claims: 2, supported: 1 -> C_c = 0.5
    # R_c = 1.0, A_c = 1.0
    assert result.metrics.precision == 0.5
    assert result.metrics.coverage == 0.5
    assert result.metrics.resolution_rate == 1.0
    assert result.metrics.attribution_accuracy == 1.0


def test_cit_011_quality_gate_threshold_enforcement(sample_evidence):
    """CIT-011: Quality gate fails if P_c < min_precision (0.90)."""
    valid_claim = ClaimVerificationItem(
        claim_id="CLM-V",
        claim_text="consolidated revenue grew by 18% to $450 million.",
        citations=[
            CitationReference(citation_id="CIT-1", document_id="doc_annual_report_2024", chunk_id="c1")
        ]
    )
    invalid_claim = ClaimVerificationItem(
        claim_id="CLM-INV",
        claim_text="Operating margin fell by 50%",
        citations=[
            CitationReference(citation_id="CIT-2", document_id="doc_annual_report_2024", chunk_id="c2")
        ]
    )
    result = CitationEvaluator.evaluate([valid_claim, invalid_claim], sample_evidence, min_precision=0.90)
    assert not result.passed
    assert "Gate: 90.00%" in result.details


def test_cit_012_full_suite_valid_pass(sample_evidence):
    """CIT-012: Full evaluation with valid fixtures passes all quality gates."""
    with open(FIXTURES_DIR / "valid_citations.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    claims = [ClaimVerificationItem(**item) for item in data]

    result = CitationEvaluator.evaluate(
        claims,
        sample_evidence,
        min_precision=0.90,
        min_coverage=0.90,
        min_resolution_rate=1.0,
        min_attribution_accuracy=0.95,
    )
    assert result.passed
    assert result.metrics.precision == 1.0
    assert result.metrics.coverage == 1.0
    assert result.metrics.resolution_rate == 1.0
    assert result.metrics.attribution_accuracy == 1.0
    assert len(result.unresolved_citations) == 0
    assert len(result.unsupported_claims) == 0
