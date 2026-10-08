"""
Tests for aegis_docprep.reading_order.
"""

from __future__ import annotations

import random
import pytest
from hypothesis import given, settings, strategies as st

from aegis_docprep.reading_order import (
    ReadingGraphConfig,
    SpatialReadingGraph,
    compute_opw_distance,
    flag_fragile_edges,
    is_reading_forward_successor,
    ollivier_ricci_curvature,
    order_preserving_wasserstein_distance,
)


def test_two_column_reading_order():
    """Verifies that reading order correctly reconstructs document layout from shuffled inputs."""
    title = {"id": "title", "x": 0.1, "y": 0.05, "w": 0.8, "h": 0.05}
    col_a1 = {"id": "col_a1", "x": 0.1, "y": 0.15, "w": 0.35, "h": 0.1}
    col_b1 = {"id": "col_b1", "x": 0.55, "y": 0.15, "w": 0.35, "h": 0.1}
    col_a2 = {"id": "col_a2", "x": 0.1, "y": 0.30, "w": 0.35, "h": 0.1}
    col_b2 = {"id": "col_b2", "x": 0.55, "y": 0.30, "w": 0.35, "h": 0.1}
    footer = {"id": "footer", "x": 0.1, "y": 0.80, "w": 0.8, "h": 0.05}

    # Shuffled input order
    elements = [footer, col_b2, col_a2, col_b1, col_a1, title]

    graph = SpatialReadingGraph()
    ordered = graph.extract_reading_order(elements)
    ordered_ids = [el["id"] for el in ordered]

    assert ordered_ids == ["title", "col_a1", "col_b1", "col_a2", "col_b2", "footer"]


def test_opw_distance():
    seq_a = ["a", "b", "c", "d"]
    seq_b = ["a", "b", "c", "d"]
    assert order_preserving_wasserstein_distance(seq_a, seq_b) == 0.0

    seq_c = ["d", "c", "b", "a"]
    dist = order_preserving_wasserstein_distance(seq_a, seq_c)
    assert dist > 0.0

    res = compute_opw_distance(seq_a, seq_b)
    assert res["distance"] == 0.0
    assert len(res["transport_plan"]) == 4


def test_ollivier_ricci_curvature_and_flagging():
    nodes = [
        {"id": "n1", "x": 0.0, "y": 0.0},
        {"id": "n2", "x": 2.0, "y": 0.0},  # Distance 2.0 -> negative curvature
    ]
    edges = [("n1", "n2")]
    curv = ollivier_ricci_curvature(nodes, edges)
    assert ("n1", "n2") in curv
    assert curv[("n1", "n2")] < 0.0

    fragile = flag_fragile_edges(curv, threshold=-0.5)
    assert ("n1", "n2") in fragile


# ============================================================================
# Theorem 6.1 & 6.2 Property-Based Verification
# ============================================================================

@st.composite
def dag_elements_and_edges(draw):
    num_nodes = draw(st.integers(min_value=3, max_value=20))
    elements = []
    for i in range(num_nodes):
        elements.append({
            "id": f"node_{i}",
            "x": draw(st.floats(min_value=0.0, max_value=600.0)),
            "y": draw(st.floats(min_value=0.0, max_value=800.0)),
            "w": draw(st.floats(min_value=10.0, max_value=200.0)),
            "h": draw(st.floats(min_value=10.0, max_value=50.0)),
        })

    edges: dict[str, list[tuple[str, float]]] = {el["id"]: [] for el in elements}
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if draw(st.booleans()) and draw(st.booleans()):
                edges[f"node_{i}"].append((f"node_{j}", 1.0))

    return elements, edges


@given(dag_elements_and_edges())
@settings(max_examples=30, deadline=None)
def test_theorem_6_1_spatial_dag_acyclicity_and_coverage(graph_data):
    """Theorem 6.1: Full coverage and topological precedence."""
    elements, edges = graph_data
    reader = SpatialReadingGraph()
    recovered = reader.recover_reading_order(elements, edges)

    assert len(recovered) == len(elements)
    recovered_ids = [el["id"] for el in recovered]
    assert set(recovered_ids) == set(el["id"] for el in elements)

    pos_map = {nid: pos for pos, nid in enumerate(recovered_ids)}
    for u_id, neighbors in edges.items():
        for v_id, _ in neighbors:
            assert pos_map[u_id] < pos_map[v_id]


@given(dag_elements_and_edges())
@settings(max_examples=30, deadline=None)
def test_theorem_6_2_kahn_topological_determinism(graph_data):
    """Theorem 6.2: Invariance under permutation of input list."""
    elements, edges = graph_data
    reader = SpatialReadingGraph()

    order_1 = reader.recover_reading_order(elements, edges)
    order_1_ids = [el["id"] for el in order_1]

    shuffled_elements = list(elements)
    random.shuffle(shuffled_elements)

    order_2 = reader.recover_reading_order(shuffled_elements, edges)
    order_2_ids = [el["id"] for el in order_2]

    assert order_1_ids == order_2_ids
