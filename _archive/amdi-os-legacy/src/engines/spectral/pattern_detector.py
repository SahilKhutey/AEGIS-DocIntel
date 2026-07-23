"""
Pattern Detection via Spectral Analysis
=======================================

Detects repetitive structural patterns in document graphs using
eigenvector analysis of the Laplacian.

Mathematical Foundation:
- Periodic patterns → dominant frequencies in spectrum
- Repeated motifs → localized eigenvector components
- Fiedler vector → bi-partition / cluster boundaries
- Spectral concentration → identify which vertices belong to a pattern

Patterns detected:
1. Bipartition patterns (Fiedler vector sign)
2. Cluster patterns (top-k eigenvectors)
3. Repeating motifs (eigenvector correlations)
4. Hub patterns (eigenvector centrality)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .adjacency import AdjacencyMatrix
from .eigen import EigenResult, EigenSolver
from .exceptions import InvalidGraphError
from .laplacian import LaplacianBuilder, LaplacianType


@dataclass
class Pattern:
    """
    A detected repetitive pattern.

    Attributes
    ----------
    id : int
        Pattern identifier.
    pattern_type : str
        'bipartition', 'cluster', 'motif', 'hub'.
    members : List[int]
        Vertex IDs participating in the pattern.
    strength : float
        Pattern strength (eigenvalue / magnitude).
    metadata : Dict
        Additional info.
    """

    id: int
    pattern_type: str
    members: List[int]
    strength: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class PatternResult:
    """
    Result of pattern detection.

    Attributes
    ----------
    patterns : List[Pattern]
    bipartition : Tuple[List[int], List[int]]
        Two sides of the Fiedler bipartition.
    hubs : List[int]
        Vertices with high eigenvector centrality.
    motif_correlations : np.ndarray
        Pairwise eigenvector correlations.
    pattern_count_by_type : Dict[str, int]
    """

    patterns: List[Pattern]
    bipartition: Tuple[List[int], List[int]]
    hubs: List[int]
    motif_correlations: np.ndarray
    pattern_count_by_type: Dict[str, int] = field(default_factory=dict)

    @property
    def num_patterns(self) -> int:
        return len(self.patterns)


class PatternDetector:
    """
    Detects repetitive patterns in graph structure via spectral analysis.
    """

    def __init__(
        self,
        hub_percentile: float = 90.0,
        correlation_threshold: float = 0.85,
        top_k_eigenvectors: int = 5,
    ) -> None:
        self.hub_percentile = hub_percentile
        self.correlation_threshold = correlation_threshold
        self.top_k_eigenvectors = top_k_eigenvectors

    def detect(
        self,
        adjacency: AdjacencyMatrix,
        eigen_result: Optional[EigenResult] = None,
    ) -> PatternResult:
        """
        Detect patterns in the graph.

        Parameters
        ----------
        adjacency : AdjacencyMatrix
        eigen_result : Optional[EigenResult]
            Pre-computed eigen-decomposition. If None, will compute.
        """
        n = adjacency.size
        if n < 3:
            raise InvalidGraphError("Need at least 3 vertices for pattern detection.")

        if eigen_result is None:
            laplacian = LaplacianBuilder.build(adjacency, LaplacianType.SYMMETRIC_NORMALIZED)
            eigen_result = EigenSolver().solve(laplacian, k=min(self.top_k_eigenvectors + 1, n))

        # 1. Bipartition from Fiedler vector
        bipartition = self._detect_bipartition(eigen_result)

        # 2. Cluster patterns from top eigenvectors
        cluster_patterns = self._detect_cluster_patterns(eigen_result)

        # 3. Hubs from eigenvector centrality
        hubs, centrality = self._detect_hubs(adjacency, eigen_result)

        # 4. Motif correlations
        motif_corr = self._compute_motif_correlations(eigen_result)

        # 5. Combine patterns
        all_patterns: List[Pattern] = []
        all_patterns.append(
            Pattern(
                id=0,
                pattern_type="bipartition",
                members=bipartition[0] + bipartition[1],
                strength=float(abs(eigen_result.fiedler_value)),
                metadata={"side_a": bipartition[0], "side_b": bipartition[1]},
            )
        )
        all_patterns.extend(cluster_patterns)
        all_patterns.extend(
            [
                Pattern(
                    id=1000 + h,
                    pattern_type="hub",
                    members=[h],
                    strength=float(centrality[h]),
                    metadata={"centrality": float(centrality[h])},
                )
                for h in hubs
            ]
        )

        # Count by type
        counts: Dict[str, int] = {}
        for p in all_patterns:
            counts[p.pattern_type] = counts.get(p.pattern_type, 0) + 1

        return PatternResult(
            patterns=all_patterns,
            bipartition=bipartition,
            hubs=hubs,
            motif_correlations=motif_corr,
            pattern_count_by_type=counts,
        )

    @staticmethod
    def _detect_bipartition(eigen_result: EigenResult) -> Tuple[List[int], List[int]]:
        """Partition vertices using sign of Fiedler vector."""
        if eigen_result.fiedler_vector is None:
            return ([], [])
        fv = eigen_result.fiedler_vector
        side_a = [int(i) for i in range(len(fv)) if fv[i] >= 0]
        side_b = [int(i) for i in range(len(fv)) if fv[i] < 0]
        return side_a, side_b

    def _detect_cluster_patterns(self, eigen_result: EigenResult) -> List[Pattern]:
        """Identify clusters from top-k eigenvectors."""
        patterns: List[Pattern] = []
        k = min(self.top_k_eigenvectors, eigen_result.eigenvectors.shape[1] - 1)
        for i in range(1, k + 1):
            v = eigen_result.eigenvectors[:, i]
            threshold = np.std(v)
            if threshold < 1e-10:
                continue
            # top contributors
            top_idx = np.argsort(np.abs(v))[::-1][: max(1, len(v) // 5)]
            patterns.append(
                Pattern(
                    id=i,
                    pattern_type="cluster",
                    members=[int(x) for x in top_idx.tolist()],
                    strength=float(eigen_result.eigenvalues[i]),
                    metadata={"eigenvector_index": i, "eigenvalue": float(eigen_result.eigenvalues[i])},
                )
            )
        return patterns

    def _detect_hubs(
        self,
        adjacency: AdjacencyMatrix,
        eigen_result: EigenResult,
    ) -> Tuple[List[int], np.ndarray]:
        """Find hub vertices via eigenvector centrality (PageRank proxy)."""
        A = adjacency.matrix
        # use top eigenvector of A as centrality
        try:
            eigvals_A, eigvecs_A = np.linalg.eig(A)
            # largest real eigenvalue
            real_mask = np.abs(eigvals_A.imag) < 1e-10
            real_eigvals = eigvals_A[real_mask].real
            real_eigvecs = eigvecs_A[:, real_mask].real
            idx = int(np.argmax(real_eigvals))
            centrality = np.abs(real_eigvecs[:, idx])
        except Exception:
            centrality = adjacency.degree_vector()

        threshold = np.percentile(centrality, self.hub_percentile)
        hubs = [int(i) for i, c in enumerate(centrality) if c >= threshold]
        return hubs, centrality

    def _compute_motif_correlations(self, eigen_result: EigenResult) -> np.ndarray:
        """Pairwise correlations between eigenvectors → motif similarity."""
        k = min(self.top_k_eigenvectors, eigen_result.eigenvectors.shape[1])
        if k < 2:
            return np.array([[1.0]])
        E = eigen_result.eigenvectors[:, 1 : k + 1]
        # row-wise: vertices, col-wise: eigenvectors
        # compute correlation between eigenvector pairs
        corr = np.corrcoef(E.T)
        return corr
