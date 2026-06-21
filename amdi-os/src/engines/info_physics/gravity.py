"""
Information Gravity
===================

Mathematical Definition:
-----------------------
Information gravity treats document elements as massive bodies that
attract attention according to inverse-square law:

    G(i, j) = (Importance_i × Connectivity_i × w_j) / (d(i, j)² + ε)

where:
    Importance_i ∈ [0, 1]   semantic importance of element i
    Connectivity_i ∈ [0, 1] how connected i is to others
    w_j                     weight of target j
    d(i, j)                 geometric / semantic distance

High-gravity elements:
    - Main tables, conclusions, abstract, summary

Gravity field G_i at element i:
    G_i = Σ_{j ≠ i} G(i, j)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .exceptions import InvalidDocumentError


@dataclass
class GravityField:
    """
    Gravity field over all elements.

    Attributes
    ----------
    gravity : np.ndarray
        G_i for each element i.
    gravity_matrix : np.ndarray
        Pairwise gravity G(i, j).
    strongest_attractor : int
        Element with maximum total gravity.
    """

    gravity: np.ndarray
    gravity_matrix: np.ndarray
    strongest_attractor: int

    @property
    def total_gravity(self) -> float:
        return float(self.gravity.sum())

    @property
    def mean_gravity(self) -> float:
        return float(self.gravity.mean())


class InformationGravity:
    """
    Information gravity container for a single pair.
    """

    def __init__(
        self,
        source_id: int,
        target_id: int,
        gravity_value: float,
        importance: float,
        connectivity: float,
        distance: float,
    ) -> None:
        self.source_id = source_id
        self.target_id = target_id
        self.gravity_value = gravity_value
        self.importance = importance
        self.connectivity = connectivity
        self.distance = distance

    def __repr__(self) -> str:
        return (
            f"Gravity({self.source_id}→{self.target_id}={self.gravity_value:.4f})"
        )


class GravityCalculator:
    """
    Computes information gravity fields.
    """

    def __init__(
        self,
        epsilon: float = 1e-6,
        importance_weight: float = 0.5,
        connectivity_weight: float = 0.5,
    ) -> None:
        self.epsilon = epsilon
        s = importance_weight + connectivity_weight
        self.importance_weight = importance_weight / s
        self.connectivity_weight = connectivity_weight / s

    def compute(
        self,
        importance: np.ndarray,
        connectivity: np.ndarray,
        distances: np.ndarray,
        target_weights: Optional[np.ndarray] = None,
    ) -> GravityField:
        """
        Compute pairwise information gravity.

        Parameters
        ----------
        importance : np.ndarray
            (n,) per-element importance in [0, 1].
        connectivity : np.ndarray
            (n,) per-element connectivity (degree centrality) in [0, 1].
        distances : np.ndarray
            (n, n) pairwise distance matrix.
        target_weights : Optional[np.ndarray]
            (n,) per-target weight (default: uniform).
        """
        imp = np.asarray(importance, dtype=np.float64)
        conn = np.asarray(connectivity, dtype=np.float64)
        dist = np.asarray(distances, dtype=np.float64)
        n = imp.shape[0]

        if conn.shape[0] != n or dist.shape != (n, n):
            raise InvalidDocumentError(
                f"Shape mismatch: importance {imp.shape}, connectivity {conn.shape}, "
                f"distances {dist.shape}"
            )

        if target_weights is None:
            w = np.ones(n, dtype=np.float64)
        else:
            w = np.asarray(target_weights, dtype=np.float64)

        # mass per source
        mass = self.importance_weight * imp + self.connectivity_weight * conn

        # gravity matrix: G[i,j] = mass[i] * w[j] / (d[i,j]² + ε)
        dist_sq = dist ** 2 + self.epsilon
        gravity_matrix = np.outer(mass, w) / dist_sq
        np.fill_diagonal(gravity_matrix, 0.0)

        # gravity per element (row sum)
        gravity = gravity_matrix.sum(axis=1)
        strongest = int(np.argmax(gravity))

        return GravityField(
            gravity=gravity,
            gravity_matrix=gravity_matrix,
            strongest_attractor=strongest,
        )

    def top_attractors(
        self,
        gravity_field: GravityField,
        k: int = 5,
    ) -> List[Tuple[int, float]]:
        """Return top-k elements by total gravity."""
        idx = np.argsort(gravity_field.gravity)[::-1][:k]
        return [(int(i), float(gravity_field.gravity[i])) for i in idx]