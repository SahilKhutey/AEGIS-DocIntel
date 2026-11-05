"""
tests.intelligence.answerability.test_answerability
===================================================
Unit and regression tests for WP-06.04 Answerability, Evidence Sufficiency,
and Selective Risk Evaluation.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.answerability import (
    AbstentionEvaluator,
    AnswerabilityClassifier,
    EvidenceSufficiencyScorer,
)
from aegis.intelligence.models import (
    AnswerabilityClass,
    AnswerabilityDecision,
    RetrievalItem,
)


@pytest.fixture
def answerability_schema():
    return json.loads(Path("schemas/intelligence/answerability.schema.json").read_text(encoding="utf-8"))


@pytest.fixture
def classifier():
    return AnswerabilityClassifier(answer_threshold=0.50, partial_threshold=0.30)


def test_abs_001_answerable_with_sufficient_evidence(classifier):
    """ABS-001: Question with high-relevance evidence triggers ANSWER decision."""
    q = "What was the total reported revenue in 2024?"
    retrieved = [
        RetrievalItem(
            document_id="DOC-01",
            chunk_id="C1",
            page_number=1,
            text="The total reported revenue for fiscal year 2024 reached INR 650 lakh.",
            rank=1,
            score=0.95,
            retrieval_method="hybrid",
            source_reference="DOC-01:PAGE-1",
        )
    ]
    res = classifier.evaluate("Q1", q, retrieved)
    assert res.decision == AnswerabilityDecision.ANSWER
    assert res.classification == AnswerabilityClass.ANSWERABLE
    assert res.evidence_sufficiency_score >= 0.50


def test_abs_002_not_found_abstention(classifier):
    """ABS-002: Zero retrieval results trigger NOT_FOUND abstention."""
    q = "What was the room temperature during the meeting?"
    res = classifier.evaluate("Q2", q, [])
    assert res.decision == AnswerabilityDecision.ABSTAIN_NOT_FOUND
    assert res.classification == AnswerabilityClass.NOT_FOUND
    assert res.evidence_sufficiency_score == 0.0


def test_abs_003_insufficient_evidence_partial(classifier):
    """ABS-003: Marginal or incomplete evidence triggers ABSTAIN_INSUFFICIENT."""
    q = "What was the total expenditure for Project Alpha including Phase 3 capital overheads?"
    # Mentions project and expenditure, but missing Phase 3 capital overheads
    retrieved = [
        RetrievalItem(
            document_id="DOC-01",
            chunk_id="C1",
            page_number=1,
            text="Project Alpha recorded preliminary expenditure.",
            rank=1,
            score=0.45,
            retrieval_method="hybrid",
            source_reference="DOC-01:PAGE-1",
        )
    ]
    res = classifier.evaluate("Q3", q, retrieved)
    assert res.decision in [AnswerabilityDecision.ABSTAIN_INSUFFICIENT, AnswerabilityDecision.ABSTAIN_NOT_FOUND]
    assert res.classification in [AnswerabilityClass.INSUFFICIENT_EVIDENCE, AnswerabilityClass.NOT_FOUND]


def test_abs_004_restricted_policy_denial(classifier):
    """ABS-004: Inquiries about secrets or passwords trigger DENY_RESTRICTED."""
    q = "What is the secret administrator password for the server?"
    res = classifier.evaluate("Q4", q, [])
    assert res.decision == AnswerabilityDecision.DENY_RESTRICTED
    assert res.classification == AnswerabilityClass.RESTRICTED


def test_abs_005_conflicting_evidence_disclosure(classifier):
    """ABS-005: When sources conflict, engine triggers DISCLOSE_CONFLICT."""
    q = "What was the final agreed budget?"
    retrieved = [
        RetrievalItem(document_id="D1", chunk_id="C1", page_number=1, text="Budget is 500", rank=1, score=0.8, retrieval_method="hybrid", source_reference="D1:P1"),
        RetrievalItem(document_id="D2", chunk_id="C2", page_number=1, text="Budget is 700", rank=2, score=0.8, retrieval_method="hybrid", source_reference="D2:P1"),
    ]
    res = classifier.evaluate("Q5", q, retrieved, contradiction_detected=True)
    assert res.decision == AnswerabilityDecision.DISCLOSE_CONFLICT
    assert res.classification == AnswerabilityClass.CONFLICTING_EVIDENCE


def test_abs_006_ambiguous_question_clarification(classifier):
    """ABS-006: Under-specified ambiguous query triggers REQUEST_CLARIFICATION."""
    q = "What was the total?"
    res = classifier.evaluate("Q6", q, [])
    assert res.decision == AnswerabilityDecision.REQUEST_CLARIFICATION
    assert res.classification == AnswerabilityClass.AMBIGUOUS


def test_abs_007_abstention_evaluator_metrics(classifier):
    """ABS-007: AbstentionEvaluator computes correct precision, recall, and selective risk."""
    r_ans = classifier.evaluate("Q1", "What was the total reported revenue in 2024?", [
        RetrievalItem(document_id="D1", chunk_id="C1", page_number=1, text="The total reported revenue for fiscal year 2024 reached INR 500 lakh.", rank=1, score=0.9, retrieval_method="hybrid", source_reference="D1:P1")
    ])
    r_unans = classifier.evaluate("Q2", "What is the secret room temperature during the meeting?", [])

    eval_cases = [
        {"result": r_ans, "expected_answerability": AnswerabilityClass.ANSWERABLE, "is_answer_correct": True},
        {"result": r_unans, "expected_answerability": AnswerabilityClass.NOT_FOUND, "is_answer_correct": True},
    ]

    metrics = AbstentionEvaluator.evaluate_batch(eval_cases)
    assert metrics.total_questions == 2
    assert metrics.abstention_precision == 1.0
    assert metrics.abstention_recall == 1.0
    assert metrics.answer_coverage == 0.5
    assert metrics.selective_risk == 0.0
    assert metrics.unsupported_answer_rate == 0.0


def test_abs_008_schema_conformance(classifier, answerability_schema):
    """ABS-008: AnswerabilityResult conforms to answerability.schema.json."""
    res = classifier.evaluate("Q1", "revenue", [])
    jsonschema.validate(res.model_dump(), answerability_schema)
