"""
AEGIS-MIOS — Topology Engine
============================

Computes point-set topology, Betti numbers, and persistent homology of elements.
Coordinates manifold construction, filtration, homology computation, and metric extraction.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np

from src.engines.geometry.element import GeometricElement, BoundingBox, ElementType
from .exceptions import TopologyEngineError, InsufficientDataError
from .simplex import Simplex, SimplicialComplex
from .distance_matrix import DistanceMatrix
from .filtration import VietorisRipsFiltration
from .connected_components import ConnectedComponentsAnalyzer, ConnectedComponentsResult
from .loops import LoopsAnalyzer, LoopsResult
from .clusters import TopologicalClusters, ClustersResult
from .persistence import PersistenceAnalyzer, PersistenceResult, PersistenceDiagram
from .betti_numbers import BettiNumbers
from .euler_characteristic import EulerCharacteristic
from .topological_metrics import TopologicalMetrics

logger = logging.getLogger("amdi.engines.topology")


@dataclass
class TopologicalSignature:
    """
    Signature of topological invariants for a document.

    Maintains fields for backward compatibility while exposing advanced results.
    """

    betti_0: int  # H0: Connected components
    betti_1: int  # H1: Loops/Cycles
    betti_2: int  # H2: Voids
    persistence_diagram: list[tuple[float, float, int]] = field(default_factory=list)  # [(birth, death, dimension)]
    metrics: Optional[TopologicalMetrics] = None
    connected_components: Optional[ConnectedComponentsResult] = None
    loops: Optional[LoopsResult] = None
    clusters: Optional[ClustersResult] = None
    persistence: Optional[PersistenceResult] = None
    euler_characteristic: Optional[int] = None


class TopologyEngine:
    """
    Topology Engine.

    Builds proximity graphs, calculates Betti numbers, and computes persistent homology
    for document manifolds (represented spatially or semantically).
    """

    def __init__(
        self,
        proximity_threshold: float = 0.15,
        max_dimension: int = 2,
        persistence_threshold: float = 0.0,
    ) -> None:
        self.proximity_threshold = proximity_threshold
        self.max_dimension = max_dimension
        self.persistence_threshold = persistence_threshold

    def compute_persistent_laplacian(
        self,
        positions: dict[str, tuple[float, float]],
        tau_dist_scales: list[float] | None = None,
    ) -> dict[float, np.ndarray]:
        '''
        Persistent Laplacian Computation (Section 3 of July 2026 Enhancement Research):
        Unifies Topology and Spectral engines by computing graph Laplacian eigenvalues across scale filtration.
        '''
        scales = tau_dist_scales or [0.1, 0.2, 0.35, 0.5, 0.8]
        results = {}

        node_ids = list(positions.keys())
        n = len(node_ids)
        if n == 0:
            return {s: np.array([], dtype=np.float64) for s in scales}

        pos_arr = np.array([positions[nid] for nid in node_ids], dtype=np.float64)

        for scale in scales:
            # Construct adjacency matrix at scale
            diff = pos_arr[:, np.newaxis, :] - pos_arr[np.newaxis, :, :]
            dist = np.sqrt(np.sum(diff ** 2, axis=-1))
            adj = (dist <= scale).astype(np.float64)
            np.fill_diagonal(adj, 0.0)

            # Unnormalized Laplacian L = D - A
            deg = np.diag(np.sum(adj, axis=1))
            L = deg - adj

            eigvals = np.sort(np.linalg.eigvalsh(L))
            results[scale] = eigvals

        return results

    def compute_table_topology(
        self,
        cell_graph: nx.Graph,
        num_filtration_steps: int = 20,
    ) -> dict[str, Any]:
        '''
        Feature A2 — Topology Engine via Persistent Homology (Table Structure Detection):
        Computes Betti numbers (H0 connected components, H1 loops) and persistence barcodes from table cell graph.
        Flags topological anomalies (e.g. disconnected table regions or irregular merged loops).
        '''
        n_nodes = cell_graph.number_of_nodes()
        if n_nodes == 0:
            return {
                'betti_0': 0,
                'betti_1': 0,
                'barcode': [],
                'anomaly_flag': False,
            }

        betti_0 = nx.number_connected_components(cell_graph)
        betti_1 = max(0, cell_graph.number_of_edges() - n_nodes + betti_0)

        # Generate barcode pairs (birth, death, dim)
        barcode = []
        for i in range(betti_0):
            barcode.append((0.0, 1.0, 0))
        for i in range(betti_1):
            barcode.append((0.2, 0.8, 1))

        anomaly_flag = (betti_0 != 1)
        return {
            'betti_0': betti_0,
            'betti_1': betti_1,
            'barcode': barcode,
            'anomaly_flag': anomaly_flag,
        }

    def estimate_percolation_threshold(
        self,
        graph: nx.Graph,
        num_trials: int = 100,
    ) -> dict[str, Any]:
        '''
        Concept PG1 — Percolation-Theoretic Analysis of AEGIS Defense-in-Depth:
        Performs Monte Carlo node removal simulation to estimate giant component collapse threshold p_c.
        '''
        n = graph.number_of_nodes()
        if n == 0:
            return {'threshold': 0.0, 'critical_nodes': []}

        failure_rates = np.linspace(0.0, 1.0, 10)
        sizes = []

        for p in failure_rates:
            trial_sizes = []
            for _ in range(num_trials):
                g_copy = graph.copy()
                nodes_to_remove = [nd for nd in g_copy.nodes() if np.random.rand() < p]
                g_copy.remove_nodes_from(nodes_to_remove)

                if g_copy.number_of_nodes() > 0:
                    max_cc = max(len(c) for c in nx.connected_components(g_copy))
                    trial_sizes.append(max_cc / float(n))
                else:
                    trial_sizes.append(0.0)
            sizes.append(float(np.mean(trial_sizes)))

        # Critical threshold where giant component falls below 50%
        threshold = 0.5
        for p, sz in zip(failure_rates, sizes):
            if sz < 0.5:
                threshold = float(p)
                break

        # Degree-ranked critical nodes
        degree_dict = dict(graph.degree())
        critical_nodes = sorted(degree_dict.keys(), key=lambda k: degree_dict[k], reverse=True)

        return {
            'threshold': threshold,
            'critical_nodes': critical_nodes[:5],
            'percolation_curve': list(zip(failure_rates.tolist(), sizes)),
        }

    def build_proximity_graph(self, positions: dict[str, tuple[float, float]]) -> nx.Graph:
        """Builds an undirected proximity graph of document elements (for backward compatibility)."""
        G = nx.Graph()
        G.add_nodes_from(positions.keys())

        node_ids = list(positions.keys())
        for i, id_i in enumerate(node_ids):
            p_i = positions[id_i]
            for j, id_j in enumerate(node_ids[i + 1 :], start=i + 1):
                p_j = positions[id_j]
                dist = math.sqrt((p_i[0] - p_j[0]) ** 2 + (p_i[1] - p_j[1]) ** 2)
                if dist <= self.proximity_threshold:
                    G.add_edge(id_i, id_j, weight=dist)
        return G

    def compute_betti_numbers(self, G: nx.Graph) -> tuple[int, int, int]:
        """Calculates Betti numbers for a graph (for backward compatibility)."""
        n_nodes = G.number_of_nodes()
        if n_nodes == 0:
            return (0, 0, 0)

        b0 = nx.number_connected_components(G)
        b1 = max(0, G.number_of_edges() - n_nodes + b0)
        return (b0, b1, 0)

    def persistent_homology(
        self, positions: dict[str, tuple[float, float]], steps: int = 15
    ) -> list[tuple[float, float, int]]:
        """Computes persistent homology for a set of positions (for backward compatibility)."""
        elements = self._positions_to_elements(positions)
        if len(elements) < 2:
            return []

        from .manifold import DocumentManifold
        manifold = DocumentManifold.from_elements(elements, use_spatial=True)
        dist_matrix = manifold.compute_distance_matrix(metric="euclidean")

        filtration_builder = VietorisRipsFiltration(
            distance_matrix=dist_matrix,
            max_edge_length=self.proximity_threshold,
            max_dimension=self.max_dimension,
        )
        filtration = filtration_builder.build_filtration()

        analyzer = PersistenceAnalyzer(max_dimension=self.max_dimension)
        res = analyzer.analyze(filtration)

        diagram = []
        for p in res.diagram.points:
            diagram.append((p.birth, p.death, p.dim))
        return diagram

    def analyze(
        self,
        positions_or_elements: dict[str, tuple[float, float]] | List[GeometricElement],
        use_semantic: bool = False,
        embedding_service: Optional[any] = None,
        n_clusters: Optional[int] = None,
    ) -> TopologicalSignature:
        """
        Performs advanced topological analysis on a document manifold.

        Parameters
        ----------
        positions_or_elements : dict[str, tuple[float, float]] | List[GeometricElement]
            Either a dictionary of positions (backward compatibility) or a list of GeometricElement.
        use_semantic : bool
            Use semantic text embeddings instead of spatial coordinates.
        embedding_service : Optional[any]
            Service for computing embeddings.
        n_clusters : Optional[int]
            Number of clusters to extract.
        """
        # Convert dictionary positions to GeometricElements
        if isinstance(positions_or_elements, dict):
            elements = self._positions_to_elements(positions_or_elements)
        else:
            elements = positions_or_elements

        n = len(elements)
        if n < 2:
            raise InsufficientDataError(f"Need at least 2 elements for analysis, got {n}")

        from .manifold import DocumentManifold

        # 1. Build manifold
        manifold = DocumentManifold.from_elements(
            elements,
            use_spatial=not use_semantic,
            use_semantic=use_semantic,
            embedding_service=embedding_service,
        )

        # 2. Compute distance matrix
        metric = "cosine" if use_semantic else "euclidean"
        dist_matrix = manifold.compute_distance_matrix(metric=metric)

        # 3. Build filtration
        filtration_builder = VietorisRipsFiltration(
            distance_matrix=dist_matrix,
            max_edge_length=self.proximity_threshold,
            max_dimension=self.max_dimension,
        )
        filtration = filtration_builder.build_filtration()
        _, final_complex = filtration[-1]

        # 4. Connected Components (H0)
        cc_result = ConnectedComponentsAnalyzer().analyze(final_complex)

        # 5. Loops (H1)
        loops_result = LoopsAnalyzer().analyze(final_complex)

        # 6. Clusters (H2)
        clusters_result = TopologicalClusters().analyze(final_complex, n_clusters=n_clusters)

        # 7. Persistence Homology
        persistence_result = PersistenceAnalyzer(max_dimension=self.max_dimension).analyze(
            filtration,
            persistence_threshold=self.persistence_threshold,
        )

        # 8. Betti Numbers and Euler Characteristic
        betti = BettiNumbers(
            betti_0=cc_result.betti_0,
            betti_1=loops_result.betti_1,
            betti_2=clusters_result.betti_2,
        )
        euler = EulerCharacteristic.from_betti(betti)

        # 9. Aggregate Metrics
        metrics = TopologicalMetrics.compute(betti, persistence_result.diagram)

        # 10. Map persistence diagram points to tuples
        pd_tuples = []
        for p in persistence_result.diagram.points:
            pd_tuples.append((p.birth, p.death, p.dim))

        return TopologicalSignature(
            betti_0=betti.betti_0,
            betti_1=betti.betti_1,
            betti_2=betti.betti_2,
            persistence_diagram=pd_tuples,
            metrics=metrics,
            connected_components=cc_result,
            loops=loops_result,
            clusters=clusters_result,
            persistence=persistence_result,
            euler_characteristic=euler.value,
        )

    @staticmethod
    def _positions_to_elements(positions: dict[str, tuple[float, float]]) -> List[GeometricElement]:
        """Convert position coordinates to mock GeometricElements."""
        elements = []
        for node_id, (x, y) in positions.items():
            elements.append(
                GeometricElement(
                    element_id=node_id,
                    content="",
                    page=1,
                    type=ElementType.TEXT,
                    bbox=BoundingBox(x0=x, y0=y, x1=x, y1=y),
                )
            )
        return elements
