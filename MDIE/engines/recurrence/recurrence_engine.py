"""
AEGIS-MDIE — Recurrence Engine
================================
R_n = R_0 for n > 0
Detects, clusters, and compresses repeating document elements.
"""
from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from MDIE.engines.geometry.element import GeometricElement

log = logging.getLogger("mdie.recurrence")


# ─────────────────────────────────────────────────────────────────
# Recurrence Group
# ─────────────────────────────────────────────────────────────────

@dataclass
class RecurrenceGroup:
    """
    R_n = R_0 — cluster of geometrically & semantically equivalent elements.

    Stores ONE representative, references all members.
    """
    recurrence_id:    str
    representative:   GeometricElement
    members:          list[str]   = field(default_factory=list)  # element_ids
    page_set:         set[int]    = field(default_factory=set)
    text_hash:        str         = ""
    spatial_sig:      np.ndarray | None = None
    element_type:     str         = ""

    @property
    def count(self) -> int:
        return len(self.members)

    @property
    def is_template(self) -> bool:
        """True if element repeats ≥ 3 times — classified as template pattern."""
        return self.count >= 3

    @property
    def is_structural(self) -> bool:
        """True if it's a header/footer/page-number pattern."""
        return self.element_type in ("header", "footer")

    def tokens_saved(self, tokens_per_element: int = 20) -> int:
        """Token savings vs storing every instance."""
        return max(0, (self.count - 1) * tokens_per_element)

    def compression_ratio(self) -> float:
        """Fraction of original storage this group uses."""
        return 1.0 / max(1, self.count)

    def to_dict(self) -> dict:
        return {
            "id":          self.recurrence_id,
            "count":       self.count,
            "pages":       sorted(self.page_set),
            "is_template": self.is_template,
            "type":        self.element_type,
            "sample":      self.representative.content[:120],
        }


# ─────────────────────────────────────────────────────────────────
# Recurrence Engine
# ─────────────────────────────────────────────────────────────────

class RecurrenceEngine:
    """
    Detects R_n = R_0 patterns.

    Matching strategy (two-phase):
        1. Exact hash match: fast O(1) lookup
        2. Spatial + Jaccard similarity for near-duplicates

    Use-cases:
        - Page headers/footers (identical text, same position every page)
        - Repeated invoice line-item rows
        - Section separators / watermarks
        - Boilerplate paragraphs
        - Duplicate table rows
    """

    def __init__(
        self,
        spatial_tolerance: float = 0.04,   # normalized coords
        text_jaccard_threshold: float = 0.92,
    ):
        self.spatial_tol  = spatial_tolerance
        self.jaccard_thr  = text_jaccard_threshold

        self.groups:         dict[str, RecurrenceGroup] = {}   # gid → group
        self._elem_to_group: dict[str, str]             = {}   # eid → gid
        self._hash_index:    dict[str, str]             = {}   # text_hash → gid

    # ──────────────────────────────────────────────────────────────
    # Main detection
    # ──────────────────────────────────────────────────────────────

    def detect(self, elements: Iterable[GeometricElement]) -> list[RecurrenceGroup]:
        """Process all elements and return recurrence groups."""
        for e in elements:
            self._process(e)
        # Back-fill frequency counts
        for e_id, gid in self._elem_to_group.items():
            # We don't have a direct ref here; freq is on the group
            pass
        log.info(
            "Recurrence detection complete: %d groups, %d templates",
            len(self.groups),
            sum(1 for g in self.groups.values() if g.is_template),
        )
        return list(self.groups.values())

    def _process(self, e: GeometricElement) -> None:
        text_hash = self._hash(e.content)
        spatial   = self._spatial_sig(e)

        # Phase 1: exact hash lookup
        if text_hash in self._hash_index:
            gid   = self._hash_index[text_hash]
            group = self.groups[gid]
            if group.element_type == e.type.value:
                self._join_group(e, gid)
                return

        # Phase 2: spatial + Jaccard scan
        for gid, group in self.groups.items():
            if group.element_type != e.type.value:
                continue
            if not self._spatial_close(group.spatial_sig, spatial):
                continue
            if not self._text_close(group.representative.content, e.content):
                continue
            self._join_group(e, gid)
            return

        # New group
        self._new_group(e, text_hash, spatial)

    def _new_group(
        self,
        e: GeometricElement,
        text_hash: str,
        spatial: np.ndarray,
    ) -> None:
        gid = f"rec-{len(self.groups):05d}"
        group = RecurrenceGroup(
            recurrence_id=gid,
            representative=e,
            members=[e.element_id],
            page_set={e.page},
            text_hash=text_hash,
            spatial_sig=spatial,
            element_type=e.type.value,
        )
        self.groups[gid]           = group
        self._elem_to_group[e.element_id] = gid
        self._hash_index[text_hash] = gid
        e.recurrence_id = gid
        e.frequency     = 1

    def _join_group(self, e: GeometricElement, gid: str) -> None:
        group = self.groups[gid]
        group.members.append(e.element_id)
        group.page_set.add(e.page)
        self._elem_to_group[e.element_id] = gid
        e.recurrence_id            = gid
        e.frequency                = group.count
        e.is_template_element      = group.is_template

    # ──────────────────────────────────────────────────────────────
    # Compressed representation
    # ──────────────────────────────────────────────────────────────

    def compress(self, elements: list[GeometricElement]) -> dict:
        """
        D = { T, R_n, Δ }  — template + recurrence + unique deltas.

        Returns:
            {
              "templates": [element_id, ...],      # representatives
              "recurrences": {gid: [pages, ...]},   # where each template appears
              "uniques": [element_id, ...],          # non-repeating content
              "stats": {...}
            }
        """
        templates   = []
        recurrences = {}
        uniques     = []
        seen_groups: set[str] = set()

        for e in elements:
            gid = self._elem_to_group.get(e.element_id)
            if gid is None:
                uniques.append(e.element_id)
                continue
            group = self.groups[gid]
            if group.is_template:
                if gid not in seen_groups:
                    seen_groups.add(gid)
                    templates.append(e.element_id)
                    recurrences[gid] = sorted(group.page_set)
                # members beyond representative are implicitly recovered
            else:
                uniques.append(e.element_id)

        total_stored   = len(templates) + len(uniques)
        total_original = len(elements)
        ratio = total_stored / max(1, total_original)

        log.info(
            "Compression: %d → %d elements (%.1f%% reduction)",
            total_original, total_stored, (1 - ratio) * 100,
        )
        return {
            "templates":   templates,
            "recurrences": recurrences,
            "uniques":     uniques,
            "stats": {
                "original":    total_original,
                "compressed":  total_stored,
                "ratio":       round(ratio, 3),
                "savings_pct": round((1 - ratio) * 100, 1),
            },
        }

    def group_of(self, element_id: str) -> RecurrenceGroup | None:
        gid = self._elem_to_group.get(element_id)
        return self.groups.get(gid) if gid else None

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(text: str) -> str:
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:20]

    @staticmethod
    def _spatial_sig(e: GeometricElement) -> np.ndarray:
        if not e.bbox:
            return np.zeros(4, dtype=np.float32)
        return np.array(
            [round(e.bbox.x0, 2), round(e.bbox.y0, 2),
             round(e.bbox.width, 2), round(e.bbox.height, 2)],
            dtype=np.float32,
        )

    def _spatial_close(self, a: np.ndarray | None, b: np.ndarray | None) -> bool:
        if a is None or b is None:
            return False
        return float(np.max(np.abs(a - b))) <= self.spatial_tol

    def _text_close(self, a: str, b: str) -> bool:
        an = " ".join(a.lower().split())
        bn = " ".join(b.lower().split())
        if an == bn:
            return True
        sa, sb = set(an.split()), set(bn.split())
        if not sa or not sb:
            return False
        return len(sa & sb) / len(sa | sb) >= self.jaccard_thr

    # ──────────────────────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────────────────────

    def statistics(self) -> dict:
        total_elem  = sum(g.count for g in self.groups.values())
        n_groups    = len(self.groups)
        n_templates = sum(1 for g in self.groups.values() if g.is_template)
        tokens_saved = sum(g.tokens_saved() for g in self.groups.values() if g.is_template)
        return {
            "total_elements":   total_elem,
            "unique_groups":    n_groups,
            "template_groups":  n_templates,
            "avg_group_size":   round(total_elem / max(1, n_groups), 2),
            "tokens_saved_est": tokens_saved,
            "largest_group":    max((g.count for g in self.groups.values()), default=0),
        }
