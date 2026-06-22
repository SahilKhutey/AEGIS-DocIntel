'''
AEGIS-MIOS — Math Concepts Unit Tests
======================================
Comprehensive test suite validating all 16 mathematical domains.
'''

from __future__ import annotations

import pytest
import numpy as np

# Import all math concepts
import src.math_concepts.physics as physics
import src.math_concepts.topology as topology
import src.math_concepts.spectral as spectral
import src.math_concepts.tensor as tensor
import src.math_concepts.graph_theory as graph_theory
import src.math_concepts.probability as probability
import src.math_concepts.optimization as optimization
import src.math_concepts.information_theory as inf_theory
import src.math_concepts.linear_algebra as lin_alg
import src.math_concepts.computational_geometry as comp_geom
import src.math_concepts.decision_theory as decision
import src.math_concepts.numerical_analysis as numerical
import src.math_concepts.control_theory as control
import src.math_concepts.dynamical_systems as dynamical
import src.math_concepts.harmonic_analysis as harmonic
import src.math_concepts.statistics as stats


# 1. Physics Engine Tests
def test_physics_engine():
    # Information Energy
    ie = physics.information_energy(2.5, 0.8)
    assert ie == pytest.approx(2.0)

    # total energy
    tot = physics.total_energy(np.array([2.0, 1.5]), np.array([0.5, 1.0]))
    assert tot == pytest.approx(2.5)

    # gravity
    g = physics.information_gravity(10.0, 5, 2.0, gravitational_constant=1.0)
    assert g == pytest.approx(12.5)

    # conservation
    cons = physics.verify_conservation(100.0, 85.0, 10.0, 5.0)
    assert cons['is_conserved'] is True
    assert cons['discard_ratio'] == pytest.approx(0.05)


# 2. Topology Engine Tests
def test_topology_engine():
    # Simplicial complex - triangle (2-simplex)
    sc = topology.SimplicialComplex()
    sc.add_simplex((0, 1, 2))
    # Betti numbers: β0=1 (connected), β1=0, β2=0
    b0, b1, b2 = sc.betti_numbers()
    assert b0 == 1
    assert b1 == 0
    assert b2 == 0

    # Intrinsic dimension
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [1.5, 0.0, 0.0]])
    dim = topology.manifold_dimension(pts)
    assert dim == 1


# 3. Spectral Engine Tests
def test_spectral_engine():
    adj = np.array([
        [0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 0.0]
    ])
    dec = spectral.spectral_decomposition(adj, k=2)
    assert len(dec['eigenvalues']) == 2
    assert dec['largest_eigenvalue'] > 0.0

    # Periodicity
    t = np.linspace(0, 10, 100)
    sig = np.sin(2.0 * np.pi * t)
    period = spectral.fourier_periodicity(sig)
    assert period > 0.5


# 4. Tensor Algebra Tests
def test_tensor_engine():
    T = np.random.rand(3, 4, 5)
    # Mode-n unfold and fold
    unfolded = tensor.mode_n_unfold(T, 1)
    assert unfolded.shape == (4, 15)
    refolded = tensor.mode_n_fold(unfolded, 1, T.shape)
    assert np.allclose(T, refolded)

    # Tucker decomposition
    core, factors = tensor.tucker_decomposition(T, ranks=(2, 2, 2))
    assert core.shape == (2, 2, 2)
    assert len(factors) == 3


# 5. Graph Theory Tests
def test_graph_theory():
    # Directed star-like graph adjacency
    adj = np.array([
        [0.0, 1.0, 1.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0]
    ])
    # PageRank power iteration
    pr = graph_theory.pagerank(adj)
    assert np.sum(pr) == pytest.approx(1.0)

    # Hypergraph
    hg = graph_theory.Hypergraph(n_nodes=4, hyperedges=[[0, 1], [1, 2, 3]])
    inc = hg.incidence_matrix()
    assert inc.shape == (4, 2)
    assert inc[1, 0] == 1.0
    assert inc[1, 1] == 1.0


# 6. Probability Engine Tests
def test_probability_engine():
    # Bayesian prior updates
    bi = probability.BayesianInference(prior=0.4)
    # update with positive likelihood
    p = bi.update(likelihood=0.8, evidence=0.6)
    assert p == pytest.approx(0.8 * 0.4 / 0.6)

    # HMM Viterbi decoding
    # 2 states, 2 observations
    hmm = probability.HiddenMarkovModel(n_states=2, n_observations=2)
    hmm.pi = np.array([0.6, 0.4])
    hmm.A = np.array([[0.7, 0.3], [0.4, 0.6]])
    hmm.B = np.array([[0.1, 0.9], [0.8, 0.2]])

    seq, prob = hmm.viterbi([0, 1, 0])
    assert len(seq) == 3
    assert prob < 0.0  # Log prob is negative


# 7. Optimization Engine Tests
def test_optimization_engine():
    # Pareto front
    objs = np.array([
        [1.0, 2.0],
        [2.0, 1.0],
        [0.5, 0.5],
        [2.0, 2.0]
    ])
    front = optimization.pareto_front(objs, maximize=True)
    # Only index 3 [2, 2] is non-dominated
    assert front[0] == False
    assert front[1] == False
    assert front[2] == False
    assert front[3] == True

    # Solve equality constrained quadratic programming (Lagrangian)
    Q = np.array([[2.0, 0.0], [0.0, 2.0]])
    c = np.array([-2.0, -2.0])
    A = np.array([[1.0, 1.0]])
    b = np.array([2.0])
    # Min (1/2)(2x1^2 + 2x2^2) - 2x1 - 2x2 s.t. x1 + x2 = 2
    # Analytical solution: x1 = 1, x2 = 1
    x, lam = optimization.solve_lagrangian_equality(Q, c, A, b)
    assert x[0] == pytest.approx(1.0)
    assert x[1] == pytest.approx(1.0)


# 8. Information Theory Tests
def test_information_theory():
    # Shannon entropy of coin flip
    p = np.array([0.5, 0.5])
    assert inf_theory.shannon_entropy(p) == pytest.approx(1.0)

    # KL Divergence between identical distributions
    assert inf_theory.kl_divergence(p, p) == pytest.approx(0.0)

    # Blahut-Arimoto for Binary Symmetric Channel (BSC) with error probability 0.1
    # Capacity should be C = 1 - H(0.1) = 1 - 0.468995 = 0.531 bits
    bsc = np.array([
        [0.9, 0.1],
        [0.1, 0.9]
    ])
    cap, dist = inf_theory.blahut_arimoto(bsc)
    assert cap == pytest.approx(0.531004, abs=1e-4)
    assert dist[0] == pytest.approx(0.5, abs=1e-3)


# 9. Linear Algebra Tests
def test_linear_algebra():
    # QR Decomposition
    A = np.array([[1.0, 2.0], [3.0, 4.0]])
    Q, R = lin_alg.qr_decomposition(A)
    assert np.allclose(Q @ R, A)
    assert np.allclose(Q.T @ Q, np.eye(2))

    # Cholesky Decomposition
    S = np.array([[4.0, 12.0], [12.0, 37.0]])
    L = lin_alg.cholesky_decomposition(S)
    assert np.allclose(L @ L.T, S)
    assert L[0, 1] == 0.0

    # Jacobi Eigenvalues
    eigvals, eigvecs = lin_alg.jacobi_eigen(S)
    assert np.allclose(eigvecs @ np.diag(eigvals) @ eigvecs.T, S)

    # SVD
    U, s, VT = lin_alg.singular_value_decomposition(A)
    S_mat = np.zeros_like(A)
    np.fill_diagonal(S_mat, s)
    assert np.allclose(U @ S_mat @ VT, A)


# 10. Computational Geometry Tests
def test_computational_geometry():
    # Convex Hull of a square plus a center point
    pts = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.0, 1.0],
        [0.5, 0.5]
    ])
    hull = comp_geom.convex_hull(pts)
    assert len(hull) == 4
    # Ensure center point is not in hull
    for p in hull:
        assert not np.array_equal(p, [0.5, 0.5])

    # KD-Tree Nearest Neighbor
    tree = comp_geom.KDTree(pts)
    pt, dist = tree.nearest_neighbor(np.array([0.4, 0.4]))
    assert np.array_equal(pt, [0.5, 0.5])
    assert dist == pytest.approx(np.sqrt(0.02))


# 11. Decision Theory Tests
def test_decision_theory():
    # Expected Utility
    outcomes = np.array([10.0, -5.0])
    probs = np.array([0.6, 0.4])
    eu = decision.expected_utility(outcomes, probs, utility_type='linear')
    assert eu == pytest.approx(4.0)

    # Nash Equilibrium 2x2 (Prisoner's Dilemma)
    # A payoffs (Cooperates=0, Defects=1)
    # B payoffs (Cooperates=0, Defects=1)
    A = np.array([[-1.0, -3.0], [0.0, -2.0]])
    B = np.array([[-1.0, 0.0], [-3.0, -2.0]])
    res = decision.nash_equilibrium_2x2(A, B)
    # defect-defect (1, 1) is PSNE
    assert (1, 1) in res['pure_equilibria']


# 12. Numerical Analysis Tests
def test_numerical_analysis():
    # Polynomial interpolation
    x_pts = np.array([0.0, 1.0, 2.0])
    y_pts = np.array([0.0, 1.0, 4.0])  # y = x^2
    val = numerical.lagrange_interpolation(x_pts, y_pts, 1.5)
    assert val == pytest.approx(2.25)

    # Integration: ∫_0^1 x^2 dx = 1/3
    def f(x):
        return x ** 2
    integral = numerical.simpsons_rule(f, 0.0, 1.0, 100)
    assert integral == pytest.approx(1.0 / 3.0, abs=1e-5)

    # ODE solver: dy/dt = y, y(0) = 1. Solution at t=1 is exp(1) = 2.71828
    def dy_dt(t, y):
        return y
    t_vals, y_vals = numerical.rk4_method(dy_dt, 1.0, (0.0, 1.0), 0.01)
    assert y_vals[-1] == pytest.approx(np.exp(1.0), abs=1e-4)


# 13. Control Theory Tests
def test_control_theory():
    # PID controller
    pid = control.PIDController(kp=1.0, ki=0.5, kd=0.1, setpoint=10.0)
    out = pid.update(measurement=8.0, dt=1.0)
    # error = 2.0. Proportional = 2.0. Integral = 2.0*1.0*0.5 = 1.0. Derivative = (2.0-0.0)/1.0*0.1 = 0.2. Total = 3.2.
    assert out == pytest.approx(3.2)

    # State Space stability
    # Stable matrix: eigenvalues have absolute values < 1
    A = np.array([[0.5, 0.0], [0.0, 0.2]])
    stab = control.analyze_stability(A)
    assert stab['is_discrete_stable'] is True


# 14. Dynamical Systems Tests
def test_dynamical_systems():
    # Lyapunov exponent of logistic map for chaotic regime (r=4.0) vs stable (r=2.0)
    lyap_stable = dynamical.lyapunov_exponent_logistic(2.0)
    lyap_chaotic = dynamical.lyapunov_exponent_logistic(4.0)
    assert lyap_stable < 0.0
    assert lyap_chaotic > 0.0  # Positive Lyapunov exponent = chaos


# 15. Harmonic Analysis Tests
def test_harmonic_analysis():
    # DFT of a sine wave
    n = 16
    t = np.arange(n)
    # Sine wave frequency k=2
    x = np.sin(2.0 * np.pi * 2.0 * t / n)
    X = harmonic.dft(x)
    # Peak at index 2 (and mirror at 14)
    assert np.argmax(np.abs(X[:n // 2])) == 2

    # Haar DWT
    a, d = harmonic.haar_dwt(x)
    assert len(a) == n // 2
    assert len(d) == n // 2


# 16. Statistics Tests
def test_statistics():
    # One-sample t-test
    x = np.array([2.0, 2.1, 1.9, 2.0, 2.0])
    t_stat, p_val = stats.t_test_one_sample(x, pop_mean=2.0)
    assert p_val > 0.05  # Mean is indeed close to 2.0

    # Linear Regression: y = 2x + 1
    xs = np.array([0.0, 1.0, 2.0, 3.0])
    ys = np.array([1.0, 3.0, 5.0, 7.0])
    reg = stats.linear_regression(xs, ys)
    assert reg['slope'] == pytest.approx(2.0)
    assert reg['intercept'] == pytest.approx(1.0)
    assert reg['r_squared'] == pytest.approx(1.0)
