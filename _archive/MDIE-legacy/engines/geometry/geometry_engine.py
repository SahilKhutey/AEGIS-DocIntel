"""
AEGIS-MDIE — Geometry Engine
==============================
Spatial index, coordinate normalization, page signatures.
e_i = (x_i, y_i, w_i, h_i, p_i, t_i, c_i)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Iterable

import numpy as np

from MDIE.engines.geometry.element import BoundingBox, ElementType, GeometricElement

log = logging.getLogger("mdie.geometry")


class GeometryEngine:
    """
    Spatial index over all document elements.

    Indexing:
        _by_page[p]    = [element_ids on page p]
        _by_type[t]    = [element_ids of type t]
        _by_section[s] = [element_ids in section s]

    Queries:
        - Region overlap (IoU)
        - Above / Below / Left-Right
        - Page spatial signature (for template detection)
        - Reading-order sort (y-first, then x)
    """

    def __init__(self):
        self.elements:    dict[str, GeometricElement] = {}
        self._by_page:    dict[int, list[str]]        = defaultdict(list)
        self._by_type:    dict[ElementType, list[str]]= defaultdict(list)
        self._by_section: dict[str, list[str]]        = defaultdict(list)
        self._page_dims:  dict[int, tuple[float, float]] = {}   # page → (W, H)

    # ──────────────────────────────────────────────────────────────
    # Insertion
    # ──────────────────────────────────────────────────────────────

    def add(self, e: GeometricElement) -> None:
        self.elements[e.element_id] = e
        self._by_page[e.page].append(e.element_id)
        self._by_type[e.type].append(e.element_id)
        if e.section:
            self._by_section[e.section].append(e.element_id)

    def add_many(self, elements: Iterable[GeometricElement]) -> None:
        for e in elements:
            self.add(e)

    # ──────────────────────────────────────────────────────────────
    # Coordinate normalization
    # ──────────────────────────────────────────────────────────────

    def register_page_dimensions(self, page: int, width: float, height: float) -> None:
        self._page_dims[page] = (width, height)

    def normalize_page(self, page: int) -> None:
        """Normalize coordinates on page to [0, 1] — scale-invariant."""
        if page not in self._page_dims:
            return
        pw, ph = self._page_dims[page]
        for eid in self._by_page[page]:
            e = self.elements[eid]
            if e.bbox is None:
                continue
            e.metadata.setdefault("raw_bbox", e.bbox.to_tuple())
            e.bbox = e.bbox.to_normalized(pw, ph)
        log.debug("Normalized page %d (%d elements)", page, len(self._by_page[page]))

    # ──────────────────────────────────────────────────────────────
    # Reading-order sort
    # ──────────────────────────────────────────────────────────────

    def reading_order(self, page: int) -> list[GeometricElement]:
        """Sort elements on a page in natural reading order (top→bottom, left→right)."""
        elems = [self.elements[eid] for eid in self._by_page[page]]
        return sorted(
            elems,
            key=lambda e: (
                e.bbox.y0 if e.bbox else 0,
                e.bbox.x0 if e.bbox else 0,
            ),
        )

    def all_in_reading_order(self) -> list[GeometricElement]:
        out: list[GeometricElement] = []
        for page in sorted(self._by_page.keys()):
            out.extend(self.reading_order(page))
        return out

    # ──────────────────────────────────────────────────────────────
    # Spatial queries
    # ──────────────────────────────────────────────────────────────

    def elements_in_region(
        self,
        page: int,
        bbox: BoundingBox,
        iou_threshold: float = 0.01,
    ) -> list[GeometricElement]:
        return [
            self.elements[eid]
            for eid in self._by_page[page]
            if self.elements[eid].bbox is not None
            and self.elements[eid].bbox.iou(bbox) >= iou_threshold
        ]

    def elements_above(self, e: GeometricElement, k: int = 3) -> list[GeometricElement]:
        if not e.bbox:
            return []
        peers = [self.elements[eid] for eid in self._by_page[e.page]
                 if eid != e.element_id and self.elements[eid].bbox]
        above = [p for p in peers if p.bbox.y1 <= e.bbox.y0]
        above.sort(key=lambda p: e.bbox.y0 - p.bbox.y1)
        return above[:k]

    def elements_below(self, e: GeometricElement, k: int = 3) -> list[GeometricElement]:
        if not e.bbox:
            return []
        peers = [self.elements[eid] for eid in self._by_page[e.page]
                 if eid != e.element_id and self.elements[eid].bbox]
        below = [p for p in peers if p.bbox.y0 >= e.bbox.y1]
        below.sort(key=lambda p: p.bbox.y0 - e.bbox.y1)
        return below[:k]

    def elements_same_column(
        self, e: GeometricElement, x_tolerance: float = 0.05
    ) -> list[GeometricElement]:
        """Elements vertically aligned with e (multi-column detection)."""
        if not e.bbox:
            return []
        cx = e.bbox.center[0]
        return [
            self.elements[eid]
            for eid in self._by_page[e.page]
            if eid != e.element_id
            and self.elements[eid].bbox is not None
            and abs(self.elements[eid].bbox.center[0] - cx) <= x_tolerance
        ]

    # ──────────────────────────────────────────────────────────────
    # Page spatial signature (for template detection)
    # ──────────────────────────────────────────────────────────────

    def page_signature(self, page: int, dim: int = 32) -> np.ndarray:
        """
        32-D spatial signature for a page.
        Used for template matching via cosine similarity.
        """
        elems = [
            self.elements[eid] for eid in self._by_page[page]
            if self.elements[eid].bbox is not None
            and self.elements[eid].type not in (ElementType.HEADER, ElementType.FOOTER)
        ]
        sig = np.zeros(dim, dtype=np.float32)
        if not elems:
            return sig

        total = len(elems)
        type_map = {t: i for i, t in enumerate(ElementType)}

        # Slots 0–11: element type frequency histogram (normalized)
        for e in elems:
            idx = type_map.get(e.type, 0)
            if idx < 12:
                sig[idx] += 1.0 / total

        # Slots 12–19: y-position histogram (8 bins over [0,1])
        ys = [e.bbox.y0 for e in elems]
        hist, _ = np.histogram(ys, bins=8, range=(0.0, 1.0))
        sig[12:20] = hist / max(1.0, hist.sum())

        # Slots 20–25: width/height statistics
        widths  = np.array([e.bbox.width  for e in elems])
        heights = np.array([e.bbox.height for e in elems])
        sig[20] = np.mean(widths);  sig[21] = np.std(widths)
        sig[22] = np.mean(heights); sig[23] = np.std(heights)

        # Slots 24–27: specific counts
        sig[24] = sum(1 for e in elems if e.type == ElementType.TABLE)   / total
        sig[25] = sum(1 for e in elems if e.type == ElementType.FIGURE)  / total
        sig[26] = sum(1 for e in elems if e.type == ElementType.EQUATION)/ total
        sig[27] = total / 50.0   # density (normalized)

        # Slots 28–31: x-spread statistics
        xs = np.array([e.bbox.x0 for e in elems])
        sig[28] = np.mean(xs); sig[29] = np.std(xs)
        sig[30] = np.min(xs);  sig[31] = np.max(xs)

        n = np.linalg.norm(sig)
        return sig / n if n > 0 else sig

    # ──────────────────────────────────────────────────────────────
    # Geometry score for retrieval  G(q, e)
    # ──────────────────────────────────────────────────────────────

    def geometry_relevance(
        self,
        query_pages: list[int] | None,
        element: GeometricElement,
        section_hint: str | None = None,
    ) -> float:
        """
        G(q, e) ∈ [0, 1] — geometric match signal.
        Higher = element is in a position relevant to the query.
        """
        score = 0.5  # baseline

        # Page proximity
        if query_pages:
            min_dist = min(abs(element.page - p) for p in query_pages)
            score += max(0.0, 0.3 - 0.05 * min_dist)

        # Section match
        if section_hint and element.section:
            if section_hint.lower() in element.section.lower():
                score += 0.2

        # Type bonus: headings and tables are geometrically salient
        if element.type in (ElementType.HEADING, ElementType.TABLE, ElementType.EQUATION):
            score += 0.15
        if element.type in (ElementType.HEADER, ElementType.FOOTER):
            score -= 0.3

        return max(0.0, min(1.0, score))

    # ──────────────────────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "total_elements": len(self.elements),
            "pages":          len(self._by_page),
            "types":          {t.value: len(ids) for t, ids in self._by_type.items()},
            "sections":       len(self._by_section),
        }
