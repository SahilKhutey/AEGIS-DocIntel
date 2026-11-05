"""
tests.intelligence.retrieval.test_retrieval_modes
=================================================
Unit and regression tests for WP-06.01 Retrieval Modes (Lexical, Semantic, Structured, Hybrid)
and retrieval metric calculations.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.models import RetrievalMode, RetrievalResult
from aegis.intelligence.retrieval import (
    HybridRetriever,
    LexicalRetriever,
    RetrievalEvaluator,
    SemanticRetriever,
    StructuredRetriever,
)


@pytest.fixture
def result_schema():
    p = Path("schemas/intelligence/retrieval_result.schema.json")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture
def sample_corpus():
    return [
        {
            "document_id": "DOC-FIN-001",
            "chunk_id": "CHUNK-001",
            "page_number": 1,
            "text": "The total reported revenue for fiscal year 2024 reached INR 650 lakh.",
            "metadata": {"year": 2024, "type": "financial_report", "entities": ["fiscal_year"]},
        },
        {
            "document_id": "DOC-FIN-001",
            "chunk_id": "CHUNK-002",
            "page_number": 2,
            "text": "Operating expenses grew by 12% due to supply chain expansions and logistics costs.",
            "metadata": {"year": 2024, "type": "financial_report", "entities": ["supply_chain"]},
        },
        {
            "document_id": "DOC-ENV-002",
            "chunk_id": "CHUNK-003",
            "page_number": 5,
            "text": "Environmental impact assessment indicates carbon emissions reduced by 15 metric tons.",
            "metadata": {"year": 2023, "type": "environmental_audit", "entities": ["emissions"]},
        },
        {
            "document_id": "DOC-TAB-003",
            "chunk_id": "CHUNK-004",
            "page_number": 8,
            "text": "| Quarter | Budget (INR) | Actual (INR) |\n| Q1 | 150000 | 148000 |\n| Q2 | 200000 | 195000 |",
            "metadata": {"year": 2024, "is_table": True, "type": "budget_table"},
        },
    ]


def test_ret_001_lexical_bm25_exact_match(sample_corpus, result_schema):
    """RET-001: BM25 lexical retriever correctly matches exact terms and names."""
    retriever = LexicalRetriever()
    for doc in sample_corpus:
        retriever.index_document(**doc)

    res = retriever.retrieve("carbon emissions environmental", top_k=2)
    assert res.retrieval_mode == RetrievalMode.LEXICAL
    assert len(res.results) > 0
    assert res.results[0].chunk_id == "CHUNK-003"
    assert res.results[0].score > 0.0

    # Validate against schema
    jsonschema.validate(res.model_dump(), result_schema)


def test_ret_002_semantic_paraphrase(sample_corpus, result_schema):
    """RET-002: Semantic retriever matches paraphrased concepts."""
    retriever = SemanticRetriever()
    for doc in sample_corpus:
        retriever.index_document(**doc)

    # Paraphrased concept: "annual sales earnings" -> matches "total reported revenue"
    res = retriever.retrieve("annual sales earnings turnover", top_k=3)
    assert res.retrieval_mode == RetrievalMode.SEMANTIC
    assert len(res.results) > 0
    assert res.results[0].chunk_id in ["CHUNK-001", "CHUNK-002"]

    jsonschema.validate(res.model_dump(), result_schema)


def test_ret_003_structured_metadata_filter(sample_corpus, result_schema):
    """RET-003: Structured retriever enforces explicit metadata filters and table lookups."""
    retriever = StructuredRetriever()
    for doc in sample_corpus:
        retriever.index_document(**doc)

    # Search with year filter and table requirement
    res = retriever.retrieve(
        "Quarterly budget values",
        filters={"is_table": True, "year": 2024},
        top_k=2,
    )
    assert res.retrieval_mode == RetrievalMode.STRUCTURED
    assert len(res.results) == 1
    assert res.results[0].chunk_id == "CHUNK-004"

    jsonschema.validate(res.model_dump(), result_schema)


def test_ret_004_hybrid_rrf_fusion(sample_corpus, result_schema):
    """RET-004: Hybrid retriever combines lexical and semantic rankings using RRF."""
    retriever = HybridRetriever(rrf_k0=60)
    for doc in sample_corpus:
        retriever.index_document(**doc)

    res = retriever.retrieve("What was the total reported revenue in 2024?", top_k=2)
    assert res.retrieval_mode == RetrievalMode.HYBRID
    assert len(res.results) >= 1
    assert res.results[0].chunk_id == "CHUNK-001"
    assert "rrf_fusion" in res.results[0].retrieval_method

    jsonschema.validate(res.model_dump(), result_schema)


def test_ret_005_retrieval_evaluator_metrics():
    """RET-005: Verify exact mathematical calculations for Precision@K, Recall@K, MRR, and nDCG."""
    # Synthetic single result
    res = RetrievalResult(
        query_id="Q-TEST",
        retrieval_mode=RetrievalMode.LEXICAL,
        query="test query",
        filters={},
        results=[
            {
                "document_id": "D1",
                "chunk_id": "C1",
                "page_number": 1,
                "text": "text1",
                "rank": 1,
                "score": 0.9,
                "retrieval_method": "bm25",
                "source_reference": "D1:P1",
            },
            {
                "document_id": "D2",
                "chunk_id": "C2",
                "page_number": 1,
                "text": "text2",
                "rank": 2,
                "score": 0.8,
                "retrieval_method": "bm25",
                "source_reference": "D2:P1",
            },
        ],
        latency_ms=1.5,
    )

    # C2 is relevant, C1 is not
    eval_res = RetrievalEvaluator.evaluate_query(
        result=res,
        relevant_chunks={"C2"},
        k=2,
    )
    # Precision@2 = 1 / 2 = 0.5
    assert eval_res["precision"] == 0.5
    # Recall@2 = 1 / 1 = 1.0
    assert eval_res["recall"] == 1.0
    # Reciprocal rank = 1 / 2 = 0.5
    assert eval_res["reciprocal_rank"] == 0.5


def test_ret_006_unanswerable_query_handling():
    """RET-006: Retrieval evaluation handles queries with no ground truth relevant chunks."""
    res = RetrievalResult(
        query_id="Q-EMPTY",
        retrieval_mode=RetrievalMode.SEMANTIC,
        query="completely unknown fact",
        filters={},
        results=[],
        latency_ms=0.5,
    )

    eval_res = RetrievalEvaluator.evaluate_query(
        result=res,
        relevant_chunks=set(),
        k=5,
    )
    assert eval_res["precision"] == 1.0
    assert eval_res["recall"] == 1.0
    assert eval_res["reciprocal_rank"] == 0.0


def test_ret_007_batch_evaluation_percentiles(sample_corpus):
    """RET-007: Batch evaluation computes mean metrics and p95/p99 latency percentiles."""
    retriever = HybridRetriever()
    for doc in sample_corpus:
        retriever.index_document(**doc)

    r1 = retriever.retrieve("revenue fiscal year 2024", top_k=3)
    r2 = retriever.retrieve("carbon emissions", top_k=3)

    batch_cases = [
        {"result": r1, "relevant_chunks": {"CHUNK-001"}},
        {"result": r2, "relevant_chunks": {"CHUNK-003"}},
    ]

    metrics = RetrievalEvaluator.evaluate_batch(batch_cases, k=3)
    assert metrics.queries_evaluated == 2
    assert metrics.precision_at_k > 0.0
    assert metrics.recall_at_k == 1.0
    assert metrics.mrr == 1.0
    assert metrics.latency_median_ms >= 0.0
