"""
AEGIS-MDIE — Graph Engine
==========================
G_D = (V_D, E_D) — Heterogeneous document graph.
Typed nodes (element types) + typed edges (structural relations).
Enables cross-page retrieval and structural path-based reasoning.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False

from MDIE.engines.geometry.element import ElementType, GeometricElement

log = logging.getLogger("mdie.graph")


# ─────────────────────────────────────────────────────────────────
# Edge Types
# ─────────────────────────────────────────────────────────────────

class EdgeType(str, Enum):
    FOLLOWS        = "follows"          # e_i immediately precedes e_j (reading order)
    CONTAINS       = "contains"         # section contains block
    BELONGS_TO     = "belongs_to"       # element is part of section
    ADJACENT       = "adjacent"         # geometrically adjacent, same page
    ABOVE          = "above"            # e_i is above e_j, same page
    BELOW          = "below"            # e_i is below e_j, same page
    SAME_SECTION   = "same_section"     # same section heading
    NEXT_SECTION   = "next_section"     # from one section to the next
    CROSS_PAGE     = "cross_page"       # same content / heading on adjacent pages
    TABLE_CAPTION  = "table_caption"    # table → its caption
    FIGURE_CAPTION = "figure_caption"   # figure → its caption
    EQ_TO_TEXT     = "eq_to_text"       # equation → surrounding paragraph
    REFERENCES     = "references"        # in-text citation → referenced content


EDGE_WEIGHTS: dict[EdgeType, float] = {
    EdgeType.FOLLOWS:        1.0,
    EdgeType.CONTAINS:       0.9,
    EdgeType.BELONGS_TO:     0.9,
    EdgeType.ADJACENT:       0.7,
    EdgeType.ABOVE:          0.7,
    EdgeType.BELOW:          0.7,
    EdgeType.SAME_SECTION:   0.8,
    EdgeType.NEXT_SECTION:   0.5,
    EdgeType.CROSS_PAGE:     0.6,
    EdgeType.TABLE_CAPTION:  1.0,
    EdgeType.FIGURE_CAPTION: 1.0,
    EdgeType.EQ_TO_TEXT:     0.85,
    EdgeType.REFERENCES:     0.9,
}


# ─────────────────────────────────────────────────────────────────
# Lightweight adjacency list graph (no NetworkX dependency required)
# ─────────────────────────────────────────────────────────────────

@dataclass
class GraphNode:
    element_id: str
    type:        ElementType
    page:        int
    section:     Optional[str]
    content:     str            # first 200 chars
    importance:  float
    bbox:        Optional[tuple]


@dataclass
class GraphEdge:
    src:    str
    dst:    str
    type:   EdgeType
    weight: float = 1.0


class DocumentGraph:
    """
    G_D = (V_D, E_D)
    Supports both plain adjacency-list traversal and NetworkX analytics.
    """

    def __init__(self):
        self.nodes:   dict[str, GraphNode]   = {}
        self.edges:   list[GraphEdge]        = []
        self._out:    dict[str, list[GraphEdge]] = defaultdict(list)
        self._in:     dict[str, list[GraphEdge]] = defaultdict(list)
        self._nx:     Optional[object]          = None   # lazy networkx graph

    # ──────────────────────────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────────────────────────

    def add_node(self, e: GeometricElement) -> None:
        self.nodes[e.element_id] = GraphNode(
            element_id = e.element_id,
            type       = e.type,
            page       = e.page,
            section    = e.section,
            content    = e.content[:200],
            importance = e.importance_weight,
            bbox       = e.bbox.to_tuple() if e.bbox else None,
        )

    def add_edge(
        self,
        src: str,
        dst: str,
        edge_type: EdgeType,
        weight: Optional[float] = None,
    ) -> None:
        if src not in self.nodes or dst not in self.nodes:
            return
        w = weight if weight is not None else EDGE_WEIGHTS.get(edge_type, 1.0)
        e = GraphEdge(src=src, dst=dst, type=edge_type, weight=w)
        self.edges.append(e)
        self._out[src].append(e)
        self._in[dst].append(e)
        self._nx = None   # invalidate NX cache

    # ──────────────────────────────────────────────────────────────
    # Traversal
    # ──────────────────────────────────────────────────────────────

    def neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "out",   # "out" | "in" | "both"
    ) -> list[GraphNode]:
        edges: list[GraphEdge] = []
        if direction in ("out", "both"):
            edges += self._out.get(node_id, [])
        if direction in ("in", "both"):
            edges += self._in.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if e.type == edge_type]
        ids = {e.dst if direction == "out" else e.src for e in edges}
        ids = {e.dst for e in self._out.get(node_id, []) if edge_type is None or e.type == edge_type}
        if direction == "in":
            ids = {e.src for e in self._in.get(node_id, []) if edge_type is None or e.type == edge_type}
        if direction == "both":
            ids = (
                {e.dst for e in self._out.get(node_id, []) if edge_type is None or e.type == edge_type}
                | {e.src for e in self._in.get(node_id, []) if edge_type is None or e.type == edge_type}
            )
        return [self.nodes[nid] for nid in ids if nid in self.nodes]

    def bfs(
        self,
        start_id: str,
        max_depth: int = 3,
        edge_type: Optional[EdgeType] = None,
    ) -> list[GraphNode]:
        """Breadth-first traversal from start_id."""
        visited = {start_id}
        queue   = [(start_id, 0)]
        result  = []
        while queue:
            nid, depth = queue.pop(0)
            if depth > max_depth:
                continue
            for nb in self.neighbors(nid, edge_type=edge_type):
                if nb.element_id not in visited:
                    visited.add(nb.element_id)
                    result.append(nb)
                    queue.append((nb.element_id, depth + 1))
        return result

    def section_subgraph(self, section: str) -> list[GraphNode]:
        """All nodes in a named section."""
        return [n for n in self.nodes.values() if n.section == section]

    def page_subgraph(self, page: int) -> list[GraphNode]:
        return [n for n in self.nodes.values() if n.page == page]

    # ──────────────────────────────────────────────────────────────
    # Graph-based retrieval  G(q, e)
    # ──────────────────────────────────────────────────────────────

    def structural_score(
        self,
        node_id: str,
        seed_ids: list[str],
        decay: float = 0.5,
    ) -> float:
        """
        G(q, e): structural proximity to seed nodes (BFS-based).
        Score = 1 if seed, decay^depth for each hop.
        """
        if node_id in seed_ids:
            return 1.0
        if node_id not in self.nodes:
            return 0.0

        best = 0.0
        visited = {node_id}
        queue   = [(node_id, 1)]
        while queue:
            nid, depth = queue.pop(0)
            if depth > 4:
                break
            for nb in self.neighbors(nid, direction="both"):
                nbid = nb.element_id
                if nbid in seed_ids:
                    score = decay ** depth
                    best  = max(best, score)
                if nbid not in visited:
                    visited.add(nbid)
                    queue.append((nbid, depth + 1))
        return best

    # ──────────────────────────────────────────────────────────────
    # NetworkX analytics (optional)
    # ──────────────────────────────────────────────────────────────

    def _build_nx(self):
        if not _HAS_NX:
            raise ImportError("networkx not installed: pip install networkx")
        G = nx.DiGraph()
        for nid, node in self.nodes.items():
            G.add_node(nid, type=node.type.value, page=node.page,
                       section=node.section, importance=node.importance)
        for edge in self.edges:
            G.add_edge(edge.src, edge.dst, type=edge.type.value, weight=edge.weight)
        self._nx = G
        return G

    def pagerank(self, damping: float = 0.85) -> dict[str, float]:
        """PageRank over the document graph — identifies structurally central nodes."""
        G = self._nx or self._build_nx()
        return nx.pagerank(G, alpha=damping, weight="weight")

    def shortest_path(self, src: str, dst: str) -> list[str]:
        """Shortest path between two elements in the graph."""
        G = self._nx or self._build_nx()
        try:
            return nx.shortest_path(G, src, dst, weight="weight")
        except nx.NetworkXNoPath:
            return []

    def hub_nodes(self, top_k: int = 10) -> list[tuple[str, float]]:
        """Return top-k structurally central elements by PageRank."""
        pr = self.pagerank()
        return sorted(pr.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # ──────────────────────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        edge_type_counts: dict[str, int] = defaultdict(int)
        for e in self.edges:
            edge_type_counts[e.type.value] += 1
        return {
            "nodes":      len(self.nodes),
            "edges":      len(self.edges),
            "edge_types": dict(edge_type_counts),
            "avg_degree": round(len(self.edges) / max(1, len(self.nodes)), 2),
        }


# ─────────────────────────────────────────────────────────────────
# Graph Engine (builder)
# ─────────────────────────────────────────────────────────────────

class GraphEngine:
    """
    Constructs the document graph from a list of GeometricElements.

    Automatic edge construction:
        - FOLLOWS: reading-order sequence
        - BELONGS_TO: heading → following elements until next heading
        - ADJACENT: elements within δ proximity on same page
        - TABLE_CAPTION: table → next caption element
        - FIGURE_CAPTION: figure → next caption element
        - SAME_SECTION: elements sharing a section
        - CROSS_PAGE: matching section headings across pages
    """

    def __init__(self, proximity_threshold: float = 0.08):
        self.graph = DocumentGraph()
        self.prox  = proximity_threshold

    def build(self, elements: list[GeometricElement]) -> DocumentGraph:
        """Build full document graph from sorted element list."""
        # 1. Add all nodes
        for e in elements:
            self.graph.add_node(e)

        # 2. Reading-order FOLLOWS edges
        self._add_follows_edges(elements)

        # 3. Section BELONGS_TO edges
        self._add_section_edges(elements)

        # 4. ADJACENT edges (same page, within threshold)
        self._add_adjacent_edges(elements)

        # 5. Caption edges (TABLE/FIGURE → next CAPTION)
        self._add_caption_edges(elements)

        # 6. SAME_SECTION edges
        self._add_same_section_edges(elements)

        # 7. CROSS_PAGE edges for matching headings
        self._add_cross_page_edges(elements)

        log.info(
            "Graph built: %d nodes, %d edges",
            len(self.graph.nodes), len(self.graph.edges),
        )
        return self.graph

    def _add_follows_edges(self, elements: list[GeometricElement]) -> None:
        for i in range(len(elements) - 1):
            a, b = elements[i], elements[i + 1]
            if a.page == b.page or b.page == a.page + 1:
                self.graph.add_edge(a.element_id, b.element_id, EdgeType.FOLLOWS)

    def _add_section_edges(self, elements: list[GeometricElement]) -> None:
        current_heading_id: Optional[str] = None
        for e in elements:
            if e.type == ElementType.HEADING:
                current_heading_id = e.element_id
            elif current_heading_id and e.type != ElementType.HEADING:
                self.graph.add_edge(e.element_id, current_heading_id, EdgeType.BELONGS_TO)

    def _add_adjacent_edges(self, elements: list[GeometricElement]) -> None:
        by_page: dict[int, list[GeometricElement]] = defaultdict(list)
        for e in elements:
            if e.bbox:
                by_page[e.page].append(e)
        for page_elems in by_page.values():
            for i, a in enumerate(page_elems):
                for b in page_elems[i + 1:]:
                    if not a.bbox or not b.bbox:
                        continue
                    # Vertical proximity on same column
                    x_overlap = (
                        min(a.bbox.x1, b.bbox.x1) - max(a.bbox.x0, b.bbox.x0)
                    ) / max(0.001, a.bbox.width)
                    v_gap = abs(b.bbox.y0 - a.bbox.y1)
                    if x_overlap > 0.3 and v_gap < self.prox:
                        self.graph.add_edge(a.element_id, b.element_id, EdgeType.ADJACENT)

    def _add_caption_edges(self, elements: list[GeometricElement]) -> None:
        for i, e in enumerate(elements):
            if e.type in (ElementType.TABLE, ElementType.FIGURE):
                for j in range(i + 1, min(i + 4, len(elements))):
                    nxt = elements[j]
                    if nxt.type == ElementType.CAPTION:
                        et = EdgeType.TABLE_CAPTION if e.type == ElementType.TABLE else EdgeType.FIGURE_CAPTION
                        self.graph.add_edge(e.element_id, nxt.element_id, et)
                        break

    def _add_same_section_edges(self, elements: list[GeometricElement]) -> None:
        by_section: dict[str, list[str]] = defaultdict(list)
        for e in elements:
            if e.section:
                by_section[e.section].append(e.element_id)
        for ids in by_section.values():
            for i in range(len(ids)):
                for j in range(i + 1, min(i + 5, len(ids))):
                    self.graph.add_edge(ids[i], ids[j], EdgeType.SAME_SECTION, weight=0.6)

    def _add_cross_page_edges(self, elements: list[GeometricElement]) -> None:
        heading_by_content: dict[str, list[str]] = defaultdict(list)
        for e in elements:
            if e.type == ElementType.HEADING:
                key = " ".join(e.content.lower().split())[:60]
                heading_by_content[key].append(e.element_id)
        for ids in heading_by_content.values():
            for i in range(len(ids) - 1):
                self.graph.add_edge(ids[i], ids[i + 1], EdgeType.CROSS_PAGE, weight=0.5)
