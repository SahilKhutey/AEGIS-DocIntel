"""
tests/test_retrieval_grounding.py
==================================
P2.4 Retrieval Quality, Answer Grounding & Evidence Integrity Verification:
1. RetrievedEvidence schema carries document_id, chunk_id, page_number, section_path, score.
2. Citation verification detects fabricated/hallucinated chunk citations.
3. Pre-retrieval tenant authorization prevents cross-tenant candidate leakages.
4. Model abstention on unanswerable queries when evidence is insufficient.
5. Hybrid retrieval Reciprocal Rank Fusion (RRF) ranking.
"""
from __future__ import annotations

import numpy as np
import pytest
from src.core.orchestrator import AMDIOrchestrator
from src.engines.geometry.element import BoundingBox, ElementType, GeometricElement
from src.engines.retrieval.hybrid_retrieval import HybridConfig, HybridRetriever
from src.engines.retrieval.retrieval_engine import (
    CitationValidationResult,
    RetrievedEvidence,
    validate_citations,
)


def test_retrieved_evidence_schema_and_provenance():
    """P2.4: RetrievedEvidence retains complete source provenance metadata."""
    ev = RetrievedEvidence(
        document_id="doc-evidence-001",
        chunk_id="chunk-p2-4",
        text="Net revenue for the fiscal quarter rose 14% to $120M.",
        page_number=4,
        section_path=("Financial Statements", "Income Statement"),
        retrieval_score=0.92,
        source_format="pdf",
    )

    assert ev.document_id == "doc-evidence-001"
    assert ev.chunk_id == "chunk-p2-4"
    assert ev.page_number == 4
    assert ev.section_path == ("Financial Statements", "Income Statement")
    assert ev.retrieval_score == 0.92
    assert ev.source_format == "pdf"


def test_citation_validation_detects_valid_citations():
    """P2.4: All citations matching retrieved evidence validate successfully."""
    evidence = [
        RetrievedEvidence(
            document_id="doc-1",
            chunk_id="chk-101",
            text="Revenue increased.",
            page_number=1,
            section_path=("Summary",),
            retrieval_score=0.88,
        ),
        RetrievedEvidence(
            document_id="doc-1",
            chunk_id="chk-102",
            text="Operating margins expanded.",
            page_number=2,
            section_path=("Financials",),
            retrieval_score=0.82,
        ),
    ]

    citations = [
        {"chunk_id": "chk-101", "doc_id": "doc-1", "snippet": "Revenue increased."},
        {"chunk_id": "chk-102", "doc_id": "doc-1", "snippet": "Operating margins."},
    ]

    res = validate_citations(citations, evidence, tenant_id="tenant-alpha")
    assert res.is_valid is True
    assert res.total_citations == 2
    assert res.valid_citations == 2
    assert len(res.invalid_citations) == 0


def test_citation_validation_flags_hallucinated_citations():
    """P2.4: Invented chunk IDs or foreign doc IDs are flagged as invalid."""
    evidence = [
        RetrievedEvidence(
            document_id="doc-1",
            chunk_id="chk-real-1",
            text="Real factual statement.",
            page_number=1,
            section_path=(),
            retrieval_score=0.9,
        )
    ]

    hallucinated_citations = [
        {"chunk_id": "chk-real-1", "doc_id": "doc-1"},
        {"chunk_id": "chk-fake-999", "doc_id": "doc-1"},  # Invented chunk
        {"chunk_id": "chk-foreign-2", "doc_id": "doc-9"},  # Foreign document
    ]

    res = validate_citations(hallucinated_citations, evidence, tenant_id="tenant-alpha")
    assert res.is_valid is False
    assert res.total_citations == 3
    assert res.valid_citations == 1
    assert len(res.invalid_citations) == 2
    assert res.invalid_citations[0]["chunk_id"] == "chk-fake-999"


@pytest.mark.asyncio
async def test_unanswerable_query_triggers_abstention():
    """P2.4: Queries with zero matching evidence cleanly abstain instead of hallucinating."""
    orchestrator = AMDIOrchestrator(config={"embedding_dim": 64})
    # Query an empty orchestrator with no documents ingested
    result = await orchestrator.query(
        question="What was the total revenue in fiscal year 2025?",
        tenant_id="tenant-empty",
    )

    assert result["grounded"] is False
    assert result["confidence"] == 0.0
    assert "I do not have sufficient evidence" in result["answer"]


@pytest.mark.asyncio
async def test_pre_retrieval_tenant_authorization():
    """P2.4: Candidate search space is strictly partitioned by tenant before retrieval scoring."""
    orchestrator = AMDIOrchestrator(config={"embedding_dim": 64})

    # Ingest doc for Tenant A
    from src.models.document_object import DocumentObject
    doc_a = DocumentObject(
        doc_id="doc-tenant-a",
        filename="confidential_a.txt",
        raw_bytes=b"Alpha confidential secrets and mergers.",
        tenant_id="tenant-a",
    )
    await orchestrator.ingest(doc_a)

    # Ingest doc for Tenant B
    doc_b = DocumentObject(
        doc_id="doc-tenant-b",
        filename="confidential_b.txt",
        raw_bytes=b"Beta proprietary strategy blueprints.",
        tenant_id="tenant-b",
    )
    await orchestrator.ingest(doc_b)

    # Query from Tenant A scoping doc_id of Tenant B must raise PermissionError
    with pytest.raises(PermissionError, match="belongs to a different tenant"):
        await orchestrator.query(
            question="What is Beta strategy?",
            doc_id="doc-tenant-b",
            tenant_id="tenant-a",
        )

    # Scoped query from Tenant A cannot see Tenant B's documents
    res_a = await orchestrator.query(
        question="What are confidential secrets?",
        tenant_id="tenant-a",
    )
    assert res_a.get("doc_id") == "doc-tenant-a"


def test_hybrid_retrieval_rrf_scoring():
    """P2.4: HybridRetriever fuses semantic and frequency ranks via Reciprocal Rank Fusion."""
    config = HybridConfig(fusion_method="rrf", rrf_k=60, top_k=5)
    retriever = HybridRetriever(config=config)

    # Populate 3 documents with embeddings and frequency tokens
    emb1 = np.array([1.0, 0.0, 0.0])
    emb2 = np.array([0.0, 1.0, 0.0])
    emb3 = np.array([0.0, 0.0, 1.0])

    retriever.add_semantic("doc_1", emb1)
    retriever.add_semantic("doc_2", emb2)
    retriever.add_semantic("doc_3", emb3)

    retriever.add_frequency("doc_1", ["revenue", "growth", "profit"])
    retriever.add_frequency("doc_2", ["revenue", "tax", "expenses"])
    retriever.add_frequency("doc_3", ["unrelated", "topic", "food"])

    # Query matching semantic emb1 and keyword "revenue"
    res = retriever.retrieve(query_embedding=emb1, query_tokens=["revenue", "growth"], top_k=3)
    assert res.num_sources >= 1
    ranked_docs = res.ranked_docs
    assert len(ranked_docs) > 0
    # doc_1 matches both semantic vector and frequency terms -> rank 1
    assert ranked_docs[0].doc_id == "doc_1"
    assert ranked_docs[0].fused_score > 0.0
    assert ranked_docs[0].fused_score > 0.0
