"""Tests for the Spectral Engine."""

import sys
from pathlib import Path
import pytest
import numpy as np

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.engines.geometry.element import GeometricElement, BoundingBox, ElementType
from src.engines.spectral import (
    SpectralEngine, SpectralReport, AdjacencyMatrix, AdjacencyType,
    LaplacianBuilder, LaplacianType, LaplacianMatrix, EigenSolver, EigenResult,
    SpectralClusterer, SpectralClusterResult, Cluster, PatternDetector,
    PatternResult, Pattern, GraphSignal, HeatKernel, HeatDiffusionResult,
    GraphFourierTransform, FourierResult, SpectralEngineError, InvalidGraphError,
    EigenDecompositionError, ConvergenceError, InsufficientDataError,
)

# ============================================================
# HELPERS
# ============================================================

def make_clique_graph(n_per_clique: int = 5) -> tuple[int, list[tuple[int, int, float]]]:
    n = n_per_clique * 2
    edges = []
    # Clique 1
    for i in range(n_per_clique):
        for j in range(i + 1, n_per_clique):
            edges.append((i, j, 1.0))
    # Clique 2
    for i in range(n_per_clique, n):
        for j in range(i + 1, n):
            edges.append((i, j, 1.0))
    # One bridge edge
    edges.append((0, n_per_clique, 0.1))
    return n, edges


# ============================================================
# 1. ADJACENCY MATRIX
# ============================================================

def test_adjacency_from_edges():
    n = 4
    edges = [(0, 1, 1.5), (1, 2, 2.0), (2, 3, 0.5)]
    adj = AdjacencyMatrix.from_edges(n, edges)
    assert adj.size == 4
    assert adj.num_edges == 3
    assert adj.matrix[0, 1] == 1.5
    assert adj.matrix[1, 0] == 1.5
    assert adj.matrix[0, 0] == 0.0
    assert adj.is_weighted
    assert abs(adj.density - 0.5) < 1e-6


def test_adjacency_invalid():
    with pytest.raises(InvalidGraphError):
        AdjacencyMatrix(matrix=np.array([[]]))
    with pytest.raises(ValueError):
        AdjacencyMatrix(matrix=np.ones((2, 3)))
    with pytest.raises(InvalidGraphError):
        AdjacencyMatrix.from_edges(3, [(0, 3, 1.0)])


def test_adjacency_from_distance():
    distances = np.array([
        [0.0, 3.0],
        [3.0, 0.0]
    ])
    adj = AdjacencyMatrix.from_distance_matrix(distances, sigma=3.0)
    assert adj.size == 2
    assert abs(adj.matrix[0, 1] - np.exp(-1.0)) < 1e-6


def test_adjacency_from_similarity():
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ])
    adj = AdjacencyMatrix.from_similarity(embeddings)
    assert adj.size == 3
    assert adj.matrix[0, 1] == 0.0  # orthogonal
    assert adj.matrix[0, 2] > 0.0  # similar


# ============================================================
# 2. LAPLACIAN BUILDER
# ============================================================

def test_laplacian_unnormalized():
    adj = AdjacencyMatrix(matrix=np.array([
        [0.0, 2.0],
        [2.0, 0.0]
    ]))
    lap = LaplacianBuilder.build(adj, LaplacianType.UNNORMALIZED)
    assert not lap.is_normalized
    assert lap.is_symmetric
    assert lap.is_psd
    # L = D - A = [[2, -2], [-2, 2]]
    assert np.allclose(lap.matrix, np.array([[2.0, -2.0], [-2.0, 2.0]]))


def test_laplacian_symmetric_normalized():
    adj = AdjacencyMatrix(matrix=np.array([
        [0.0, 2.0],
        [2.0, 0.0]
    ]))
    lap = LaplacianBuilder.build(adj, LaplacianType.SYMMETRIC_NORMALIZED)
    assert lap.is_normalized
    assert lap.is_symmetric
    # L_sym = [[1, -1], [-1, 1]]
    assert np.allclose(lap.matrix, np.array([[1.0, -1.0], [-1.0, 1.0]]))


def test_laplacian_random_walk():
    adj = AdjacencyMatrix(matrix=np.array([
        [0.0, 1.0, 1.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0]
    ]))
    lap = LaplacianBuilder.build(adj, LaplacianType.RANDOM_WALK)
    assert lap.is_normalized
    assert not lap.is_symmetric
    # row sums of L_rw are 0
    assert np.allclose(lap.matrix.sum(axis=1), 0.0)


# ============================================================
# 3. EIGEN SOLVER
# ============================================================

def test_eigen_solve_dense():
    # Complete graph on 3 nodes
    adj = AdjacencyMatrix(matrix=np.array([
        [0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 0.0]
    ]))
    lap = LaplacianBuilder.build(adj, LaplacianType.UNNORMALIZED)
    solver = EigenSolver()
    res = solver.solve(lap)
    assert res.num_eigenvalues == 3
    assert abs(res.eigenvalues[0]) < 1e-10  # λ0 = 0
    assert abs(res.fiedler_value - 3.0) < 1e-6  # λ1 = n for complete graph
    assert res.num_zero_eigenvalues == 1
    assert len(res.spectral_gaps) == 2


def test_eigen_solve_sparse():
    n, edges = make_clique_graph(10)
    adj = AdjacencyMatrix.from_edges(n, edges)
    lap = LaplacianBuilder.build(adj, LaplacianType.SYMMETRIC_NORMALIZED)
    solver = EigenSolver()
    res = solver.solve(lap, k=5)
    # sparse solver might return k eigenvalues/vectors
    assert res.num_eigenvalues <= n


# ============================================================
# 4. SPECTRAL CLUSTERING
# ============================================================

def test_spectral_clustering_cliques():
    n, edges = make_clique_graph(8)
    adj = AdjacencyMatrix.from_edges(n, edges)
    clusterer = SpectralClusterer(n_clusters=2)
    res = clusterer.cluster(adj)
    assert res.n_clusters == 2
    assert len(res.clusters) == 2
    # Verify separation
    c0 = set(res.clusters[0].members)
    c1 = set(res.clusters[1].members)
    assert len(c0) == 8
    assert len(c1) == 8
    assert len(c0.intersection(c1)) == 0
    assert res.silhouette > 0.5


# ============================================================
# 5. PATTERN DETECTION
# ============================================================

def test_pattern_detection():
    n, edges = make_clique_graph(6)
    adj = AdjacencyMatrix.from_edges(n, edges)
    detector = PatternDetector()
    res = detector.detect(adj)
    assert res.num_patterns > 0
    assert len(res.bipartition) == 2
    # Check hubs (bridge nodes 0 and 6 should have high degree/centrality)
    assert len(res.hubs) > 0
    assert res.motif_correlations.shape[0] > 0


# ============================================================
# 6. GRAPH SIGNALS
# ============================================================

def test_graph_signals():
    sig = GraphSignal(values=np.array([1.0, 2.0, 3.0]), name="test")
    assert sig.size == 3
    assert sig.energy == 14.0
    assert sig.mean == 2.0
    assert sig.max == 3.0
    assert sig.min == 1.0

    sig_norm = sig.normalize()
    assert abs(sig_norm.energy - 1.0) < 1e-6

    sig_smooth = sig.smooth(np.array([2.0, 2.0, 2.0]))
    assert np.allclose(sig_smooth.values, np.array([2.0, 4.0, 6.0]))


# ============================================================
# 7. GRAPH FOURIER TRANSFORM
# ============================================================

def test_graph_fourier_transform():
    adj = AdjacencyMatrix(matrix=np.array([
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0]
    ]))
    lap = LaplacianBuilder.build(adj, LaplacianType.SYMMETRIC_NORMALIZED)
    eigen_res = EigenSolver().solve(lap)
    
    sig = GraphSignal(values=np.array([1.0, 2.0, 1.0]))
    fourier_res = GraphFourierTransform.forward(sig, eigen_res)
    assert len(fourier_res.coefficients) == 3
    assert fourier_res.energy_concentration > 0.0

    # Roundtrip
    sig_recon = GraphFourierTransform.inverse(fourier_res, eigen_res)
    assert np.allclose(sig.values, sig_recon.values)

    # Lowpass
    sig_lp = GraphFourierTransform.filter_lowpass(sig, eigen_res, cutoff=1)
    assert sig_lp.size == 3


# ============================================================
# 8. HEAT KERNEL DIFFUSION
# ============================================================

def test_heat_kernel_diffusion():
    adj = AdjacencyMatrix(matrix=np.array([
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0]
    ]))
    initial = np.array([1.0, 0.0, 0.0])
    times = [0.1, 0.5, 1.0]
    kernel = HeatKernel()
    res = kernel.diffuse(adj, initial, times)
    assert len(res.diffused_signals) == 3
    assert 1.0 in res.diffused_signals
    assert len(res.diagonal) == 3
    assert len(res.heat_sources) == 1
    assert res.heat_sources[0] == 0

    # Importance Ranking
    ranking = kernel.importance_ranking(adj, seed_vertices=[0], t=0.5)
    assert len(ranking) == 3
    assert ranking[0] > ranking[2] # node 0 should retain more heat than node 2


# ============================================================
# 9. INTEGRATION ORCHESTRATOR
# ============================================================

def test_spectral_engine_orchestrator():
    n, edges = make_clique_graph(5)
    adj = AdjacencyMatrix.from_edges(n, edges)
    signal = GraphSignal(values=np.arange(n, dtype=float))
    
    engine = SpectralEngine()
    report = engine.analyze_graph(
        adjacency=adj,
        laplacian_type=LaplacianType.SYMMETRIC_NORMALIZED,
        n_clusters=2,
        signal=signal,
        times=[0.5, 1.0]
    )
    
    assert report.adjacency.size == 10
    assert report.clustering.n_clusters == 2
    assert len(report.patterns.patterns) > 0
    assert report.fourier is not None
    assert report.heat is not None
    
    report_dict = report.to_dict()
    assert report_dict["adjacency"]["size"] == 10
    assert report_dict["clustering"]["n_clusters"] == 2
    assert "fourier" in report_dict
    assert "heat" in report_dict


# ============================================================
# 10. EXCEPTIONS & BOUNDS
# ============================================================

def test_spectral_engine_exceptions():
    engine = SpectralEngine()
    # Insufficient data
    adj = AdjacencyMatrix(matrix=np.array([[0.0]]))
    with pytest.raises(InsufficientDataError):
        engine.analyze_graph(adj)


# ============================================================
# 11. LEGACY backward compatibility APIs
# ============================================================

def test_spectral_engine_legacy_apis():
    engine = SpectralEngine()
    
    # Sine wave signal representing periodic spacing
    t = np.linspace(0, 10, 32)
    signal = np.sin(t)
    
    freqs, power = engine.fourier_transform(signal)
    assert len(freqs) == 32
    
    periodicity = engine.compute_periodicity(signal)
    assert periodicity > 0.0
    
    adj = np.array([
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0]
    ], dtype=np.float64)
    eigvals = engine.eigenvalue_decomposition(adj, k=2)
    assert len(eigvals) == 2
    assert eigvals[0] > 0.0

    # analyze method
    sig = engine.analyze(signal, adj)
    assert sig.periodicity == periodicity
    assert len(sig.eigenvalues) == 3

    # element profiling and entropy
    el1 = GeometricElement(element_id="1", content="Quantum decoherence", page=1, type=ElementType.TEXT, bbox=BoundingBox(0.0,0.0,0.5,0.1))
    el2 = GeometricElement(element_id="2", content="System fidelity", page=1, type=ElementType.TEXT, bbox=BoundingBox(0.0,0.2,0.5,0.3))
    engine.fit_idf([el1, el2])
    
    ent1 = engine.element_entropy(el1)
    assert ent1 > 0.0
    
    score1 = engine.entropy_score(el1)
    assert 0.0 <= score1 <= 1.0

    profiles = engine.profile_elements([el1, el2])
    assert len(profiles) == 2
    assert profiles[0].entropy > 0.0
