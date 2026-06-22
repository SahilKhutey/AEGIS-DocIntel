"""
Core Tensor Operations
======================

Mathematical Foundations:
------------------------
A tensor T ∈ R^{I₁ × I₂ × ... × I_N} has N modes.

Mode-n unfolding (matricization):
    T_(n) ∈ R^{Iₙ × (I₁...Iₙ₋₁Iₙ₊₁...Iₙ)}

Mode-n product:
    (T ×ₙ U)_i₁...iₙ₋₁ j iₙ₊₁...iₙ = Σᵢₙ T_i₁...iₙ U_{j iₙ}

Khatri-Rao product (column-wise Kronecker):
    (A ⊙ B) ∈ R^{(I₁I₂) × K}

Hadamard (element-wise) product:
    (T ∘ S)_{i₁...iₙ} = T_{i₁...iₙ} · S_{i₁...iₙ}
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .exceptions import DimensionMismatchError, InvalidTensorError


def unfold(tensor: np.ndarray, mode: int) -> np.ndarray:
    """
    Mode-n unfolding (matricization) of a tensor.

    Parameters
    ----------
    tensor : np.ndarray
        Input tensor of shape (I₁, I₂, ..., I_N).
    mode : int
        0-indexed mode to unfold along.

    Returns
    -------
    np.ndarray
        Matrix of shape (I_mode, prod(other_dims)).
    """
    tensor = np.asarray(tensor)
    if tensor.ndim == 0:
        raise InvalidTensorError("Cannot unfold a scalar tensor.")
    n = tensor.ndim
    if not (0 <= mode < n):
        raise InvalidTensorError(f"Mode {mode} out of bounds for tensor with {n} modes.")
    return np.moveaxis(tensor, mode, 0).reshape(tensor.shape[mode], -1)


def fold(matrix: np.ndarray, mode: int, shape: Tuple[int, ...]) -> np.ndarray:
    """
    Fold a matrix back into a tensor along the specified mode.

    Inverse of `unfold`.
    """
    matrix = np.asarray(matrix)
    n = len(shape)
    if not (0 <= mode < n):
        raise InvalidTensorError(f"Mode {mode} out of bounds.")
    full_shape = list(shape)
    mode_dim = full_shape.pop(mode)
    # the matrix has shape (mode_dim, prod(others))
    target_shape = list(shape)
    new_order = list(range(1, n))
    new_order.insert(mode, 0)
    reshaped = matrix.reshape([mode_dim] + full_shape)
    return np.moveaxis(reshaped, 0, mode)


def mode_n_product(tensor: np.ndarray, matrix: np.ndarray, mode: int) -> np.ndarray:
    """
    Compute the mode-n product: T ×ₙ M.

    Parameters
    ----------
    tensor : np.ndarray
    matrix : np.ndarray
        Shape (J, Iₙ) — transforms mode-n of size Iₙ to size J.
    mode : int
    """
    tensor = np.asarray(tensor)
    matrix = np.asarray(matrix)
    if tensor.ndim == 0:
        raise InvalidTensorError("Cannot multiply a scalar tensor.")
    if not (0 <= mode < tensor.ndim):
        raise InvalidTensorError(f"Mode {mode} out of bounds.")
    if matrix.ndim != 2:
        raise InvalidTensorError("Matrix must be 2-D.")
    new_shape = list(tensor.shape)
    new_shape[mode] = matrix.shape[0]
    return np.tensordot(matrix, tensor, axes=([1], [mode])).transpose(
        _mode_permutation(matrix.ndim, tensor.ndim, mode)
    )


def _mode_permutation(mat_ndim: int, tens_ndim: int, mode: int) -> Tuple[int, ...]:
    """Helper: compute permutation for tensordot result."""
    perm = list(range(1, tens_ndim))
    perm.insert(mode, 0)
    return tuple(perm)


def tensor_norm(tensor: np.ndarray, ord: str = "frobenius") -> float:
    """
    Compute tensor norms.

    Parameters
    ----------
    tensor : np.ndarray
    ord : str
        'frobenius', 'l1', 'l2', 'linf'
    """
    tensor = np.asarray(tensor)
    if ord == "frobenius":
        return float(np.linalg.norm(tensor))
    if ord == "l1":
        return float(np.abs(tensor).sum())
    if ord == "l2":
        return float(np.sqrt(np.sum(tensor ** 2)))
    if ord == "linf":
        return float(np.abs(tensor).max())
    raise ValueError(f"Unknown norm: {ord}")


def outer_product(vectors: List[np.ndarray]) -> np.ndarray:
    """
    Compute the outer product of a list of vectors.

    For N vectors, returns a tensor of order N.
    """
    if not vectors:
        raise InvalidTensorError("Need at least one vector.")
    result = np.asarray(vectors[0])
    for v in vectors[1:]:
        result = np.multiply.outer(result, v)
    return result


def khatri_rao_product(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Khatri-Rao (column-wise Kronecker) product.

    For A ∈ R^{I×K}, B ∈ R^{J×K}: result ∈ R^{(IJ)×K}.
    """
    A = np.asarray(A)
    B = np.asarray(B)
    if A.ndim != 2 or B.ndim != 2:
        raise InvalidTensorError("Khatri-Rao inputs must be 2-D.")
    if A.shape[1] != B.shape[1]:
        raise DimensionMismatchError(
            f"A.columns={A.shape[1]} ≠ B.columns={B.shape[1]}"
        )
    I, K = A.shape
    J = B.shape[0]
    out = np.zeros((I * J, K), dtype=np.result_type(A, B))
    for k in range(K):
        out[:, k] = np.kron(A[:, k], B[:, k])
    return out


def hadamard_product(T: np.ndarray, S: np.ndarray) -> np.ndarray:
    """Element-wise (Hadamard) product."""
    T = np.asarray(T)
    S = np.asarray(S)
    if T.shape != S.shape:
        raise DimensionMismatchError(
            f"Shape mismatch: {T.shape} vs {S.shape}"
        )
    return T * S