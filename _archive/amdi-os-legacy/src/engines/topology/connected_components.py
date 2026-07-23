"""
Connected Components Analysis (H₀ Homology)
============================================

Mathematical Definition:
-----------------------
H₀(X) counts the number of connected components of a topological space X.

In a simplicial complex, two vertices belong to the same component iff
there exists a path of edges connecting them.

Equivalently, β₀ = |V| - rank(∂₁)
where ∂₁ is the boundary map from 1-chains to 0-chains.

In AMDI-OS:
- Each connected component represents an isolated section/region of a document.
- Components are computed via Union-Find (Disjoint Set Union).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .exceptions import InsufficientDataError
from .simplex import SimplicialComplex


class _UnionFind:
    """Disjoint Set Union (Union-Find) with path compression."""

    def __init__(self, n: int) -> None:
        self.parent: List[int] = list(range(n))
        self.rank: List[int] = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


@dataclass
class ConnectedComponentsResult:
    """
    Result of connected components analysis.

    Attributes
    ----------
    betti_0 : int
        Number of connected components (Betti number β₀).
    components : List[Set[int]]
        List of vertex sets, one per connected component.
    component_map : Dict[int, int]
        Mapping from vertex ID → component ID.
    """

    betti_0: int
    components: List[Set[int]] = field(default_factory=list)
    component_map: Dict[int, int] = field(default_factory=dict)

    @property
    def num_components(self) -> int:
        return self.betti_0

    @property
    def largest_component_size(self) -> int:
        if not self.components:
            return 0
        return max(len(c) for c in self.components)

    @property
    def smallest_component_size(self) -> int:
        if not self.components:
            return 0
        return min(len(c) for c in self.components)

    @property
    def mean_component_size(self) -> float:
        if not self.components:
            return 0.0
        return float(sum(len(c) for c in self.components)) / len(self.components)


class ConnectedComponentsAnalyzer:
    """
    Computes connected components (0-dimensional homology) of a simplicial complex.

    Algorithm:
        1. Initialize Union-Find with one element per vertex.
        2. For each edge, union its endpoints.
        3. Components are the equivalence classes under the Union-Find structure.
    """

    def analyze(self, complex_: SimplicialComplex) -> ConnectedComponentsResult:
        """
        Compute connected components of the given simplicial complex.

        Parameters
        ----------
        complex_ : SimplicialComplex
            The input simplicial complex.

        Returns
        -------
        ConnectedComponentsResult
        """
        vertices = sorted(complex_.vertices())
        n = len(vertices)
        if n == 0:
            raise InsufficientDataError("Complex has no vertices.")

        # Map vertex → index in union-find
        idx_map = {v: i for i, v in enumerate(vertices)}
        uf = _UnionFind(n)

        # Union all edges
        for edge in complex_.simplices.get(1, []):
            vlist = list(edge.vertices)
            uf.union(idx_map[vlist[0]], idx_map[vlist[1]])

        # Build components
        groups: Dict[int, Set[int]] = {}
        for v in vertices:
            root = uf.find(idx_map[v])
            if root not in groups:
                groups[root] = set()
            groups[root].add(v)

        components = list(groups.values())
        component_map: Dict[int, int] = {}
        for cid, comp in enumerate(components):
            for v in comp:
                component_map[v] = cid

        return ConnectedComponentsResult(
            betti_0=len(components),
            components=components,
            component_map=component_map,
        )
