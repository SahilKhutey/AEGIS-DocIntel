"""
Distance Matrix Computation
===========================

Computes pairwise distances between document elements (vertices)
to be used as input for Vietoris-Rips filtration.

Distance types supported:
- Euclidean (geometric coordinates)
- Semantic (cosine distance from embeddings)
- Combined (weighted sum)

Mathematical Definition:
d(v_i, v_j) = sqrt(Σ_k (x_ik - x_jk)²)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from .exceptions import InsufficientDataError


@dataclass
class DistanceMatrix:
    """
    Square symmetric distance matrix between document elements.

    Attributes
    ----------
    matrix : np.ndarray
        Square (n x n) symmetric matrix of pairwise distances.
    labels : List[str]
        Optional human-readable labels for each element.
    """

    matrix: np.ndarray
    labels: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.matrix.ndim != 2:
            raise ValueError("Distance matrix must be 2-dimensional.")
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Distance matrix must be square.")
        n = self.matrix.shape[0]
        if n < 2:
            raise InsufficientDataError(
                f"Need at least 2 elements to compute distances; got {n}."
            )
        # enforce symmetry
        self.matrix = 0.5 * (self.matrix + self.matrix.T)
        # enforce zero diagonal
        np.fill_diagonal(self.matrix, 0.0)

    @property
    def size(self) -> int:
        """Number of elements (vertices)."""
        return self.matrix.shape[0]

    @property
    def mean_distance(self) -> float:
        """Mean off-diagonal distance."""
        n = self.size
        if n < 2:
            return 0.0
        mask = ~np.eye(n, dtype=bool)
        return float(self.matrix[mask].mean())

    @property
    def max_distance(self) -> float:
        """Maximum off-diagonal distance."""
        n = self.size
        if n < 2:
            return 0.0
        return float(self.matrix[~np.eye(n, dtype=bool)].max())

    @property
    def min_distance(self) -> float:
        """Minimum off-diagonal distance (excluding zero diagonal)."""
        n = self.size
        if n < 2:
            return 0.0
        masked = self.matrix[~np.eye(n, dtype=bool)]
        return float(masked.min()) if masked.size > 0 else 0.0

    @classmethod
    def from_coordinates(
        cls,
        coordinates: np.ndarray,
        labels: Optional[List[str]] = None,
        metric: str = "euclidean",
    ) -> "DistanceMatrix":
        """
        Build a distance matrix from a set of coordinate vectors.

        Parameters
        ----------
        coordinates : np.ndarray
            (n, d) array of n points in d-dimensional space.
        labels : Optional[List[str]]
            Optional labels for each point.
        metric : str
            Distance metric: 'euclidean', 'cosine', 'manhattan'.
        """
        from scipy.spatial.distance import cdist

        coords = np.asarray(coordinates, dtype=np.float64)
        if coords.ndim != 2:
            raise ValueError("coordinates must be 2D (n, d).")
        if coords.shape[0] < 2:
            raise InsufficientDataError("Need at least 2 points.")
        dists = cdist(coords, coords, metric=metric)
        return cls(matrix=dists, labels=labels)
