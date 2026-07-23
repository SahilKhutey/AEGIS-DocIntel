"""
AEGIS-MIOS — Graph Engine
============================
G = (V, E) — Heterogeneous document graph.

Operations:
- Node Builder: Create nodes from elements
- Edge Builder: Create typed edges (FOLLOWS, NEXT_PAGE, REFERENCES, etc.)
- Centrality: Degree, Betweenness, Closeness, Eigenvector
- PageRank: Power iteration algorithm
- Relationship Mapping: Discover implicit relationships

Theorems:
- β_0 = number of connected components
- χ(G) = V - E (for connected graph)
- PageRank: π = (1-d)/N · 1 + d · M^T π
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

import networkx as nx
import numpy as np

from src.engines.geometry.element import GeometricElement, ElementType

logger = logging.getLogger(__name__)


# ============================================================
# EDGE TYPES
# ============================================================

class EdgeType(str, Enum):
    """Types of edges in the document graph."""
    # Reading order
    FOLLOWS = "follows"
    PRECEDES = "precedes"

    # Spatial
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"

    # Cross-page
    NEXT_PAGE = "next_page"
    PREVIOUS_PAGE = "previous_page"
    SAME_SECTION = "same_section"

    # Semantic
    REFERENCES = "references"
    REFERENCED_BY = "referenced_by"
    SIMILAR_TO = "similar_to"
    MENTIONED_WITH = "mentioned_with"

    # Structural
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    TABLE_OF = "table_of"
    FIGURE_OF = "figure_of"
    CAPTION_OF = "caption_of"

    # Logical
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    EXPLAINS = "explains"
    EXAMPLE_OF = "example_of"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class GraphNode:
    """A node in the document graph."""
    node_id: str
    node_type: str  # 'element', 'page', 'section', 'entity', 'table', 'figure'
    label: str = ""
    page: int = 0
    section: str | None = None
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge in the document graph."""
    edge_id: str
    src_id: str
    dst_id: str
    edge_type: EdgeType
    weight: float = 1.0
    bidirectional: bool = False
    properties: dict = field(default_factory=dict)


@dataclass
class GraphMetrics:
    """Computed graph metrics."""
    n_nodes: int = 0
    n_edges: int = 0
    density: float = 0.0
    n_components: int = 0
    avg_degree: float = 0.0
    max_degree: int = 0
    clustering_coefficient: float = 0.0
    diameter: int = 0
    is_connected: bool = False

    @property
    def is_dense(self) -> bool:
        return self.density > 0.5


@dataclass
class CentralityScores:
    """Centrality metrics for a single node."""
    node_id: str
    degree: float = 0.0
    betweenness: float = 0.0
    closeness: float = 0.0
    eigenvector: float = 0.0
    pagerank: float = 0.0
    in_degree: int = 0
    out_degree: int = 0


@dataclass
class RelationshipPath:
    """A path between two nodes."""
    src_id: str
    dst_id: str
    path: list[str]
    length: int
    edge_types: list[EdgeType]
    total_weight: float


# ============================================================
# DOCUMENT GRAPH
# ============================================================

@dataclass
class DocumentGraph:
    """The complete document graph G = (V, E)."""
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        """Add a node."""
        self.nodes[node.node_id] = node
        self.graph.add_node(
            node.node_id,
            type=node.node_type,
            label=node.label,
            page=node.page,
            section=node.section,
            weight=node.weight,
        )

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge."""
        self.edges.append(edge)
        self.graph.add_edge(
            edge.src_id, edge.dst_id,
            type=edge.edge_type.value,
            weight=edge.weight,
        )
        if edge.bidirectional:
            self.graph.add_edge(
                edge.dst_id, edge.src_id,
                type=edge.edge_type.value,
                weight=edge.weight,
            )

    def neighbors(self, node_id: str) -> list[str]:
        """Get all neighbors of a node."""
        if node_id not in self.graph:
            return []
        return list(self.graph.successors(node_id))

    def predecessors(self, node_id: str) -> list[str]:
        """Get predecessors of a node."""
        if node_id not in self.graph:
            return []
        return list(self.graph.predecessors(node_id))

    def degree(self, node_id: str) -> int:
        """Get degree of a node."""
        if node_id not in self.graph:
            return 0
        return self.graph.degree(node_id)

    def statistics(self) -> GraphMetrics:
        """Compute graph metrics."""
        G = self.graph
        n = G.number_of_nodes()
        m = G.number_of_edges()
        if n == 0:
            return GraphMetrics()
        max_edges = n * (n - 1)  # directed
        density = m / max_edges if max_edges > 0 else 0.0
        components = nx.number_weakly_connected_components(G)
        degrees = [d for _, d in G.degree()]
        avg_degree = float(np.mean(degrees)) if degrees else 0.0
        max_degree = max(degrees) if degrees else 0
        clustering = nx.average_clustering(G) if n > 0 else 0.0
        # Diameter (only for connected component)
        try:
            if components == 1 and n > 1:
                diameter = nx.diameter(G.to_undirected())
            else:
                diameter = 0
        except Exception:
            diameter = 0
        return GraphMetrics(
            n_nodes=n,
            n_edges=m,
            density=density,
            n_components=components,
            avg_degree=avg_degree,
            max_degree=max_degree,
            clustering_coefficient=clustering,
            diameter=diameter,
            is_connected=(components == 1),
        )


# ============================================================
# GRAPH ENGINE
# ============================================================

class GraphEngine:
    """
    Phase 12: Graph Engine.

    Builds heterogeneous document graphs and computes
    structural metrics: centrality, PageRank, paths.
    """

    # Default PageRank damping factor
    DAMPING_FACTOR = 0.85
    DEFAULT_TOLERANCE = 1e-8

    def __init__(self, damping: float = DAMPING_FACTOR):
        self.damping = damping
        self.graph = DocumentGraph()

    # ============================================================
    # 1. NODE BUILDER
    # ============================================================

    def build_nodes(self, elements: list[GeometricElement]) -> list[GraphNode]:
        """
        Build graph nodes from geometric elements.

        Each element becomes a node with properties:
        - id, type, page, section, content, importance
        """
        nodes = []
        for e in elements:
            node = GraphNode(
                node_id=e.element_id,
                node_type=e.type.value,
                label=e.content[:100],
                page=e.page,
                section=e.section,
                weight=e.importance_weight,
                properties={
                    "content": e.content,
                    "importance": e.importance_weight,
                    "frequency": e.frequency,
                    "recurrence_id": e.recurrence_id,
                },
            )
            self.graph.add_node(node)
            nodes.append(node)
        return nodes

    def build_section_nodes(self, sections: list[str]) -> list[GraphNode]:
        """Build nodes for document sections."""
        nodes = []
        for i, section in enumerate(sections):
            node = GraphNode(
                node_id=f"section-{i}",
                node_type="section",
                label=section,
                weight=1.0,
                section=section,
                properties={"index": i},
            )
            self.graph.add_node(node)
            nodes.append(node)
        return nodes

    def build_page_nodes(self, n_pages: int) -> list[GraphNode]:
        """Build nodes for pages."""
        nodes = []
        for p in range(1, n_pages + 1):
            node = GraphNode(
                node_id=f"page-{p}",
                node_type="page",
                label=f"Page {p}",
                page=p,
            )
            self.graph.add_node(node)
            nodes.append(node)
        return nodes

    def build_entity_nodes(self, entities: list, doc_id: str) -> list[GraphNode]:
        """Build nodes for named entities."""
        nodes = []
        seen = set()
        for ent in entities:
            key = (ent.text.lower(), ent.type)
            if key in seen:
                continue
            seen.add(key)
            node = GraphNode(
                node_id=f"entity-{len(nodes)}",
                node_type="entity",
                label=ent.text,
                weight=ent.confidence,
                properties={"type": ent.type},
            )
            self.graph.add_node(node)
            nodes.append(node)
        return nodes

    # ============================================================
    # 2. EDGE BUILDER
    # ============================================================

    def build_edges(
        self,
        elements: list[GeometricElement],
    ) -> list[GraphEdge]:
        """
        Build graph edges from elements.

        Edge types:
        - FOLLOWS: Reading order (top-to-bottom, left-to-right)
        - NEXT_PAGE: Cross-page continuity
        - ABOVE/BELOW: Spatial relationships
        - SAME_SECTION: Section membership
        """
        edges = []
        # Group by page
        by_page: dict[int, list[GeometricElement]] = defaultdict(list)
        for e in elements:
            by_page[e.page].append(e)

        # Reading order edges (within page)
        for page, page_elements in by_page.items():
            sorted_elements = self._reading_order(page_elements)
            for i in range(len(sorted_elements) - 1):
                edge = GraphEdge(
                    edge_id=f"e-follows-{sorted_elements[i].element_id}",
                    src_id=sorted_elements[i].element_id,
                    dst_id=sorted_elements[i + 1].element_id,
                    edge_type=EdgeType.FOLLOWS,
                    weight=1.0,
                )
                self.graph.add_edge(edge)
                edges.append(edge)

        # Cross-page edges (same section)
        by_section: dict[str, list[GeometricElement]] = defaultdict(list)
        for e in elements:
            if e.section:
                by_section[e.section].append(e)

        for section, sec_elements in by_section.items():
            sorted_sec = sorted(sec_elements, key=lambda x: x.page)
            # Edge from last on page N to first on page N+1
            for i in range(len(sorted_sec) - 1):
                if sorted_sec[i].page != sorted_sec[i + 1].page:
                    edge = GraphEdge(
                        edge_id=f"e-next-{sorted_sec[i].element_id}",
                        src_id=sorted_sec[i].element_id,
                        dst_id=sorted_sec[i + 1].element_id,
                        edge_type=EdgeType.NEXT_PAGE,
                        weight=0.8,
                    )
                    self.graph.add_edge(edge)
                    edges.append(edge)

        # Same-section edges (within section)
        for section, sec_elements in by_section.items():
            for i in range(len(sec_elements)):
                for j in range(i + 1, len(sec_elements)):
                    if sec_elements[i].element_id != sec_elements[j].element_id:
                        edge = GraphEdge(
                            edge_id=f"e-section-{section}-{i}-{j}",
                            src_id=sec_elements[i].element_id,
                            dst_id=sec_elements[j].element_id,
                            edge_type=EdgeType.SAME_SECTION,
                            weight=0.3,
                        )
                        self.graph.add_edge(edge)
                        edges.append(edge)

        return edges

    def build_spatial_edges(self, elements: list[GeometricElement]) -> list[GraphEdge]:
        """Build ABOVE/BELOW spatial edges."""
        edges = []
        for i, e1 in enumerate(elements):
            if e1.bbox is None:
                continue
            for e2 in elements[i + 1:]:
                if e2.bbox is None or e1.page != e2.page:
                    continue
                # Check if e1 is above e2
                if e1.bbox.y1 <= e2.bbox.y0:
                    edge = GraphEdge(
                        edge_id=f"e-above-{e1.element_id}-{e2.element_id}",
                        src_id=e1.element_id,
                        dst_id=e2.element_id,
                        edge_type=EdgeType.ABOVE,
                        weight=0.5,
                    )
                    self.graph.add_edge(edge)
                    edges.append(edge)
                elif e2.bbox.y1 <= e1.bbox.y0:
                    edge = GraphEdge(
                        edge_id=f"e-below-{e1.element_id}-{e2.element_id}",
                        src_id=e1.element_id,
                        dst_id=e2.element_id,
                        edge_type=EdgeType.BELOW,
                        weight=0.5,
                    )
                    self.graph.add_edge(edge)
                    edges.append(edge)
        return edges

    def build_reference_edges(
        self,
        elements: list[GeometricElement],
        references: list[tuple[str, str, str]],
    ) -> list[GraphEdge]:
        """
        Build reference edges from detected references.

        references: list of (src_id, dst_id, reference_text)
        """
        edges = []
        for src_id, dst_id, ref_text in references:
            edge = GraphEdge(
                edge_id=f"e-ref-{src_id}-{dst_id}",
                src_id=src_id,
                dst_id=dst_id,
                edge_type=EdgeType.REFERENCES,
                weight=1.0,
                properties={"reference_text": ref_text},
            )
            self.graph.add_edge(edge)
            edges.append(edge)
        return edges

    def build_table_caption_edges(
        self, elements: list[GeometricElement]
    ) -> list[GraphEdge]:
        """Build edges between tables/figures and their captions."""
        edges = []
        tables_figs = [e for e in elements
                        if e.type in (ElementType.TABLE, ElementType.FIGURE)]
        captions = [e for e in elements if e.type == ElementType.CAPTION]
        for tf in tables_figs:
            if tf.bbox is None:
                continue
            for cap in captions:
                if cap.bbox is None or tf.page != cap.page:
                    continue
                # Check proximity
                if abs(tf.bbox.center[0] - cap.bbox.center[0]) < 0.3:
                    edge = GraphEdge(
                        edge_id=f"e-cap-{tf.element_id}-{cap.element_id}",
                        src_id=tf.element_id,
                        dst_id=cap.element_id,
                        edge_type=EdgeType.CAPTION_OF,
                        weight=0.9,
                    )
                    self.graph.add_edge(edge)
                    edges.append(edge)
                    break
        return edges

    # ============================================================
    # READING ORDER
    # ============================================================

    @staticmethod
    def _reading_order(elements: list[GeometricElement]) -> list[GeometricElement]:
        """Sort elements in reading order (top-to-bottom, left-to-right)."""
        return sorted(
            elements,
            key=lambda e: (
                e.page,
                e.bbox.y0 if e.bbox else 0,
                e.bbox.x0 if e.bbox else 0,
            ),
        )

    # ============================================================
    # 3. CENTRALITY
    # ============================================================

    def degree_centrality(self) -> dict[str, float]:
        """
        C_D(v) = deg(v) / (N - 1)

        Degree centrality for all nodes.
        """
        if self.graph.graph.number_of_nodes() == 0:
            return {}
        return {n: float(c) for n, c in nx.degree_centrality(self.graph.graph).items()}

    def betweenness_centrality(self, normalized: bool = True) -> dict[str, float]:
        """
        C_B(v) = Σ σ_st(v) / σ_st

        Betweenness centrality (how often node is on shortest paths).
        """
        if self.graph.graph.number_of_nodes() < 3:
            return {n: 0.0 for n in self.graph.graph.nodes()}
        try:
            return {
                n: float(c)
                for n, c in nx.betweenness_centrality(self.graph.graph, normalized=normalized).items()
            }
        except Exception as e:
            logger.warning(f"Betweenness centrality failed: {e}")
            return {n: 0.0 for n in self.graph.graph.nodes()}

    def closeness_centrality(self) -> dict[str, float]:
        """
        C_C(v) = (N - 1) / Σ d(v, u)

        Closeness centrality (inverse of sum of distances).
        """
        if self.graph.graph.number_of_nodes() < 2:
            return {n: 0.0 for n in self.graph.graph.nodes()}
        try:
            return {
                n: float(c)
                for n, c in nx.closeness_centrality(self.graph.graph).items()
            }
        except Exception as e:
            logger.warning(f"Closeness centrality failed: {e}")
            return {n: 0.0 for n in self.graph.graph.nodes()}

    def eigenvector_centrality(self, max_iter: int = 1000) -> dict[str, float]:
        """
        Eigenvector centrality (influence via neighbors).
        """
        if self.graph.graph.number_of_nodes() < 2:
            return {n: 0.0 for n in self.graph.graph.nodes()}
        try:
            return {
                n: float(c)
                for n, c in nx.eigenvector_centrality(
                    self.graph.graph, max_iter=max_iter
                ).items()
            }
        except Exception:
            try:
                return {
                    n: float(c)
                    for n, c in nx.eigenvector_centrality_numpy(self.graph.graph).items()
                }
            except Exception as e:
                logger.warning(f"Eigenvector centrality failed: {e}")
                return {n: 0.0 for n in self.graph.graph.nodes()}

    def compute_all_centralities(
        self, include_eigenvector: bool = True
    ) -> dict[str, CentralityScores]:
        """Compute all centrality metrics for all nodes."""
        degrees = dict(self.graph.graph.degree())
        in_degrees = dict(self.graph.graph.in_degree())
        out_degrees = dict(self.graph.graph.out_degree())
        deg_cent = self.degree_centrality()
        betw_cent = self.betweenness_centrality()
        close_cent = self.closeness_centrality()
        eigen_cent = self.eigenvector_centrality() if include_eigenvector else {}
        pr = self.pagerank()
        scores = {}
        for node_id in self.graph.graph.nodes():
            scores[node_id] = CentralityScores(
                node_id=node_id,
                degree=deg_cent.get(node_id, 0.0),
                betweenness=betw_cent.get(node_id, 0.0),
                closeness=close_cent.get(node_id, 0.0),
                eigenvector=eigen_cent.get(node_id, 0.0),
                pagerank=pr.get(node_id, 0.0),
                in_degree=in_degrees.get(node_id, 0),
                out_degree=out_degrees.get(node_id, 0),
            )
        return scores

    # ============================================================
    # 4. PAGERANK
    # ============================================================

    def pagerank(
        self,
        damping: float | None = None,
        max_iter: int = 100,
        tol: float = DEFAULT_TOLERANCE,
    ) -> dict[str, float]:
        """
        PageRank algorithm via power iteration.

        π = (1-d)/N · 1 + d · M^T π
        """
        if self.graph.graph.number_of_nodes() == 0:
            return {}
        d = damping if damping is not None else self.damping
        try:
            return {
                n: float(p)
                for n, p in nx.pagerank(
                    self.graph.graph, alpha=d, max_iter=max_iter, tol=tol
                ).items()
            }
        except Exception as e:
            logger.warning(f"PageRank failed: {e}")
            # Uniform fallback
            n = self.graph.graph.number_of_nodes()
            return {node: 1.0 / n for node in self.graph.graph.nodes()}

    def personalized_pagerank(
        self,
        personalization: dict[str, float],
        damping: float | None = None,
        max_iter: int = 100,
    ) -> dict[str, float]:
        """
        Personalized PageRank with query biasing.

        personalization: {node_id: weight, ...}
        """
        if self.graph.graph.number_of_nodes() == 0:
            return {}
        d = damping if damping is not None else self.damping
        try:
            return {
                n: float(p)
                for n, p in nx.pagerank(
                    self.graph.graph,
                    alpha=d,
                    personalization=personalization,
                    max_iter=max_iter,
                ).items()
            }
        except Exception as e:
            logger.warning(f"Personalized PageRank failed: {e}")
            return self.pagerank(damping=d)

    def power_iteration_pagerank(
        self,
        damping: float | None = None,
        max_iter: int = 100,
        tol: float = DEFAULT_TOLERANCE,
    ) -> dict[str, float]:
        """
        Manual power iteration for PageRank.
        """
        G = self.graph.graph
        n = G.number_of_nodes()
        if n == 0:
            return {}
        d = damping if damping is not None else self.damping
        nodes = list(G.nodes())
        # Build transition matrix
        M = np.zeros((n, n))
        for i, src in enumerate(nodes):
            out_edges = list(G.successors(src))
            if out_edges:
                weight = 1.0 / len(out_edges)
                for dst in out_edges:
                    j = nodes.index(dst)
                    M[j, i] = weight  # Column-stochastic
        # Initialize
        pr = np.ones(n) / n
        teleport = np.ones(n) / n
        for _ in range(max_iter):
            pr_new = (1 - d) * teleport + d * M @ pr
            if np.linalg.norm(pr_new - pr, 1) < tol:
                break
            pr = pr_new
        return {nodes[i]: float(pr[i]) for i in range(n)}

    # ============================================================
    # 5. RELATIONSHIP MAPPING
    # ============================================================

    def find_paths(
        self,
        src_id: str,
        dst_id: str,
        max_length: int = 5,
    ) -> list[RelationshipPath]:
        """Find all paths between two nodes (up to max_length)."""
        if src_id == dst_id:
            return []
        if src_id not in self.graph.graph or dst_id not in self.graph.graph:
            return []
        paths = []
        try:
            for path in nx.all_simple_paths(
                self.graph.graph, src_id, dst_id, cutoff=max_length
            ):
                edge_types = []
                total_weight = 0.0
                for i in range(len(path) - 1):
                    edge_data = self.graph.graph.get_edge_data(path[i], path[i + 1])
                    if edge_data:
                        edge_types.append(EdgeType(edge_data.get("type", "follows")))
                        total_weight += edge_data.get("weight", 1.0)
                paths.append(RelationshipPath(
                    src_id=src_id, dst_id=dst_id,
                    path=path, length=len(path) - 1,
                    edge_types=edge_types, total_weight=total_weight,
                ))
        except Exception as e:
            logger.warning(f"Path finding failed: {e}")
        # Sort by length, then weight
        paths.sort(key=lambda p: (p.length, -p.total_weight))
        return paths

    def shortest_path(
        self, src_id: str, dst_id: str, weight: str | None = "weight"
    ) -> RelationshipPath | None:
        """Find shortest weighted path."""
        if src_id not in self.graph.graph or dst_id not in self.graph.graph:
            return None
        try:
            path = nx.shortest_path(
                self.graph.graph, src_id, dst_id, weight=weight
            )
            length = nx.shortest_path_length(
                self.graph.graph, src_id, dst_id, weight=weight
            )
            edge_types = []
            for i in range(len(path) - 1):
                edge_data = self.graph.graph.get_edge_data(path[i], path[i + 1])
                if edge_data:
                    edge_types.append(EdgeType(edge_data.get("type", "follows")))
            return RelationshipPath(
                src_id=src_id, dst_id=dst_id,
                path=list(path), length=length,
                edge_types=edge_types, total_weight=length,
            )
        except nx.NetworkXNoPath:
            return None
        except Exception as e:
            logger.warning(f"Shortest path failed: {e}")
            return None

    def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[str]:
        """Get neighbors, optionally filtered by edge type."""
        if node_id not in self.graph.graph:
            return []
        if edge_type is None:
            return list(self.graph.graph.successors(node_id))
        result = []
        for successor in self.graph.graph.successors(node_id):
            edge_data = self.graph.graph.get_edge_data(node_id, successor)
            if edge_data and edge_data.get("type") == edge_type.value:
                result.append(successor)
        return result

    def find_relationships(self, node_id: str, max_hops: int = 3) -> dict[str, list]:
        """Find all relationships within N hops of a node."""
        if node_id not in self.graph.graph:
            return {}
        relationships: dict[str, list] = defaultdict(list)
        # BFS
        visited = {node_id}
        queue = [(node_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_hops:
                continue
            for neighbor in self.graph.graph.successors(current):
                edge_data = self.graph.graph.get_edge_data(current, neighbor)
                if edge_data:
                    edge_type = edge_data.get("type", "follows")
                    relationships[edge_type].append({
                        "from": current,
                        "to": neighbor,
                        "weight": edge_data.get("weight", 1.0),
                    })
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))
        return dict(relationships)

    def find_similar_nodes(self, node_id: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Find nodes with similar connection patterns."""
        if node_id not in self.graph.graph:
            return []
        similarities = []
        node_neighbors = set(self.graph.graph.successors(node_id))
        for other_id in self.graph.graph.nodes():
            if other_id == node_id:
                continue
            other_neighbors = set(self.graph.graph.successors(other_id))
            # Jaccard similarity
            if not node_neighbors and not other_neighbors:
                sim = 0.0
            else:
                intersection = len(node_neighbors & other_neighbors)
                union = len(node_neighbors | other_neighbors)
                sim = intersection / union if union > 0 else 0.0
            similarities.append((other_id, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_subgraph_by_node_type(self, node_type: str) -> "DocumentGraph":
        """Extract subgraph containing only nodes of a specific type."""
        subgraph = DocumentGraph()
        matching_nodes = [
            n for n in self.graph.nodes.values()
            if n.node_type == node_type
        ]
        for node in matching_nodes:
            subgraph.add_node(node)
        for edge in self.graph.edges:
            if edge.src_id in subgraph.nodes and edge.dst_id in subgraph.nodes:
                subgraph.add_edge(edge)
        return subgraph

    def get_subgraph_by_section(self, section: str) -> "DocumentGraph":
        """Extract subgraph for a specific section."""
        subgraph = DocumentGraph()
        for node in self.graph.nodes.values():
            if node.section == section:
                subgraph.add_node(node)
        for edge in self.graph.edges:
            if edge.src_id in subgraph.nodes and edge.dst_id in subgraph.nodes:
                subgraph.add_edge(edge)
        return subgraph

    # ============================================================
    # QUERIES
    # ============================================================

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get node by ID."""
        return self.graph.nodes.get(node_id)

    def get_edge(self, src_id: str, dst_id: str) -> GraphEdge | None:
        """Get edge between two nodes."""
        for edge in self.graph.edges:
            if edge.src_id == src_id and edge.dst_id == dst_id:
                return edge
        return None

    def get_edges_by_type(self, edge_type: EdgeType) -> list[GraphEdge]:
        """Get all edges of a specific type."""
        return [e for e in self.graph.edges if e.edge_type == edge_type]

    def get_nodes_by_type(self, node_type: str) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [n for n in self.graph.nodes.values() if n.node_type == node_type]

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self) -> GraphMetrics:
        """Get graph statistics."""
        return self.graph.statistics()

    def edge_type_distribution(self) -> dict[str, int]:
        """Distribution of edge types."""
        dist: dict[str, int] = {}
        for e in self.graph.edges:
            t = e.edge_type.value
            dist[t] = dist.get(t, 0) + 1
        return dist

    def node_type_distribution(self) -> dict[str, int]:
        """Distribution of node types."""
        dist: dict[str, int] = {}
        for n in self.graph.nodes.values():
            dist[n.node_type] = dist.get(n.node_type, 0) + 1
        return dist

    def clear(self) -> None:
        """Clear graph."""
        self.graph = DocumentGraph()

    def export_to_json(self) -> dict:
        """Export graph to JSON-serializable dict."""
        return {
            "nodes": [
                {
                    "id": n.node_id, "type": n.node_type,
                    "label": n.label, "page": n.page,
                    "section": n.section, "weight": n.weight,
                }
                for n in self.graph.nodes.values()
            ],
            "edges": [
                {
                    "id": e.edge_id, "src": e.src_id, "dst": e.dst_id,
                    "type": e.edge_type.value, "weight": e.weight,
                }
                for e in self.graph.edges
            ],
            "statistics": self.statistics(),
        }
