"""
Loop Detection (H₁ Homology)
============================

Mathematical Definition:
-----------------------
H₁(X) counts 1-dimensional "holes" — closed loops that are not boundaries
of any 2-chain.

In graph/simplicial complex terms:
    β₁ = |E| - |V| + β₀ - (number of independent triangles)

Equivalently, via the rank-nullity theorem applied to the boundary maps:

    rank(∂₁) = |V| - β₀        (cycles from edges)
    rank(∂₂) = (number of 2-simplices that are independent)
    β₁       = rank(∂₁) - rank(∂₂)
             = |E| - |V| + β₀ - (independent triangles)

In AMDI-OS, loops correspond to cyclic references between document sections
(e.g., A → B → C → A).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import numpy as np

from .connected_components import ConnectedComponentsAnalyzer
from .exceptions import InsufficientDataError
from .simplex import Simplex, SimplicialComplex


@dataclass
class Loop:
    """
    Represents a detected 1-cycle (loop).

    Attributes
    ----------
    vertices : List[int]
        Vertices forming the loop, in traversal order.
    length : int
        Number of edges in the loop.
    weight : float
        Average edge weight / filtration value.
    """

    vertices: List[int]
    length: int
    weight: float = 0.0


@dataclass
class LoopsResult:
    """
    Result of loop analysis.

    Attributes
    ----------
    betti_1 : int
        First Betti number (number of independent loops).
    loops : List[Loop]
        Detected loops (a basis for H₁).
    cycle_space_dimension : int
        Dimension of the cycle space: |E| - |V| + β₀.
    """

    betti_1: int
    loops: List[Loop] = field(default_factory=list)
    cycle_space_dimension: int = 0

    @property
    def num_loops(self) -> int:
        return self.betti_1

    @property
    def mean_loop_length(self) -> float:
        if not self.loops:
            return 0.0
        return float(sum(L.length for L in self.loops)) / len(self.loops)

    @property
    def max_loop_length(self) -> int:
        if not self.loops:
            return 0
        return max(L.length for L in self.loops)


class LoopsAnalyzer:
    """
    Detects 1-dimensional homology (loops) in a simplicial complex.

    Algorithm:
        1. Compute β₀ via ConnectedComponentsAnalyzer.
        2. Compute cycle space dimension: c = |E| - |V| + β₀
        3. Compute rank of ∂₂ (independent 2-simplices) via Gaussian elimination
           on the boundary matrix.
        4. β₁ = c - rank(∂₂)
    """

    def analyze(self, complex_: SimplicialComplex) -> LoopsResult:
        if complex_.num_vertices == 0:
            raise InsufficientDataError("Complex has no vertices.")

        # Step 1: β₀
        cc_analyzer = ConnectedComponentsAnalyzer()
        cc_result = cc_analyzer.analyze(complex_)
        beta_0 = cc_result.betti_0

        # Step 2: Cycle space dimension
        V = complex_.num_vertices
        E = complex_.num_edges
        cycle_dim = E - V + beta_0
        if cycle_dim < 0:
            cycle_dim = 0

        # Step 3: rank(∂₂)
        rank_d2 = self._rank_boundary_2(complex_)

        # Step 4: β₁
        beta_1 = max(0, cycle_dim - rank_d2)

        # Step 5: extract representative loops
        loops = self._extract_loops(complex_, beta_1)

        return LoopsResult(
            betti_1=beta_1,
            loops=loops,
            cycle_space_dimension=cycle_dim,
        )

    @staticmethod
    def _rank_boundary_2(complex_: SimplicialComplex) -> int:
        """
        Compute rank of ∂₂ : C₂ → C₁ using Gaussian elimination.
        """
        triangles = complex_.simplices.get(2, [])
        if not triangles:
            return 0

        # Map edges → index
        edges_list: List[Simplex] = complex_.simplices.get(1, [])
        edge_index: Dict[frozenset, int] = {
            e.vertices: i for i, e in enumerate(edges_list)
        }

        # Build boundary matrix (triangles × edges)
        matrix = np.zeros((len(triangles), len(edges_list)), dtype=np.int8)
        for ti, tri in enumerate(triangles):
            vlist = list(tri.vertices)
            for r in range(3):
                a, b = vlist[r], vlist[(r + 1) % 3]
                edge_key = frozenset({a, b})
                if edge_key in edge_index:
                    # sign by orientation
                    sign = 1 if (r == 0) else -1
                    matrix[ti, edge_index[edge_key]] = sign

        # Gaussian elimination over GF(2)
        return _gf2_rank(matrix)

    @staticmethod
    def _extract_loops(
        complex_: SimplicialComplex,
        num_loops: int,
    ) -> List[Loop]:
        """
        Extract up to `num_loops` representative cycles by searching
        for shortest cycles through BFS from each vertex.
        """
        if num_loops == 0:
            return []

        # Build adjacency
        adj: Dict[int, Set[int]] = {v: set() for v in complex_.vertices()}
        for edge in complex_.simplices.get(1, []):
            vlist = list(edge.vertices)
            adj[vlist[0]].add(vlist[1])
            adj[vlist[1]].add(vlist[0])

        loops: List[Loop] = []
        visited_cycles: Set[Tuple[int, ...]] = set()

        for start in sorted(complex_.vertices()):
            if len(loops) >= num_loops:
                break
            cycle = _shortest_cycle(adj, start)
            if cycle is None:
                continue
            key = tuple(sorted(cycle))
            if key in visited_cycles:
                continue
            visited_cycles.add(key)
            
            # Find the weights of the edges in the cycle
            cycle_edges = [
                frozenset({cycle[k], cycle[(k + 1) % len(cycle)]})
                for k in range(len(cycle))
            ]
            edge_weights = []
            for edge_key in cycle_edges:
                for edge in complex_.simplices.get(1, []):
                    if edge.vertices == edge_key:
                        edge_weights.append(edge.weight)
                        break
            
            weight = float(np.mean(edge_weights)) if edge_weights else 0.0
            loops.append(Loop(vertices=cycle, length=len(cycle), weight=weight))

        return loops


def _gf2_rank(matrix: np.ndarray) -> int:
    """Compute rank of a binary matrix over GF(2) via Gaussian elimination."""
    if matrix.size == 0:
        return 0
    m = matrix.copy().astype(np.int8) % 2
    rows, cols = m.shape
    rank = 0
    r = 0
    for c in range(cols):
        # find pivot
        pivot = None
        for i in range(r, rows):
            if m[i, c] == 1:
                pivot = i
                break
        if pivot is None:
            continue
        # swap rows
        m[[r, pivot]] = m[[pivot, r]]
        # eliminate
        for i in range(rows):
            if i != r and m[i, c] == 1:
                m[i] = (m[i] + m[r]) % 2
        r += 1
        rank += 1
        if r == rows:
            break
    return rank


def _shortest_cycle(adj: Dict[int, Set[int]], start: int) -> List[int] | None:
    """
    Find the shortest cycle containing `start` using BFS.

    Returns the cycle as a list of vertices, or None if no cycle exists.
    """
    if start not in adj:
        return None
    parent: Dict[int, int] = {start: -1}
    queue = [start]
    head = 0
    target_neighbor: Tuple[int, int] | None = None
    while head < len(queue) and target_neighbor is None:
        u = queue[head]
        head += 1
        for v in adj[u]:
            if v == start and len(parent) > 1:
                target_neighbor = (u, v)
                break
            if v not in parent:
                parent[v] = u
                queue.append(v)
    if target_neighbor is None:
        return None
    # Reconstruct path from u back to start
    u, _ = target_neighbor
    path: List[int] = []
    cur = u
    while cur != -1:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    path.append(start)
    return path
