"""
Unit tests for the Hybrid Retrieval Engine.
"""

from __future__ import annotations

import pytest
import numpy as np

from src.engines.retrieval import (
    RetrievalEngine,
    RetrievalReport,
    HybridRetriever,
    HybridConfig,
    SemanticSearch,
    SemanticResult,
    MatrixSearch,
    MatrixResult,
    GeometrySearch,
    GeometryResult,
    GraphSearch,
    GraphResult,
    TemplateSearch,
    TemplateResult,
    FrequencySearch,
    FrequencyResult,
    RecurrenceSearch,
    RecurrenceResult,
    HybridRanker,
    HybridRanking,
    RankedDocument,
    RetrievalEngineError,
    EmptyIndexError,
    InvalidQueryError,
    RankFusionError,
    IndexDimensionError,
)

def test_semantic_search() -> None:
    search = SemanticSearch(metric="cosine")
    search.add("doc1", np.array([1.0, 0.0]))
    search.add("doc2", np.array([0.0, 1.0]))
    
    # Cosine match
    res = search.search(np.array([1.0, 0.1]), top_k=1)
    assert len(res) == 1
    assert res[0].doc_id == "doc1"
    assert res[0].score > 0.9
    
    # Dot product metric
    search_dot = SemanticSearch(metric="dot")
    search_dot.add("doc1", np.array([2.0, 0.0]))
    res_dot = search_dot.search(np.array([1.5, 0.0]))
    assert res_dot[0].score == 3.0

def test_matrix_search() -> None:
    search = MatrixSearch()
    table = np.array([[1.0, 2.0], [3.0, 4.0]])
    search.add("table1", table)
    
    # Column similarity
    cols = search.search_column(np.array([1.0, 3.0]))
    assert len(cols) > 0
    assert cols[0].item_id == "table1::col_0"
    
    # Cell value search
    cells = search.search_value(4.0, tolerance=0.1)
    assert len(cells) == 1
    assert cells[0].location == (1, 1)
    
    # SVD search
    svd_res = search.search_semantic_svd(np.array([1.0, 3.0]), n_components=1)
    assert len(svd_res) > 0

def test_geometry_search() -> None:
    search = GeometrySearch(metric="euclidean")
    search.add("p1", np.array([0.0, 0.0]))
    search.add("p2", np.array([10.0, 10.0]))
    
    # KNN
    knn_res = search.knn(np.array([1.0, 1.0]), k=1)
    assert knn_res[0].item_id == "p1"
    assert knn_res[0].similarity > 0.3
    
    # Radius
    rad_res = search.radius(np.array([1.0, 1.0]), radius=3.0)
    assert len(rad_res) == 1
    assert rad_res[0].item_id == "p1"
    
    # Bounding Box
    bbox_res = search.bbox((0.0, 0.0, 5.0, 5.0))
    assert len(bbox_res) == 1
    assert bbox_res[0].item_id == "p1"

def test_graph_search() -> None:
    search = GraphSearch(damping=0.85)
    search.add_node("A")
    search.add_node("B")
    search.add_edge("A", "B", weight=2.0, directed=True)
    
    # BFS
    bfs_res = search.bfs("A", max_depth=1)
    assert len(bfs_res) == 2
    assert bfs_res[1].node_id == "B"
    assert bfs_res[1].distance == 1
    
    # Personalized PageRank
    ppr_res = search.personalized_pagerank(["A"], top_k=2)
    assert len(ppr_res) == 2
    assert ppr_res[0].node_id == "A"

def test_template_search() -> None:
    search = TemplateSearch(fingerprint_type="set")
    search.add("t1", {1, 2, 3})
    search.add("t2", {4, 5, 6})
    
    # Jaccard set matching
    res = search.search({1, 2}, top_k=1)
    assert res[0].template_id == "t1"
    assert res[0].similarity > 0.5

def test_frequency_search() -> None:
    search = FrequencySearch(method="bm25")
    search.add("doc1", ["apple", "banana", "cherry"])
    search.add("doc2", ["cherry", "date", "fig"])
    
    res = search.search(["cherry", "apple"], top_k=2)
    assert len(res) == 2
    assert res[0].doc_id == "doc1"  # Matches both terms

def test_recurrence_search() -> None:
    search = RecurrenceSearch(num_hashes=16, bands=4, rows_per_band=4)
    search.add("doc1", {1, 2, 3, 4})
    search.add("doc2", {1, 2, 8, 9})
    
    res = search.query({1, 2, 3}, top_k=2)
    assert len(res) > 0
    assert res[0].item_id == "doc1"

def test_hybrid_ranker() -> None:
    ranker = HybridRanker(method="rrf", rrf_k=60)
    
    method_results = {
        "semantic": [("doc1", 0.9), ("doc2", 0.5)],
        "frequency": [("doc2", 0.8), ("doc1", 0.2)]
    }
    
    # RRF
    res_rrf = ranker.fuse(method_results)
    assert len(res_rrf.ranked_docs) == 2
    
    # Borda
    ranker_borda = HybridRanker(method="borda")
    res_borda = ranker_borda.fuse(method_results)
    assert len(res_borda.ranked_docs) == 2
    
    # Weighted Sum
    ranker_ws = HybridRanker(method="weighted_sum", weights={"semantic": 0.7, "frequency": 0.3})
    res_ws = ranker_ws.fuse(method_results)
    assert len(res_ws.ranked_docs) == 2
    
    # Condorcet
    ranker_cond = HybridRanker(method="condorcet")
    res_cond = ranker_cond.fuse(method_results)
    assert len(res_cond.ranked_docs) == 2

def test_hybrid_retriever_compatibility() -> None:
    # 1. Test legacy instantiation wrapper
    class MockEngine:
        pass
        
    mock_embed = MockEngine()
    mock_vs = MockEngine()
    mock_geo = MockEngine()
    mock_rec = MockEngine()
    mock_freq = MockEngine()
    mock_matrix = MockEngine()
    mock_tmpl = MockEngine()
    
    legacy_retriever = HybridRetriever(
        mock_embed,
        mock_vs,
        mock_geo,
        mock_rec,
        mock_freq,
        mock_matrix,
        mock_tmpl
    )
    assert hasattr(legacy_retriever, "vector_store")
    assert legacy_retriever.vector_store is mock_vs
    
    # 2. Test new config-driven instantiation
    config = HybridConfig(fusion_method="borda")
    new_retriever = HybridRetriever(config=config)
    assert hasattr(new_retriever, "semantic")
    assert new_retriever.config.fusion_method == "borda"

def test_retrieval_engine_e2e() -> None:
    engine = RetrievalEngine()
    
    # Index elements
    engine.add_semantic("doc1", np.array([1.0, 0.0]))
    engine.add_geometry("doc1", np.array([1.0, 1.0]))
    engine.add_frequency("doc1", ["cat", "dog"])
    
    engine.add_semantic("doc2", np.array([0.0, 1.0]))
    engine.add_geometry("doc2", np.array([10.0, 10.0]))
    engine.add_frequency("doc2", ["dog", "bird"])
    
    # Retrieve
    ranking = engine.retrieve(
        query_embedding=np.array([0.9, 0.1]),
        query_coords=np.array([1.1, 1.1]),
        query_tokens=["cat", "dog"]
    )
    
    assert len(ranking.ranked_docs) == 2
    assert ranking.ranked_docs[0].doc_id == "doc1"
    
    # Generate report
    report = engine.generate_report(ranking, latency_ms=12.5, metadata={"query": "test"})
    assert report.latency_ms == 12.5
    assert report.ranking is ranking
    assert report.to_dict()["ranking"]["method"] == "rrf"
