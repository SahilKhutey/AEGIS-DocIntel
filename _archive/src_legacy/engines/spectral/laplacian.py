"""
Graph Laplacian
===============

Three variants:
1. Unnormalized: L = D - A
2. Symmetric normalized: L_sym = D^(-1/2) L D^(-1/2) = I - D^(-1/2) A D^(-1/2)
3. Random walk (left) normalized: L_rw = D^(-1) L = I - D^(-1) A

Properties:
- L is symmetric, positive semi-definite
- Eigenvalues: 0 = λ₀ ≤ λ₁ ≤ ... ≤ λ_{n-1}
- Multiplicity of eigenvalue 0 = number of connected components (β₀)
- Fiedler value (λ₁) = algebraic connectivity
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

from .adjacency import AdjacencyMatrix
from .exceptions import InvalidGraphError


class LaplacianType(Enum):
    """Type of graph Laplacian."""

    UNNORMALIZED = "unnormalized"
    SYMMETRIC_NORMALIZED = "symmetric_normalized"
    RANDOM_WALK = "random_walk"


@dataclass
class LaplacianMatrix:
    """
    Graph Laplacian matrix.

    Attributes
    ----------
    matrix : np.ndarray
        The Laplacian.
    laplacian_type : LaplacianType
        Type of Laplacian.
    is_normalized : bool
    """

    matrix: np.ndarray
    laplacian_type: LaplacianType
    is_normalized: bool = False

    @property
    def size(self) -> int:
        return self.matrix.shape[0]

    @property
    def is_symmetric(self) -> bool:
        return np.allclose(self.matrix, self.matrix.T)

    @property
    def is_psd(self) -> bool:
        """Check if positive semi-definite."""
        eigvals = np.linalg.eigvalsh(self.matrix)
        return bool(np.all(eigvals >= -1e-10))


class LaplacianBuilder:
    """
    Build Laplacian matrices from adjacency matrices.
    """

    @staticmethod
    def build(
        adjacency: AdjacencyMatrix,
        laplacian_type: LaplacianType = LaplacianType.SYMMETRIC_NORMALIZED,
    ) -> LaplacianMatrix:
        """
        Compute the specified Laplacian.

        Parameters
        ----------
        adjacency : AdjacencyMatrix
        laplacian_type : LaplacianType
        """
        A = adjacency.matrix
        n = A.shape[0]
        if n < 2:
            raise InvalidGraphError("Need at least 2 vertices.")

        # Degree vector
        deg = A.sum(axis=1)
        D = np.diag(deg)
        L = D - A

        if laplacian_type == LaplacianType.UNNORMALIZED:
            return LaplacianMatrix(
                matrix=L,
                laplacian_type=laplacian_type,
                is_normalized=False,
            )

        if laplacian_type == LaplacianType.SYMMETRIC_NORMALIZED:
            d_inv_sqrt = np.zeros_like(deg)
            nonzero = deg > 1e-12
            d_inv_sqrt[nonzero] = 1.0 / np.sqrt(deg[nonzero])
            D_inv_sqrt = np.diag(d_inv_sqrt)
            L_sym = D_inv_sqrt @ L @ D_inv_sqrt
            return LaplacianMatrix(
                matrix=L_sym,
                laplacian_type=laplacian_type,
                is_normalized=True,
            )

        if laplacian_type == LaplacianType.RANDOM_WALK:
            d_inv = np.zeros_like(deg)
            nonzero = deg > 1e-12
            d_inv[nonzero] = 1.0 / deg[nonzero]
            D_inv = np.diag(d_inv)
            L_rw = D_inv @ L
            return LaplacianMatrix(
                matrix=L_rw,
                laplacian_type=laplacian_type,
                is_normalized=True,
            )

        raise ValueError(f"Unknown Laplacian type: {laplacian_type}")
