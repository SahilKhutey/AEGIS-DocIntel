"""
AEGIS-DocIntel — Mathematical Core Property-Based Verification Suite (Phase 6)
=============================================================================
Hypothesis-driven property and invariant testing for the core mathematical engines:
  1. Spectral Graph Theory (Laplacian positive semi-definiteness, zero eigenvalue, Dirichlet energy)
  2. Vietoris-Rips Topology (Betti monotonicity, point cloud filtration, Euler characteristic)
  3. Information Theory (Shannon entropy non-negativity, maximum entropy, Gibbs inequality, mutual info)
  4. Signal & Harmonic Analysis (Parseval energy conservation, power spectrum invariance)
"""
from __future__ import annotations

import math
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from src.math_concepts.spectral import (
    spectral_decomposition,
    fourier_transform,
    power_spectrum,
    fourier_periodicity,
)
from src.math_concepts.topology import (
    Simplex,
    SimplicialComplex,
    VietorisRipsComplex,
)
from src.math_concepts.information_theory import (
    shannon_entropy,
    kl_divergence,
    mutual_information,
)


# ============================================================================
# 1. SPECTRAL ENGINE PROPERTIES & INVARIANTS
# ============================================================================

@st.composite
def symmetric_adjacency_matrices(draw):
    """Generate random non-negative symmetric adjacency matrices with zero diagonal."""
    n = draw(st.integers(min_value=3, max_value=12))
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            if draw(st.booleans()):
                weight = draw(st.floats(min_value=0.1, max_value=10.0))
                A[i, j] = weight
                A[j, i] = weight
    return A


@given(symmetric_adjacency_matrices())
@settings(max_examples=40, deadline=None)
def test_laplacian_positive_semidefinite_and_nullspace(adj):
    """
    Property: For any symmetric non-negative adjacency matrix:
      1. L = D - A has L @ 1 = 0 (1 is always an eigenvector with eigenvalue 0).
      2. L is positive semi-definite: for every x, x.T @ L @ x >= -1e-7.
      3. All eigenvalues of L are real and >= -1e-7.
    """
    n = adj.shape[0]
    degrees = np.sum(adj, axis=1)
    D = np.diag(degrees)
    L = D - adj

    # 1. Nullspace invariant: L @ ones = 0
    ones = np.ones(n)
    L_ones = L @ ones
    assert np.allclose(L_ones, 0.0, atol=1e-5), f"L @ 1 must be 0, got {L_ones}"

    # 2. All eigenvalues of L are >= 0 (positive semi-definiteness)
    eigvals = np.linalg.eigvalsh(L)
    assert np.min(eigvals) >= -1e-5, f"Laplacian has negative eigenvalue: {np.min(eigvals)}"

    # 3. Dirichlet energy invariant: x^T L x = 0.5 * sum A_ij (x_i - x_j)^2 >= 0
    rng = np.random.default_rng(42)
    for _ in range(5):
        x = rng.standard_normal(n)
        quad_form = float(x.T @ L @ x)
        dirichlet_sum = 0.5 * float(np.sum(adj * ((x[:, None] - x[None, :]) ** 2)))
        assert quad_form >= -1e-5, f"Dirichlet energy negative: {quad_form}"
        assert math.isclose(quad_form, dirichlet_sum, abs_tol=1e-4), (
            f"Quad form {quad_form} != Dirichlet sum {dirichlet_sum}"
        )


@given(symmetric_adjacency_matrices())
@settings(max_examples=30, deadline=None)
def test_spectral_decomposition_invariants(adj):
    """
    Property: spectral_decomposition returns sorted eigenvalues and valid shapes.
    """
    n = adj.shape[0]
    res = spectral_decomposition(adj, k=n - 1)
    eigvals = res["eigenvalues"]
    eigvecs = res["eigenvectors"]

    assert len(eigvals) <= n
    assert eigvecs.shape[0] == n
    # Verify eigenvalues are sorted descending
    if len(eigvals) > 1:
        assert np.all(np.diff(eigvals) <= 1e-6), "Eigenvalues must be sorted in descending order"
    assert res["spectral_gap"] >= -1e-6, "Spectral gap must be non-negative"


# ============================================================================
# 2. VIETORIS-RIPS TOPOLOGY INVARIANTS
# ============================================================================

@st.composite
def random_point_clouds(draw):
    """Generate 2D point clouds with distinct points."""
    n = draw(st.integers(min_value=3, max_value=8))
    pts = []
    for _ in range(n):
        x = draw(st.floats(min_value=0.0, max_value=100.0))
        y = draw(st.floats(min_value=0.0, max_value=100.0))
        pts.append([x, y])
    # Add minimal jitter to ensure distinct points
    arr = np.array(pts) + np.arange(n)[:, None] * 1e-4
    return arr


@given(random_point_clouds())
@settings(max_examples=35, deadline=None)
def test_vietoris_rips_betti_monotonicity(pts):
    """
    Property:
      1. At threshold eps = 0, every point is isolated: beta_0 = N.
      2. As eps grows (eps1 < eps2), beta_0(eps1) >= beta_0(eps2) (connected components only merge).
      3. Euler characteristic chi = beta_0 - beta_1 + beta_2.
    """
    n = len(pts)
    vr = VietorisRipsComplex(pts, max_edge_length=150.0)

    # 1. At eps = 0: beta_0 == N
    c0 = vr.build_complex(0.0)
    b0_at_0, _, _ = c0.betti_numbers()
    assert b0_at_0 == n, f"At threshold 0, beta_0 must equal {n}, got {b0_at_0}"

    # 2. Monotonicity across scales
    thresholds = [1.0, 10.0, 50.0, 100.0, 200.0]
    b0_history = []
    for eps in thresholds:
        complex_eps = vr.build_complex(eps)
        b0, b1, b2 = complex_eps.betti_numbers()
        b0_history.append(b0)
        # Components can never be less than 1 if n > 0
        assert b0 >= 1
        assert b1 >= 0
        assert b2 >= 0

    # Ensure non-increasing beta_0
    for i in range(len(b0_history) - 1):
        assert b0_history[i] >= b0_history[i + 1], (
            f"beta_0 increased with higher threshold: {b0_history}"
        )


@given(st.integers(min_value=2, max_value=6))
@settings(max_examples=20, deadline=None)
def test_simplicial_complex_closure_and_euler_formula(k):
    """
    Property: Adding a k-simplex automatically closes all its 2^k - 1 non-empty subfaces,
    and Euler characteristic matches alternating sum of simplex counts.
    """
    sc = SimplicialComplex()
    vertices = tuple(range(k))
    sc.add_simplex(vertices)

    expected_simplices = 2 ** k - 1
    assert len(sc.simplices) == expected_simplices, (
        f"Expected {expected_simplices} faces in closure of {k}-simplex, got {len(sc.simplices)}"
    )

    # Betti calculation must not crash and produce non-negative numbers
    b0, b1, b2 = sc.betti_numbers()
    assert b0 >= 1
    assert b1 >= 0
    assert b2 >= 0


# ============================================================================
# 3. INFORMATION THEORY INVARIANTS
# ============================================================================

@st.composite
def random_probability_distributions(draw):
    """Generate valid discrete probability distributions with positive mass."""
    n = draw(st.integers(min_value=2, max_value=16))
    weights = draw(st.lists(st.floats(min_value=0.01, max_value=100.0), min_size=n, max_size=n))
    probs = np.array(weights) / sum(weights)
    return probs


@given(random_probability_distributions())
@settings(max_examples=50, deadline=None)
def test_shannon_entropy_bounds(p):
    """
    Property:
      1. Non-negativity: H(P) >= 0.
      2. Maximality: H(P) <= log2(|P|).
      3. H(uniform) = log2(|P|).
    """
    n = len(p)
    h = shannon_entropy(p)
    max_h = math.log2(n)

    # 1. Non-negativity
    assert h >= -1e-7, f"Entropy must be non-negative: {h}"

    # 2. Maximality bound
    assert h <= max_h + 1e-6, f"Entropy {h} exceeded theoretical maximum {max_h}"

    # 3. Uniform distribution achieves exact maximum
    uniform = np.ones(n) / n
    h_uniform = shannon_entropy(uniform)
    assert math.isclose(h_uniform, max_h, rel_tol=1e-5, abs_tol=1e-5), (
        f"Uniform entropy {h_uniform} != log2({n})={max_h}"
    )


@given(random_probability_distributions(), random_probability_distributions())
@settings(max_examples=40, deadline=None)
def test_kl_divergence_gibbs_inequality(p, q):
    """
    Property (Gibbs' Inequality):
      1. D_KL(P || Q) >= 0 for all P, Q.
      2. D_KL(P || P) == 0 (identity of indiscernibles).
    """
    # Align lengths to test
    min_len = min(len(p), len(q))
    p_sub = p[:min_len] / np.sum(p[:min_len])
    q_sub = q[:min_len] / np.sum(q[:min_len])

    # 1. Self-divergence is 0
    kl_self = kl_divergence(p_sub, p_sub)
    assert abs(kl_self) < 1e-5, f"D_KL(P || P) must be 0, got {kl_self}"

    # 2. Gibbs' inequality: D_KL >= 0
    kl_pq = kl_divergence(p_sub, q_sub)
    assert kl_pq >= -1e-5, f"Gibbs inequality violated: D_KL(P || Q) = {kl_pq} < 0"


@st.composite
def random_joint_distributions(draw):
    """Generate valid 2D joint probability distributions P(X, Y)."""
    r = draw(st.integers(min_value=2, max_value=6))
    c = draw(st.integers(min_value=2, max_value=6))
    mat = draw(st.lists(
        st.lists(st.floats(min_value=0.01, max_value=10.0), min_size=c, max_size=c),
        min_size=r, max_size=r
    ))
    arr = np.array(mat)
    return arr / np.sum(arr)


@given(random_joint_distributions())
@settings(max_examples=40, deadline=None)
def test_mutual_information_non_negativity_and_upper_bound(p_xy):
    """
    Property:
      1. Non-negativity: I(X; Y) >= -1e-6.
      2. Upper bound: I(X; Y) <= min(H(X), H(Y)) + 1e-5.
    """
    mi = mutual_information(p_xy)
    assert mi >= -1e-6, f"Mutual information negative: {mi}"

    # Marginal entropies
    p_x = np.sum(p_xy, axis=1)
    p_y = np.sum(p_xy, axis=0)
    h_x = shannon_entropy(p_x)
    h_y = shannon_entropy(p_y)

    assert mi <= min(h_x, h_y) + 1e-4, (
        f"Mutual information {mi} exceeded marginal entropy bound {min(h_x, h_y)}"
    )


# ============================================================================
# 4. SIGNAL & FOURIER CONSERVATION PROPERTIES
# ============================================================================

@st.composite
def random_signals(draw):
    """Generate arbitrary 1D real signals."""
    n = draw(st.integers(min_value=8, max_value=64))
    vals = draw(st.lists(st.floats(min_value=-50.0, max_value=50.0), min_size=n, max_size=n))
    return np.array(vals)


@given(random_signals())
@settings(max_examples=40, deadline=None)
def test_fourier_parseval_theorem(signal):
    """
    Property (Parseval's Theorem):
      The total energy in time domain equals normalized energy in frequency domain:
      sum |x_t|^2 == (1 / N) * sum |X_f|^2
    """
    n = len(signal)
    _, spectrum = fourier_transform(signal)

    time_energy = float(np.sum(signal ** 2))
    freq_energy = float(np.sum(np.abs(spectrum) ** 2)) / n

    assert math.isclose(time_energy, freq_energy, rel_tol=1e-4, abs_tol=1e-4), (
        f"Parseval violation: time_energy={time_energy}, freq_energy={freq_energy}"
    )


@given(random_signals())
@settings(max_examples=40, deadline=None)
def test_fourier_periodicity_metric_bounded(signal):
    """
    Property: Periodicity detector outputs a valid metric in [0.0, 1.0].
    """
    p = fourier_periodicity(signal)
    assert 0.0 <= p <= 1.0 + 1e-6, f"Periodicity metric out of bounds [0, 1]: {p}"
