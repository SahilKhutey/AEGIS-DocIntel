"""
Unit tests for the Verification Engine
======================================
"""

from __future__ import annotations

import pytest

from src.verification.exceptions import (
    VerificationEngineError,
    CitationMissingError,
    FactMismatchError,
    ConfidenceThresholdError,
    HallucinationDetectedError,
)
from src.verification.citation_verifier import CitationVerifier, CitationMatchStatus
from src.verification.fact_verifier import FactVerifier, FactStatus
from src.verification.confidence_scorer import ConfidenceScorer
from src.verification.hallucination_detector import HallucinationDetector, HallucinationType
from src.verification.consistency_checker import ConsistencyChecker
from src.verification.source_verifier import SourceVerifier
from src.verification.verification_engine import VerificationEngine


def test_exceptions():
    with pytest.raises(VerificationEngineError):
        raise CitationMissingError("citation missing")

    with pytest.raises(VerificationEngineError):
        raise FactMismatchError("fact mismatch")

    with pytest.raises(VerificationEngineError):
        raise ConfidenceThresholdError("low confidence")

    with pytest.raises(VerificationEngineError):
        raise HallucinationDetectedError("hallucination detected")


def test_citation_verifier():
    source_docs = {
        "doc1": {
            "pages": {
                "1": "The Quick Brown Fox jumps over the lazy dog.",
                "2": "Another page of text is here."
            }
        },
        "doc2": "A simple string document content."
    }

    # Strict verifier
    verifier_strict = CitationVerifier(strict=True)

    # Perfect exact match
    res_exact = verifier_strict.verify(
        "[doc1, p.1] The Quick Brown Fox jumps over the lazy dog.",
        source_docs
    )
    assert res_exact.total_citations == 1
    assert res_exact.correct_citations == 1
    assert res_exact.accuracy == 1.0
    assert res_exact.matches[0].status == CitationMatchStatus.EXACT_MATCH

    # Non-strict fuzzy verifier
    verifier_fuzzy = CitationVerifier(strict=False, fuzzy_threshold=0.6)

    # Partial match
    res_partial = verifier_fuzzy.verify(
        "[doc1, p.1] The Quick Brown Fox jumps over the lazy dog and a cat and a mouse and a bear and a rabbit.",
        source_docs
    )
    assert res_partial.correct_citations == 0
    assert res_partial.partial_matches == 1
    assert res_partial.accuracy == 1.0
    assert res_partial.matches[0].status == CitationMatchStatus.PARTIAL_MATCH

    # No match / incorrect citation
    res_fail = verifier_fuzzy.verify(
        "[doc1, p.1] Completely unrelated sentence about something else.",
        source_docs
    )
    assert res_fail.no_match_citations == 1
    assert res_fail.accuracy == 0.0

    # Missing doc ID
    res_missing = verifier_fuzzy.verify(
        "[nonexistent, p.1] Some content.",
        source_docs
    )
    assert res_missing.missing_citations == 1
    assert res_missing.accuracy == 0.0

    # No citations in response
    res_none = verifier_fuzzy.verify("No citations here.", source_docs)
    assert res_none.total_citations == 0
    assert res_none.accuracy == 1.0


def test_fact_verifier():
    kb = {
        "amdi.version": "1.0.0",
        "amdi.author": "AEGIS Dev Team",
        "system.status": "running"
    }

    verifier = FactVerifier(knowledge_base=kb, fuzzy_threshold=0.7)

    # Valid claim
    res_valid = verifier.verify("System status is running.")
    assert res_valid.total_claims == 1
    assert res_valid.supported_claims == 1
    assert res_valid.accuracy == 1.0

    # Partial claim
    res_partial = verifier.verify("The version of amdi is 1.0.0.")
    assert res_partial.total_claims == 1
    assert res_partial.partially_supported_claims == 1
    assert res_partial.accuracy == 0.5

    # Unverified claim
    res_unverified = verifier.verify("Paris is the capital of France.")
    assert res_unverified.unverified_claims == 1
    assert res_unverified.accuracy == 0.0

    # Empty case
    res_empty = verifier.verify("Hello?")
    assert res_empty.total_claims == 0
    assert res_empty.accuracy == 1.0


def test_confidence_scorer():
    scorer = ConfidenceScorer(
        citation_weight=0.3,
        fact_weight=0.3,
        hallucination_weight=0.2,
        source_weight=0.1,
        explained_variance_weight=0.1,
        passing_threshold=0.7
    )

    # High score
    score_high = scorer.score(
        citation_accuracy=0.9,
        fact_accuracy=0.9,
        hallucination_rate=0.0,
        source_reliability=1.0,
        explained_variance=0.9
    )
    assert score_high.overall >= 0.8
    assert score_high.grade in ("A", "B")
    assert not score_high.issues

    # Low score triggering threshold raise
    with pytest.raises(ConfidenceThresholdError):
        scorer.score_or_raise(
            citation_accuracy=0.3,
            fact_accuracy=0.3,
            hallucination_rate=0.4,
            source_reliability=0.5,
            explained_variance=0.5
        )


def test_hallucination_detector():
    detector = HallucinationDetector()
    source_docs = {
        "doc1": "The Quick Brown Fox is 5 years old. Author is Jane Doe."
    }

    # No hallucination
    res_clean = detector.detect(
        "[doc1, p.1] The Quick Brown Fox is 5 years old.",
        source_documents=source_docs
    )
    assert not res_clean.is_hallucinated

    # Uncited number / percentage
    res_uncited = detector.detect("This is an uncited claim with 99.9% accuracy.")
    assert any(i.hallucination_type == HallucinationType.UNCITED_CLAIM for i in res_uncited.indicators)

    # Numeric range inconsistency
    res_num_incons = detector.detect("The value ranges between 10 and 5.")
    assert any(i.hallucination_type == HallucinationType.NUMERICAL_INCONSISTENCY for i in res_num_incons.indicators)

    # Specificity paradox
    res_spec = detector.detect("The exact weight is precisely 42.12345 kg.")
    assert any(i.hallucination_type == HallucinationType.SPECIFICITY_PARADOX for i in res_spec.indicators)

    # Entity confusion
    res_ent = detector.detect("George Washington is the author.", source_documents=source_docs)
    assert any(i.hallucination_type == HallucinationType.ENTITY_CONFUSION for i in res_ent.indicators)


def test_consistency_checker():
    checker = ConsistencyChecker()

    # Consistent text
    res_consistent = checker.check("AMDI version is 1.0.0. The system is active.")
    assert res_consistent.is_consistent
    assert not res_consistent.issues

    # Inconsistent range
    res_numeric = checker.check("The range low is between 150 and 100.")
    assert res_numeric.consistency_score < 1.0
    assert len(res_numeric.issues) == 1
    assert any(iss["type"] == "numerical" for iss in res_numeric.issues)

    # Logical contradiction
    res_logical = checker.check("System status is online. System status is not online.")
    assert res_logical.consistency_score < 1.0
    assert any(iss["type"] == "logical" for iss in res_logical.issues)


def test_source_verifier():
    verifier = SourceVerifier()

    # Valid doc
    docs_valid = {
        "doc1": {
            "title": "Good Source",
            "text": "This is a long and valid source document containing enough text to pass checks."
        }
    }
    res_valid = verifier.verify(docs_valid)
    assert res_valid.is_authentic
    assert res_valid.source_reliability >= 0.9

    # Bad docs
    docs_bad = {
        "doc1": "",  # Empty (reliability 0.7)
        "doc2": {
            "text": ""  # empty + missing metadata (reliability 0.6)
        }
    }
    res_bad = verifier.verify(docs_bad)
    assert not res_bad.is_authentic
    assert res_bad.source_reliability < 0.7
    assert len(res_bad.issues) >= 2


def test_verification_engine_pipeline():
    kb = {"fox.color": "brown"}
    engine = VerificationEngine(min_confidence=0.7, kb=kb)

    source_docs = {
        "doc1": {
            "pages": {"1": "The Quick Brown Fox is fast."}
        }
    }

    # E2E valid verify
    report = engine.verify(
        response_text="[doc1, p.1] The Quick Brown Fox is fast. Fox color is brown.",
        source_documents=source_docs
    )
    assert report.is_valid
    assert report.overall_confidence >= 0.7
    report.raise_for_status()

    # E2E fail verify
    report_fail = engine.verify(
        response_text="This is a simple response without any numbers.",
        source_documents={}
    )
    assert not report_fail.is_valid
    with pytest.raises(ConfidenceThresholdError):
        report_fail.raise_for_status()

    # Serialize
    rep_dict = report.to_dict()
    assert "passed" in rep_dict
    assert "metrics" in rep_dict
    assert "citation_result" in rep_dict
