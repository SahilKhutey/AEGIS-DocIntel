"""
Vietoris-Rips Filtration
========================

Mathematical Definition:
-----------------------
Given a metric space (X, d) and a parameter ε ≥ 0, the Vietoris-Rips
complex VR(X, ε) contains a simplex σ = {v₀, ..., v_k} iff:

    d(v_i, v_j) ≤ ε  for all pairs i, j

As ε increases, simplices are added — this defines a filtration:
    VR(X, ε₁) ⊆ VR(X, ε₂)  when  ε₁ ≤ ε₂

Persistent homology tracks which topological features (components, loops)
appear (birth) and disappear (death) as ε varies.

In AMDI-OS, the elements are document vertices (paragraphs, tables, figures)
and distances are computed from semantic/structural embeddings.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .distance_matrix import DistanceMatrix
from .exceptions import FiltrationError, InsufficientDataError
from .simplex import Simplex, SimplicialComplex


@dataclass
class VietorisRipsFiltration:
    """
    Builds a Vietoris-Rips filtration from a distance matrix.

    Attributes
    ----------
    distance_matrix : DistanceMatrix
        Pairwise distances between vertices.
    max_edge_length : Optional[float]
        Maximum edge length to include. If None, uses max distance.
    max_dimension : int
        Maximum simplex dimension to construct (default: 2).
    """

    distance_matrix: DistanceMatrix
    max_edge_length: Optional[float] = None
    max_dimension: int = 2

    def __post_init__(self) -> None:
        if self.max_edge_length is None:
            self.max_edge_length = float(self.distance_matrix.max_distance)

    def build_filtration(self) -> List[Tuple[float, SimplicialComplex]]:
        """
        Build the filtration as a list of (epsilon, complex) pairs.

        For efficiency, returns a sorted list of "critical values"
        (epsilon values where new simplices appear) along with the
        incremental complex.
        """
        n = self.distance_matrix.size
        if n < 2:
            raise InsufficientDataError("Need at least 2 vertices.")

        # Collect all pairwise distances (excluding diagonal)
        edges: List[Tuple[float, Tuple[int, int]]] = []
        for i in range(n):
            for j in range(i + 1, n):
                d = float(self.distance_matrix.matrix[i, j])
                if d <= self.max_edge_length:
                    edges.append((d, (i, j)))

        # Sort edges by distance (ascending)
        edges.sort(key=lambda x: x[0])

        # Collect distinct critical epsilon values
        critical_values = sorted({e[0] for e in edges})

        # Build filtration
        filtration: List[Tuple[float, SimplicialComplex]] = []
        current_complex = SimplicialComplex()

        # add all vertices at ε = 0
        for v in range(n):
            current_complex.add_simplex(Simplex(frozenset({v}), 0.0))
        filtration.append((0.0, self._copy_complex(current_complex)))

        edge_index = 0
        for eps in critical_values:
            # add all edges at this epsilon
            while edge_index < len(edges) and edges[edge_index][0] <= eps:
                _, (i, j) = edges[edge_index]
                current_complex.add_simplex(Simplex(frozenset({i, j}), eps))

                # add higher-dimensional simplices if requested
                if self.max_dimension >= 2:
                    self._add_higher_simplices(current_complex, eps, i, j)

                edge_index += 1
            filtration.append((eps, self._copy_complex(current_complex)))

        return filtration

    def _add_higher_simplices(
        self,
        complex_: SimplicialComplex,
        eps: float,
        new_i: int,
        new_j: int,
    ) -> None:
        """Add 2-simplices (triangles) that become valid when edge (i,j) is added."""
        n = self.distance_matrix.size
        # For each existing vertex k, check if triangle (i,j,k) is valid
        for k in range(n):
            if k == new_i or k == new_j:
                continue
            d_ik = float(self.distance_matrix.matrix[new_i, k])
            d_jk = float(self.distance_matrix.matrix[new_j, k])
            if d_ik <= eps and d_jk <= eps:
                complex_.add_simplex(Simplex(frozenset({new_i, new_j, k}), eps))

    @staticmethod
    def _copy_complex(c: SimplicialComplex) -> SimplicialComplex:
        """Deep copy a simplicial complex."""
        new_c = SimplicialComplex()
        for dim, simps in c.simplices.items():
            for s in simps:
                new_c.add_simplex(Simplex(frozenset(s.vertices), s.weight))
        return new_c
