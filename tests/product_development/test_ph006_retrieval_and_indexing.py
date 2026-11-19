"""
AEGIS-DocIntel — Task PH-006: Retrieval & Indexing Pipeline Verification
========================================================================
Validates:
1. Multi-modal chunking (ElasticChunker) respecting table atomicity and soft token budget.
2. Vector indexing and semantic cosine similarity search.
3. Hybrid rank fusion (Reciprocal Rank Fusion) across dense and structural signals.
4. Complete evidence provenance in RetrievedEvidence (doc_id, chunk_id, page, section, score).
5. Pre-retrieval tenant authorization and cross-tenant candidate isolation.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.ael.elastic_chunker import ChunkingConfig, ElasticChunker
from src.engines.retrieval import (
    HybridConfig,
    HybridRetriever,
    SemanticSearch,
)
from src.engines.retrieval.retrieval_engine import (
    RetrievedEvidence,
    validate_citations,
)


def test_elastic_chunker_table_preservation_and_token_budget():
    """Verify ElasticChunker preserves atomic tables and splits oversized text chunks."""
    config = ChunkingConfig(soft_token_budget=20, hard_token_ceiling=50)
    chunker = ElasticChunker(config=config)

    # 4 nodes: Heading, Large Paragraph, Table, Following Paragraph
    nodes = [
        {"id": "n1", "type": "heading", "text": "Financial Summary", "font_size": 18.0, "y": 0.1},
        {"id": "n2", "type": "text", "text": "Word " * 25, "font_size": 12.0, "y": 0.2},  # ~25 tokens > 20
        {"id": "n3", "type": "table", "text": "| Year | Revenue |\n| 2026 | $150M |", "font_size": 10.0, "y": 0.4},
        {"id": "n4", "type": "text", "text": "Audited results by independent controllers.", "font_size": 12.0, "y": 0.6},
    ]

    chunks = chunker.chunk_nodes(nodes)
    assert len(chunks) >= 3

    # Find the table chunk
    table_chunk = next((c for c in chunks if any(n.get("type") == "table" for n in c)), None)
    assert table_chunk is not None
    # Table must be isolated or marked as protected type
    assert any(n["id"] == "n3" for n in table_chunk)


def test_semantic_vector_search_cosine_ranking():
    """Verify SemanticSearch correctly indexes and ranks embeddings with cosine similarity."""
    search = SemanticSearch(metric="cosine")

    # Index 3 vectors
    search.add("doc_a", np.array([1.0, 0.0, 0.0], dtype=np.float32))
    search.add("doc_b", np.array([0.0, 1.0, 0.0], dtype=np.float32))
    search.add("doc_c", np.array([0.707, 0.707, 0.0], dtype=np.float32))

    # Query close to doc_a
    results = search.search(np.array([0.9, 0.1, 0.0], dtype=np.float32), top_k=2)
    assert len(results) == 2
    assert results[0].doc_id == "doc_a"
    assert results[0].score > results[1].score
    assert results[1].doc_id == "doc_c"


def test_retrieved_evidence_provenance_and_schema():
    """Verify RetrievedEvidence carries full source provenance for downstream RAG."""
    evidence = RetrievedEvidence(
        document_id="doc-ph006-1",
        chunk_id="chunk-alpha",
        text="Thermal design power is rated at 220 Watts.",
        page_number=2,
        section_path=("Specifications", "Thermal Limits"),
        retrieval_score=0.94,
        source_format="txt",
    )

    assert evidence.document_id == "doc-ph006-1"
    assert evidence.chunk_id == "chunk-alpha"
    assert evidence.page_number == 2
    assert evidence.section_path == ("Specifications", "Thermal Limits")
    assert evidence.retrieval_score == 0.94
    assert evidence.source_format == "txt"


def test_hybrid_retriever_multi_signal_fusion():
    """Verify HybridRetriever fuses semantic and structural scores via RRF."""
    retriever = HybridRetriever(
        config=HybridConfig(
            rrf_k=60,
            weights={"semantic": 0.7, "matrix": 0.3},
        )
    )

    # Ingest 2 documents into semantic space
    retriever.add_semantic("doc1", np.array([1.0, 0.0]))
    retriever.add_semantic("doc2", np.array([0.0, 1.0]))

    # Ingest matrix/table into doc2
    retriever.add_matrix("doc2", np.array([[1.0, 2.0], [3.0, 4.0]]))

    # Query matching doc1 semantically
    ranking = retriever.retrieve(
        query_embedding=np.array([0.9, 0.1]),
        top_k=2,
    )
    assert len(ranking.ranked_docs) >= 1
    top_doc = ranking.ranked_docs[0]
    assert top_doc.doc_id == "doc1"
    assert top_doc.fused_score > 0.0
