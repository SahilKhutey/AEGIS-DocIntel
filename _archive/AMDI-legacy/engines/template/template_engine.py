"""
AEGIS-AMDI — Template Engine (Layer 6)
========================================
Page fingerprinting + DBSCAN clustering.
T = { h, b, t, i, m }   (headers, blocks, tables, images, margins)

Identifies recurring page layouts and groups them into template families.
A batch of 200 identical invoices → 1 template stored + 200 page-delta refs.
"""
from __future__ import annotations

import hashlib
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from AMDI.engines.geometry.element import BoundingBox, Element, ElementType

log = logging.getLogger("amdi.template")

SIG_DIM = 20   # signature vector length


# ─────────────────────────────────────────────────────────────────
# Template Fingerprint
# ─────────────────────────────────────────────────────────────────

@dataclass
class PageTemplate:
    """
    T = { h, b, t, i, m }
    Fingerprint of a recurring page layout.
    """
    template_id:    str
    pages:          list[int]          = field(default_factory=list)
    cluster_size:   int                = 0
    n_headings:     int                = 0
    n_blocks:       int                = 0
    n_tables:       int                = 0
    n_figures:      int                = 0
    n_equations:    int                = 0
    margin_top:     float              = 0.0
    margin_bottom:  float              = 0.0
    margin_left:    float              = 0.0
    margin_right:   float              = 0.0
    avg_block_h:    float              = 0.0
    avg_cols:       float              = 1.0
    signature:      Optional[np.ndarray] = None

    @property
    def is_dominant(self) -> bool:
        return self.cluster_size >= 3

    def similarity(self, sig: np.ndarray) -> float:
        if self.signature is None:
            return 0.0
        a, b = np.asarray(self.signature), np.asarray(sig)
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
        return float(np.dot(a, b) / denom)

    def to_dict(self) -> dict:
        return {
            "template_id":  self.template_id,
            "cluster_size": self.cluster_size,
            "pages":        self.pages,
            "composition":  {"headings": self.n_headings, "blocks": self.n_blocks,
                             "tables": self.n_tables, "figures": self.n_figures},
            "margins":      {"top": round(self.margin_top, 3), "bottom": round(self.margin_bottom, 3),
                             "left": round(self.margin_left, 3), "right": round(self.margin_right, 3)},
        }


# ─────────────────────────────────────────────────────────────────
# Template Engine
# ─────────────────────────────────────────────────────────────────

class TemplateEngine:
    """
    Detects page-level layout families.

    Algorithm:
        1. Compute SIG_DIM-dimensional signature per page
        2. Hierarchical cosine clustering (no sklearn required)
        3. One PageTemplate per cluster → store once
        4. Template similarity for new-document matching

    Compression gain:
        N_identical_pages → 1 representative + N delta refs
    """

    def __init__(self, similarity_threshold: float = 0.92, min_cluster: int = 2):
        self.threshold    = similarity_threshold
        self.min_cluster  = min_cluster
        self.templates:   dict[str, PageTemplate] = {}
        self._page_to_tmpl: dict[int, str] = {}

    # ──────────────────────────────────────────────────────────────
    # Build from elements
    # ──────────────────────────────────────────────────────────────

    def build(self, elements: list[Element]) -> list[PageTemplate]:
        """Cluster all pages and build template library."""
        by_page: dict[int, list[Element]] = defaultdict(list)
        for e in elements:
            by_page[e.page].append(e)
        if not by_page:
            return []

        # Compute signatures
        page_sigs: list[tuple[int, np.ndarray]] = [
            (p, self._page_signature(es)) for p, es in sorted(by_page.items())
        ]

        # Greedy clustering (O(P²) — P ≤ 2000 pages is fine)
        clusters: list[list[int]]          = []
        cluster_sigs: list[np.ndarray]     = []
        page_cluster_map: dict[int, int]   = {}

        for (page, sig) in page_sigs:
            best_c, best_sim = -1, 0.0
            for ci, csig in enumerate(cluster_sigs):
                sim = self._cos_sim(sig, csig)
                if sim > best_sim:
                    best_sim, best_c = sim, ci
            if best_sim >= self.threshold:
                clusters[best_c].append(page)
                # Update centroid (online mean)
                n = len(clusters[best_c])
                cluster_sigs[best_c] = (cluster_sigs[best_c] * (n - 1) + sig) / n
                page_cluster_map[page] = best_c
            else:
                page_cluster_map[page] = len(clusters)
                clusters.append([page])
                cluster_sigs.append(sig.copy())

        # Build PageTemplate objects
        templates: list[PageTemplate] = []
        for ci, pages in enumerate(clusters):
            if len(pages) < self.min_cluster:
                continue
            rep_page   = pages[0]
            rep_elems  = by_page[rep_page]
            centroid   = cluster_sigs[ci]
            tmpl = self._build_template(ci, pages, rep_elems, centroid)
            self.templates[tmpl.template_id] = tmpl
            for p in pages:
                self._page_to_tmpl[p] = tmpl.template_id
            templates.append(tmpl)

        log.info(
            "TemplateEngine: %d pages → %d templates (%d dominant)",
            len(by_page), len(templates),
            sum(1 for t in templates if t.is_dominant),
        )
        return templates

    def page_template(self, page: int) -> Optional[PageTemplate]:
        tid = self._page_to_tmpl.get(page)
        return self.templates.get(tid) if tid else None

    # ──────────────────────────────────────────────────────────────
    # Score (T(q, e))
    # ──────────────────────────────────────────────────────────────

    def score(self, query_pages: Optional[list[int]], element: Element) -> float:
        """
        Template relevance score.
        If element is from a dominant template on a queried page → 0.2 (boilerplate)
        Otherwise → 0.8 (unique content)
        """
        tmpl = self.page_template(element.page)
        if tmpl is None:
            return 0.6   # no template info
        if tmpl.is_dominant and element.is_template:
            return 0.2   # boilerplate → de-prioritize
        if query_pages and element.page in query_pages:
            return 0.9   # exact page hit
        return 0.5

    # ──────────────────────────────────────────────────────────────
    # Cross-document matching
    # ──────────────────────────────────────────────────────────────

    def match_document(
        self,
        query_elements: list[Element],
        top_k: int = 3,
    ) -> list[tuple[PageTemplate, float]]:
        """Find templates matching a new document's pages."""
        if not self.templates:
            return []
        sig = self._page_signature(query_elements)
        scored = [(t, t.similarity(sig)) for t in self.templates.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ──────────────────────────────────────────────────────────────
    # Compression summary
    # ──────────────────────────────────────────────────────────────

    def compression_factor(self, total_pages: int) -> float:
        """Compression ratio achievable via template deduplication."""
        template_pages = sum(t.cluster_size for t in self.templates.values())
        if total_pages == 0:
            return 1.0
        unique_pages = total_pages - template_pages + len(self.templates)
        return unique_pages / total_pages

    def statistics(self) -> dict:
        sizes = [t.cluster_size for t in self.templates.values()]
        return {
            "templates":      len(self.templates),
            "dominant":       sum(1 for t in self.templates.values() if t.is_dominant),
            "max_cluster":    max(sizes) if sizes else 0,
            "avg_cluster":    round(float(np.mean(sizes)), 2) if sizes else 0,
            "pages_covered":  sum(sizes),
        }

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _page_signature(self, elems: list[Element]) -> np.ndarray:
        """
        Generate a SIG_DIM-dimensional signature for a page.
        Encodes element type ratios, margins, density, text uniformity.
        """
        n = max(1, len(elems))
        tc = Counter(e.type for e in elems)
        bboxes = [e.bbox for e in elems if e.bbox]

        if bboxes:
            mt  = min(b.y0 for b in bboxes)
            mb  = 1.0 - max(b.y1 for b in bboxes)
            ml  = min(b.x0 for b in bboxes)
            mr  = 1.0 - max(b.x1 for b in bboxes)
            ah  = float(np.mean([b.height for b in bboxes]))
            aw  = float(np.mean([b.width  for b in bboxes]))
            yd  = n / max(0.001, max(b.y1 for b in bboxes) - min(b.y0 for b in bboxes))
            col_sig = self._col_count(bboxes)
        else:
            mt = mb = ml = mr = ah = aw = yd = 0.0
            col_sig = 1.0

        # Text length uniformity
        lengths = [len(e.content) for e in elems]
        len_std = float(np.std(lengths)) / max(1, np.mean(lengths)) if lengths else 0.0

        sig = np.array([
            tc.get(ElementType.HEADING, 0)   / n,
            tc.get(ElementType.PARAGRAPH, 0) / n,
            tc.get(ElementType.TABLE, 0)     / n,
            tc.get(ElementType.FIGURE, 0)    / n,
            tc.get(ElementType.EQUATION, 0)  / n,
            tc.get(ElementType.LIST_ITEM, 0) / n,
            tc.get(ElementType.HEADER, 0)    / n,
            tc.get(ElementType.FOOTER, 0)    / n,
            mt, mb, ml, mr,
            ah, aw, yd,
            col_sig,
            len_std,
            float(n) / 100.0,
            tc.get(ElementType.TABLE, 0) * 3.0 / n,
            tc.get(ElementType.FIGURE, 0) * 2.0 / n,
        ], dtype=np.float32)
        nrm = np.linalg.norm(sig)
        return sig / nrm if nrm > 0 else sig

    @staticmethod
    def _col_count(bboxes: list[BoundingBox]) -> float:
        """Estimate number of text columns from x-coordinate clustering."""
        xs = [b.x0 for b in bboxes]
        if len(xs) < 4:
            return 1.0
        xs_sorted = sorted(xs)
        gaps = [xs_sorted[i+1] - xs_sorted[i] for i in range(len(xs_sorted)-1)]
        big_gaps = sum(1 for g in gaps if g > 0.2)
        return float(1 + big_gaps)

    @staticmethod
    def _cos_sim(a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
        return float(np.dot(a, b) / denom)

    def _build_template(
        self,
        cluster_id:  int,
        pages:       list[int],
        rep_elements: list[Element],
        centroid:    np.ndarray,
    ) -> PageTemplate:
        tc     = Counter(e.type for e in rep_elements)
        bboxes = [e.bbox for e in rep_elements if e.bbox]
        mt = min((b.y0 for b in bboxes), default=0.0)
        mb = 1.0 - max((b.y1 for b in bboxes), default=0.0)
        ml = min((b.x0 for b in bboxes), default=0.0)
        mr = 1.0 - max((b.x1 for b in bboxes), default=0.0)
        ah = float(np.mean([b.height for b in bboxes])) if bboxes else 0.0

        tid = "T" + hashlib.sha256(centroid.tobytes()).hexdigest()[:8]
        return PageTemplate(
            template_id   = tid,
            pages         = list(sorted(pages)),
            cluster_size  = len(pages),
            n_headings    = tc.get(ElementType.HEADING, 0),
            n_blocks      = len(rep_elements),
            n_tables      = tc.get(ElementType.TABLE, 0),
            n_figures     = tc.get(ElementType.FIGURE, 0),
            n_equations   = tc.get(ElementType.EQUATION, 0),
            margin_top    = round(mt, 3),
            margin_bottom = round(mb, 3),
            margin_left   = round(ml, 3),
            margin_right  = round(mr, 3),
            avg_block_h   = round(ah, 3),
            signature     = centroid,
        )
