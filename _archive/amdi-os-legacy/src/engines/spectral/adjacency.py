"""
Adjacency Matrix Construction
=============================

Builds the adjacency matrix A of a graph:

    A[i,j] = w_ij  if (i,j) ∈ E
    A[i,j] = 0      otherwise

Variants:
- Unweighted (binary)
- Weighted
- Distance-decayed (w_ij = exp(-d_ij² / σ²))
- Cosine similarity (for embeddings)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from .exceptions import InvalidGraphError


class AdjacencyType(Enum):
    """Adjacency matrix construction strategies."""

    UNWEIGHTED = "unweighted"
    WEIGHTED = "weighted"
    GAUSSIAN = "gaussian"
    COSINE = "cosine"


@dataclass
class AdjacencyMatrix:
    """
    Graph adjacency matrix with associated metadata.

    Attributes
    ----------
    matrix : np.ndarray
        Square (n, n) symmetric matrix.
    labels : Optional[List[str]]
        Optional vertex labels.
    weights : Optional[Dict[Tuple[int, int], float]]
        Original edge weights for reference.
    """

    matrix: np.ndarray
    labels: Optional[List[str]] = None
    weights: Optional[Dict[Tuple[int, int], float]] = None

    def __post_init__(self) -> None:
        if self.matrix.ndim != 2:
            raise ValueError("Adjacency matrix must be 2-dimensional.")
        if self.matrix.size == 0:
            raise InvalidGraphError("Adjacency matrix cannot be empty.")
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Adjacency matrix must be square.")
        # enforce symmetry
        self.matrix = 0.5 * (self.matrix + self.matrix.T)
        # zero diagonal
        np.fill_diagonal(self.matrix, 0.0)
        # ensure non-negative
        self.matrix = np.maximum(self.matrix, 0.0)

    @property
    def size(self) -> int:
        """Number of vertices."""
        return self.matrix.shape[0]

    @property
    def num_edges(self) -> int:
        """Number of edges (upper triangle count)."""
        return int(np.sum(self.matrix > 0) / 2)

    @property
    def is_weighted(self) -> bool:
        """Check if adjacency has non-binary values."""
        unique = np.unique(self.matrix)
        return not (len(unique) <= 2 and np.all((unique == 0) | (unique == 1)))

    @property
    def density(self) -> float:
        """Edge density: 2|E| / |V|(|V|-1)."""
        n = self.size
        if n < 2:
            return 0.0
        max_edges = n * (n - 1) / 2
        return self.num_edges / max_edges if max_edges > 0 else 0.0

    def degree_vector(self) -> np.ndarray:
        """Degree of each vertex."""
        return self.matrix.sum(axis=1)

    @classmethod
    def from_edges(
        cls,
        n: int,
        edges: List[Tuple[int, int, float]],
        labels: Optional[List[str]] = None,
    ) -> "AdjacencyMatrix":
        """
        Build from explicit edge list.

        Parameters
        ----------
        n : int
            Number of vertices.
        edges : List[Tuple[int, int, float]]
            List of (source, target, weight).
        labels : Optional[List[str]]
            Vertex labels.
        """
        A = np.zeros((n, n), dtype=np.float64)
        weight_map: Dict[Tuple[int, int], float] = {}
        for u, v, w in edges:
            if u < 0 or v < 0 or u >= n or v >= n:
                raise InvalidGraphError(
                    f"Edge ({u},{v}) out of bounds for n={n}."
                )
            A[u, v] = w
            A[v, u] = w
            weight_map[(u, v)] = w
            weight_map[(v, u)] = w
        return cls(matrix=A, labels=labels, weights=weight_map)

    @classmethod
    def from_distance_matrix(
        cls,
        distances: np.ndarray,
        sigma: float = 1.0,
        threshold: Optional[float] = None,
        labels: Optional[List[str]] = None,
    ) -> "AdjacencyMatrix":
        """
        Build adjacency from a distance matrix using Gaussian kernel.

        w_ij = exp(-d_ij² / σ²)

        Parameters
        ----------
        distances : np.ndarray
            Pairwise distance matrix.
        sigma : float
            Gaussian kernel bandwidth.
        threshold : Optional[float]
            If given, drop entries above threshold.
        """
        D = np.asarray(distances, dtype=np.float64)
        if D.ndim != 2 or D.shape[0] != D.shape[1]:
            raise InvalidGraphError("Distance matrix must be square.")
        A = np.exp(-(D ** 2) / (sigma ** 2))
        np.fill_diagonal(A, 0.0)
        if threshold is not None:
            A[A < threshold] = 0.0
        return cls(matrix=A, labels=labels)

    @classmethod
    def from_similarity(
        cls,
        embeddings: np.ndarray,
        labels: Optional[List[str]] = None,
        threshold: Optional[float] = None,
    ) -> "AdjacencyMatrix":
        """
        Build adjacency from cosine similarity between embeddings.
        """
        from sklearn.metrics.pairwise import cosine_similarity

        E = np.asarray(embeddings, dtype=np.float64)
        if E.ndim != 2 or E.shape[0] < 2:
            raise InvalidGraphError("Embeddings must be (n, d) with n ≥ 2.")
        S = cosine_similarity(E)
        np.fill_diagonal(S, 0.0)
        # keep only positive similarities
        S = np.maximum(S, 0.0)
        if threshold is not None:
            S[S < threshold] = 0.0
        return cls(matrix=S, labels=labels)
