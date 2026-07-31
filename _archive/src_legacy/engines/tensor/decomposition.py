"""
Tensor Decompositions
=====================

1. Tucker Decomposition
------------------------
A tensor T ∈ R^{I₁×I₂×...×I_N} is decomposed as:

    T ≈ G ×₁ U₁ ×₂ U₂ ... ×ₙ Uₙ

where:
    G ∈ R^{R₁×R₂×...×R_N}  is the core tensor
    Uₖ ∈ R^{Iₖ×Rₖ}        are factor matrices

This is a generalization of PCA to higher orders.

2. CP / PARAFAC Decomposition
------------------------------
A tensor is decomposed as a sum of rank-1 tensors:

    T ≈ Σᵣ λᵣ u₁ʳ ∘ u₂ʳ ∘ ... ∘ uₙʳ

where:
    λᵣ  are scalar weights
    uₖʳ ∈ R^{Iₖ} are normalized factor vectors
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .exceptions import DecompositionError, InvalidTensorError
from .tensor_ops import khatri_rao_product, mode_n_product, tensor_norm, unfold


@dataclass
class TuckerResult:
    """
    Result of Tucker decomposition.

    Attributes
    ----------
    core : np.ndarray
        Core tensor G.
    factors : List[np.ndarray]
        Factor matrices [U₁, U₂, ..., Uₙ].
    ranks : Tuple[int, ...]
        Tucker ranks (R₁, R₂, ..., Rₙ).
    reconstruction_error : float
        ||T - T̂||_F / ||T||_F.
    explained_variance : float
        1 - reconstruction_error² (R²-style metric).
    n_iterations : int
    converged : bool
    """

    core: np.ndarray
    factors: List[np.ndarray]
    ranks: Tuple[int, ...]
    reconstruction_error: float
    explained_variance: float
    n_iterations: int = 0
    converged: bool = False

    def reconstruct(self) -> np.ndarray:
        """Reconstruct the tensor from core and factors."""
        result = np.asarray(self.core)
        for n, U in enumerate(self.factors):
            result = mode_n_product(result, U, n)
        return result

    @property
    def compression_ratio(self) -> float:
        """Ratio of original size to compressed size."""
        original = int(np.prod([U.shape[0] for U in self.factors]))
        compressed = int(np.prod(self.core.shape)) + sum(U.size for U in self.factors)
        return original / compressed if compressed > 0 else float("inf")


@dataclass
class CPResult:
    """
    Result of CP decomposition.

    Attributes
    ----------
    weights : np.ndarray
        Scalar weights λᵣ.
    factors : List[np.ndarray]
        Factor matrices [U₁, U₂, ..., Uₙ] where Uₖ ∈ R^{Iₖ×R}.
    rank : int
        CP rank R.
    reconstruction_error : float
    explained_variance : float
    n_iterations : int
    converged : bool
    """

    weights: np.ndarray
    factors: List[np.ndarray]
    rank: int
    reconstruction_error: float
    explained_variance: float
    n_iterations: int = 0
    converged: bool = False

    def reconstruct(self) -> np.ndarray:
        """Reconstruct tensor from CP components."""
        n_modes = len(self.factors)
        shapes = [U.shape[0] for U in self.factors]
        result = np.zeros(shapes, dtype=np.float64)
        for r in range(self.rank):
            components = [self.factors[n][:, r] * self.weights[r] for n in range(n_modes)]
            outer = components[0]
            for c in components[1:]:
                outer = np.multiply.outer(outer, c)
            result += outer
        return result

    @property
    def compression_ratio(self) -> float:
        original = int(np.prod([U.shape[0] for U in self.factors]))
        compressed = sum(U.size for U in self.factors) + self.weights.size
        return original / compressed if compressed > 0 else float("inf")


class TuckerDecomposition:
    """
    Higher-Order Orthogonal Iteration (HOOI) for Tucker decomposition.
    """

    def __init__(
        self,
        ranks: Optional[Tuple[int, ...]] = None,
        max_iter: int = 50,
        tol: float = 1e-6,
    ) -> None:
        self.ranks = ranks
        self.max_iter = max_iter
        self.tol = tol

    def decompose(self, tensor: np.ndarray) -> TuckerResult:
        """
        Perform Tucker decomposition via HOOI.
        """
        T = np.asarray(tensor, dtype=np.float64)
        if T.ndim < 2:
            raise InvalidTensorError("Tucker requires order ≥ 2.")
        N = T.ndim
        # default ranks: min(shape, 10)
        if self.ranks is None:
            ranks = tuple(min(s, 10) for s in T.shape)
        else:
            ranks = tuple(self.ranks)
            if len(ranks) != N:
                raise InvalidTensorError(
                    f"ranks length {len(ranks)} ≠ tensor order {N}."
                )
            for r, s in zip(ranks, T.shape):
                if r <= 0 or r > s:
                    raise InvalidTensorError(f"Invalid rank {r} for mode size {s}.")

        # initialize factor matrices randomly
        factors: List[np.ndarray] = []
        for n, (I_n, R_n) in enumerate(zip(T.shape, ranks)):
            rng = np.random.RandomState(42 + n)
            U = rng.rand(I_n, R_n)
            # orthonormalize
            U, _ = np.linalg.qr(U)
            factors.append(U)

        prev_err = float("inf")
        T_norm = tensor_norm(T)
        n_iter = 0
        converged = False

        for it in range(self.max_iter):
            n_iter = it + 1
            for n in range(N):
                # unfold along mode n
                Tn = unfold(T, n)
                # build the projection of T onto all other modes
                proj = Tn
                for m in range(N):
                    if m != n:
                        # use the most recent factor
                        proj = proj @ np.kron(
                            np.eye(1),
                            factors[m].T,
                        ) if False else _project_along_mode(T, factors, n)
                        break
                # re-unfold and compute SVD
                proj_matrix = _project_along_mode(T, factors, n)
                U_n, _, _ = np.linalg.svd(proj_matrix, full_matrices=False)
                factors[n] = U_n[:, : ranks[n]]
            # compute reconstruction error
            G = _compute_core(T, factors)
            T_hat = G
            for n, U_n in enumerate(factors):
                T_hat = mode_n_product(T_hat, U_n, n)
            err = tensor_norm(T - T_hat) / max(T_norm, 1e-12)
            if abs(prev_err - err) < self.tol:
                converged = True
                break
            prev_err = err

        # final reconstruction error
        G = _compute_core(T, factors)
        T_hat = G
        for n, U_n in enumerate(factors):
            T_hat = mode_n_product(T_hat, U_n, n)
        err = tensor_norm(T - T_hat) / max(T_norm, 1e-12)
        explained = max(0.0, 1.0 - err ** 2)

        return TuckerResult(
            core=G,
            factors=factors,
            ranks=ranks,
            reconstruction_error=float(err),
            explained_variance=float(explained),
            n_iterations=n_iter,
            converged=converged,
        )


class CPDecomposition:
    """
    CP / PARAFAC decomposition via alternating least squares (ALS).
    """

    def __init__(
        self,
        rank: int = 5,
        max_iter: int = 100,
        tol: float = 1e-6,
    ) -> None:
        if rank <= 0:
            raise ValueError("rank must be positive.")
        self.rank = rank
        self.max_iter = max_iter
        self.tol = tol

    def decompose(self, tensor: np.ndarray) -> CPResult:
        """
        Perform CP decomposition via ALS.
        """
        T = np.asarray(tensor, dtype=np.float64)
        if T.ndim < 2:
            raise InvalidTensorError("CP requires order ≥ 2.")
        N = T.ndim
        R = self.rank

        # initialize factor matrices
        factors: List[np.ndarray] = []
        for n in range(N):
            rng = np.random.RandomState(7 + n)
            factors.append(rng.rand(T.shape[n], R))

        T_norm = tensor_norm(T)
        prev_err = float("inf")
        n_iter = 0
        converged = False

        for it in range(self.max_iter):
            n_iter = it + 1
            for n in range(N):
                # build the Khatri-Rao product of all other factor matrices
                others = [factors[m] for m in range(N) if m != n]
                KR = others[0]
                for M in others[1:]:
                    KR = khatri_rao_product(KR, M)
                # unfold T along mode n
                Tn = unfold(T, n)
                # ALS update: A_n = T_(n) · (KR) · pinv(KR^T KR)
                KtK = KR.T @ KR
                try:
                    A_n = Tn @ KR @ np.linalg.pinv(KtK)
                except np.linalg.LinAlgError as exc:
                    raise DecompositionError(f"CP ALS failed: {exc}") from exc
                factors[n] = np.maximum(A_n, 0.0)  # non-negativity

            # compute reconstruction error
            weights = np.ones(R)
            cp_res = CPResult(
                weights=weights,
                factors=factors,
                rank=R,
                reconstruction_error=0.0,
                explained_variance=0.0,
            )
            T_hat = cp_res.reconstruct()
            err = tensor_norm(T - T_hat) / max(T_norm, 1e-12)
            if abs(prev_err - err) < self.tol:
                converged = True
                break
            prev_err = err

        # final error
        T_hat = CPResult(
            weights=np.ones(R),
            factors=factors,
            rank=R,
            reconstruction_error=0.0,
            explained_variance=0.0,
        ).reconstruct()
        err = tensor_norm(T - T_hat) / max(T_norm, 1e-12)
        explained = max(0.0, 1.0 - err ** 2)
        weights = np.ones(R)

        return CPResult(
            weights=weights,
            factors=factors,
            rank=R,
            reconstruction_error=float(err),
            explained_variance=float(explained),
            n_iterations=n_iter,
            converged=converged,
        )


# ============================================================================
# HELPERS
# ============================================================================


def _project_along_mode(
    T: np.ndarray, factors: List[np.ndarray], mode: int
) -> np.ndarray:
    """
    Project T onto all modes except `mode`, returning the unfolded matrix
    along `mode` after contracting the other factors.
    """
    result = T
    for n, U_n in enumerate(factors):
        if n != mode:
            result = mode_n_product(result, U_n.T, n)
    return unfold(result, mode)


def _compute_core(T: np.ndarray, factors: List[np.ndarray]) -> np.ndarray:
    """Compute Tucker core tensor G."""
    G = T
    for n, U_n in enumerate(factors):
        G = mode_n_product(G, U_n.T, n)
    return G