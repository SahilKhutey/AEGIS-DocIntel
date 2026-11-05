"""
tests.intelligence.questions.test_golden_questions
==================================================
Unit and regression tests for WP-06.02 Golden Question Dataset.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.models import AnswerabilityClass, DifficultyLevel, TaskType
from aegis.intelligence.questions import GoldenQuestionLoader, QuestionPartitioner


@pytest.fixture
def golden_dataset_path():
    return Path("data/intelligence/golden_questions.jsonl")


@pytest.fixture
def loaded_questions(golden_dataset_path):
    loader = GoldenQuestionLoader()
    return loader.load_jsonl(golden_dataset_path, validate_schema=True)


def test_gq_001_total_quantity_and_categories(loaded_questions):
    """GQ-001: Exactly 130 human-verified benchmark questions across all required categories."""
    assert len(loaded_questions) == 130

    # Verify category counts
    task_counts = {}
    for q in loaded_questions:
        task_counts[q.task_type] = task_counts.get(q.task_type, 0) + 1

    assert task_counts[TaskType.DIRECT_FACTUAL] == 20
    assert task_counts[TaskType.ENTITY_EXTRACTION] == 15
    assert task_counts[TaskType.NUMERIC_EXTRACTION] == 20
    assert task_counts[TaskType.TEMPORAL_REASONING] == 10
    assert task_counts[TaskType.MULTI_HOP] == 15
    assert task_counts[TaskType.CROSS_DOCUMENT] == 10
    assert task_counts[TaskType.SUMMARIZATION] == 10
    assert task_counts[TaskType.UNANSWERABLE] == 20
    assert (
        task_counts.get(TaskType.AMBIGUITY_CLARIFICATION, 0)
        + task_counts.get(TaskType.CONFLICT_ANALYSIS, 0)
    ) == 10


def test_gq_002_schema_conformance(golden_dataset_path):
    """GQ-002: All questions conform strictly to golden_question.schema.json."""
    schema = json.loads(Path("schemas/intelligence/golden_question.schema.json").read_text(encoding="utf-8"))
    with open(golden_dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            jsonschema.validate(json.loads(line.strip()), schema)


def test_gq_003_answerability_distribution(loaded_questions):
    """GQ-003: Golden questions represent diverse answerability states."""
    ans_classes = {q.answerability for q in loaded_questions}
    assert AnswerabilityClass.ANSWERABLE in ans_classes
    assert AnswerabilityClass.NOT_FOUND in ans_classes
    assert AnswerabilityClass.RESTRICTED in ans_classes
    assert AnswerabilityClass.AMBIGUOUS in ans_classes
    assert AnswerabilityClass.CONFLICTING_EVIDENCE in ans_classes


def test_gq_004_evidence_grounding_validity(loaded_questions):
    """GQ-004: All answerable questions have specific source document and evidence citations."""
    for q in loaded_questions:
        if q.answerability == AnswerabilityClass.ANSWERABLE:
            assert len(q.required_evidence) >= 1
            for ev in q.required_evidence:
                assert ev.document_id in q.document_scope
                assert len(ev.evidence_text) > 0


def test_gq_005_partition_no_document_leakage(loaded_questions):
    """GQ-005: Deterministic partitioner guarantees zero document scope leakage across splits."""
    partitioner = QuestionPartitioner(seed=20261103)
    splits = partitioner.partition(loaded_questions, dev_ratio=0.60, val_ratio=0.20)

    dev_docs = {doc for q in splits["development"] for doc in q.document_scope}
    val_docs = {doc for q in splits["validation"] for doc in q.document_scope}
    holdout_docs = {doc for q in splits["holdout"] for doc in q.document_scope}

    assert len(dev_docs.intersection(val_docs)) == 0
    assert len(dev_docs.intersection(holdout_docs)) == 0
    assert len(val_docs.intersection(holdout_docs)) == 0


def test_gq_006_loader_filtering(loaded_questions):
    """GQ-006: Filter helper functions correctly subset by task type and answerability."""
    fact_qs = GoldenQuestionLoader.filter_by_category(loaded_questions, TaskType.DIRECT_FACTUAL)
    assert len(fact_qs) == 20
    unans_qs = GoldenQuestionLoader.filter_by_answerability(loaded_questions, AnswerabilityClass.NOT_FOUND)
    assert len(unans_qs) > 0


def test_gq_007_difficulty_level_coverage(loaded_questions):
    """GQ-007: Questions span operational difficulty levels (easy, medium, hard, expert)."""
    diffs = {q.difficulty for q in loaded_questions}
    assert DifficultyLevel.EASY in diffs
    assert DifficultyLevel.MEDIUM in diffs
    assert DifficultyLevel.HARD in diffs
    assert DifficultyLevel.EXPERT in diffs
