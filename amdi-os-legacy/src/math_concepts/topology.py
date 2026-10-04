'''
AEGIS-MIOS — Topology & Persistent Homology
==============================================
- Betti numbers: β_0, β_1, β_2
- Persistent homology diagrams
- Manifold representations
- Simplicial complexes
'''

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from scipy.spatial import Delaunay


@dataclass
class Simplex:
    '''n-simplex: e.g., 2-simplex is a triangle.'''
    vertices: tuple
    dimension: int = 0

    def __post_init__(self):
        self.dimension = len(self.vertices) - 1

    def __hash__(self):
        return hash(self.vertices)

    def __eq__(self, other):
        return self.vertices == other.vertices


@dataclass
class PersistencePoint:
    '''Birth-death pair for topological feature.'''
    birth: float
    death: float
    dimension: int
    representative: tuple = field(default_factory=tuple)

    @property
    def persistence(self) -> float:
        return self.death - self.birth

    @property
    def is_infinite(self) -> bool:
        return self.death == float('inf')


class SimplicialComplex:
    '''Abstract simplicial complex.'''

    def __init__(self):
        self.simplices: set[Simplex] = set()

    def add_simplex(self, vertices: tuple) -> None:
        '''Add simplex and all its faces (closure).'''
        n = len(vertices)
        for k in range(1, n + 1):
            for face in combinations(vertices, k):
                self.simplices.add(Simplex(face))

    def add_many(self, simplex_list: list[tuple]) -> None:
        for s in simplex_list:
            self.add_simplex(s)

    def betti_numbers(self) -> tuple[int, int, int]:
        '''
        Compute Betti numbers via Euler characteristic:
        χ = Σ (-1)^k × (number of k-simplices)
        β_0 - β_1 + β_2 = χ

        Also: β_0 = number of connected components
        '''
        counts = defaultdict(int)
        for s in self.simplices:
            counts[s.dimension] += 1
        chi = sum((-1) ** k * counts[k] for k in counts)
        # β_0 = connected components (requires union-find)
        beta_0 = self._count_components()
        # β_2 ≈ voids (count 2-simplices - edges + vertices)
        beta_2 = counts.get(2, 0) - counts.get(1, 0) + counts.get(0, 0) - beta_0
        beta_2 = max(0, beta_2)
        # χ = β_0 - β_1 + β_2 → β_1 = β_0 + β_2 - χ
        beta_1 = max(0, beta_0 + beta_2 - chi)
        return beta_0, beta_1, beta_2

    def _count_components(self) -> int:
        '''Count connected components via union-find on 1-skeleton.'''
        vertices = set()
        edges = []
        for s in self.simplices:
            if s.dimension == 0:
                vertices.add(s.vertices[0])
            elif s.dimension == 1:
                edges.append(s.vertices)
                vertices.update(s.vertices)
        # Union-find
        parent = {v: v for v in vertices}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        return len(set(find(v) for v in vertices))


class VietorisRipsComplex:
    '''
    Vietoris-Rips complex: simplicial complex from distance matrix.

    Used for persistent homology of point clouds (document positions).
    '''

    def __init__(self, points: np.ndarray, max_edge_length: float):
        self.points = points
        self.max_edge_length = max_edge_length
        self._distance_matrix = self._compute_distances()

    def _compute_distances(self) -> np.ndarray:
        n = len(self.points)
        D = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(self.points[i] - self.points[j])
                D[i, j] = d
                D[j, i] = d
        return D

    def build_complex(self, threshold: float) -> SimplicialComplex:
        '''Build Vietoris-Rips complex at given threshold.'''
        K = SimplicialComplex()
        n = len(self.points)
        # Add 0-simplices
        for i in range(n):
            K.add_simplex((i,))
        # Add k-simplices where all pairwise distances < threshold
        for k in range(2, n + 1):
            for combo in combinations(range(n), k):
                if all(self._distance_matrix[i, j] < threshold for i, j in combinations(combo, 2)):
                    K.add_simplex(combo)
        return K


class PersistentHomology:
    '''
    Compute persistent homology of a point cloud.

    Returns persistence diagram with birth-death pairs.
    '''

    def __init__(self, max_dimension: int = 2):
        self.max_dim = max_dimension

    def compute(
        self,
        points: np.ndarray,
        thresholds: np.ndarray | None = None,
    ) -> list[PersistencePoint]:
        '''
        Compute persistent homology across a range of scales.

        For each threshold ε:
        - Build Vietoris-Rips complex
        - Compute Betti numbers
        - Track births and deaths of features
        '''
        if thresholds is None:
            thresholds = np.linspace(0.01, 2.0, 30)

        # Track features across scales
        active_h0 = set(range(len(points)))  # All start as separate components
        h0_births = {i: 0.0 for i in range(len(points))}
        h1_births: dict[int, float] = {}

        diagram: list[PersistencePoint] = []
        prev_betti = (len(points), 0, 0)

        for eps in thresholds:
            K = VietorisRipsComplex(points, max_edge_length=eps).build_complex(eps)
            betti = K.betti_numbers()

            # H_0 deaths (when components merge)
            if betti[0] < prev_betti[0]:
                deaths = prev_betti[0] - betti[0]
                # Pick the most recently born components to kill
                sorted_by_age = sorted(active_h0, key=lambda x: h0_births.get(x, 0), reverse=True)
                for _ in range(deaths):
                    if sorted_by_age:
                        victim = sorted_by_age.pop(0)
                        active_h0.discard(victim)
                        diagram.append(PersistencePoint(
                            birth=h0_births[victim],
                            death=eps,
                            dimension=0,
                            representative=(victim,),
                        ))

            # H_1 births (new loops)
            if betti[1] > prev_betti[1]:
                for new_id in range(betti[1] - prev_betti[1]):
                    h1_births[new_id] = eps

            # H_1 deaths (loops filled in)
            if betti[1] < prev_betti[1] and h1_births:
                deaths = prev_betti[1] - betti[1]
                sorted_by_age = sorted(h1_births.items(), key=lambda x: x[1], reverse=True)
                for _ in range(deaths):
                    if sorted_by_age:
                        kid, birth = sorted_by_age.pop(0)
                        diagram.append(PersistencePoint(
                            birth=birth, death=eps, dimension=1,
                        ))
                        del h1_births[kid]

            prev_betti = betti

        # Persistent (infinite) features
        for vid in active_h0:
            diagram.append(PersistencePoint(
                birth=h0_births[vid], death=float('inf'), dimension=0,
                representative=(vid,),
            ))

        return diagram

    def persistence_summary(self, diagram: list[PersistencePoint]) -> dict:
        '''Summarize persistence diagram.'''
        h0 = [p for p in diagram if p.dimension == 0]
        h1 = [p for p in diagram if p.dimension == 1]
        h2 = [p for p in diagram if p.dimension == 2]
        return {
            'n_features': len(diagram),
            'n_h0': len(h0),
            'n_h1': len(h1),
            'n_h2': len(h2),
            'max_persistence_h1': max((p.persistence for p in h1), default=0),
            'total_persistence_h0': sum(p.persistence for p in h0 if not p.is_infinite),
        }


# ============================================================
# GEOMETRIC COMPLEXES FROM DELAUNAY TRIANGULATION
# ============================================================

def delaunay_triangulation(points: np.ndarray) -> SimplicialComplex:
    '''
    Build Delaunay triangulation as a simplicial complex.

    Used for: 2D manifold analysis, surface reconstruction.
    '''
    if len(points) < 3:
        return SimplicialComplex()
    K = SimplicialComplex()
    tri = Delaunay(points)
    for simplex in tri.simplices:
        K.add_simplex(tuple(simplex))
    return K


def manifold_dimension(points: np.ndarray, threshold: float = 0.95) -> int:
    '''
    Estimate intrinsic manifold dimension using PCA eigenvalue ratio.

    Returns 1 (line), 2 (plane), 3 (volume), etc.
    '''
    if len(points) < 3:
        return 1
    centered = points - points.mean(axis=0)
    cov = np.cov(centered.T)
    eigvals = np.linalg.eigvalsh(cov)[::-1]
    eigvals = np.maximum(eigvals, 1e-10)
    total = eigvals.sum()
    cumsum = np.cumsum(eigvals) / total
    return int(np.searchsorted(cumsum, threshold) + 1)
