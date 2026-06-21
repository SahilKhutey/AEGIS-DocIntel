"""
AEGIS-AMDI — Hypergraph Engine (Layer 8)
==========================================
HG = (V, E*)
One hyperedge connects ≥ 2 nodes.

Extends the binary graph with multi-element groupings:
  • Table + Caption + Referencing Paragraph
  • Figure + Caption + Discussion
  • Equation + Surrounding Text
  • Section → All Children

Enables holistic retrieval: fetching a table also retrieves its caption
and the text that analyses it.
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from AMDI.engines.geometry.element import BoundingBox, Element, ElementType

log = logging.getLogger("amdi.hypergraph")


# ─────────────────────────────────────────────────────────────────
# Hyperedge + Hypergraph
# ─────────────────────────────────────────────────────────────────

@dataclass
class Hyperedge:
    """
    e* ⊆ V,  |e*| ≥ 2
    Typed association between multiple document elements.
    """
    hid:      str
    nodes:    list[str]      # element_ids
    type:     str            # "table_group" | "figure_group" | "section_group" | ...
    weight:   float = 1.0
    metadata: dict = field(default_factory=dict)

    @property
    def arity(self) -> int:
        return len(self.nodes)


class Hypergraph:
    """
    HG = (V, E*)
    Stores hyperedges and provides fast lookup.
    """

    def __init__(self):
        self.nodes:      set[str]              = set()
        self.hyperedges: list[Hyperedge]       = []
        self._n2e:       dict[str, list[str]]  = defaultdict(list)  # node → hid list

    def add(self, h: Hyperedge) -> None:
        self.hyperedges.append(h)
        self.nodes.update(h.nodes)
        for n in h.nodes:
            self._n2e[n].append(h.hid)

    def edges_of(self, node_id: str) -> list[Hyperedge]:
        hids = set(self._n2e.get(node_id, []))
        return [h for h in self.hyperedges if h.hid in hids]

    def co_members(self, node_id: str, edge_type: Optional[str] = None) -> list[str]:
        """All nodes that share a hyperedge with node_id."""
        result = set()
        for h in self.edges_of(node_id):
            if edge_type and h.type != edge_type:
                continue
            result.update(n for n in h.nodes if n != node_id)
        return list(result)

    def hyperedge_vector(self, hid: str) -> Optional[np.ndarray]:
        """Return centroid embedding of a hyperedge's members (if available)."""
        for h in self.hyperedges:
            if h.hid == hid:
                return None  # populated externally
        return None

    def statistics(self) -> dict:
        arities = [h.arity for h in self.hyperedges]
        return {
            "nodes":       len(self.nodes),
            "hyperedges":  len(self.hyperedges),
            "avg_arity":   round(float(np.mean(arities)), 2) if arities else 0,
            "max_arity":   max(arities) if arities else 0,
            "types":       list({h.type for h in self.hyperedges}),
        }


# ─────────────────────────────────────────────────────────────────
# Hypergraph Engine
# ─────────────────────────────────────────────────────────────────

class HypergraphEngine:
    """
    Builds the document hypergraph from a list of Elements.

    Automatic hyperedge construction:
        1. TABLE + nearby CAPTION + referencing PARAGRAPH
        2. FIGURE + nearby CAPTION + surrounding TEXT
        3. EQUATION + preceding/following TEXT
        4. HEADING + all children in its section
        5. SECTION groups (same section, same page)
    """

    def __init__(self, proximity_y: float = 0.12, proximity_x: float = 0.5):
        self.prox_y = proximity_y
        self.prox_x = proximity_x
        self.graph  = Hypergraph()

    def build(self, elements: list[Element]) -> Hypergraph:
        self.graph = Hypergraph()
        self._build_table_groups(elements)
        self._build_figure_groups(elements)
        self._build_equation_groups(elements)
        self._build_section_groups(elements)
        log.info(
            "HypergraphEngine: %d nodes, %d hyperedges",
            len(self.graph.nodes), len(self.graph.hyperedges),
        )
        return self.graph

    # ──────────────────────────────────────────────────────────────
    # Hyperedge builders
    # ──────────────────────────────────────────────────────────────

    def _build_table_groups(self, elements: list[Element]) -> None:
        tables   = [e for e in elements if e.type == ElementType.TABLE and e.bbox]
        captions = [e for e in elements if e.type == ElementType.CAPTION and e.bbox]
        paras    = [e for e in elements if e.type in (ElementType.PARAGRAPH, ElementType.TEXT) and e.bbox]
        for i, tbl in enumerate(tables):
            members = [tbl.element_id]
            # Nearby captions
            for c in captions:
                if c.page == tbl.page and self._vy(tbl.bbox, c.bbox) < self.prox_y:
                    members.append(c.element_id)
            # Referencing paragraphs (mentions "table", "above", etc.)
            for p in paras:
                if p.page in (tbl.page, tbl.page + 1):
                    if ("table" in p.content.lower() or "above" in p.content.lower()
                            or f"table {i+1}" in p.content.lower()):
                        members.append(p.element_id)
            if len(members) >= 2:
                self.graph.add(Hyperedge(
                    hid=f"tg-{i}", nodes=list(dict.fromkeys(members)),
                    type="table_group", weight=0.95,
                ))

    def _build_figure_groups(self, elements: list[Element]) -> None:
        figures  = [e for e in elements if e.type == ElementType.FIGURE and e.bbox]
        captions = [e for e in elements if e.type == ElementType.CAPTION and e.bbox]
        paras    = [e for e in elements if e.type in (ElementType.PARAGRAPH, ElementType.TEXT) and e.bbox]
        for i, fig in enumerate(figures):
            members = [fig.element_id]
            for c in captions:
                if c.page == fig.page and self._vy(fig.bbox, c.bbox) < self.prox_y:
                    members.append(c.element_id)
            for p in paras:
                if p.page == fig.page and self._vy(fig.bbox, p.bbox) < self.prox_y * 3:
                    members.append(p.element_id)
            if len(members) >= 2:
                self.graph.add(Hyperedge(
                    hid=f"fg-{i}", nodes=list(dict.fromkeys(members)),
                    type="figure_group", weight=0.85,
                ))

    def _build_equation_groups(self, elements: list[Element]) -> None:
        eqs   = [e for e in elements if e.type in (ElementType.EQUATION, ElementType.FORMULA) and e.bbox]
        texts = [e for e in elements if e.type in (ElementType.PARAGRAPH, ElementType.TEXT) and e.bbox]
        for i, eq in enumerate(eqs):
            members = [eq.element_id]
            for t in texts:
                if t.page == eq.page and self._vy(eq.bbox, t.bbox) < self.prox_y:
                    members.append(t.element_id)
            if len(members) >= 2:
                self.graph.add(Hyperedge(
                    hid=f"eq-{i}", nodes=list(dict.fromkeys(members)),
                    type="equation_group", weight=0.80,
                ))

    def _build_section_groups(self, elements: list[Element]) -> None:
        by_section: dict[str, list[str]] = defaultdict(list)
        for e in elements:
            if e.section:
                by_section[e.section].append(e.element_id)
        for i, (section, members) in enumerate(by_section.items()):
            if len(members) >= 3:
                self.graph.add(Hyperedge(
                    hid=f"sg-{i}", nodes=members[:20],   # cap at 20
                    type="section_group", weight=0.60,
                    metadata={"section": section},
                ))

    # ──────────────────────────────────────────────────────────────
    # Retrieval — score element via hypergraph membership
    # ──────────────────────────────────────────────────────────────

    def hypergraph_score(
        self,
        element: Element,
        seed_ids: set[str],
        decay: float = 0.6,
    ) -> float:
        """
        Hypergraph proximity to seed set.
        If element shares a hyperedge with a seed → score = weight × decay
        """
        if element.element_id in seed_ids:
            return 1.0
        best = 0.0
        for h in self.graph.edges_of(element.element_id):
            if any(n in seed_ids for n in h.nodes):
                s = h.weight * decay
                best = max(best, s)
        return best

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _vy(b1: BoundingBox, b2: BoundingBox) -> float:
        """Vertical gap between two bboxes (normalized)."""
        if b1.y1 < b2.y0:
            return b2.y0 - b1.y1
        if b2.y1 < b1.y0:
            return b1.y0 - b2.y1
        return 0.0  # overlapping
