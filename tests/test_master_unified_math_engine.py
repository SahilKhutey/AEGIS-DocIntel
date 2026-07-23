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
