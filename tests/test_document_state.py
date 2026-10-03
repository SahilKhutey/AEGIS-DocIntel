"""
Unit tests for the Canonical DocumentState Schema: D = (P, S, G, R, F, M, T, X, H, E).
"""

import pytest
from pydantic import ValidationError

from src.core.document_state import (
    DocumentState,
    PhysicalLayer,
    BoundingBox,
    LayoutElement,
    ReadingOrderDAG,
    SemanticLayer,
    Keyphrase,
    Entity,
    GraphLayer,
    GraphNode,
    GraphEdge,
    MatrixLayer,
    TableData,
    TopologyLayer,
    PersistenceInterval,
    InfoPhysicsLayer,
    HypergraphLayer,
    HyperEdge,
    TelemetryLayer,
)


def test_document_state_default_instantiation():
    """Verify clean instantiation of all 10 mathematical layers."""
    state = DocumentState()
    assert state.doc_id is not None
    assert state.tenant_id == "default"
    assert state.page_count == 1

    # Verify mathematical aliases
    assert state.P is state.physical
    assert state.S is state.semantic
    assert state.G is state.graph
    assert state.R is state.recurrence
    assert state.F is state.spectral
    assert state.M is state.matrix
    assert state.T is state.topology
    assert state.X is state.physics
    assert state.H is state.hypergraph
    assert state.E is state.telemetry


def test_bounding_box_geometry():
    """Verify BoundingBox geometry calculations."""
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=60.0, y1=100.0)
    assert bbox.width == 50.0
    assert bbox.height == 80.0
    assert bbox.area == 4000.0


def test_euler_characteristic_invariant():
    """Verify Euler-Poincare characteristic chi = sum (-1)^k beta_k."""
    # Default: beta = [1, 0, 0] -> chi = 1
    t1 = TopologyLayer()
    assert t1.euler_characteristic == 1

    # Torus: beta_0 = 1, beta_1 = 2, beta_2 = 1 -> chi = 1 - 2 + 1 = 0
    t2 = TopologyLayer(betti_numbers=[1, 2, 1])
    assert t2.euler_characteristic == 0

    # Complex with 3 connected components and 5 loops: beta_0 = 3, beta_1 = 5 -> chi = 3 - 5 = -2
    t3 = TopologyLayer(betti_numbers=[3, 5])
    assert t3.euler_characteristic == -2


def test_persistence_interval_validation():
    """Verify death >= birth validation."""
    valid = PersistenceInterval(dimension=1, birth=0.5, death=1.2)
    assert valid.birth == 0.5
    assert valid.death == 1.2

    with pytest.raises(ValidationError):
        PersistenceInterval(dimension=1, birth=1.5, death=0.5)


def test_pipeline_stage_telemetry():
    """Verify stage telemetry recording and cumulative duration."""
    state = DocumentState()
    assert len(state.telemetry.stages) == 0
    assert state.telemetry.total_latency_ms == 0.0

    state.record_stage("ingest", 12.5, success=True)
    state.record_stage("geometry", 25.0, success=True)
    state.record_stage("topology", 15.0, success=True)

    assert len(state.telemetry.stages) == 3
    assert state.telemetry.total_latency_ms == 52.5
    summary = state.summary()
    assert "ingest" in summary["stages_completed"]
    assert "geometry" in summary["stages_completed"]
    assert "topology" in summary["stages_completed"]


def test_state_transition_validation():
    """Verify monotonic pipeline invariants across state transitions."""
    state1 = DocumentState()
    state1.record_stage("ingest", 10.0)

    # Valid forward transition
    state2 = state1.model_copy(deep=True)
    state2.record_stage("parse", 20.0)
    assert DocumentState.validate_transition(state1, state2) is True

    # Invalid: doc_id mutated
    state_mutated_doc = state2.model_copy(deep=True)
    state_mutated_doc.telemetry.doc_id = "different-uuid"
    with pytest.raises(ValueError, match="doc_id changed"):
        DocumentState.validate_transition(state2, state_mutated_doc)

    # Invalid: tenant_id mutated
    state_mutated_tenant = state2.model_copy(deep=True)
    state_mutated_tenant.telemetry.tenant_id = "tenant-evil"
    with pytest.raises(ValueError, match="tenant_id changed"):
        DocumentState.validate_transition(state2, state_mutated_tenant)

    # Invalid: stage history truncated
    state_truncated = state2.model_copy(deep=True)
    state_truncated.telemetry.stages = []
    with pytest.raises(ValueError, match="stage history was truncated"):
        DocumentState.validate_transition(state2, state_truncated)


def test_to_ueo_bridge():
    """Verify lossless conversion from DocumentState to UniversalExportObject."""
    state = DocumentState()
    state.telemetry.source_filename = "financial_report.pdf"
    state.physical.elements.append(
        LayoutElement(
            element_id="el_001",
            content="Operating revenue increased by 22% in Q4.",
            page=1,
            bbox=BoundingBox(x0=0.1, y0=0.1, x1=0.9, y1=0.2),
            importance_weight=0.95,
        )
    )
    state.semantic.keyphrases.append(Keyphrase(text="operating revenue", score=0.88))
    state.semantic.entities.append(Entity(text="Q4", type="DATE", confidence=0.99, page=1))
    state.matrix.tables.append(
        TableData(
            table_id="tbl_001",
            page=1,
            headers=["Quarter", "Revenue"],
            rows=[["Q3", "100M"], ["Q4", "122M"]],
            computed_metrics={"revenue_growth": 0.22},
        )
    )
    state.graph.nodes.append(GraphNode(id="n1", label="Revenue"))
    state.graph.edges.append(GraphEdge(src="n1", dst="n2", type="grew_in", weight=1.0))

    ueo = state.to_ueo(query="What was Q4 revenue?")
    assert ueo.metadata.document_name == "financial_report.pdf"
    assert ueo.metadata.total_elements == 1
    assert ueo.metadata.total_tables == 1
    assert len(ueo.citations) == 1
    assert ueo.citations[0].element_id == "el_001"
    assert len(ueo.matrix.tables) == 1
    assert ueo.matrix.tables[0]["computed_metrics"]["revenue_growth"] == 0.22


def test_serialization_roundtrip():
    """Verify JSON serialization and deserialization integrity."""
    state = DocumentState()
    state.telemetry.source_filename = "contract.pdf"
    state.physical.total_words = 1250
    state.physics.shannon_entropy = 4.32
    state.hypergraph.hyperedges.append(
        HyperEdge(edge_id="he1", node_ids=["n1", "n2", "t1"], weight=0.75)
    )

    json_data = state.model_dump_json()
    reconstructed = DocumentState.model_validate_json(json_data)

    assert reconstructed.doc_id == state.doc_id
    assert reconstructed.telemetry.source_filename == "contract.pdf"
    assert reconstructed.physical.total_words == 1250
    assert reconstructed.physics.shannon_entropy == 4.32
    assert len(reconstructed.hypergraph.hyperedges) == 1
    assert reconstructed.hypergraph.hyperedges[0].node_ids == ["n1", "n2", "t1"]
