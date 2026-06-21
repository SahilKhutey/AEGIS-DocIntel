"""
Unit tests for the AMDI-OS Tensor Engine.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import pytest
import numpy as np

from src.engines.tensor import (
    TensorEngine,
    DocumentTensor,
    TensorMode,
    TensorBuilder,
    unfold,
    fold,
    mode_n_product,
    tensor_norm,
    outer_product,
    khatri_rao_product,
    hadamard_product,
    TuckerDecomposition,
    CPDecomposition,
    TensorReducer,
    marginalize,
    contract,
    TTDecomposition,
    rank_truncate,
    explained_variance_ratio,
    reconstruction_error,
    TensorMetrics,
    TensorEngineError,
    InvalidTensorError,
    DecompositionError,
    CompressionError,
)


def test_tensor_builders():
    """Test building DocumentTensors from various inputs."""
    # 1. Random builder
    shape = (2, 3, 4, 2, 5)
    dt_rand = TensorBuilder.from_random(shape, density=0.3, seed=123)
    assert dt_rand.shape == shape
    assert dt_rand.order == 5
    assert dt_rand.density > 0.0
    assert dt_rand.nnz > 0

    # 2. Dense builder
    arr = np.arange(24).reshape((2, 3, 4))
    dt_dense = TensorBuilder.from_dense_array(arr)
    assert dt_dense.shape == (2, 3, 4)
    assert dt_dense.order == 3
    assert dt_dense.size == 24
    assert np.array_equal(dt_dense.to_dense(), arr)

    # 3. Sparse token counts builder
    counts = {
        (0, 0, 0, 0, 0): 1.5,
        (0, 1, 2, 1, 4): 3.0,
        (1, 0, 1, 2, 2): 2.0,
    }
    dt_sparse = TensorBuilder.from_token_counts(
        counts, n_pages=2, n_sections=2, n_rows=3, n_cols=3, n_tokens=5
    )
    assert dt_sparse.shape == (2, 2, 3, 3, 5)
    assert dt_sparse.data[0, 0, 0, 0, 0] == 1.5
    assert dt_sparse.data[0, 1, 2, 1, 4] == 3.0
    assert dt_sparse.data[1, 0, 1, 2, 2] == 2.0
    # out of bounds should be ignored
    counts_oob = {(2, 0, 0, 0, 0): 10.0}
    dt_oob = TensorBuilder.from_token_counts(
        counts_oob, n_pages=2, n_sections=2, n_rows=3, n_cols=3, n_tokens=5
    )
    assert np.all(dt_oob.data == 0.0)

    # 4. Matrix builder
    mat = np.array([[1.0, 2.0], [3.0, 4.0]])
    dt_mat = TensorBuilder.from_matrix(mat)
    assert dt_mat.shape == (2, 2)
    assert dt_mat.order == 2


def test_document_tensor_properties():
    """Test operations on DocumentTensor instances."""
    arr = np.random.rand(3, 4, 5)
    dt = DocumentTensor(data=arr)
    assert dt.order == 3
    assert dt.shape == (3, 4, 5)
    assert dt.size == 60
    assert dt.density == 1.0

    # Normalization
    dt_norm = dt.normalize(ord="frobenius")
    assert np.isclose(tensor_norm(dt_norm.data, "frobenius"), 1.0)
    dt_norm_l1 = dt.normalize(ord="l1")
    assert np.isclose(tensor_norm(dt_norm_l1.data, "l1"), 1.0)

    # Fibers and slices
    fiber = dt.mode_n_fiber(mode=1, index=(1, 2))  # shape should be (4,)
    assert fiber.shape == (4,)
    
    slice_tensor = dt.mode_n_slice(mode=0, idx=1)  # shape should be (4, 5)
    assert slice_tensor.shape == (4, 5)

    # Sparse representation
    sparse_repr = dt.to_sparse()
    assert sparse_repr.shape == (3, 20)

    # Error handling
    with pytest.raises(InvalidTensorError):
        DocumentTensor(data=np.array([1, 2]))  # Requires order >= 2
    with pytest.raises(InvalidTensorError):
        dt.mode_n_fiber(mode=1, index=(1,))  # index length != order - 1


def test_tensor_ops():
    """Test core tensor algebra operations."""
    # Unfolding and folding
    T = np.arange(24).reshape((2, 3, 4))
    
    # Mode 0 unfolding
    unfolded_0 = unfold(T, mode=0)
    assert unfolded_0.shape == (2, 12)
    folded_0 = fold(unfolded_0, mode=0, shape=T.shape)
    assert np.array_equal(folded_0, T)

    # Mode 1 unfolding
    unfolded_1 = unfold(T, mode=1)
    assert unfolded_1.shape == (3, 8)
    folded_1 = fold(unfolded_1, mode=1, shape=T.shape)
    assert np.array_equal(folded_1, T)

    # Mode 2 unfolding
    unfolded_2 = unfold(T, mode=2)
    assert unfolded_2.shape == (4, 6)
    folded_2 = fold(unfolded_2, mode=2, shape=T.shape)
    assert np.array_equal(folded_2, T)

    # Mode-n product
    T = np.random.rand(2, 3, 4)
    M = np.random.rand(5, 3)  # transforms mode 1 from 3 to 5
    res = mode_n_product(T, M, mode=1)
    assert res.shape == (2, 5, 4)

    # Tensor norm
    assert tensor_norm(T, "frobenius") == np.linalg.norm(T)
    assert tensor_norm(T, "l1") == np.abs(T).sum()
    assert np.isclose(tensor_norm(T, "l2"), np.sqrt(np.sum(T**2)))
    assert tensor_norm(T, "linf") == np.abs(T).max()

    # Outer product
    v1 = np.array([1.0, 2.0])
    v2 = np.array([3.0, 4.0, 5.0])
    v3 = np.array([6.0, 7.0])
    out = outer_product([v1, v2, v3])
    assert out.shape == (2, 3, 2)
    assert out[0, 1, 1] == v1[0] * v2[1] * v3[1]

    # Khatri-Rao product
    A = np.array([[1.0, 2.0], [3.0, 4.0]])
    B = np.array([[5.0, 6.0], [7.0, 8.0], [9.0, 10.0]])
    KR = khatri_rao_product(A, B)
    assert KR.shape == (6, 2)
    assert KR[0, 0] == A[0, 0] * B[0, 0]
    assert KR[5, 1] == A[1, 1] * B[2, 1]

    # Hadamard product
    S = np.random.rand(2, 3, 4)
    had = hadamard_product(T, S)
    assert had.shape == T.shape
    assert np.allclose(had, T * S)

    # Error conditions
    with pytest.raises(InvalidTensorError):
        unfold(np.array(5.0), mode=0)
    with pytest.raises(InvalidTensorError):
        unfold(T, mode=5)
    with pytest.raises(InvalidTensorError):
        fold(unfolded_0, mode=4, shape=T.shape)
    with pytest.raises(InvalidTensorError):
        mode_n_product(T, np.random.rand(3,), mode=1)
    with pytest.raises(InvalidTensorError):
        outer_product([])


def test_tucker_decomposition():
    """Test Tucker decomposition via HOOI."""
    # Synthetic rank-2 tensor
    rng = np.random.RandomState(42)
    U0 = rng.rand(3, 2)
    U1 = rng.rand(4, 2)
    U2 = rng.rand(5, 2)
    core_syn = rng.rand(2, 2, 2)
    T = core_syn.copy()
    T = mode_n_product(T, U0, 0)
    T = mode_n_product(T, U1, 1)
    T = mode_n_product(T, U2, 2)

    ranks = (2, 2, 2)
    td = TuckerDecomposition(ranks=ranks, tol=1e-5, max_iter=20)
    res = td.decompose(T)
    assert res.converged or res.n_iterations > 0
    assert res.core.shape == ranks
    assert len(res.factors) == 3
    assert res.factors[0].shape == (3, 2)
    assert res.factors[1].shape == (4, 2)
    assert res.factors[2].shape == (5, 2)
    assert res.reconstruction_error < 0.1
    assert res.explained_variance > 0.9

    reconstructed = res.reconstruct()
    assert reconstructed.shape == T.shape
    assert np.allclose(reconstructed, T, atol=0.1)
    assert res.compression_ratio > 0.0


def test_cp_decomposition():
    """Test CP decomposition via ALS."""
    rng = np.random.RandomState(42)
    A = rng.rand(3, 2)
    B = rng.rand(4, 2)
    C = rng.rand(5, 2)
    weights = np.array([2.0, 1.0])
    
    # Construct rank-2 tensor
    T = np.zeros((3, 4, 5))
    for r in range(2):
        T += weights[r] * np.multiply.outer(np.multiply.outer(A[:, r], B[:, r]), C[:, r])

    cpd = CPDecomposition(rank=2, tol=1e-5, max_iter=50)
    res = cpd.decompose(T)
    assert len(res.factors) == 3
    assert res.factors[0].shape == (3, 2)
    assert res.factors[1].shape == (4, 2)
    assert res.factors[2].shape == (5, 2)
    
    reconstructed = res.reconstruct()
    assert reconstructed.shape == T.shape
    # CP decomposition might converge to slightly different factor scaling
    # but the reconstructed tensor should match the original.
    assert np.allclose(reconstructed, T, atol=0.2)
    assert res.compression_ratio > 0.0


def test_tensor_reduction():
    """Test tensor reductions (marginalization and contraction)."""
    T = np.arange(24).reshape((2, 3, 4))
    
    # Marginalize sum
    sum_0 = marginalize(T, mode=0, method="sum")
    assert sum_0.shape == (3, 4)
    assert sum_0[0, 0] == T[0, 0, 0] + T[1, 0, 0]

    # Marginalize mean with keepdims
    mean_1 = marginalize(T, mode=1, method="mean", keepdims=True)
    assert mean_1.shape == (2, 1, 4)

    # Contraction
    S = np.random.rand(4, 5)
    contracted = contract(T, S, mode_T=2, mode_S=0)
    assert contracted.shape == (2, 3, 5)

    # TensorReducer orchestrator
    dt = DocumentTensor(data=T.astype(np.float64))
    dt_reduced = TensorReducer.marginalize_all(dt, modes=[1])
    assert dt_reduced.shape == (2, 4)

    mat = TensorReducer.to_matrix(dt, row_mode=0, col_mode=2)
    assert mat.shape == (2, 4)

    vec = TensorReducer.to_vector(dt)
    assert vec.ndim == 1


def test_tensor_compression():
    """Test Tensor Train (TT) decomposition and rank truncation."""
    T = np.random.rand(3, 4, 5, 2)
    
    # Tensor Train SVD
    tt = TTDecomposition(max_rank=3, tol=1e-8)
    res = tt.decompose(T)
    assert len(res.cores) == 4
    # cores are (r_k-1, I_k, r_k)
    assert res.cores[0].shape[0] == 1
    assert res.cores[-1].shape[2] == 1
    assert len(res.ranks) == 5
    assert res.ranks[0] == 1
    assert res.ranks[-1] == 1

    # Reconstruction
    T_hat = res.reconstruct()
    assert T_hat.shape == T.shape
    # Check that error is reasonable (depending on max_rank truncation)
    assert res.reconstruction_error >= 0.0
    assert res.compression_ratio > 0.0

    # Rank Truncation
    # 1. Tucker Result Truncation
    ranks = (3, 3, 3)
    tucker_res = TuckerDecomposition(ranks=ranks).decompose(np.random.rand(3, 4, 5))
    trunc_tucker = rank_truncate(tucker_res, method="tucker", max_rank=2)
    assert trunc_tucker.method == "tucker_truncated"
    assert trunc_tucker.compression_ratio > 0.0

    # 2. CP Result Truncation
    cp_res = CPDecomposition(rank=3).decompose(np.random.rand(3, 4, 5))
    trunc_cp = rank_truncate(cp_res, method="cp", max_rank=2)
    assert trunc_cp.method == "cp_truncated"


def test_tensor_metrics():
    """Test explained variance and relative error calculations."""
    T = np.random.rand(2, 3, 4)
    R = T + np.random.normal(scale=0.01, size=T.shape)

    evr = explained_variance_ratio(T, R)
    assert 0.0 <= evr <= 1.0
    assert evr > 0.9

    err = reconstruction_error(T, R, norm="frobenius")
    assert err < 0.1


def test_tensor_engine_e2e():
    """Test TensorEngine end-to-end building, decomposition, and report generation."""
    te = TensorEngine()
    elements = [
        {"page": 1, "section": "intro", "content": "The stock index is 105.2"},
        {"page": 1, "section": "intro", "content": "Volume is 1000"},
        {"page": 1, "section": "body", "content": "Price is 99.95"},
        {"page": 2, "section": "conclusion", "content": "Final output score"},
    ]

    # Build 5-mode tensor
    dt = te.build_tensor(elements, max_rows=3, max_cols=3)
    assert dt.shape[0] == 2  # 2 pages
    assert dt.shape[1] == 3  # 3 sections (intro, body, conclusion)
    assert dt.shape[2] == 3  # max_rows
    assert dt.shape[3] == 3  # max_cols
    assert dt.shape[4] > 5   # vocabulary size

    # Tucker decomposition e2e
    core, factors = te.tucker_decomposition(dt, ranks=[2, 2, 2, 2, 2])
    assert core.shape == (2, 2, 2, 2, 2)
    assert len(factors) == 5
    assert factors[0].shape == (2, 2)

    # CP decomposition e2e
    cp_factors = te.cp_decomposition(dt, rank=3)
    assert len(cp_factors) == 5
    assert cp_factors[0].shape == (2, 3)

    # Mode-n product delegation
    M = np.random.rand(4, dt.shape[0])
    prod = te.mode_n_product(dt.data, M, mode=0)
    assert prod.shape == (4, dt.shape[1], dt.shape[2], dt.shape[3], dt.shape[4])

    # Report generation
    report = te.analyze(dt, method="tucker", rank=2)
    report_dict = report.to_dict()
    assert report_dict["method"] == "tucker"
    assert report_dict["original_shape"] == list(dt.shape)
    assert report_dict["compression_ratio"] > 0.0
