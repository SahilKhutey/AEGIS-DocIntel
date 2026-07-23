"""
Topological Clusters (H₂ + Clustering)
======================================

Mathematical Definition:
-----------------------
H₂(X) counts 2-dimensional "voids" — enclosed cavities in 3D space
or, in document context, tightly coupled structural clusters.

For simplicial complexes in AMDI-OS, clusters are detected via:
    1. H₂ Betti number (2-dimensional homology).
    2. Spectral clustering on the graph Laplacian.
    3. Hierarchical clustering on persistent diagram.

Mathematical Foundation:
- Cluster cohesion: C = (internal edges) / (total possible internal edges)
- Cluster separation: S = (external edges) / (cluster size)

Cluster Quality Index:
    Q = α · C - β · S
    where α + β = 1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from .connected_components import ConnectedComponentsAnalyzer
from .exceptions import InsufficientDataError
from .simplex import Simplex, SimplicialComplex


@dataclass
class Cluster:
    """
    Represents a topological cluster.

    Attributes
    ----------
    id : int
        Cluster identifier.
    vertices : Set[int]
        Vertices in the cluster.
    cohesion : float
        Internal edge density (0 to 1).
    separation : float
        External edge ratio.
    quality : float
        Combined quality score.
    """

    id: int
    vertices: Set[int]
    cohesion: float = 0.0
    separation: float = 0.0
    quality: float = 0.0

    @property
    def size(self) -> int:
        return len(self.vertices)


@dataclass
class ClustersResult:
    """
    Result of topological clustering.

    Attributes
    ----------
    betti_2 : int
        Second Betti number (number of 2-dimensional voids).
    clusters : List[Cluster]
        Detected clusters.
    cluster_map : Dict[int, int]
        Mapping from vertex → cluster ID.
    silhouette : float
        Mean silhouette coefficient.
    """

    betti_2: int
    clusters: List[Cluster] = field(default_factory=list)
    cluster_map: Dict[int, int] = field(default_factory=dict)
    silhouette: float = 0.0

    @property
    def num_clusters(self) -> int:
        return len(self.clusters)

    @property
    def largest_cluster_size(self) -> int:
        if not self.clusters:
            return 0
        return max(c.size for c in self.clusters)

    @property
    def mean_cluster_size(self) -> float:
        if not self.clusters:
            return 0.0
        return float(sum(c.size for c in self.clusters)) / len(self.clusters)


class TopologicalClusters:
    """
    Detects topological clusters via:
        1. H₂ Betti number computation
        2. Spectral clustering on the graph Laplacian
        3. Quality scoring using cohesion and separation metrics
    """

    def __init__(self, alpha: float = 0.6, beta: float = 0.4) -> None:
        if alpha + beta <= 0:
            raise ValueError("alpha + beta must be positive.")
        self.alpha = alpha / (alpha + beta)
        self.beta = beta / (alpha + beta)

    def analyze(
        self,
        complex_: SimplicialComplex,
        n_clusters: Optional[int] = None,
    ) -> ClustersResult:
        """
        Perform topological cluster analysis.

        Parameters
        ----------
        complex_ : SimplicialComplex
            Input simplicial complex.
        n_clusters : Optional[int]
            Target number of clusters. If None, estimated via spectral gap.
        """
        if complex_.num_vertices < 2:
            raise InsufficientDataError("Need at least 2 vertices for clustering.")

        # Step 1: Build adjacency matrix
        vertices = sorted(complex_.vertices())
        idx = {v: i for i, v in enumerate(vertices)}
        n = len(vertices)
        A = np.zeros((n, n), dtype=np.float64)
        for edge in complex_.simplices.get(1, []):
            vlist = list(edge.vertices)
            i, j = idx[vlist[0]], idx[vlist[1]]
            A[i, j] = 1.0
            A[j, i] = 1.0

        # Step 2: Compute degree & Laplacian
        D = np.diag(A.sum(axis=1))
        L = D - A

        # Step 3: Spectral clustering
        if n_clusters is None:
            n_clusters = self._estimate_n_clusters(L)

        n_clusters = max(1, min(n_clusters, n))
        labels = self._spectral_cluster(A, L, n_clusters)

        # Step 4: Compute H₂ (number of independent 2-simplices)
        beta_2 = self._compute_betti_2(complex_)

        # Step 5: Build cluster objects with quality metrics
        clusters: List[Cluster] = []
        cluster_map: Dict[int, int] = {}
        for cid in range(n_clusters):
            members = {vertices[i] for i in range(n) if labels[i] == cid}
            if not members:
                continue
            cohesion, separation = self._compute_quality(A, labels, cid)
            quality = self.alpha * cohesion - self.beta * separation
            clusters.append(
                Cluster(
                    id=cid,
                    vertices=members,
                    cohesion=cohesion,
                    separation=separation,
                    quality=quality,
                )
            )
            for v in members:
                cluster_map[v] = cid

        # Step 6: silhouette
        sil = self._silhouette(A, labels)

        return ClustersResult(
            betti_2=beta_2,
            clusters=clusters,
            cluster_map=cluster_map,
            silhouette=sil,
        )

    @staticmethod
    def _estimate_n_clusters(L: np.ndarray) -> int:
        """Estimate number of clusters via eigengap heuristic."""
        n = L.shape[0]
        if n < 3:
            return 1
        eigvals = np.sort(np.linalg.eigvalsh(L))
        if len(eigvals) < 2:
            return 1
        # eigengap heuristic on normalized Laplacian
        gaps = np.diff(eigvals)
        # choose k = argmax gap, capped sensibly
        k = int(np.argmax(gaps[: min(10, len(gaps))])) + 1
        return max(1, min(k, max(1, n // 2)))

    @staticmethod
    def _spectral_cluster(A: np.ndarray, L: np.ndarray, k: int) -> np.ndarray:
        """Perform spectral clustering with k clusters."""
        from sklearn.cluster import KMeans

        n = A.shape[0]
        if k >= n:
            return np.arange(n)

        # Compute normalized Laplacian
        deg = A.sum(axis=1)
        d_inv_sqrt = np.zeros_like(deg)
        nonzero = deg > 0
        d_inv_sqrt[nonzero] = 1.0 / np.sqrt(deg[nonzero])
        D_inv_sqrt = np.diag(d_inv_sqrt)
        L_norm = D_inv_sqrt @ L @ D_inv_sqrt

        # Eigen decomposition
        try:
            eigvals, eigvecs = np.linalg.eigh(L_norm)
            embedding = eigvecs[:, :k]
        except np.linalg.LinAlgError:
            return np.zeros(n, dtype=int)

        # Normalize rows
        norms = np.linalg.norm(embedding, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embedding = embedding / norms

        # K-means on embedding
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(embedding)
        return labels

    @staticmethod
    def _compute_quality(
        A: np.ndarray, labels: np.ndarray, cluster_id: int
    ) -> Tuple[float, float]:
        """Compute cohesion and separation for a cluster."""
        members = labels == cluster_id
        n_members = int(members.sum())
        if n_members < 2:
            return 0.0, 0.0

        internal = A[members][:, members]
        cohesion = internal.sum() / (n_members * (n_members - 1))

        external = A[members][:, ~members]
        separation = external.sum() / (n_members * max(1, (~members).sum()))
        return float(cohesion), float(separation)

    @staticmethod
    def _compute_betti_2(complex_: SimplicialComplex) -> int:
        """Compute β₂: number of independent 2-simplices (filled triangles)."""
        triangles = complex_.simplices.get(2, [])
        if not triangles:
            return 0

        # Build ∂₂ matrix (triangles × edges)
        edges_list = complex_.simplices.get(1, [])
        edge_index = {e.vertices: i for i, e in enumerate(edges_list)}

        from .loops import _gf2_rank

        matrix = np.zeros((len(triangles), len(edges_list)), dtype=np.int8)
        for ti, tri in enumerate(triangles):
            vlist = list(tri.vertices)
            for r in range(3):
                a, b = vlist[r], vlist[(r + 1) % 3]
                edge_key = frozenset({a, b})
                if edge_key in edge_index:
                    sign = 1 if r == 0 else -1
                    matrix[ti, edge_index[edge_key]] = sign

        # β₂ = |triangles| - rank(∂₂)
        rank_d2 = _gf2_rank(matrix)
        return max(0, len(triangles) - rank_d2)

    @staticmethod
    def _silhouette(A: np.ndarray, labels: np.ndarray) -> float:
        """Compute mean silhouette coefficient."""
        from sklearn.metrics import silhouette_score

        n = len(labels)
        if len(set(labels)) < 2 or n < 3:
            return 0.0
        # convert adjacency to distance
        dist = 1.0 - A
        np.fill_diagonal(dist, 0.0)
        try:
            return float(silhouette_score(dist, labels, metric="precomputed"))
        except Exception:
            return 0.0
