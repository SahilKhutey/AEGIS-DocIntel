"""
Extended test suite for the 7 retrieval backends in src/engines/retrieval/.

Covers edge cases, shape mismatches, sink nodes in PageRank,
mathematical stability, and hybrid fusion.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.engines.retrieval import (
    FrequencySearch,
    GeometrySearch,
    GraphSearch,
    HybridConfig,
    HybridRetriever,
    MatrixSearch,
    RecurrenceSearch,
    SemanticSearch,
    TemplateSearch,
)


def test_matrix_search_svd_query_shape_mismatch() -> None:
    """
    Test that MatrixSearch.search_semantic_svd handles query vectors whose shape
    does not match the table row dimension gracefully without crashing.
    """
    search = MatrixSearch()
    # 4 rows x 2 cols matrix
    table_4x2 = np.array([
        [1.0, 0.0],
        [2.0, 0.0],
        [3.0, 0.0],
        [4.0, 1.0],
    ])
    search.add("table1", table_4x2)

    # Query vector has length 2 (fewer than 4 rows)
    query_short = np.array([1.0, 2.0])

    # Must not raise shape mismatch exception in search_semantic_svd
    res = search.search_semantic_svd(query_short, n_components=1)
    assert res == []

    # Matching query vector length 4
    query_exact = np.array([1.0, 2.0, 3.0, 4.0])
    res_exact = search.search_semantic_svd(query_exact, n_components=1)
    assert len(res_exact) == 2
    assert res_exact[0].item_id == "table1::svd_col_0"


def test_graph_pagerank_dangling_nodes_mass_conservation() -> None:
    """
    Test that Personalized PageRank on graphs with dangling (sink) nodes
    conserves total probability mass (sum of scores == 1.0).
    """
    search = GraphSearch(damping=0.85, max_iter=100)
    # A -> B -> C (C has no outgoing edges: sink node)
    search.add_node("A")
    search.add_node("B")
    search.add_node("C")
    search.add_edge("A", "B", directed=True)
    search.add_edge("B", "C", directed=True)

    results = search.personalized_pagerank(seed_nodes=["A"], top_k=3)
    assert len(results) == 3

    total_mass = sum(r.score for r in results)
    assert pytest.approx(total_mass, abs=1e-4) == 1.0
    assert results[0].node_id in ("A", "B", "C")


def test_frequency_tfidf_single_doc_smooth_idf() -> None:
    """
    Test that FrequencySearch TF-IDF handles single-document indices
    without returning 0 score for unique terms due to non-smoothed log(1/1).
    """
    search = FrequencySearch(method="tfidf")
    search.add("doc1", ["apple", "banana"])

    res = search.search(["apple"], top_k=1)
    assert len(res) == 1
    assert res[0].doc_id == "doc1"
    assert res[0].score > 0.0


def test_template_search_numerical_empty_fingerprint() -> None:
    """
    Test TemplateSearch numerical comparison with zero-length or zero-norm vectors.
    """
    search = TemplateSearch(fingerprint_type="numerical")
    search.add("t_zero", [0.0, 0.0, 0.0])
    search.add("t_normal", [1.0, 2.0, 3.0])

    res = search.search([0.0, 0.0, 0.0], top_k=2)
    assert len(res) == 2
    # Zero vector query with zero vector target should be handled safely
    assert res[0].similarity >= 0.0


def test_geometry_search_metric_types() -> None:
    """
    Test GeometrySearch with euclidean, manhattan, and chebyshev metrics.
    """
    for metric in ("euclidean", "manhattan", "chebyshev"):
        search = GeometrySearch(metric=metric)
        search.add("p1", np.array([0.0, 0.0]))
        search.add("p2", np.array([3.0, 4.0]))

        knn_res = search.knn(np.array([0.0, 0.0]), k=2)
        assert len(knn_res) == 2
        assert knn_res[0].item_id == "p1"
        assert knn_res[0].distance == 0.0


def test_recurrence_search_min_similarity_filter() -> None:
    """
    Test RecurrenceSearch min_similarity filtering.
    """
    search = RecurrenceSearch(num_hashes=16, bands=4, rows_per_band=4)
    search.add("doc1", {1, 2, 3, 4, 5})
    search.add("doc2", {10, 11, 12, 13, 14})

    # Query matching doc1
    res = search.query({1, 2, 3, 4}, min_similarity=0.5)
    assert len(res) >= 1
    assert res[0].item_id == "doc1"


def test_hybrid_retriever_full_pipeline_all_backends() -> None:
    """
    Test HybridRetriever populating and querying all 7 backends simultaneously.
    """
    retriever = HybridRetriever(config=HybridConfig(fusion_method="rrf"))

    # Populate 7 search backends
    retriever.add_semantic("doc1", np.array([1.0, 0.0, 0.0]))
    retriever.add_matrix("tab1", np.array([[1.0, 2.0], [3.0, 4.0]]))
    retriever.add_geometry("geo1", np.array([1.0, 1.0]))
    retriever.add_graph_node("node1")
    retriever.add_graph_edge("node1", "node2")
    retriever.add_template("tmpl1", np.array([1, 0, 1]))
    retriever.add_frequency("doc1", ["query", "term"])
    retriever.add_recurrence("doc1", {1, 2, 3, 4})

    # Execute hybrid query
    ranking = retriever.retrieve(
        query_embedding=np.array([1.0, 0.0, 0.0]),
        query_matrix_vec=np.array([1.0, 3.0]),
        query_coords=np.array([1.0, 1.0]),
        query_graph_seeds=["node1"],
        query_fingerprint=np.array([1, 0, 1]),
        query_tokens=["query"],
        query_set={1, 2, 3},
        top_k=5,
    )

    assert ranking.num_docs > 0
    assert ranking.num_sources > 0
    assert len(ranking.ranked_docs) > 0
