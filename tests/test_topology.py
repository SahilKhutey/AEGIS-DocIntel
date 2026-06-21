"""Tests for the Topology Engine."""

import sys
from pathlib import Path
import pytest
import numpy as np
import networkx as nx

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.engines.geometry.element import GeometricElement, BoundingBox, ElementType
from src.engines.topology import (
    TopologyEngine, TopologicalSignature, DocumentManifold,
    ConnectedComponentsAnalyzer, ConnectedComponentsResult,
    LoopsAnalyzer, LoopsResult, Loop,
    TopologicalClusters, ClustersResult, Cluster,
    PersistenceAnalyzer, PersistenceResult, PersistenceDiagram, PersistencePoint,
    VietorisRipsFiltration, SimplicialComplex, Simplex,
    BettiNumbers, EulerCharacteristic, DistanceMatrix, TopologicalMetrics,
    TopologyEngineError, InvalidManifoldError, InsufficientDataError,
)


# ============================================================
# HELPERS
# ============================================================

def make_element(element_id: str, x: float, y: float) -> GeometricElement:
    return GeometricElement(
        element_id=element_id,
        content=f"Content of {element_id}",
        page=1,
        type=ElementType.TEXT,
        bbox=BoundingBox(x0=x, y0=y, x1=x + 0.05, y1=y + 0.05),
    )


# ============================================================
# 1. SIMPLEX & SIMPLICIAL COMPLEX
# ============================================================

def test_simplex_creation():
    s = Simplex(frozenset({1, 2, 3}), weight=0.5)
    assert s.dimension == 2
    assert s.weight == 0.5
    assert len(s.faces()) == 6 # 3 vertices + 3 edges
    assert Simplex(frozenset({1, 2})).is_face_of(s)
    assert not Simplex(frozenset({1, 4})).is_face_of(s)


def test_simplex_empty():
    with pytest.raises(TopologyEngineError):
        Simplex(frozenset())


def test_simplicial_complex():
    sc = SimplicialComplex()
    assert sc.num_vertices == 0
    assert sc.num_edges == 0

    sc.add_simplex(Simplex(frozenset({0, 1}), weight=0.2))
    assert sc.num_vertices == 2
    assert sc.num_edges == 1
    assert sc.max_dimension == 1

    # Adding high dim automatically adds faces
    sc.add_simplex(Simplex(frozenset({0, 1, 2}), weight=0.5))
    assert sc.num_vertices == 3
    assert sc.num_edges == 3
    assert sc.num_triangles == 1
    assert sc.max_dimension == 2
    assert len(sc) == 7 # 3 vertices + 3 edges + 1 triangle


# ============================================================
# 2. DISTANCE MATRIX
# ============================================================

def test_distance_matrix():
    coords = np.array([
        [0.0, 0.0],
        [3.0, 0.0],
        [0.0, 4.0]
    ])
    dm = DistanceMatrix.from_coordinates(coords, labels=["A", "B", "C"])
    assert dm.size == 3
    assert abs(dm.matrix[0, 1] - 3.0) < 1e-6
    assert abs(dm.matrix[0, 2] - 4.0) < 1e-6
    assert abs(dm.matrix[1, 2] - 5.0) < 1e-6
    assert dm.max_distance == 5.0
    assert dm.min_distance == 3.0
    assert abs(dm.mean_distance - 4.0) < 1e-6


def test_distance_matrix_invalid():
    with pytest.raises(ValueError):
        DistanceMatrix(matrix=np.ones((2, 3)))
    with pytest.raises(InsufficientDataError):
        DistanceMatrix(matrix=np.zeros((1, 1)))


# ============================================================
# 3. VIETORIS-RIPS FILTRATION
# ============================================================

def test_vietoris_rips_filtration():
    coords = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ])
    dm = DistanceMatrix.from_coordinates(coords)
    vr = VietorisRipsFiltration(dm, max_edge_length=1.5, max_dimension=2)
    filtration = vr.build_filtration()
    
    assert len(filtration) > 0
    # Birth of vertices at 0
    assert filtration[0][0] == 0.0
    assert filtration[0][1].num_vertices == 4
    assert filtration[0][1].num_edges == 0

    # Last step should have edges
    assert filtration[-1][1].num_edges == 6 # 4 sides + 2 diagonals (length 1.0, 1.0, 1.0, 1.0, 1.414, 1.414)


# ============================================================
# 4. CONNECTED COMPONENTS (H0)
# ============================================================

def test_connected_components():
    sc = SimplicialComplex()
    # 2 disjoint components: {0, 1} and {2, 3}
    sc.add_simplex(Simplex(frozenset({0, 1})))
    sc.add_simplex(Simplex(frozenset({2, 3})))

    analyzer = ConnectedComponentsAnalyzer()
    res = analyzer.analyze(sc)
    
    assert res.betti_0 == 2
    assert len(res.components) == 2
    assert res.largest_component_size == 2
    assert res.smallest_component_size == 2
    assert res.mean_component_size == 2.0
    assert res.component_map[0] != res.component_map[2]


# ============================================================
# 5. CYCLE DETECTION (H1)
# ============================================================

def test_loops_analyzer_triangle():
    sc = SimplicialComplex()
    # A single filled triangle {0, 1, 2}
    sc.add_simplex(Simplex(frozenset({0, 1, 2})))

    analyzer = LoopsAnalyzer()
    res = analyzer.analyze(sc)
    # The triangle is filled, so H1 should be 0!
    assert res.betti_1 == 0


def test_loops_analyzer_circle():
    sc = SimplicialComplex()
    # An empty loop {0, 1}, {1, 2}, {2, 0}
    sc.add_simplex(Simplex(frozenset({0, 1})))
    sc.add_simplex(Simplex(frozenset({1, 2})))
    sc.add_simplex(Simplex(frozenset({2, 0})))

    analyzer = LoopsAnalyzer()
    res = analyzer.analyze(sc)
    # No 2-simplices, so H1 should be 1!
    assert res.betti_1 == 1
    assert len(res.loops) == 1
    assert res.loops[0].length == 3


# ============================================================
# 6. TOPOLOGICAL CLUSTERS (H2)
# ============================================================

def test_topological_clusters():
    sc = SimplicialComplex()
    # Two well-separated triangles
    sc.add_simplex(Simplex(frozenset({0, 1, 2})))
    sc.add_simplex(Simplex(frozenset({3, 4, 5})))

    clusters_analyzer = TopologicalClusters()
    res = clusters_analyzer.analyze(sc, n_clusters=2)
    
    assert res.num_clusters == 2
    assert res.largest_cluster_size == 3
    assert res.mean_cluster_size == 3.0
    # Group 1 and Group 2 should be separated
    assert res.cluster_map[0] == res.cluster_map[1]
    assert res.cluster_map[0] != res.cluster_map[3]


# ============================================================
# 7. PERSISTENT HOMOLOGY
# ============================================================

def test_persistent_homology():
    coords = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ])
    dm = DistanceMatrix.from_coordinates(coords)
    vr = VietorisRipsFiltration(dm, max_edge_length=2.0, max_dimension=2)
    filtration = vr.build_filtration()

    analyzer = PersistenceAnalyzer(max_dimension=2)
    res = analyzer.analyze(filtration)

    assert res.diagram.num_features > 0
    # There should be exactly one infinite H0 component
    h0_points = res.diagram.by_dimension(0)
    assert any(p.is_infinite for p in h0_points)
    
    # H1 loops and H2 voids
    h1_points = res.diagram.by_dimension(1)
    h2_points = res.diagram.by_dimension(2)
    assert len(h0_points) > 0


# ============================================================
# 8. METRICS, BETTI & EULER CHARACTERISTIC
# ============================================================

def test_betti_and_euler():
    sc = SimplicialComplex()
    # Empty loop: Betti_0 = 1, Betti_1 = 1, Betti_2 = 0
    sc.add_simplex(Simplex(frozenset({0, 1})))
    sc.add_simplex(Simplex(frozenset({1, 2})))
    sc.add_simplex(Simplex(frozenset({2, 0})))

    betti = BettiNumbers.compute(sc)
    assert betti.betti_0 == 1
    assert betti.betti_1 == 1
    assert betti.betti_2 == 0

    euler = EulerCharacteristic.from_betti(betti)
    assert euler.value == 0 # Betti: 1 - 1 + 0 = 0

    euler_complex = EulerCharacteristic.from_complex(sc)
    assert euler_complex.value == 0 # Simplex: 3 vertices - 3 edges = 0


# ============================================================
# 9. DOCUMENT MANIFOLD & TOPOLOGY ENGINE
# ============================================================

def test_document_manifold():
    elements = [
        make_element("e1", 0.0, 0.0),
        make_element("e2", 0.1, 0.1),
        make_element("e3", 0.5, 0.5),
    ]
    manifold = DocumentManifold.from_elements(elements, use_spatial=True)
    assert len(manifold.elements) == 3
    assert manifold.coordinates.shape == (3, 2)
    
    dm = manifold.compute_distance_matrix()
    assert dm.size == 3


def test_topology_engine_legacy():
    engine = TopologyEngine(proximity_threshold=0.3)
    positions = {
        "A": (0.0, 0.0),
        "B": (0.1, 0.0),
        "C": (0.0, 0.2),
        "D": (0.5, 0.5),
    }

    # Test legacy methods
    G = engine.build_proximity_graph(positions)
    assert G.number_of_nodes() == 4
    assert G.has_edge("A", "B")
    assert G.has_edge("A", "C")
    assert not G.has_edge("A", "D")

    betti_tuple = engine.compute_betti_numbers(G)
    assert betti_tuple[0] == 2 # components: {A, B, C} and {D}
    assert betti_tuple[1] == 1 # loop A-B-C

    ph = engine.persistent_homology(positions)
    assert len(ph) > 0


def test_topology_engine_analyze():
    engine = TopologyEngine(proximity_threshold=0.3)
    elements = [
        make_element("e1", 0.0, 0.0),
        make_element("e2", 0.1, 0.0),
        make_element("e3", 0.0, 0.2),
        make_element("e4", 0.5, 0.5),
    ]

    sig = engine.analyze(elements)
    assert isinstance(sig, TopologicalSignature)
    assert sig.betti_0 == 2
    assert sig.betti_1 == 0
    assert sig.euler_characteristic == 2 # 2 - 0 + 0 = 2
    assert sig.metrics is not None
    assert sig.connected_components is not None
    assert sig.loops is not None
    assert sig.clusters is not None
    assert sig.persistence is not None


def test_topology_engine_insufficient_data():
    engine = TopologyEngine()
    with pytest.raises(InsufficientDataError):
        engine.analyze([make_element("e1", 0.0, 0.0)])
