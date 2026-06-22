"""
Eigenvalue / Eigenvector Solver
===============================

Computes the spectral decomposition of the graph Laplacian:

    L v_i = λ_i v_i,    i = 0, ..., n-1

Returns (λ₀, λ₁, ..., λ_{n-1}) and the corresponding eigenvectors.

Mathematical Significance:
- λ₀ = 0 with multiplicity = β₀ (connected components)
- λ₁ = Fiedler value = algebraic connectivity
- Eigenvector gaps reveal community structure
- Spectral embedding = (v₁, v₂, ..., v_k)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .exceptions import EigenDecompositionError, InvalidGraphError
from .laplacian import LaplacianMatrix


@dataclass
class EigenResult:
    """
    Result of eigen-decomposition.

    Attributes
    ----------
    eigenvalues : np.ndarray
        Sorted ascending eigenvalues.
    eigenvectors : np.ndarray
        Columns are eigenvectors (n, k).
    fiedler_value : float
        λ₁ — algebraic connectivity.
    fiedler_vector : Optional[np.ndarray]
        The Fiedler eigenvector.
    num_zero_eigenvalues : int
        Multiplicity of λ=0 (β₀).
    spectral_gaps : np.ndarray
        λ_{i+1} - λ_i for each i.
    """

    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    fiedler_value: float
    fiedler_vector: Optional[np.ndarray] = None
    num_zero_eigenvalues: int = 0
    spectral_gaps: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self) -> None:
        if len(self.eigenvalues) > 1:
            self.spectral_gaps = np.diff(self.eigenvalues)
        if len(self.eigenvalues) > 1:
            self.fiedler_value = float(self.eigenvalues[1])
            if self.fiedler_vector is None and self.eigenvectors.shape[1] > 1:
                self.fiedler_vector = self.eigenvectors[:, 1]
        else:
            self.fiedler_value = 0.0

    @property
    def num_eigenvalues(self) -> int:
        return len(self.eigenvalues)

    @property
    def spectral_radius(self) -> float:
        """Largest eigenvalue."""
        return float(self.eigenvalues[-1]) if len(self.eigenvalues) > 0 else 0.0

    @property
    def eigengap(self) -> int:
        """Index of the largest spectral gap (eigengap heuristic)."""
        if len(self.spectral_gaps) == 0:
            return 0
        return int(np.argmax(self.spectral_gaps))

    @property
    def estimated_clusters(self) -> int:
        """Number of clusters suggested by eigengap heuristic."""
        return self.eigengap + 1

    def top_k_eigenvectors(self, k: int) -> np.ndarray:
        """Return the top-k eigenvectors (skip the trivial zero eigenvector)."""
        k = min(k, self.eigenvectors.shape[1])
        return self.eigenvectors[:, :k]


class EigenSolver:
    """
    Computes eigenvalues and eigenvectors of a Laplacian.

    Uses scipy/numpy dense eigensolvers with optional sparse acceleration.
    """

    def __init__(self, tolerance: float = 1e-10, max_eigenvalues: Optional[int] = None) -> None:
        self.tolerance = tolerance
        self.max_eigenvalues = max_eigenvalues

    def solve(
        self,
        laplacian: LaplacianMatrix,
        k: Optional[int] = None,
    ) -> EigenResult:
        """
        Compute eigenvalues and eigenvectors.

        Parameters
        ----------
        laplacian : LaplacianMatrix
        k : Optional[int]
            If given, compute only the k smallest eigenvalues/eigenvectors.
            Useful for large graphs.
        """
        L = laplacian.matrix
        n = L.shape[0]
        if n < 2:
            raise InvalidGraphError("Need at least 2 vertices.")

        try:
            if k is not None and 2 <= k < n - 1:
                # sparse shift-invert mode for smallest eigenvalues
                eigvals, eigvecs = self._solve_smallest_k(L, k)
            else:
                # full dense solver
                eigvals, eigvecs = np.linalg.eigh(L)
        except np.linalg.LinAlgError as exc:
            raise EigenDecompositionError(f"Eigen-decomposition failed: {exc}") from exc

        # sort ascending (np.linalg.eigh returns ascending)
        eigvals = np.asarray(eigvals, dtype=np.float64)
        eigvecs = np.asarray(eigvecs, dtype=np.float64)

        # count zero eigenvalues (within tolerance)
        num_zero = int(np.sum(np.abs(eigvals) < self.tolerance))

        # Fiedler vector (if available)
        fiedler = None
        if num_zero < n and eigvecs.shape[1] > num_zero:
            fiedler = eigvecs[:, num_zero]

        return EigenResult(
            eigenvalues=eigvals,
            eigenvectors=eigvecs,
            fiedler_value=float(eigvals[num_zero]) if num_zero < n else 0.0,
            fiedler_vector=fiedler,
            num_zero_eigenvalues=num_zero,
        )

    def _solve_smallest_k(self, L: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Use scipy.sparse.linalg.eigsh for smallest k eigenvalues."""
        try:
            from scipy.sparse import csr_matrix
            from scipy.sparse.linalg import eigsh

            L_sparse = csr_matrix(L)
            # sigma=0 → eigenvalues closest to 0
            eigvals, eigvecs = eigsh(
                L_sparse, k=k, sigma=0.0, which="LM", tol=self.tolerance
            )
            # sort ascending
            idx = np.argsort(eigvals)
            eigvals = eigvals[idx]
            eigvecs = eigvecs[:, idx]
            return eigvals, eigvecs
        except Exception:
            # fallback to dense solver
            return np.linalg.eigh(L)
