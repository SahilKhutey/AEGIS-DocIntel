"""
hypergraph_engine.py
====================
AEGIS-AMDI-OS · Hypergraph Engine

Models rich multi-way relationships between document elements as a
*hypergraph* — a generalisation of a graph in which a single *hyperedge*
can connect an arbitrary number of nodes (elements).

Four hyperedge families are detected automatically:

* **table_group**   — TABLE + nearby CAPTION + referencing PARAGRAPHs
* **figure_group**  — FIGURE + nearby CAPTION + surrounding TEXT
* **equation_group**— EQUATION + nearby TEXT elements
* **section_group** — all elements sharing the same section header
  (≥ 3 members required)

Typical usage
-------------
>>> engine = HypergraphEngine()
>>> hg = engine.build(elements)
>>> score = engine.hypergraph_score(element, seed_ids={"id1", "id2"})
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from src.engines.geometry.element import GeometricElement, ElementType  # noqa: E402

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_PROXIMITY_THRESHOLD: float = 0.12   # Normalised vertical gap (page fraction)
_MIN_SECTION_SIZE: int = 3           # Minimum members to form a section group

_TABLE_KEYWORDS = frozenset({"table", "tbl", "above", "below", "see table"})
_FIGURE_KEYWORDS = frozenset({"figure", "fig", "shown above", "shown below"})

# Default hyperedge weights per family
_WEIGHTS: dict[str, float] = {
    "table_group": 0.9,
    "figure_group": 0.85,
    "equation_group": 0.75,
    "section_group": 0.6,
}


# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class Hyperedge:
    """A hyperedge connecting two or more document elements.

    Attributes
    ----------
    hid:
        Unique string identifier for this hyperedge (e.g. ``"tbl_0"``).
    nodes:
        List of ``element_id`` strings that belong to this hyperedge.
    type:
        Semantic family: one of ``"table_group"``, ``"figure_group"``,
        ``"equation_group"``, ``"section_group"``.
    weight:
        Confidence / relevance weight in ``[0, 1]``.
    metadata:
        Arbitrary key-value pairs for downstream consumers.
    """

    hid: str
    nodes: List[str]
    type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def arity(self) -> int:
        """Number of nodes (elements) in this hyperedge."""
        return len(self.nodes)


# ---------------------------------------------------------------------------
# Hypergraph container
# ---------------------------------------------------------------------------

class Hypergraph:
    """In-memory hypergraph data structure.

    Maintains a bipartite index between node IDs and their incident
    hyperedges to support O(deg) neighbourhood queries.

    Attributes
    ----------
    nodes:
        Set of all node IDs present in at least one hyperedge.
    hyperedges:
        Ordered list of all ``Hyperedge`` objects.
    """

    def __init__(self) -> None:
        self.nodes: Set[str] = set()
        self.hyperedges: List[Hyperedge] = []
        # node_id → list of Hyperedge objects
        self._n2e: defaultdict[str, List[Hyperedge]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, hyperedge: Hyperedge) -> None:
        """Insert a hyperedge and update the node-to-edge index.

        Parameters
        ----------
        hyperedge:
            The hyperedge to insert.  Duplicate ``hid`` values are
            silently overwritten at query time (not deduplicated here).
        """
        self.hyperedges.append(hyperedge)
        for nid in hyperedge.nodes:
            self.nodes.add(nid)
            self._n2e[nid].append(hyperedge)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def edges_of(self, node_id: str) -> List[Hyperedge]:
        """Return all hyperedges incident to *node_id*.

        Parameters
        ----------
        node_id:
            Element ID to look up.

        Returns
        -------
        list[Hyperedge]
            Possibly empty list of incident hyperedges.
        """
        return list(self._n2e.get(node_id, []))

    def co_members(
        self, node_id: str, edge_type: Optional[str] = None
    ) -> Set[str]:
        """Return all nodes that share at least one hyperedge with *node_id*.

        Parameters
        ----------
        node_id:
            The query node.
        edge_type:
            If supplied, restrict co-membership to hyperedges of this
            semantic type.

        Returns
        -------
        set[str]
            All co-member node IDs (excluding *node_id* itself).
        """
        members: Set[str] = set()
        for h in self._n2e.get(node_id, []):
            if edge_type is not None and h.type != edge_type:
                continue
            members.update(h.nodes)
        members.discard(node_id)
        return members

    def statistics(self) -> Dict[str, Any]:
        """Return a summary statistics dictionary.

        Returns
        -------
        dict
            Keys: ``nodes``, ``hyperedges``, ``mean_arity``,
            ``types`` (per-type counts).
        """
        arities = [h.arity for h in self.hyperedges]
        type_counts: Counter = defaultdict(int)  # type: ignore[type-arg]
        for h in self.hyperedges:
            type_counts[h.type] += 1
        return {
            "nodes": len(self.nodes),
            "hyperedges": len(self.hyperedges),
            "mean_arity": float(sum(arities) / max(len(arities), 1)),
            "types": dict(type_counts),
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class HypergraphEngine:
    """Constructs and queries a document hypergraph.

    The engine analyses element types, spatial proximity, and textual
    cross-references to build four families of hyperedges.  The resulting
    ``Hypergraph`` can then be used to propagate relevance scores across
    structurally linked elements.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        elements: List[GeometricElement],
        graph: Any = None,
    ) -> Hypergraph:
        """Build a ``Hypergraph`` from a flat list of document elements.

        The method detects four hyperedge families (table groups, figure
        groups, equation groups, and section groups) and assembles them
        into a single ``Hypergraph`` object.

        Parameters
        ----------
        elements:
            Flat list of all ``GeometricElement`` objects for the document.
        graph:
            Optional pre-built graph object (e.g. from ``GraphEngine``).
            Currently unused but reserved for future graph-guided grouping.

        Returns
        -------
        Hypergraph
            Populated hypergraph with all detected hyperedges.
        """
        hg = Hypergraph()
        counter = {"t": 0, "f": 0, "e": 0, "s": 0}

        for h in self._build_table_groups(elements, counter):
            hg.add(h)
        for h in self._build_figure_groups(elements, counter):
            hg.add(h)
        for h in self._build_equation_groups(elements, counter):
            hg.add(h)
        for h in self._build_section_groups(elements, counter):
            hg.add(h)

        stats = hg.statistics()
        log.info(
            "HypergraphEngine.build: %d nodes, %d hyperedges (%s)",
            stats["nodes"],
            stats["hyperedges"],
            stats["types"],
        )
        return hg

    def hypergraph_score(
        self, element: GeometricElement, seed_ids: Set[str]
    ) -> float:
        """Score an element's relevance based on hypergraph connectivity.

        Rules:
        * A *seed* element (directly relevant) gets score **1.0**.
        * Non-seed elements receive ``max(h.weight * 0.6)`` over all
          hyperedges that contain at least one seed node and the element
          itself.
        * Elements with no shared hyperedge with any seed receive **0.0**.

        Parameters
        ----------
        element:
            The element to score.
        seed_ids:
            Set of element IDs already deemed relevant (seeds).

        Returns
        -------
        float
            Relevance score in ``[0, 1]``.
        """
        eid = getattr(element, "element_id", None)
        if eid in seed_ids:
            return 1.0

        # Access the attached hypergraph if the element carries one;
        # otherwise fall back to 0.0 — callers should pass scored elements
        hg: Optional[Hypergraph] = getattr(element, "_hypergraph", None)
        if hg is None:
            return 0.0

        best = 0.0
        for h in hg.edges_of(eid or ""):
            if any(nid in seed_ids for nid in h.nodes):
                candidate = h.weight * 0.6
                if candidate > best:
                    best = candidate
        return float(best)

    # ------------------------------------------------------------------
    # Hyperedge builders — private
    # ------------------------------------------------------------------

    def _build_table_groups(
        self, elements: List[GeometricElement], counter: dict
    ) -> List[Hyperedge]:
        """Build TABLE + CAPTION + referencing PARAGRAPH hyperedges.

        A table group consists of:
        * Exactly one TABLE element (anchor).
        * Any CAPTION elements within ``_PROXIMITY_THRESHOLD`` vertically.
        * Any PARAGRAPH elements that mention keywords like *table* or
          *above* and lie within ``_PROXIMITY_THRESHOLD`` vertically.

        Parameters
        ----------
        elements:
            All document elements.
        counter:
            Shared mutable counter dict for generating unique IDs.

        Returns
        -------
        list[Hyperedge]
            One ``Hyperedge`` per TABLE element that has ≥ 1 neighbour.
        """
        tables = [e for e in elements if self._is_type(e, ElementType.TABLE)]
        result: List[Hyperedge] = []

        for tbl in tables:
            members: List[str] = [tbl.element_id]

            for other in elements:
                if other is tbl:
                    continue
                etype = self._get_type(other)
                vy = self._vy(
                    getattr(tbl, "bbox", None), getattr(other, "bbox", None)
                )
                if vy > _PROXIMITY_THRESHOLD:
                    continue

                if etype == ElementType.CAPTION:
                    members.append(other.element_id)
                elif etype == ElementType.PARAGRAPH:
                    text = (getattr(other, "text", "") or "").lower()
                    if any(kw in text for kw in _TABLE_KEYWORDS):
                        members.append(other.element_id)

            if len(members) >= 2:
                hid = f"tbl_{counter['t']}"
                counter["t"] += 1
                result.append(
                    Hyperedge(
                        hid=hid,
                        nodes=members,
                        type="table_group",
                        weight=_WEIGHTS["table_group"],
                        metadata={"anchor": tbl.element_id},
                    )
                )

        log.debug("_build_table_groups: %d hyperedges", len(result))
        return result

    def _build_figure_groups(
        self, elements: List[GeometricElement], counter: dict
    ) -> List[Hyperedge]:
        """Build FIGURE + CAPTION + surrounding TEXT hyperedges.

        A figure group consists of:
        * Exactly one FIGURE element (anchor).
        * Any CAPTION elements within ``_PROXIMITY_THRESHOLD`` vertically.
        * Any TEXT/PARAGRAPH elements within ``_PROXIMITY_THRESHOLD``
          that mention figure-related keywords.

        Parameters
        ----------
        elements:
            All document elements.
        counter:
            Shared mutable counter dict for generating unique IDs.

        Returns
        -------
        list[Hyperedge]
            One ``Hyperedge`` per FIGURE element that has ≥ 1 neighbour.
        """
        figures = [e for e in elements if self._is_type(e, ElementType.FIGURE)]
        result: List[Hyperedge] = []

        for fig in figures:
            members: List[str] = [fig.element_id]

            for other in elements:
                if other is fig:
                    continue
                etype = self._get_type(other)
                vy = self._vy(
                    getattr(fig, "bbox", None), getattr(other, "bbox", None)
                )
                if vy > _PROXIMITY_THRESHOLD:
                    continue

                if etype == ElementType.CAPTION:
                    members.append(other.element_id)
                elif etype in (ElementType.TEXT, ElementType.PARAGRAPH):
                    text = (getattr(other, "text", "") or "").lower()
                    if any(kw in text for kw in _FIGURE_KEYWORDS):
                        members.append(other.element_id)

            if len(members) >= 2:
                hid = f"fig_{counter['f']}"
                counter["f"] += 1
                result.append(
                    Hyperedge(
                        hid=hid,
                        nodes=members,
                        type="figure_group",
                        weight=_WEIGHTS["figure_group"],
                        metadata={"anchor": fig.element_id},
                    )
                )

        log.debug("_build_figure_groups: %d hyperedges", len(result))
        return result

    def _build_equation_groups(
        self, elements: List[GeometricElement], counter: dict
    ) -> List[Hyperedge]:
        """Build EQUATION + nearby TEXT hyperedges.

        An equation group consists of:
        * Exactly one EQUATION element (anchor).
        * Any TEXT/PARAGRAPH elements within ``_PROXIMITY_THRESHOLD``
          vertically.

        Parameters
        ----------
        elements:
            All document elements.
        counter:
            Shared mutable counter dict for generating unique IDs.

        Returns
        -------
        list[Hyperedge]
            One ``Hyperedge`` per EQUATION element that has ≥ 1 neighbour.
        """
        equations = [
            e for e in elements if self._is_type(e, ElementType.EQUATION)
        ]
        result: List[Hyperedge] = []

        for eq in equations:
            members: List[str] = [eq.element_id]

            for other in elements:
                if other is eq:
                    continue
                etype = self._get_type(other)
                vy = self._vy(
                    getattr(eq, "bbox", None), getattr(other, "bbox", None)
                )
                if vy > _PROXIMITY_THRESHOLD:
                    continue

                if etype in (ElementType.TEXT, ElementType.PARAGRAPH):
                    members.append(other.element_id)

            if len(members) >= 2:
                hid = f"eq_{counter['e']}"
                counter["e"] += 1
                result.append(
                    Hyperedge(
                        hid=hid,
                        nodes=members,
                        type="equation_group",
                        weight=_WEIGHTS["equation_group"],
                        metadata={"anchor": eq.element_id},
                    )
                )

        log.debug("_build_equation_groups: %d hyperedges", len(result))
        return result

    def _build_section_groups(
        self, elements: List[GeometricElement], counter: dict
    ) -> List[Hyperedge]:
        """Build section-level hyperedges grouping co-section elements.

        Elements are grouped by their ``section_id`` attribute.  Only
        groups with at least ``_MIN_SECTION_SIZE`` members form a
        hyperedge.

        Parameters
        ----------
        elements:
            All document elements.
        counter:
            Shared mutable counter dict for generating unique IDs.

        Returns
        -------
        list[Hyperedge]
            One ``Hyperedge`` per qualifying section.
        """
        by_section: defaultdict[str, List[str]] = defaultdict(list)
        for el in elements:
            sid = getattr(el, "section_id", None) or getattr(el, "section", None)
            if sid is not None:
                by_section[str(sid)].append(el.element_id)

        result: List[Hyperedge] = []
        for sid, member_ids in by_section.items():
            if len(member_ids) < _MIN_SECTION_SIZE:
                continue
            hid = f"sec_{counter['s']}"
            counter["s"] += 1
            result.append(
                Hyperedge(
                    hid=hid,
                    nodes=member_ids,
                    type="section_group",
                    weight=_WEIGHTS["section_group"],
                    metadata={"section_id": sid},
                )
            )

        log.debug("_build_section_groups: %d hyperedges", len(result))
        return result

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _vy(b1: Any, b2: Any) -> float:
        """Compute the normalised vertical gap between two bounding boxes.

        The gap is the minimum vertical distance between the two boxes,
        normalised to ``[0, ∞)`` in page-fraction units.  Overlapping or
        touching boxes return 0.0.  If either box is ``None`` the method
        returns ``∞`` so that the proximity check fails gracefully.

        Parameters
        ----------
        b1, b2:
            Bounding-box objects that expose ``.y0`` / ``.y1`` attributes
            or support positional indexing ``[1]`` / ``[3]``.

        Returns
        -------
        float
            Non-negative vertical gap, or ``float('inf')`` if unavailable.
        """
        if b1 is None or b2 is None:
            return float("inf")

        try:
            ay0 = float(getattr(b1, "y0", b1[1]))
            ay1 = float(getattr(b1, "y1", b1[3]))
            by0 = float(getattr(b2, "y0", b2[1]))
            by1 = float(getattr(b2, "y1", b2[3]))
        except (TypeError, IndexError, AttributeError):
            return float("inf")

        gap = max(0.0, max(ay0, by0) - min(ay1, by1))
        return gap

    # ------------------------------------------------------------------
    # Type helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_type(element: GeometricElement) -> Optional[ElementType]:
        """Safely retrieve the ``ElementType`` of an element."""
        etype = getattr(element, "element_type", None) or getattr(
            element, "type", None
        )
        if isinstance(etype, ElementType):
            return etype
        if isinstance(etype, str):
            try:
                return ElementType[etype.upper()]
            except KeyError:
                return None
        return None

    def _is_type(self, element: GeometricElement, target: ElementType) -> bool:
        """Return ``True`` if *element*'s type equals *target*."""
        return self._get_type(element) == target
