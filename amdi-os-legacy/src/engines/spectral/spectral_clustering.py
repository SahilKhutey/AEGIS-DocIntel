"""
Spectral Clustering (Ng-Jordan-Weiss Algorithm)
==============================================

Algorithm (Shi & Malik, Ng et al., Jordan & Weiss):

    1. Build similarity graph → adjacency A
    2. Compute normalized Laplacian L_sym
    3. Compute k smallest eigenvectors → embedding U ∈ R^{n×k}
    4. Normalize rows of U: Y_ij = U_ij / (Σ_j U_ij²)^(1/2)
    5. Cluster rows of Y using K-means → labels

In AMDI-OS, this discovers document section clusters based on
structural similarity rather than content alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans

from .adjacency import AdjacencyMatrix
from .eigen import EigenSolver
from .exceptions import ConvergenceError, InvalidGraphError
from .laplacian import LaplacianBuilder, LaplacianMatrix, LaplacianType


@dataclass
class Cluster:
    """A spectral cluster."""

    id: int
    members: List[int]
    centroid: Optional[np.ndarray] = None
    cohesion: float = 0.0


@dataclass
class SpectralClusterResult:
    """
    Result of spectral clustering.

    Attributes
    ----------
    labels : np.ndarray
        Cluster label for each vertex.
    n_clusters : int
        Number of clusters.
    clusters : List[Cluster]
        Cluster objects.
    embedding : np.ndarray
        The spectral embedding (n, k).
    cluster_map : Dict[int, int]
        Vertex → cluster label.
    inertia : float
        K-means inertia (intra-cluster sum of squares).
    silhouette : float
        Silhouette score in embedding space.
    """

    labels: np.ndarray
    n_clusters: int
    clusters: List[Cluster]
    embedding: np.ndarray
    cluster_map: Dict[int, int] = field(default_factory=dict)
    inertia: float = 0.0
    silhouette: float = 0.0

    @property
    def num_clusters(self) -> int:
        return self.n_clusters

    @property
    def largest_cluster_size(self) -> int:
        if not self.clusters:
            return 0
        return max(len(c.members) for c in self.clusters)

    @property
    def mean_cluster_size(self) -> float:
        if not self.clusters:
            return 0.0
        return float(np.mean([len(c.members) for c in self.clusters]))


class SpectralClusterer:
    """
    Ng-Jordan-Weiss spectral clustering implementation.
    """

    def __init__(
        self,
        n_clusters: Optional[int] = None,
        laplacian_type: LaplacianType = LaplacianType.SYMMETRIC_NORMALIZED,
        normalize_embedding: bool = True,
        random_state: int = 42,
    ) -> None:
        self.n_clusters = n_clusters
        self.laplacian_type = laplacian_type
        self.normalize_embedding = normalize_embedding
        self.random_state = random_state

    def cluster(
        self,
        adjacency: AdjacencyMatrix,
        n_clusters: Optional[int] = None,
    ) -> SpectralClusterResult:
        """
        Perform spectral clustering.

        Parameters
        ----------
        adjacency : AdjacencyMatrix
            Input adjacency matrix.
        n_clusters : Optional[int]
            Override the number of clusters.
        """
        n = adjacency.size
        if n < 2:
            raise InvalidGraphError("Need at least 2 vertices.")

        k = n_clusters or self.n_clusters

        # Step 1: Build Laplacian
        laplacian = LaplacianBuilder.build(adjacency, self.laplacian_type)

        # Step 2: Estimate k via eigengap if not specified
        if k is None or k <= 0:
            k = self._estimate_k(laplacian, max_k=min(20, n - 1))

        # need k+1 eigenvectors (include the trivial one)
        k_eigs = min(k + 1, n)
        eig_result = EigenSolver().solve(laplacian, k=k_eigs)

        # Step 3: Build embedding (skip first trivial eigenvector)
        embedding = eig_result.eigenvectors[:, 1:k_eigs]

        # Step 4: Row-normalize the embedding
        if self.normalize_embedding:
            norms = np.linalg.norm(embedding, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embedding = embedding / norms

        # Step 5: K-means on the embedding
        if k >= n:
            labels = np.arange(n)
            km = None
        else:
            km = KMeans(
                n_clusters=k,
                n_init=10,
                random_state=self.random_state,
            )
            try:
                labels = km.fit_predict(embedding)
            except Exception as exc:
                raise ConvergenceError(f"K-means failed: {exc}") from exc

        # Step 6: Build cluster objects
        clusters: List[Cluster] = []
        cluster_map: Dict[int, int] = {}
        unique_labels = sorted(set(labels.tolist()))
        for cid in unique_labels:
            members = [int(i) for i in range(n) if labels[i] == cid]
            cluster_map.update({m: cid for m in members})
            centroid = embedding[members].mean(axis=0) if members else None
            # cohesion = mean intra-cluster similarity in embedding
            if len(members) > 1:
                from scipy.spatial.distance import pdist
                dists = pdist(embedding[members])
                cohesion = float(1.0 - dists.mean()) if len(dists) > 0 else 0.0
            else:
                cohesion = 0.0
            clusters.append(
                Cluster(
                    id=cid,
                    members=members,
                    centroid=centroid,
                    cohesion=cohesion,
                )
            )

        # Step 7: Quality metrics
        inertia = float(km.inertia_) if km is not None else 0.0
        silhouette = self._silhouette(embedding, labels)

        return SpectralClusterResult(
            labels=labels,
            n_clusters=len(unique_labels),
            clusters=clusters,
            embedding=embedding,
            cluster_map=cluster_map,
            inertia=inertia,
            silhouette=silhouette,
        )

    @staticmethod
    def _estimate_k(laplacian: LaplacianMatrix, max_k: int = 10) -> int:
        """Eigengap heuristic for choosing k."""
        eig_result = EigenSolver().solve(laplacian, k=min(max_k + 1, laplacian.size))
        # eigengap after zero eigenvalues
        nonzero_eigs = eig_result.eigenvalues[eig_result.num_zero_eigenvalues:]
        if len(nonzero_eigs) < 2:
            return 1
        gaps = np.diff(nonzero_eigs)
        return int(np.argmax(gaps)) + 1

    @staticmethod
    def _silhouette(embedding: np.ndarray, labels: np.ndarray) -> float:
        """Mean silhouette coefficient."""
        from sklearn.metrics import silhouette_score

        n = len(labels)
        if len(set(labels.tolist())) < 2 or n < 3:
            return 0.0
        try:
            return float(silhouette_score(embedding, labels))
        except Exception:
            return 0.0
