"""
tests.intelligence.citations.test_citation_correctness
======================================================
Unit and regression tests for WP-06.03 Citation Correctness, Claim Decomposition,
and 7-Label Support Entailment.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.citations import (
    CitationResolver,
    ClaimExtractor,
    SupportEvaluator,
)
from aegis.intelligence.models import (
    CitationRef,
    ClaimItem,
    ClaimSupportStatus,
    SupportLabel,
)


@pytest.fixture
def claim_schema():
    return json.loads(Path("schemas/intelligence/claim_citation.schema.json").read_text(encoding="utf-8"))


@pytest.fixture
def resolver():
    res = CitationResolver()
    res.register_document("DOC-001", page_count=5, chunks={"c1", "c2"})
    return res


def test_cit_001_claim_decomposition():
    """CIT-001: Extract atomic factual claims from compound sentences."""
    answer = "The project started in 2023, and it received INR 50 lakh in municipal funding."
    claims = ClaimExtractor.extract_claims(answer)
    assert len(claims) == 2
    assert "started in 2023" in claims[0].text
    assert "INR 50 lakh" in claims[1].text


def test_cit_002_citation_resolver_valid_and_invalid(resolver):
    """CIT-002: CitationResolver validates authentic documents and flags out-of-bounds pages."""
    valid_cit = CitationRef(citation_id="C1", document_id="DOC-001", page_number=3, chunk_id="c1")
    is_valid, reason = resolver.is_resolvable(valid_cit)
    assert is_valid is True
    assert reason is None

    # Invalid page bounds (page 10 > 5)
    bad_page = CitationRef(citation_id="C2", document_id="DOC-001", page_number=10)
    is_valid, reason = resolver.is_resolvable(bad_page)
    assert is_valid is False
    assert "PAGE_OUT_OF_BOUNDS" in reason

    # Unknown document
    bad_doc = CitationRef(citation_id="C3", document_id="DOC-UNKNOWN", page_number=1)
    is_valid, reason = resolver.is_resolvable(bad_doc)
    assert is_valid is False
    assert "UNKNOWN_DOCUMENT_ID" in reason


def test_cit_003_supports_label_entailment(resolver):
    """CIT-003: Evidence directly entailing the claim is labeled SUPPORTS."""
    evaluator = SupportEvaluator(resolver=resolver)
    claim = "Consolidated revenue grew by 18% in FY2024 to $450 million."
    cit = CitationRef(citation_id="C1", document_id="DOC-001", page_number=1, chunk_id="c1")
    ev = "In fiscal year 2024, consolidated revenue grew by 18% to $450 million."

    label = evaluator.evaluate_citation(claim, cit, ev)
    assert label == SupportLabel.SUPPORTS


def test_cit_004_partial_support_label(resolver):
    """CIT-004: Evidence containing some but not all material facts labeled PARTIALLY_SUPPORTS."""
    evaluator = SupportEvaluator(resolver=resolver)
    claim = "Revenue reached $450 million and operating margin was 20%."
    cit = CitationRef(citation_id="C1", document_id="DOC-001", page_number=1, chunk_id="c1")
    ev = "Revenue reached $450 million."

    label = evaluator.evaluate_citation(claim, cit, ev)
    assert label == SupportLabel.PARTIALLY_SUPPORTS


def test_cit_005_contradiction_detection(resolver):
    """CIT-005: Evidence conflicting in direction or quantity labeled CONTRADICTS."""
    evaluator = SupportEvaluator(resolver=resolver)
    claim = "Operating expenses increased by 15%."
    cit = CitationRef(citation_id="C1", document_id="DOC-001", page_number=1, chunk_id="c1")
    ev = "Operating expenses decreased by 15%."

    label = evaluator.evaluate_citation(claim, cit, ev)
    assert label == SupportLabel.CONTRADICTS


def test_cit_006_unrelated_and_irrelevant_labels(resolver):
    """CIT-006: Topical but unsupporting text is RELATED_ONLY; off-topic is IRRELEVANT."""
    evaluator = SupportEvaluator(resolver=resolver)
    claim = "The server utilizes SQLite in WAL mode."
    cit = CitationRef(citation_id="C1", document_id="DOC-001", page_number=1, chunk_id="c1")

    # Topical but non-substantiating (shares 'server' keyword)
    ev_related = "The server database storage architectures require concurrent transactional isolation."
    lbl_related = evaluator.evaluate_citation(claim, cit, ev_related)
    assert lbl_related == SupportLabel.RELATED_ONLY

    # Off-topic
    ev_irrelevant = "Carbon emissions dropped 10% following solar panel installation."
    lbl_irrel = evaluator.evaluate_citation(claim, cit, ev_irrelevant)
    assert lbl_irrel == SupportLabel.IRRELEVANT


def test_cit_007_schema_conformance(resolver, claim_schema):
    """CIT-007: Answer-level claim citation evaluation conforms to claim_citation.schema.json."""
    evaluator = SupportEvaluator(resolver=resolver)
    claim1 = ClaimItem(
        claim_id="CLM-01",
        text="Revenue grew by 18% in FY2024 to $450 million.",
        citations=[CitationRef(citation_id="C1", document_id="DOC-001", page_number=1, chunk_id="c1")],
    )

    ev_store = {"C1": "Consolidated revenue grew by 18% in FY2024 to $450 million."}
    eval_res = evaluator.evaluate_answer(
        answer_id="ANS-001",
        answer_text="Revenue grew by 18% in FY2024 to $450 million.",
        claims=[claim1],
        evidence_store=ev_store,
        question_id="GQ-001",
    )

    assert eval_res.evaluation_summary.citation_precision == 1.0
    assert eval_res.evaluation_summary.claim_support_rate == 1.0
    assert eval_res.claims[0].support_status == ClaimSupportStatus.FULLY_SUPPORTED

    jsonschema.validate(eval_res.model_dump(), claim_schema)
