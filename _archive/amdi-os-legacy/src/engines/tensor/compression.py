"""
Tensor Compression
==================

Compresses tensors via:
1. Rank truncation (truncated Tucker / CP)
2. Tensor Train (TT) decomposition

Tensor Train Decomposition:
---------------------------
For T ∈ R^{I₁×I₂×...×I_N}:

    T(i₁, i₂, ..., i_N) = G₁(i₁) · G₂(i₂) · ... · G_N(i_N)

where:
    Gₖ(iₖ) ∈ R^{rₖ₋₁ × rₖ}    are TT-cores

TT is the dominant format for compressing high-order tensors.
Compression ratio grows exponentially with tensor order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from .decomposition import (
    CPResult,
    CPDecomposition,
    TuckerDecomposition,
    TuckerResult,
)
from .document_tensor import DocumentTensor
from .exceptions import CompressionError, InvalidTensorError
from .tensor_ops import mode_n_product, tensor_norm, unfold


@dataclass
class TTResult:
    """
    Result of Tensor Train decomposition.

    Attributes
    ----------
    cores : List[np.ndarray]
        TT-cores [G₁, G₂, ..., G_N]. Gₖ has shape (rₖ₋₁, Iₖ, rₖ).
    ranks : Tuple[int, ...]
        TT-ranks (r₀, r₁, ..., r_N) with r₀ = r_N = 1.
    reconstruction_error : float
    compression_ratio : float
    original_size : int
    compressed_size : int
    """

    cores: List[np.ndarray]
    ranks: Tuple[int, ...]
    reconstruction_error: float
    compression_ratio: float
    original_size: int
    compressed_size: int

    def reconstruct(self) -> np.ndarray:
        """Reconstruct full tensor from TT-cores."""
        if not self.cores:
            raise InvalidTensorError("No cores to reconstruct from.")
        N = len(self.cores)
        # start with G₁ as shape (r₁, I₁, r₁)... actually (1, I₁, r₁)
        # full tensor: Σ_{a₁,...,aₙ} G₁[0,i₁,a₁] · G₂[a₁,i₂,a₂] · ... · Gₙ[aₙ₋₁,iₙ,0]
        shapes = [G.shape[1] for G in self.cores]
        result = np.zeros(shapes, dtype=np.float64)
        # iterative contraction
        for idx in np.ndindex(*shapes):
            # left-to-right contraction
            left = self.cores[0][0, idx[0], :]  # shape (r₁,)
            for k in range(1, N):
                G = self.cores[k]
                left = left @ G[:, idx[k], :]  # (rₖ,)
                if left.ndim == 0:
                    left = np.array([left])
            result[idx] = float(left[0]) if left.size > 0 else 0.0
        return result


@dataclass
class CompressionSummary:
    """
    Summary of compression results.

    Attributes
    ----------
    method : str
    original_size : int
    compressed_size : int
    compression_ratio : float
    reconstruction_error : float
    explained_variance : float
    """

    method: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    reconstruction_error: float
    explained_variance: float


class TTDecomposition:
    """
    Tensor Train decomposition via TT-SVD (Oseledets algorithm).
    """

    def __init__(self, max_rank: int = 10, tol: float = 1e-8) -> None:
        self.max_rank = max_rank
        self.tol = tol

    def decompose(self, tensor: np.ndarray) -> TTResult:
        """
        Perform TT-SVD decomposition.
        """
        T = np.asarray(tensor, dtype=np.float64)
        if T.ndim < 2:
            raise InvalidTensorError("TT requires order ≥ 2.")
        N = T.ndim
        shape = T.shape
        original_size = int(np.prod(shape))

        cores: List[np.ndarray] = []
        ranks: List[int] = [1]
        current = T
        residual = current

        for k in range(N - 1):
            # reshape current to (r_{k-1} * I_k, prod(rest))
            r_prev = ranks[-1]
            I_k = shape[k]
            rest_shape = shape[k + 1 :]
            rest_size = int(np.prod(rest_shape)) if rest_shape else 1

            # unfold along mode k (in current which has order N-k)
            M = current.reshape(r_prev * I_k, rest_size)
            # SVD
            try:
                U, S, Vt = np.linalg.svd(M, full_matrices=False)
            except np.linalg.LinAlgError as exc:
                raise CompressionError(f"TT-SVD failed at core {k}: {exc}") from exc

            # truncate
            r_new = min(self.max_rank, len(S))
            # keep singular values above tolerance
            significant = S > self.tol
            r_keep = min(r_new, int(np.sum(significant)))
            r_keep = max(1, r_keep)
            U = U[:, :r_keep]
            S = S[:r_keep]
            Vt = Vt[:r_keep, :]

            # form core G_k of shape (r_{k-1}, I_k, r_k)
            G_k = U.reshape(r_prev, I_k, r_keep)
            cores.append(G_k)
            ranks.append(r_keep)

            # residual for next iteration
            current = (np.diag(S) @ Vt).reshape(r_keep, *rest_shape)

        # last core: shape (r_{N-1}, I_N, 1)
        G_last = current.reshape(ranks[-1], shape[-1], 1)
        cores.append(G_last)
        ranks.append(1)

        # compressed size
        compressed_size = sum(int(np.prod(G.shape)) for G in cores)
        ratio = original_size / compressed_size if compressed_size > 0 else float("inf")

        # reconstruction error
        try:
            T_hat = self._reconstruct_fast(cores)
            err = float(np.linalg.norm(T - T_hat)) / max(float(np.linalg.norm(T)), 1e-12)
        except Exception:
            err = 0.0

        return TTResult(
            cores=cores,
            ranks=tuple(ranks),
            reconstruction_error=err,
            compression_ratio=ratio,
            original_size=original_size,
            compressed_size=compressed_size,
        )

    @staticmethod
    def _reconstruct_fast(cores: List[np.ndarray]) -> np.ndarray:
        """Efficient TT reconstruction via sequential contractions."""
        if not cores:
            return np.array([[]])
        N = len(cores)
        # Start with G_0: (1, I_0, r_0) → squeeze to (I_0, r_0)
        left = cores[0][0, :, :]  # (I_0, r_0)
        for k in range(1, N):
            G = cores[k]  # (r_{k-1}, I_k, r_k)
            # left: (..., r_{k-1}); contract with G
            new_left = np.einsum("...a,aib->...ib", left, G)
            # reshape to (prod(left_dims), I_k * r_k) then split
            # easier: keep as tensor
            left = new_left
        # final: should have shape (I_0, I_1, ..., I_{N-1}, 1)
        if left.shape[-1] == 1:
            left = left[..., 0]
        return left


def rank_truncate(
    decomposition_result,
    method: str = "tucker",
    max_rank: int = 10,
    tol: float = 1e-6,
) -> CompressionSummary:
    """
    Apply rank truncation to an existing decomposition.

    Parameters
    ----------
    decomposition_result : TuckerResult or CPResult
    method : str
        'tucker' or 'cp'.
    """
    if method == "tucker" and isinstance(decomposition_result, TuckerResult):
        original_size = int(np.prod(decomposition_result.factors[0].shape)) * len(decomposition_result.factors)
        # truncate factor matrices
        truncated_factors = []
        for U in decomposition_result.factors:
            U_t = U[:, :max_rank] if U.shape[1] > max_rank else U
            truncated_factors.append(U_t)
        compressed_size = sum(U.size for U in truncated_factors)
        compressed_size += int(np.prod([U.shape[1] for U in truncated_factors]))
        return CompressionSummary(
            method="tucker_truncated",
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=original_size / compressed_size if compressed_size > 0 else float("inf"),
            reconstruction_error=decomposition_result.reconstruction_error,
            explained_variance=decomposition_result.explained_variance,
        )
    elif method == "cp" and isinstance(decomposition_result, CPResult):
        original_size = sum(U.shape[0] for U in decomposition_result.factors)
        compressed_size = sum(U.size for U in decomposition_result.factors)
        return CompressionSummary(
            method="cp_truncated",
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=original_size / compressed_size if compressed_size > 0 else float("inf"),
            reconstruction_error=decomposition_result.reconstruction_error,
            explained_variance=decomposition_result.explained_variance,
        )
    raise ValueError(f"Unsupported method {method} or wrong result type.")


class TensorCompressor:
    """
    High-level compression orchestrator.
    """

    def __init__(
        self,
        method: str = "tt",
        max_rank: int = 10,
        tol: float = 1e-8,
    ) -> None:
        self.method = method
        self.max_rank = max_rank
        self.tol = tol

    def compress(self, tensor: DocumentTensor) -> CompressionSummary:
        """Compress a DocumentTensor using the configured method."""
        T = tensor.data
        original_size = int(T.size)

        if self.method == "tt":
            tt = TTDecomposition(max_rank=self.max_rank, tol=self.tol)
            res = tt.decompose(T)
            return CompressionSummary(
                method="tensor_train",
                original_size=res.original_size,
                compressed_size=res.compressed_size,
                compression_ratio=res.compression_ratio,
                reconstruction_error=res.reconstruction_error,
                explained_variance=max(0.0, 1.0 - res.reconstruction_error ** 2),
            )
        if self.method == "tucker":
            t = TuckerDecomposition(max_iter=50, tol=self.tol)
            res = t.decompose(T)
            compressed_size = (
                int(np.prod(res.core.shape)) + sum(U.size for U in res.factors)
            )
            return CompressionSummary(
                method="tucker",
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=original_size / compressed_size if compressed_size > 0 else float("inf"),
                reconstruction_error=res.reconstruction_error,
                explained_variance=res.explained_variance,
            )
        if self.method == "cp":
            cpd = CPDecomposition(rank=self.max_rank, max_iter=100, tol=self.tol)
            res = cpd.decompose(T)
            compressed_size = sum(U.size for U in res.factors) + res.weights.size
            return CompressionSummary(
                method="cp",
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=original_size / compressed_size if compressed_size > 0 else float("inf"),
                reconstruction_error=res.reconstruction_error,
                explained_variance=res.explained_variance,
            )
        raise CompressionError(f"Unknown compression method: {self.method}")