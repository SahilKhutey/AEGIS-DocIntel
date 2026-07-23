"""
Persistent Homology Analysis
============================

Mathematical Definition:
-----------------------
Persistent homology tracks the birth and death of topological features
across all scales of a filtration.

Given filtration:  ∅ = K₀ ⊆ K₁ ⊆ ... ⊆ Kₙ = K

Each feature is represented as a pair (birth, death):
    - H₀ features: connected components
    - H₁ features: loops
    - H₂ features: voids

Persistence of a feature: pers = death - birth

Larger persistence ⇒ more significant topological feature.

In AMDI-OS:
- Birth time = filtration value at which the simplex is added
- Death time = filtration value at which the feature becomes trivial
- Persistence diagrams encode structural salience of document regions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .connected_components import ConnectedComponentsAnalyzer
from .exceptions import InsufficientDataError
from .filtration import VietorisRipsFiltration
from .loops import LoopsAnalyzer, _gf2_rank
from .simplex import Simplex, SimplicialComplex


@dataclass
class PersistencePoint:
    """
    A single point in a persistence diagram.

    Attributes
    ----------
    dim : int
        Homological dimension (0 for components, 1 for loops, 2 for voids).
    birth : float
        Filtration value at birth.
    death : float
        Filtration value at death (∞ for infinite features).
    representative : Optional[List[int]]
        Optional simplices representing the feature.
    """

    dim: int
    birth: float
    death: float
    representative: Optional[List[int]] = None

    @property
    def persistence(self) -> float:
        """Lifetime of the feature."""
        if self.death == float("inf"):
            return float("inf")
        return self.death - self.birth

    @property
    def is_infinite(self) -> bool:
        return self.death == float("inf")


@dataclass
class PersistenceDiagram:
    """
    Full persistence diagram.

    Attributes
    ----------
    points : List[PersistencePoint]
        All persistence points across dimensions.
    """

    points: List[PersistencePoint] = field(default_factory=list)

    def by_dimension(self, dim: int) -> List[PersistencePoint]:
        return [p for p in self.points if p.dim == dim]

    @property
    def betti_0_curve(self) -> List[Tuple[float, int]]:
        """Evolution of β₀ across filtration."""
        return [(p.birth, p.death) for p in self.by_dimension(0)]

    @property
    def betti_1_curve(self) -> List[Tuple[float, int]]:
        """Evolution of β₁ across filtration."""
        return [(p.birth, p.death) for p in self.by_dimension(1)]

    @property
    def total_persistence(self) -> float:
        return float(
            sum(p.persistence for p in self.points if not p.is_infinite)
        )

    @property
    def max_persistence(self) -> float:
        finite = [p.persistence for p in self.points if not p.is_infinite]
        return max(finite) if finite else 0.0

    @property
    def num_features(self) -> int:
        return len(self.points)

    @property
    def num_infinite(self) -> int:
        return sum(1 for p in self.points if p.is_infinite)


@dataclass
class PersistenceResult:
    """
    Complete persistence analysis result.

    Attributes
    ----------
    diagram : PersistenceDiagram
        Full persistence diagram.
    bottleneck_distance : Optional[float]
        Optional comparison metric (against reference diagram).
    significant_features : List[PersistencePoint]
        Features with persistence > persistence_threshold.
    persistence_threshold : float
        Threshold used to select significant features.
    """

    diagram: PersistenceDiagram
    bottleneck_distance: Optional[float] = None
    significant_features: List[PersistencePoint] = field(default_factory=list)
    persistence_threshold: float = 0.0

    @property
    def significant_count(self) -> int:
        return len(self.significant_features)

    @property
    def significant_ratio(self) -> float:
        if self.diagram.num_features == 0:
            return 0.0
        return self.significant_count / self.diagram.num_features


class PersistenceAnalyzer:
    """
    Computes persistent homology via the standard algorithm:

        1. Build filtration of simplicial complexes.
        2. Sort simplices by filtration value.
        3. Use Union-Find to track component merges (H₀).
        4. Track cycles via boundary matrix reduction (H₁, H₂).
        5. Output persistence diagram.
    """

    def __init__(self, max_dimension: int = 1) -> None:
        self.max_dimension = max_dimension

    def analyze(
        self,
        filtration: List[Tuple[float, SimplicialComplex]],
        persistence_threshold: float = 0.0,
    ) -> PersistenceResult:
        """
        Run persistence analysis on a filtration.

        Parameters
        ----------
        filtration : List[Tuple[float, SimplicialComplex]]
            Output of VietorisRipsFiltration.build_filtration().
        persistence_threshold : float
            Minimum persistence for a feature to be marked significant.
        """
        if not filtration:
            raise InsufficientDataError("Filtration is empty.")

        # Collect all simplices with their birth times
        all_simplices: List[Tuple[float, Simplex, int]] = []
        seen: Dict[frozenset, float] = {}
        for eps, K in filtration:
            for dim, simps in K.simplices.items():
                for s in simps:
                    if s.vertices not in seen:
                        seen[s.vertices] = eps
                        all_simplices.append((eps, s, dim))

        # Sort by (birth, dimension) — lower-dim first at same birth
        all_simplices.sort(key=lambda x: (x[0], x[2]))

        # Compute H₀ persistence via Union-Find
        points: List[PersistencePoint] = []
        points.extend(self._compute_h0_persistence(all_simplices))

        # Compute H₁ persistence via boundary reduction
        if self.max_dimension >= 1:
            points.extend(self._compute_h1_persistence(all_simplices))

        # Compute H₂ persistence
        if self.max_dimension >= 2:
            points.extend(self._compute_h2_persistence(all_simplices))

        diagram = PersistenceDiagram(points=points)
        significant = [
            p for p in points if p.persistence > persistence_threshold
        ]

        return PersistenceResult(
            diagram=diagram,
            significant_features=significant,
            persistence_threshold=persistence_threshold,
        )

    @staticmethod
    def _compute_h0_persistence(
        simplices: List[Tuple[float, Simplex, int]],
    ) -> List[PersistencePoint]:
        """H₀: connected components — birth at vertex, death at merge."""
        from .connected_components import _UnionFind

        # Index vertices
        vertex_ids: List[int] = []
        vertex_set: set = set()
        for _, s, dim in simplices:
            if dim == 0:
                v = list(s.vertices)[0]
                if v not in vertex_set:
                    vertex_set.add(v)
                    vertex_ids.append(v)

        vertex_ids.sort()
        idx = {v: i for i, v in enumerate(vertex_ids)}
        n = len(vertex_ids)

        uf = _UnionFind(n)
        component_birth: Dict[int, float] = {
            i: 0.0 for i in range(n)
        }  # root → birth time

        points: List[PersistencePoint] = []

        for birth, s, dim in simplices:
            if dim == 1:
                vlist = list(s.vertices)
                i, j = idx[vlist[0]], idx[vlist[1]]
                ri, rj = uf.find(i), uf.find(j)
                if ri != rj:
                    # merge: older component stays, younger dies
                    if component_birth[ri] > component_birth[rj]:
                        dying_root = ri
                        dying_birth = component_birth[ri]
                    else:
                        dying_root = rj
                        dying_birth = component_birth[rj]

                    uf.union(ri, rj)
                    new_root = uf.find(ri)
                    component_birth[new_root] = min(
                        component_birth[ri], component_birth[rj]
                    )

                    points.append(
                        PersistencePoint(
                            dim=0,
                            birth=dying_birth,
                            death=birth,
                        )
                    )

        # The remaining root has infinite lifetime
        roots = set(uf.find(i) for i in range(n))
        for r in roots:
            points.append(
                PersistencePoint(
                    dim=0,
                    birth=component_birth[r],
                    death=float("inf"),
                )
            )

        return points

    @staticmethod
    def _compute_h1_persistence(
        simplices: List[Tuple[float, Simplex, int]],
    ) -> List[PersistencePoint]:
        """H₁: 1-cycles — birth at edge addition, death at triangle fill."""
        # Find all edges (1-simplices) and triangles (2-simplices)
        edges = [s for _, s, dim in simplices if dim == 1]
        triangles = [s for _, s, dim in simplices if dim == 2]

        if not edges:
            return []

        # Maps
        edge_to_idx = {e.vertices: i for i, e in enumerate(edges)}
        T = len(triangles)
        E = len(edges)

        # Columns of D (each column is a list of edge indices)
        cols = []
        for tri in triangles:
            col = []
            vlist = list(tri.vertices)
            for r in range(3):
                edge_key = frozenset({vlist[r], vlist[(r + 1) % 3]})
                if edge_key in edge_to_idx:
                    col.append(edge_to_idx[edge_key])
            col.sort()
            cols.append(col)

        # Pivots maps
        pivots = {}
        for j in range(T):
            col = cols[j]
            while col:
                pivot = col[-1]
                if pivot in pivots:
                    other_col = cols[pivots[pivot]]
                    new_col = sorted(list(set(col) ^ set(other_col)))
                    col = new_col
                else:
                    pivots[pivot] = j
                    break
            cols[j] = col

        paired_edges = set(pivots.keys())

        # Determine cycle creators
        vertex_set = set()
        for s in edges:
            vertex_set.update(s.vertices)

        vertex_list = sorted(list(vertex_set))
        v_to_idx = {v: i for i, v in enumerate(vertex_list)}

        from .connected_components import _UnionFind
        uf = _UnionFind(len(vertex_list))

        cycle_creators = []
        for i, edge in enumerate(edges):
            vlist = list(edge.vertices)
            u, v = v_to_idx[vlist[0]], v_to_idx[vlist[1]]
            if uf.find(u) == uf.find(v):
                cycle_creators.append(i)
            else:
                uf.union(u, v)

        # Generate H1 points
        points = []
        for idx in cycle_creators:
            birth_val = edges[idx].weight
            if idx in paired_edges:
                tri_idx = pivots[idx]
                death_val = triangles[tri_idx].weight
                if death_val >= birth_val:
                    points.append(
                        PersistencePoint(
                            dim=1,
                            birth=birth_val,
                            death=death_val,
                            representative=[idx]
                        )
                    )
            else:
                points.append(
                    PersistencePoint(
                        dim=1,
                        birth=birth_val,
                        death=float("inf"),
                        representative=[idx]
                    )
                )
        return points

    @staticmethod
    def _compute_h2_persistence(
        simplices: List[Tuple[float, Simplex, int]],
    ) -> List[PersistencePoint]:
        """H₂: 2-cycles (voids) — birth at triangle addition, death at tetrahedron fill."""
        edges = [s for _, s, dim in simplices if dim == 1]
        triangles = [s for _, s, dim in simplices if dim == 2]

        if not triangles:
            return []

        edge_to_idx = {e.vertices: i for i, e in enumerate(edges)}
        T = len(triangles)

        cols = []
        for tri in triangles:
            col = []
            vlist = list(tri.vertices)
            for r in range(3):
                edge_key = frozenset({vlist[r], vlist[(r + 1) % 3]})
                if edge_key in edge_to_idx:
                    col.append(edge_to_idx[edge_key])
            col.sort()
            cols.append(col)

        pivots = {}
        zero_columns = []

        for j in range(T):
            col = cols[j]
            while col:
                pivot = col[-1]
                if pivot in pivots:
                    other_col = cols[pivots[pivot]]
                    new_col = sorted(list(set(col) ^ set(other_col)))
                    col = new_col
                else:
                    pivots[pivot] = j
                    break
            cols[j] = col
            if not col:
                zero_columns.append(j)

        points = []
        for j in zero_columns:
            birth_val = triangles[j].weight
            points.append(
                PersistencePoint(
                    dim=2,
                    birth=birth_val,
                    death=float("inf"),
                    representative=[j]
                )
            )
        return points
