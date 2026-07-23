'''
AEGIS-DocIntel / AMDI-OS — Master Unified Math Engine Test Suite
================================================================
Verifies full 16-domain mathematical engine evaluation over document state D:
  - Topology, Spectral, Physics, Information Theory, Graph Theory, Optimization,
    Tensor, Probability, Statistics, Harmonic Analysis, Computational Geometry,
    Control Theory, Decision Theory, Dynamical Systems, Linear Algebra, Numerical Analysis
'''
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.math_concepts.master_math_engine import MasterUnifiedMathEngine
from src.main import app

client = TestClient(app)


def test_master_unified_math_engine_direct():
    engine = MasterUnifiedMathEngine()
    doc = {
        'id': 'doc_unified_1',
        'elements': [
            {'id': 'e1', 'text': 'Title header text', 'type': 'heading'},
            {'id': 'e2', 'text': 'Paragraph content text', 'type': 'paragraph'},
        ],
    }
    res = engine.evaluate_document_state(doc)

    assert res.document_id == 'doc_unified_1'
    assert res.topology_betti['betti_0'] >= 1
    assert res.spectral_gap >= 0.0
    assert res.entropy > 0.0
    assert len(res.domain_scores) == 16


def test_master_unified_math_engine_api_endpoint():
    resp = client.post(
        "/v1/advanced/math/unified-evaluation",
        json={
            "document": {
                "id": "doc_api_1",
                "elements": [{"id": "e1", "text": "Financial quarterly earnings report."}],
            }
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["document_id"] == "doc_api_1"
    assert "topology_betti" in data
    assert "condition_number" in data
    assert len(data["domain_scores"]) == 16


def test_spatial_reading_dag_construction():
    from src.math_concepts.graph_theory import build_spatial_reading_dag
    import networkx as nx

    elements = [
        {'id': 'e1', 'x': 0.1, 'y': 0.1, 'w': 0.8, 'h': 0.05},
        {'id': 'e2', 'x': 0.1, 'y': 0.2, 'w': 0.8, 'h': 0.05},
    ]
    dag = build_spatial_reading_dag(elements)
    assert nx.is_directed_acyclic_graph(dag)
    assert dag.has_edge(0, 1)


def test_hypergraph_spectral_clustering():
    from src.math_concepts.graph_theory import Hypergraph

    hg = Hypergraph(n_nodes=4, hyperedges=[[0, 1], [2, 3]])
    labels = hg.hypergraph_spectral_clustering(k=2)
    assert len(labels) == 4
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
