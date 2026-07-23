"""
AEGIS-AMDI-OS — Recurrence Engine
====================================
R_n = R_{n-1}

Detects repeated structures for compression:
- Headers (top of pages)
- Footers (bottom of pages)
- Logos (small images at fixed positions)
- Tables (similar structure across pages)
- Duplicate text blocks

Storage: O(|R_0| + n · log(p_max))
Compression ratio: 1/n + O(log(p_max)/|R_0|)

Theorems:
- 9.1 (Compression): For n repeats, storage ≈ 1/n of naive
"""
from __future__ import annotations

import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.engines.geometry.element import ElementType, GeometricElement, BoundingBox

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# MinHash (zero-dependency implementation for backward compatibility)
# ─────────────────────────────────────────────────────────────────

class MinHasher:
    """Lightweight MinHash for approximate near-duplicate detection."""

    def __init__(self, n_perm: int = 64, seed: int = 42):
        rng = np.random.default_rng(seed)
        self._a = rng.integers(1, (1 << 31) - 1, size=n_perm, dtype=np.int64)
        self._b = rng.integers(0, (1 << 31) - 1, size=n_perm, dtype=np.int64)
        self._p = (1 << 31) - 1
        self.n_perm = n_perm

    def signature(self, tokens: set[str]) -> np.ndarray:
        sig = np.full(self.n_perm, np.iinfo(np.int64).max, dtype=np.int64)
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16) & 0x7FFFFFFF
            vals = (self._a * h + self._b) % self._p
            sig = np.minimum(sig, vals)
        return sig

    def jaccard_estimate(self, s1: np.ndarray, s2: np.ndarray) -> float:
        return float(np.mean(s1 == s2))


# ─────────────────────────────────────────────────────────────────
# Recurrence Group
# ─────────────────────────────────────────────────────────────────

@dataclass
class RecurrenceGroup:
    """
    R_n = R_0

    A group of equivalent elements detected across the document.
    """
    recurrence_id: str
    representative: GeometricElement
    members: list[str] = field(default_factory=list)  # element_ids
    page_set: set[int] = field(default_factory=set)
    group_type: str = "general"  # header, footer, logo, table, duplicate

    # For legacy compatibility properties
    @property
    def group_id(self) -> str:
        return self.recurrence_id

    @property
    def type(self) -> str:
        return self.group_type

    @property
    def count(self) -> int:
        return len(self.members)

    @property
    def is_template(self) -> bool:
        """Appears 3+ times → significant template."""
        return self.count >= 3

    @property
    def is_dominant(self) -> bool:
        """Appears 5+ times → dominant template."""
        return self.count >= 5

    @property
    def pages(self) -> list[int]:
        return sorted(self.page_set)

    def compression_ratio(self) -> float:
        """
        Compression ratio for storing this group:
        CR = 1/n (where n is the group count)

        For n=3: CR=0.33 (3x compression)
        For n=10: CR=0.10 (10x compression)
        """
        return 1.0 / max(1, self.count)

    def to_dict(self) -> dict:
        return {
            "recurrence_id": self.recurrence_id,
            "group_type": self.group_type,
            "count": self.count,
            "pages": self.pages,
            "is_template": self.is_template,
            "is_dominant": self.is_dominant,
            "compression_ratio": self.compression_ratio(),
            "representative_content": self.representative.content[:100],
        }


# ─────────────────────────────────────────────────────────────────
# Recurrence Group List (legacy compatibility wrapper)
# ─────────────────────────────────────────────────────────────────

class RecurrenceGroupList(list):
    """
    Backward-compatible subclass of list representing RecurrenceMap.
    """
    def __init__(self, groups: list[RecurrenceGroup], template_ids: set[str]):
        super().__init__(groups)
        self.groups = self
        self.template_ids = template_ids

    def statistics(self) -> dict:
        return {
            "groups":          len(self.groups),
            "template_count":  len(self.template_ids),
            "largest_group":   max((g.count for g in self.groups), default=0),
            "avg_group_size":  round(
                sum(g.count for g in self.groups) / max(1, len(self.groups)), 1
            ),
        }


@dataclass
class RecurrenceStats:
    """Statistics about recurrence analysis."""
    n_elements: int = 0
    n_groups: int = 0
    n_template_groups: int = 0
    n_dominant_groups: int = 0
    total_compression_ratio: float = 1.0
    avg_frequency: float = 1.0
    max_frequency: int = 1
    group_types: dict[str, int] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# Recurrence Engine
# ─────────────────────────────────────────────────────────────────

class RecurrenceEngine:
    """
    Phase 08: Recurrence Engine.

    Detects repeated structures:
    - Headers and footers (top/bottom of pages)
    - Logos (small images at fixed positions)
    - Tables (similar structure)
    - Duplicate text blocks
    - Generic recurrence

    All detected groups enable compression via R_n = R_0.
    """

    # Thresholds
    HEADER_Y_THRESHOLD = 0.08  # Top 8% of page
    FOOTER_Y_THRESHOLD = 0.92  # Bottom 8% of page
    LOGO_MAX_AREA = 0.05  # 5% of page
    TABLE_MIN_ROWS = 3
    DUPLICATE_MIN_COUNT = 2

    # Legacy Compatibility Thresholds
    HEADER_Y_MAX  = 0.08
    FOOTER_Y_MIN  = 0.92
    MIN_GROUP     = 2          # minimum size to call it a recurrence
    NEAR_DUP_THR  = 0.80       # MinHash Jaccard threshold

    def __init__(self, spatial_tolerance: float = 0.05, hash_precision: int = 16, n_perm: int = 64, near_dup_threshold: float = 0.80):
        self.spatial_tol = spatial_tolerance
        self.hash_precision = hash_precision
        self.groups: dict[str, RecurrenceGroup] = {}
        self._element_to_group: dict[str, str] = {}
        self._text_hash_index: dict[str, str] = {}

        # Legacy
        self.n_perm = n_perm
        self.near_dup_threshold = near_dup_threshold
        self._hasher = MinHasher(n_perm=n_perm)
        self._rec_map = RecurrenceGroupList([], set())

    # ============================================================
    # MAIN DETECTION
    # ============================================================

    def detect(self, elements: list[GeometricElement]) -> RecurrenceGroupList:
        """
        Detect all types of recurrence.

        Returns list-like RecurrenceGroupList of RecurrenceGroup objects.
        """
        self.groups = {}
        self._element_to_group = {}
        self._text_hash_index = {}

        # Clear old recurrence fields on input elements
        for e in elements:
            e.recurrence_id = None
            e.is_template = False

        # Run all detection methods
        self._detect_headers(elements)
        self._detect_footers(elements)
        self._detect_logos(elements)
        self._detect_tables(elements)
        self._detect_duplicates(elements)
        self._detect_generic(elements)

        # Clean up any "general" groups that ended up with only 1 member
        to_delete = [gid for gid, g in self.groups.items() if g.group_type == "general" and g.count == 1]
        for gid in to_delete:
            group = self.groups.pop(gid)
            for eid in group.members:
                self._element_to_group.pop(eid, None)
                for e in elements:
                    if e.element_id == eid:
                        e.recurrence_id = None
                        e.frequency = 1
                        e.is_template = False
                        break

        # Build template_ids set for backward compatibility
        template_ids = set()

        # Update element attributes
        for eid, gid in self._element_to_group.items():
            group = self.groups[gid]
            for e in elements:
                if e.element_id == eid:
                    e.recurrence_id = gid
                    e.frequency = group.count
                    e.is_template = group.is_template
                    if group.is_template:
                        template_ids.add(e.element_id)
                    break

        # Additional legacy positional template marking:
        # Elements positioned in the header/footer areas or marked as header/footer type
        # are flagged as template elements.
        for e in elements:
            if e.type in (ElementType.HEADER, ElementType.FOOTER):
                e.is_template = True
                template_ids.add(e.element_id)
                continue
            if e.bbox:
                cy = (e.bbox.y0 + e.bbox.y1) / 2
                if cy < self.HEADER_Y_MAX or cy > self.FOOTER_Y_MIN:
                    e.is_template = True
                    template_ids.add(e.element_id)

        self._rec_map = RecurrenceGroupList(list(self.groups.values()), template_ids)
        return self._rec_map

    # ============================================================
    # 1. HEADER DETECTION
    # ============================================================

    def _detect_headers(self, elements: list[GeometricElement]) -> None:
        """
        Detect headers (top of pages, similar content/position).
        """
        header_candidates = [
            e for e in elements
            if e.bbox and min(e.bbox.y0, e.bbox.y1) < self.HEADER_Y_THRESHOLD
            and e.type in (ElementType.HEADER, ElementType.HEADING, ElementType.TITLE, ElementType.TEXT)
        ]
        # Group by content similarity
        for e in header_candidates:
            self._try_add_to_group(e, group_type="header")

    # ============================================================
    # 2. FOOTER DETECTION
    # ============================================================

    def _detect_footers(self, elements: list[GeometricElement]) -> None:
        """
        Detect footers (bottom of pages, similar content/position).
        """
        footer_candidates = [
            e for e in elements
            if e.bbox and max(e.bbox.y0, e.bbox.y1) > self.FOOTER_Y_THRESHOLD
            and e.type in (ElementType.FOOTER, ElementType.TEXT, ElementType.CAPTION)
        ]
        for e in footer_candidates:
            self._try_add_to_group(e, group_type="footer")

    # ============================================================
    # 3. LOGO DETECTION
    # ============================================================

    def _detect_logos(self, elements: list[GeometricElement]) -> None:
        """
        Detect logos (small images at fixed positions, typically top-left).

        Criteria:
        - Type = FIGURE
        - Small area (< LOGO_MAX_AREA)
        - At consistent position (top-left corner typically)
        - Appears on multiple pages
        """
        logo_candidates = [
            e for e in elements
            if e.type == ElementType.FIGURE
            and e.bbox
            and (e.bbox.width * e.bbox.height) < self.LOGO_MAX_AREA
        ]
        for e in logo_candidates:
            self._try_add_to_group(e, group_type="logo")

    # ============================================================
    # 4. TABLE DETECTION
    # ============================================================

    def _detect_tables(self, elements: list[GeometricElement]) -> None:
        """
        Detect tables with similar structure across pages.

        Strategy:
        - Find all TABLE elements
        - Group by structural signature (column count, headers)
        """
        table_candidates = [
            e for e in elements if e.type == ElementType.TABLE
        ]
        # Build structure hash for each table
        for e in table_candidates:
            # Use first few rows as structure signature
            structure = self._extract_table_structure(e)
            if structure:
                e.metadata["table_structure"] = structure
                self._try_add_to_group(
                    e, group_type="table",
                    dedup_key=f"table_{structure}",
                )

    def _extract_table_structure(self, element: GeometricElement) -> str:
        """Extract structural signature from table content."""
        if not element.content:
            return ""
        lines = element.content.split("\n")[:3]  # First 3 rows
        # Count columns (number of | characters)
        col_count = max(line.count("|") for line in lines)
        # Use first row as signature
        first_row = lines[0] if lines else ""
        return f"{col_count}_{hashlib.md5(first_row.encode()).hexdigest()[:8]}"

    # ============================================================
    # 5. DUPLICATE DETECTION
    # ============================================================

    def _detect_duplicates(self, elements: list[GeometricElement]) -> None:
        """
        Detect exact or near-duplicate text blocks.
        """
        # Build text hash index
        hash_to_elements: dict[str, list[GeometricElement]] = defaultdict(list)
        for e in elements:
            if e.element_id in self._element_to_group:
                continue
            if not e.content:
                continue
            text_hash = self._hash_text(e.content)
            hash_to_elements[text_hash].append(e)

        # Add groups for elements appearing 2+ times
        for text_hash, dupes in hash_to_elements.items():
            if len(dupes) >= self.DUPLICATE_MIN_COUNT:
                representative = dupes[0]
                gid = self._next_id("duplicate")
                self.groups[gid] = RecurrenceGroup(
                    recurrence_id=gid,
                    representative=representative,
                    members=[e.element_id for e in dupes],
                    page_set={e.page for e in dupes},
                    group_type="duplicate",
                )
                for e in dupes:
                    self._element_to_group[e.element_id] = gid

    # ============================================================
    # 6. GENERIC RECURRENCE (fallback)
    # ============================================================

    def _detect_generic(self, elements: list[GeometricElement]) -> None:
        """
        Detect any remaining recurrence by content similarity.

        For elements not already in a group with same type and similar position.
        """
        for e in elements:
            if e.element_id in self._element_to_group:
                continue  # Already in a group
            if not e.content:
                continue
            self._try_add_to_group(e, group_type="general")

    # ============================================================
    # GROUP MANAGEMENT
    # ============================================================

    def _try_add_to_group(
        self,
        element: GeometricElement,
        group_type: str = "general",
        dedup_key: str = "",
    ) -> None:
        """Try to add element to an existing group or create new one."""
        # Use dedup_key if provided, else hash text
        if dedup_key:
            key = dedup_key
        else:
            key = self._hash_text(element.content)

        text_hash = self._hash_text(element.content)

        # Check if matches an existing group of same type
        for gid, group in self.groups.items():
            if group.group_type != group_type:
                continue
            # For typed groups, also check spatial similarity
            if group_type in ("header", "footer", "logo"):
                if not self._spatial_close(group.representative, element):
                    continue

            # Match condition
            matched = False
            if group_type == "table":
                # Compare table structure signature
                rep_struct = self._extract_table_structure(group.representative)
                elem_struct = self._extract_table_structure(element)
                if rep_struct and rep_struct == elem_struct:
                    matched = True
            else:
                if self._hash_text(group.representative.content) == text_hash:
                    matched = True

            if matched:
                group.members.append(element.element_id)
                group.page_set.add(element.page)
                self._element_to_group[element.element_id] = gid
                element.recurrence_id = gid
                element.frequency = group.count
                return

        # Create new group
        gid = self._next_id(group_type)
        self.groups[gid] = RecurrenceGroup(
            recurrence_id=gid,
            representative=element,
            members=[element.element_id],
            page_set={element.page},
            group_type=group_type,
        )
        self._element_to_group[element.element_id] = gid
        element.recurrence_id = gid

    def _next_id(self, prefix: str) -> str:
        """Generate next group ID."""
        return f"{prefix}-{len([g for g in self.groups.values() if g.group_type == prefix]) + 1}"

    # ============================================================
    # SPATIAL / HASHING HELPERS
    # ============================================================

    def _spatial_close(self, a: GeometricElement, b: GeometricElement) -> bool:
        """Check if two elements are at similar positions."""
        if a.bbox is None or b.bbox is None:
            return False
        return (
            abs(a.bbox.x0 - b.bbox.x0) < self.spatial_tol
            and abs(a.bbox.y0 - b.bbox.y0) < self.spatial_tol
        )

    def _hash_text(self, text: str) -> str:
        """Generate hash for text content."""
        if not text:
            return ""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:self.hash_precision]

    # ============================================================
    # QUERIES
    # ============================================================

    def get_group(self, recurrence_id: str) -> RecurrenceGroup | None:
        """Get group by ID."""
        return self.groups.get(recurrence_id)

    def get_group_for_element(self, element_id: str) -> RecurrenceGroup | None:
        """Get group containing a specific element."""
        gid = self._element_to_group.get(element_id)
        if gid:
            return self.groups.get(gid)
        return None

    def get_groups_by_type(self, group_type: str) -> list[RecurrenceGroup]:
        """Get all groups of a specific type."""
        return [g for g in self.groups.values() if g.group_type == group_type]

    def get_headers(self) -> list[RecurrenceGroup]:
        """Get all header groups."""
        return self.get_groups_by_type("header")

    def get_footers(self) -> list[RecurrenceGroup]:
        """Get all footer groups."""
        return self.get_groups_by_type("footer")

    def get_logos(self) -> list[RecurrenceGroup]:
        """Get all logo groups."""
        return self.get_groups_by_type("logo")

    def get_tables(self) -> list[RecurrenceGroup]:
        """Get all table groups."""
        return self.get_groups_by_type("table")

    def get_duplicates(self) -> list[RecurrenceGroup]:
        """Get all duplicate groups."""
        return self.get_groups_by_type("duplicate")

    # ============================================================
    # 7. COMPRESSION
    # ============================================================

    def compression_stats(self) -> dict:
        """
        Compute overall compression statistics.

        For each group:
        CR_i = 1/n_i (compression ratio)
        Total: average compression across all elements

        Returns dict with:
        - n_groups: total groups
        - n_template_groups: groups with 3+ occurrences
        - avg_compression: average CR across all elements
        - estimated_storage_saved: bytes saved
        """
        if not self.groups:
            return {
                "n_groups": 0,
                "n_template_groups": 0,
                "avg_compression": 1.0,
                "estimated_storage_saved_bytes": 0,
            }

        total_elements = sum(g.count for g in self.groups.values())
        naive_storage = total_elements  # Each element stored fully
        compressed_storage = len(self.groups)  # One per group + references

        n_template = sum(1 for g in self.groups.values() if g.is_template)
        avg_compression = compressed_storage / max(1, naive_storage)

        # Estimate bytes saved (assume avg 200 bytes per element)
        avg_size = 200
        bytes_saved = (naive_storage - compressed_storage) * avg_size

        return {
            "n_groups": len(self.groups),
            "n_template_groups": n_template,
            "avg_compression": avg_compression,
            "compression_ratio_pct": (1 - avg_compression) * 100,
            "estimated_storage_saved_bytes": bytes_saved,
            "total_elements": total_elements,
            "unique_templates": compressed_storage,
        }

    def compress_storage(self, elements: list[GeometricElement]) -> dict:
        """
        Simulate storage compression.

        Returns storage plan:
        {
            "templates": [
                {"id": "header-1", "content": "...", "pages": [1, 2, 3], "count": 3},
                ...
            ],
            "unique_elements": [...],  # Elements not in any group
            "stats": {...}
        }
        """
        templates = []
        unique = []
        for gid, group in self.groups.items():
            if group.is_template:
                templates.append({
                    "id": gid,
                    "type": group.group_type,
                    "content": group.representative.content,
                    "pages": group.pages,
                    "count": group.count,
                    "compression": group.compression_ratio(),
                })
            else:
                for eid in group.members:
                    for e in elements:
                        if e.element_id == eid:
                            unique.append({
                                "id": eid,
                                "content": e.content,
                                "page": e.page,
                            })
                            break

        # Also add any elements that are not grouped at all to unique
        for e in elements:
            if not e.recurrence_id:
                unique.append({
                    "id": e.element_id,
                    "content": e.content,
                    "page": e.page,
                })

        return {
            "templates": templates,
            "unique_elements": unique,
            "stats": self.compression_stats(),
        }

    def reference_compression_ratio(self, elements: list[GeometricElement]) -> float:
        """
        Compute compression ratio using reference storage.

        Reference storage = n · |R_0|
        Compressed storage = |R_0| + n · log(p_max) + n · ref_size

        Returns compression ratio (0-1, lower is better).
        """
        if not self.groups:
            return 1.0
        total_elements = sum(g.count for g in self.groups.values())
        if total_elements == 0:
            return 1.0
        # Naive: store every element
        naive = total_elements
        # Compressed: 1 per group + small references
        # Assume log(p_max) ≈ 4 bytes for page reference
        compressed = len(self.groups) + total_elements * 0.1  # 10% overhead
        return compressed / max(1, naive)

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self) -> RecurrenceStats:
        """Get comprehensive statistics."""
        if not self.groups:
            return RecurrenceStats()
        total = sum(g.count for g in self.groups.values())
        types: dict[str, int] = {}
        for g in self.groups.values():
            types[g.group_type] = types.get(g.group_type, 0) + 1
        return RecurrenceStats(
            n_elements=total,
            n_groups=len(self.groups),
            n_template_groups=sum(1 for g in self.groups.values() if g.is_template),
            n_dominant_groups=sum(1 for g in self.groups.values() if g.is_dominant),
            total_compression_ratio=self.reference_compression_ratio([]),
            avg_frequency=total / max(1, len(self.groups)),
            max_frequency=max(g.count for g in self.groups.values()),
            group_types=types,
        )

    def get_repeated_content_pages(self, content: str) -> list[int]:
        """Get pages where specific content appears."""
        content_hash = self._hash_text(content)
        pages = []
        for gid, group in self.groups.items():
            if self._hash_text(group.representative.content) == content_hash:
                pages = group.pages
                break
        return pages

    # Legacy Compatibility Methods
    def score(self, query: str, elements: list[GeometricElement]) -> dict[str, float]:
        """Compute recurrence scores for all elements."""
        return {e.element_id: self.recurrence_score(e) for e in elements}

    def recurrence_score(self, element: GeometricElement) -> float:
        """
        R(q, e) ∈ [0, 1]
        Low score = template/boilerplate (de-prioritize)
        High score = unique content (prioritize)
        """
        if element.element_id in self._rec_map.template_ids or element.is_template:
            return 0.15
        if element.recurrence_id:
            group = self.get_group(element.recurrence_id)
            if group and group.count >= 2:
                return 0.40
        return 0.90
