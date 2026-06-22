'''
AEGIS-MIOS — Tensor Algebra
=============================
T_{ijkl} — Multilinear representations
Operations: CP, Tucker, mode-n product, contraction
'''

from __future__ import annotations

import numpy as np
from numpy.linalg import svd


# ============================================================
# MODE-n PRODUCT: T ×_n M
# ============================================================

def mode_n_product(T: np.ndarray, M: np.ndarray, mode: int) -> np.ndarray:
    '''
    T ×_n M — Mode-n tensor-matrix product.

    Multiplies T along mode-n by matrix M.
    If T has shape (I_1, ..., I_n, ..., I_N),
    result has shape (I_1, ..., J, ..., I_N) where J = M.shape[0].
    '''
    T_moved = np.moveaxis(T, mode, 0)
    orig_shape = T_moved.shape
    unfolded = T_moved.reshape(T.shape[mode], -1)
    result_unfolded = M @ unfolded
    new_shape = list(orig_shape)
    new_shape[0] = M.shape[0]
    result_moved = result_unfolded.reshape(new_shape)
    return np.moveaxis(result_moved, 0, mode)


def mode_n_unfold(T: np.ndarray, mode: int) -> np.ndarray:
    '''
    Mode-n unfolding (matricization).
    T_{(n)} has shape (I_n, prod(I_m for m != n))
    '''
    return np.moveaxis(T, mode, 0).reshape(T.shape[mode], -1)


def mode_n_fold(matrix: np.ndarray, mode: int, shape: tuple) -> np.ndarray:
    '''Inverse of mode-n unfolding.'''
    full_shape = list(shape)
    mode_dim = full_shape.pop(mode)
    new_shape = [mode_dim] + full_shape
    return np.moveaxis(matrix.reshape(new_shape), 0, mode)


# ============================================================
# CP DECOMPOSITION (CANDECOMP/PARAFAC)
# ============================================================

def cp_decomposition(
    T: np.ndarray,
    rank: int,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> tuple[list[np.ndarray], np.ndarray]:
    '''
    CP decomposition: T ≈ Σ_r λ_r × a_r^1 ⊗ a_r^2 ⊗ ... ⊗ a_r^N

    Returns: (factor_matrices, weights)
    '''
    n_modes = T.ndim
    # Initialize factor matrices randomly
    factors = [np.random.rand(T.shape[m], rank) for m in range(n_modes)]
    weights = np.ones(rank)

    for iteration in range(max_iter):
        # Update each mode
        for m in range(n_modes):
            # Compute the Khatri-Rao product of all other modes
            khatri_rao = factors[n_modes - 1]
            for j in range(n_modes - 2, -1, -1):
                if j != m:
                    khatri_rao = _khatri_rao_product(factors[j], khatri_rao)
            # Unfold T along mode m
            T_unfold = mode_n_unfold(T, m)
            # Update factor m
            new_factor = T_unfold @ khatri_rao @ np.linalg.pinv(
                (khatri_rao.T @ khatri_rao) * (factors[m].T @ factors[m])
            )
            # Normalize columns
            norms = np.linalg.norm(new_factor, axis=0, keepdims=True)
            norms[norms == 0] = 1
            new_factor = new_factor / norms
            weights *= norms.flatten()
            factors[m] = new_factor

        # Check convergence
        reconstructed = _cp_reconstruct(factors, weights)
        error = np.linalg.norm(T - reconstructed) / np.linalg.norm(T)
        if error < tol:
            break

    return factors, weights


def _khatri_rao_product(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    '''Khatri-Rao product (column-wise Kronecker).'''
    n_cols = A.shape[1]
    if B.shape[1] != n_cols:
        raise ValueError('Number of columns must match')
    result = np.zeros((A.shape[0] * B.shape[0], n_cols))
    for i in range(n_cols):
        result[:, i] = np.kron(A[:, i], B[:, i])
    return result


def _cp_reconstruct(factors: list[np.ndarray], weights: np.ndarray) -> np.ndarray:
    '''Reconstruct tensor from CP factors.'''
    rank = factors[0].shape[1]
    # Initialize with first factor * weights
    result = weights[0] * factors[0][:, 0:1]
    for r in range(1, rank):
        result = result + weights[r] * factors[0][:, r:r+1]
    result = result.reshape(-1, 1)

    # Compute CP as sum of outer products
    cp = np.zeros_like(factors[0][:, 0])
    for r in range(rank):
        outer = factors[0][:, r]
        for m in range(1, len(factors)):
            outer = np.tensordot(outer, factors[m][:, r], axes=0)
        cp += weights[r] * outer
    return cp.reshape(*[f.shape[0] for f in factors])


# ============================================================
# TUCKER DECOMPOSITION
# ============================================================

def tucker_decomposition(
    T: np.ndarray,
    ranks: tuple | None = None,
    max_iter: int = 50,
    tol: float = 1e-6,
) -> tuple[np.ndarray, list[np.ndarray]]:
    '''
    Tucker decomposition: T ≈ G ×_1 U^(1) ×_2 U^(2) × ... ×_N U^(N)

    Higher-Order Orthogonal Iteration (HOOI).
    Returns: (core_tensor, factor_matrices)
    '''
    n_modes = T.ndim
    if ranks is None:
        ranks = tuple(min(s, 10) for s in T.shape)
    # Initialize factor matrices
    factors = [np.random.randn(T.shape[m], ranks[m]) for m in range(n_modes)]

    for iteration in range(max_iter):
        for m in range(n_modes):
            # Compute the product of all other modes' unfoldings
            tensor_to_unfold = T
            for j in range(n_modes):
                if j != m:
                    tensor_to_unfold = mode_n_product(
                        tensor_to_unfold, factors[j].T, j
                    )
            # SVD of the unfolded result
            unfolding = mode_n_unfold(tensor_to_unfold, m)
            U, _, _ = svd(unfolding, full_matrices=False)
            factors[m] = U[:, :ranks[m]]

        # Check convergence
        core = T.copy()
        for m in range(n_modes):
            core = mode_n_product(core, factors[m].T, m)
        error = np.linalg.norm(core)  # reconstruction error
        if error < tol:
            break

    # Final core tensor
    core = T.copy()
    for m in range(n_modes):
        core = mode_n_product(core, factors[m].T, m)
    return core, factors


# ============================================================
# TENSOR CONTRACTIONS
# ============================================================

def tensor_contraction(
    T1: np.ndarray,
    T2: np.ndarray,
    axes1: int | tuple,
    axes2: int | tuple,
) -> np.ndarray:
    '''
    Einstein summation contraction.
    np.tensordot(T1, T2, axes=([axes1], [axes2]))
    '''
    if isinstance(axes1, int):
        axes1 = (axes1,)
    if isinstance(axes2, int):
        axes2 = (axes2,)
    return np.tensordot(T1, T2, axes=(list(axes1), list(axes2)))


def inner_product(T1: np.ndarray, T2: np.ndarray) -> float:
    '''Tensor inner product: <T1, T2> = Σ T1 ⊙ T2'''
    return float(np.sum(T1 * T2))


def frobenius_norm(T: np.ndarray) -> float:
    '''‖T‖_F = √(Σ T²)'''
    return float(np.sqrt(np.sum(T ** 2)))


# ============================================================
# TENSOR DECOMPOSITION FOR DOCUMENT ANALYSIS
# ============================================================

def document_tensor_decompose(
    document_tensor: np.ndarray,
    rank: int = 5,
) -> dict:
    '''
    Specialized decomposition for 4D document tensors.
    T_{page, section, row, col}
    '''
    core, factors = tucker_decomposition(document_tensor, ranks=(rank, rank, rank, rank))
    # Interpret factors
    page_importance = np.linalg.norm(factors[0], axis=1)
    section_importance = np.linalg.norm(factors[1], axis=1)
    row_importance = np.linalg.norm(factors[2], axis=1)
    col_importance = np.linalg.norm(factors[3], axis=1)
    return {
        'core_shape': core.shape,
        'core_energy': float(np.linalg.norm(core)),
        'page_importance': page_importance,
        'section_importance': section_importance,
        'row_importance': row_importance,
        'col_importance': col_importance,
        'reconstruction_error': float(np.linalg.norm(
            document_tensor - reconstruct_from_core(core, factors)
        )),
    }


def reconstruct_from_core(core: np.ndarray, factors: list[np.ndarray]) -> np.ndarray:
    '''Reconstruct full tensor from Tucker core and factors.'''
    result = core.copy()
    for m, f in enumerate(factors):
        result = mode_n_product(result, f, m)
    return result
