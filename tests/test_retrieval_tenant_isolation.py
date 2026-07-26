"""
Phase 0 Audit Test Suite: Tenant Isolation across all 7 Retrieval Search Backends.

Tests that SemanticSearch, FrequencySearch, GeometrySearch, GraphSearch,
MatrixSearch, RecurrenceSearch, and TemplateSearch enforce strict tenant boundaries
and prevent cross-tenant data leakage when executing queries with tenant_id specified.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.engines.retrieval.semantic_search import SemanticSearch
from src.engines.retrieval.frequency_search import FrequencySearch
from src.engines.retrieval.geometry_search import GeometrySearch
from src.engines.retrieval.graph_search import GraphSearch
from src.engines.retrieval.matrix_search import MatrixSearch
from src.engines.retrieval.recurrence_search import RecurrenceSearch
from src.engines.retrieval.template_search import TemplateSearch


def test_semantic_search_tenant_isolation():
    engine = SemanticSearch(metric="cosine")
    v_a = np.array([1.0, 0.0, 0.0])
    v_b = np.array([0.9, 0.1, 0.0])
    
    engine.add("doc_a", v_a, tenant_id="tenant-a")
    engine.add("doc_b", v_b, tenant_id="tenant-b")
    
    # Query with tenant-a must NOT return tenant-b doc
    res_a = engine.search(v_a, top_k=10, tenant_id="tenant-a")
    assert len(res_a) == 1
    assert res_a[0].doc_id == "doc_a"

    # Query with tenant-b must NOT return tenant-a doc
    res_b = engine.search(v_a, top_k=10, tenant_id="tenant-b")
    assert len(res_b) == 1
    assert res_b[0].doc_id == "doc_b"


def test_frequency_search_tenant_isolation():
    engine = FrequencySearch(method="bm25")
    tokens = ["aegis", "document", "intelligence"]
    
    engine.add("doc_a", tokens, tenant_id="tenant-a")
    engine.add("doc_b", tokens, tenant_id="tenant-b")
    
    res_a = engine.search(["aegis"], top_k=10, tenant_id="tenant-a")
    assert len(res_a) == 1
    assert res_a[0].doc_id == "doc_a"

    res_b = engine.search(["aegis"], top_k=10, tenant_id="tenant-b")
    assert len(res_b) == 1
    assert res_b[0].doc_id == "doc_b"


def test_geometry_search_tenant_isolation():
    engine = GeometrySearch(metric="euclidean")
    coord = np.array([10.0, 20.0])
    
    engine.add("item_a", coord, tenant_id="tenant-a")
    engine.add("item_b", coord, tenant_id="tenant-b")
    
    knn_a = engine.knn(coord, k=10, tenant_id="tenant-a")
    assert len(knn_a) == 1
    assert knn_a[0].item_id == "item_a"

    radius_a = engine.radius(coord, radius=5.0, tenant_id="tenant-a")
    assert len(radius_a) == 1
    assert radius_a[0].item_id == "item_a"

    bbox_a = engine.bbox((0.0, 0.0, 30.0, 30.0), tenant_id="tenant-a")
    assert len(bbox_a) == 1
    assert bbox_a[0].item_id == "item_a"


def test_graph_search_tenant_isolation():
    engine = GraphSearch()
    engine.add_node("node_a", tenant_id="tenant-a")
    engine.add_node("node_a_child", tenant_id="tenant-a")
    engine.add_node("node_b", tenant_id="tenant-b")
    
    engine.add_edge("node_a", "node_a_child")
    engine.add_edge("node_a", "node_b")

    results_a = engine.bfs("node_a", max_depth=2, tenant_id="tenant-a")
    retrieved_ids = [r.node_id for r in results_a]
    assert "node_a" in retrieved_ids
    assert "node_a_child" in retrieved_ids
    assert "node_b" not in retrieved_ids


def test_matrix_search_tenant_isolation():
    engine = MatrixSearch()
    mat = np.array([[1.0, 2.0], [3.0, 4.0]])
    
    engine.add("table_a", mat, tenant_id="tenant-a")
    engine.add("table_b", mat, tenant_id="tenant-b")
    
    query_v = np.array([1.0, 2.0])
    cols_a = engine.search_column(query_v, top_k=10, tenant_id="tenant-a")
    assert all("table_a" in r.item_id for r in cols_a)
    assert not any("table_b" in r.item_id for r in cols_a)

    rows_a = engine.search_row(query_v, top_k=10, tenant_id="tenant-a")
    assert all("table_a" in r.item_id for r in rows_a)
    assert not any("table_b" in r.item_id for r in rows_a)


def test_recurrence_search_tenant_isolation():
    engine = RecurrenceSearch(num_hashes=16, bands=4, rows_per_band=4)
    item_set = {101, 102, 103, 104}
    
    engine.add("rec_a", item_set, tenant_id="tenant-a")
    engine.add("rec_b", item_set, tenant_id="tenant-b")
    
    res_a = engine.query(item_set, top_k=10, tenant_id="tenant-a")
    assert len(res_a) == 1
    assert res_a[0].item_id == "rec_a"


def test_template_search_tenant_isolation():
    engine = TemplateSearch(fingerprint_type="binary")
    fp = np.array([1, 0, 1, 1, 0], dtype=np.int8)
    
    engine.add("tmpl_a", fp, tenant_id="tenant-a")
    engine.add("tmpl_b", fp, tenant_id="tenant-b")
    
    res_a = engine.search(fp, top_k=10, tenant_id="tenant-a")
    assert len(res_a) == 1
    assert res_a[0].template_id == "tmpl_a"
