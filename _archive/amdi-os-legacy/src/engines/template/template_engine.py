"""
AEGIS-AMDI-OS — Template Engine
=================================
T = {h, b, t, i, m} — Page fingerprint clustering.

Detects page-level templates via:
1. Fingerprint Generation: Per-page feature vector
2. Signature Creation: Statistical signature
3. Template Clustering: DBSCAN grouping
4. Duplicate Detection: Near-duplicate pages

Theorems:
- Template families compress storage by 1/n
- Dominant templates (5+ pages) enable massive optimization
"""
from __future__ import annotations

import hashlib
import logging
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional, Any

import numpy as np
from sklearn.cluster import DBSCAN

try:
    from src.core.geometric_element import ElementType, GeometricElement
except ImportError:
    from src.engines.geometry.element import ElementType, GeometricElement

try:
    from src.core.normalized_document import BoundingBox
except ImportError:
    from src.engines.geometry.element import BoundingBox

logger = logging.getLogger(__name__)


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class PageFingerprint:
    """
    Fingerprint of a single page.

    F_p = (type_counts, area_stats, layout_features, text_stats)
    """
    page_number: int
    n_elements: int
    type_histogram: dict[str, int] = field(default_factory=dict)
    type_fractions: dict[str, float] = field(default_factory=dict)
    total_area: float = 0.0
    avg_area: float = 0.0
    text_density: float = 0.0
    n_tables: int = 0
    n_figures: int = 0
    n_headings: int = 0
    signature: np.ndarray | None = None
    content_hash: str = ""


@dataclass
class PageTemplate:
    """
    T = {h, b, t, i, m}

    A template family detected across pages.
    """
    template_id: str
    pages: list[int] = field(default_factory=list)
    cluster_size: int = 0
    centroid: np.ndarray | None = None
    composition: dict[str, int] = field(default_factory=dict)
    sample_content: str = ""
    fingerprint: PageFingerprint | None = None
    created_at: float = field(default_factory=time.time)

    # Legacy fields for backward-compatibility
    signature: np.ndarray | None = None
    n_headings: int = 0
    n_blocks: int = 0
    n_tables: int = 0
    n_figures: int = 0
    margin_top: float = 0.0
    margin_bottom: float = 0.0
    margin_left: float = 0.0
    margin_right: float = 0.0

    def __post_init__(self) -> None:
        # Sync signature and centroid
        if self.centroid is None and self.signature is not None:
            self.centroid = self.signature
        elif self.signature is None and self.centroid is not None:
            self.signature = self.centroid

    @property
    def is_template(self) -> bool:
        """2+ pages = template."""
        return self.cluster_size >= 2

    @property
    def is_dominant(self) -> bool:
        """3+ pages = dominant template (satisfies legacy and new requirements)."""
        return self.cluster_size >= 3

    @property
    def compression_ratio(self) -> float:
        """1/n for n pages."""
        return 1.0 / max(1, self.cluster_size)

    def similarity(self, sig: np.ndarray) -> float:
        """Calculate cosine similarity with signature."""
        target_sig = self.centroid if self.centroid is not None else self.signature
        if target_sig is None:
            return 0.0
        a, b = np.asarray(target_sig), np.asarray(sig)
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
        return float(np.dot(a, b) / denom)

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "pages": self.pages,
            "cluster_size": self.cluster_size,
            "is_template": self.is_template,
            "is_dominant": self.is_dominant,
            "compression_ratio": self.compression_ratio,
            "composition": self.composition,
        }


@dataclass
class DuplicateGroup:
    """Group of near-duplicate pages."""
    group_id: str
    pages: list[int]
    similarity_scores: list[float] = field(default_factory=list)
    representative_page: int = 0
    content_hash: str = ""


@dataclass
class TemplateStats:
    """Statistics about template analysis."""
    n_pages: int = 0
    n_templates: int = 0
    n_dominant_templates: int = 0
    n_template_pages: int = 0
    avg_cluster_size: float = 0.0
    max_cluster_size: int = 0
    compression_ratio: float = 1.0
    n_duplicates: int = 0

    def __getitem__(self, key: str) -> Any:
        # Support dictionary-like access for legacy tests
        mapping = {
            "templates": self.n_templates,
            "dominant": self.n_dominant_templates,
            "pages_covered": self.n_template_pages,
            "max_cluster": self.max_cluster_size,
        }
        if key in mapping:
            return mapping[key]
        return getattr(self, key)


# ============================================================
# TEMPLATE ENGINE
# ============================================================

class TemplateEngine:
    """
    Phase 10: Template Engine.

    Detects page-level templates via fingerprinting + DBSCAN clustering.
    """

    DEFAULT_EPS = 0.15            # DBSCAN neighborhood radius
    DEFAULT_MIN_SAMPLES = 2       # Min samples for cluster
    DUPLICATE_THRESHOLD = 0.95    # Cosine similarity for duplicates
    DOMINANT_THRESHOLD = 5        # Pages to be "dominant"

    def __init__(
        self,
        eps: float = DEFAULT_EPS,
        min_samples: int = DEFAULT_MIN_SAMPLES,
        duplicate_threshold: float = DUPLICATE_THRESHOLD,
        similarity_threshold: float | None = None,
        min_cluster: int | None = None,
    ):
        self.eps = eps
        # Handle legacy constructor parameter similarity_threshold (eps = 1 - sim_threshold)
        if similarity_threshold is not None:
            self.eps = 1.0 - similarity_threshold

        self.min_samples = min_samples
        # Handle legacy constructor parameter min_cluster
        if min_cluster is not None:
            self.min_samples = min_cluster

        self.duplicate_threshold = duplicate_threshold
        self.templates: dict[str, PageTemplate] = {}
        self.fingerprints: dict[int, PageFingerprint] = {}
        self.duplicates: list[DuplicateGroup] = []
        self._page_to_tmpl: dict[int, str] = {}

    # ============================================================
    # 1. FINGERPRINT GENERATION
    # ============================================================

    def generate_fingerprint(
        self,
        page_number: int,
        elements: list[GeometricElement],
    ) -> PageFingerprint:
        """
        Generate a fingerprint for a page.

        F_p = (type_histogram, area_stats, text_density, layout_features)
        """
        # Type counts and fractions
        type_counts: Counter = Counter()
        total_area = 0.0
        text_chars = 0
        n_tables = 0
        n_figures = 0
        n_headings = 0
        for e in elements:
            etype_str = e.type.value if hasattr(e.type, "value") else str(e.type)
            type_counts[etype_str] += 1
            if e.bbox:
                w = getattr(e.bbox, "width", 0.0)
                h = getattr(e.bbox, "height", 0.0)
                if w == 0.0 and h == 0.0 and hasattr(e.bbox, "x0"):
                    w = e.bbox.x1 - e.bbox.x0
                    h = e.bbox.y1 - e.bbox.y0
                total_area += w * h
            text_chars += len(e.content) if e.content else 0
            if e.type == ElementType.TABLE:
                n_tables += 1
            elif e.type == ElementType.FIGURE:
                n_figures += 1
            elif e.type in (ElementType.HEADING, ElementType.TITLE):
                n_headings += 1

        n = len(elements)
        type_fractions = {
            t: c / max(1, n) for t, c in type_counts.items()
        }

        fp = PageFingerprint(
            page_number=page_number,
            n_elements=n,
            type_histogram=dict(type_counts),
            type_fractions=type_fractions,
            total_area=total_area,
            avg_area=total_area / max(1, n),
            text_density=text_chars / max(1.0, total_area) if total_area > 0 else 0.0,
            n_tables=n_tables,
            n_figures=n_figures,
            n_headings=n_headings,
        )
        # Compute signature
        fp.signature = self.create_signature(fp)
        # Compute content hash
        fp.content_hash = self._hash_page_content(elements)
        # Store
        self.fingerprints[page_number] = fp
        return fp

    def _hash_page_content(self, elements: list[GeometricElement]) -> str:
        """Hash the concatenated content of a page."""
        content = " ".join(e.content for e in elements if e.content)
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    # ============================================================
    # 2. SIGNATURE CREATION
    # ============================================================

    def create_signature(self, fingerprint: PageFingerprint) -> np.ndarray:
        """
        Create a numerical signature vector for clustering.

        Signature components:
        [0-6]:   Type fractions (text, table, figure, heading, header, footer, list)
        [7-9]:   Counts (tables, figures, headings)
        [10-11]: Area stats (avg, total)
        [12]:    Text density
        [13-14]: Reserved
        [15]:    Normalized page index (for ordering)

        Returns normalized 16-D vector.
        """
        type_names = ["text", "table", "figure", "heading", "header", "footer", "list_item"]
        sig = np.zeros(16, dtype=np.float32)

        # Type fractions
        for i, t in enumerate(type_names):
            if t == "text":
                sig[i] = fingerprint.type_fractions.get("text", 0.0) + fingerprint.type_fractions.get("paragraph", 0.0)
            elif t == "heading":
                sig[i] = fingerprint.type_fractions.get("heading", 0.0) + fingerprint.type_fractions.get("title", 0.0) + fingerprint.type_fractions.get("subtitle", 0.0)
            else:
                sig[i] = fingerprint.type_fractions.get(t, 0.0)

        # Counts (normalized by max possible)
        sig[7] = min(1.0, fingerprint.n_tables / 5.0)
        sig[8] = min(1.0, fingerprint.n_figures / 5.0)
        sig[9] = min(1.0, fingerprint.n_headings / 5.0)

        # Area stats
        sig[10] = min(1.0, fingerprint.avg_area * 2)
        sig[11] = min(1.0, fingerprint.total_area)

        # Text density (normalized)
        sig[12] = min(1.0, fingerprint.text_density / 1000.0)

        # Element count (normalized)
        sig[13] = min(1.0, fingerprint.n_elements / 50.0)

        # Reserved
        sig[14] = 0.0

        # Page position hint
        sig[15] = 0.0

        # Normalize to unit vector
        norm = np.linalg.norm(sig)
        if norm > 0:
            sig = sig / norm
        return sig

    # Legacy 20-D signature for backwards compatibility tests
    def _page_sig(self, elems: list[GeometricElement]) -> np.ndarray:
        n = max(1, len(elems))
        tc = Counter(e.type for e in elems)
        bb = [e.bbox for e in elems if e.bbox]
        mt = min((b.y0 for b in bb), default=0.0)
        mb = 1. - max((b.y1 for b in bb), default=1.0)
        ml = min((b.x0 for b in bb), default=0.0)
        mr = 1. - max((b.x1 for b in bb), default=1.0)
        ah = float(np.mean([b.height for b in bb])) if bb else 0.0
        aw = float(np.mean([b.width  for b in bb])) if bb else 0.0
        yd = n / max(0.001, max((b.y1 for b in bb), default=1.) - min((b.y0 for b in bb), default=0.))
        ls = [len(e.content) for e in elems if e.content]
        ls_std = float(np.std(ls)) / max(1, np.mean(ls)) if ls else 0.

        sig = np.array([
            tc.get(ElementType.HEADING,   0) / n,
            tc.get(ElementType.PARAGRAPH, 0) / n,
            tc.get(ElementType.TABLE,     0) / n,
            tc.get(ElementType.FIGURE,    0) / n,
            tc.get(ElementType.EQUATION,  0) / n,
            tc.get(ElementType.LIST_ITEM, 0) / n,
            tc.get(ElementType.HEADER,    0) / n,
            tc.get(ElementType.FOOTER,    0) / n,
            mt, mb, ml, mr, ah, aw, yd, ls_std,
            float(n) / 100.,
            tc.get(ElementType.TABLE, 0) * 3. / n,
            tc.get(ElementType.FIGURE, 0) * 2. / n,
            float(len(bb)) / n,
        ], dtype=np.float32)
        nrm = np.linalg.norm(sig)
        return sig / nrm if nrm > 0 else sig

    # ============================================================
    # 3. TEMPLATE CLUSTERING (DBSCAN)
    # ============================================================

    def build_templates(
        self, elements_by_page: dict[int, list[GeometricElement]]
    ) -> list[PageTemplate]:
        """
        Detect template families via DBSCAN clustering.

        1. Generate fingerprint per page
        2. Stack signatures into matrix
        3. Cluster with DBSCAN (cosine similarity)
        4. Build PageTemplate for each cluster
        """
        # Clear previous
        self.templates = {}
        self.fingerprints = {}
        self._page_to_tmpl = {}

        if not elements_by_page:
            return []

        # Generate fingerprints
        for page, elements in sorted(elements_by_page.items()):
            self.generate_fingerprint(page, elements)

        if len(self.fingerprints) < 2:
            # Not enough pages for clustering
            for page, fp in self.fingerprints.items():
                template = self._make_singleton_template(page, fp)
                self.templates[template.template_id] = template
                self._page_to_tmpl[page] = template.template_id
            return list(self.templates.values())

        # Stack signatures
        pages_sorted = sorted(self.fingerprints.keys())
        signatures = np.stack([self.fingerprints[p].signature for p in pages_sorted])

        # DBSCAN clustering
        try:
            labels = DBSCAN(
                eps=self.eps,
                min_samples=self.min_samples,
                metric="cosine",
            ).fit(signatures).labels_
        except Exception as e:
            logger.warning(f"DBSCAN failed: {e}. Assigning all to single cluster.")
            labels = np.zeros(len(signatures), dtype=int)

        # Build templates from clusters
        clusters: dict[int, list[int]] = defaultdict(list)
        for page, label in zip(pages_sorted, labels):
            clusters[int(label)].append(page)

        templates = []
        for cluster_id, pages in clusters.items():
            if cluster_id == -1:
                # Noise points - treat as individual
                for page in pages:
                    template = self._make_singleton_template(page, self.fingerprints[page])
                    self.templates[template.template_id] = template
                    self._page_to_tmpl[page] = template.template_id
                    templates.append(template)
            else:
                template = self._build_cluster_template(cluster_id, pages)
                self.templates[template.template_id] = template
                for page in pages:
                    self._page_to_tmpl[page] = template.template_id
                templates.append(template)

        return sorted(templates, key=lambda t: -t.cluster_size)

    def _make_singleton_template(
        self, page: int, fp: PageFingerprint
    ) -> PageTemplate:
        """Create a template for a single page (no cluster)."""
        tid = f"T-singleton-{page}"
        return PageTemplate(
            template_id=tid,
            pages=[page],
            cluster_size=1,
            centroid=fp.signature,
            composition=fp.type_histogram,
            sample_content="",
            fingerprint=fp,
            n_headings=fp.n_headings,
            n_tables=fp.n_tables,
            n_figures=fp.n_figures,
            n_blocks=fp.n_elements,
        )

    def _build_cluster_template(
        self, cluster_id: int, pages: list[int]
    ) -> PageTemplate:
        """Build a PageTemplate from a cluster of pages."""
        # Use median fingerprint as centroid
        fps = [self.fingerprints[p] for p in pages]
        signatures = np.stack([fp.signature for fp in fps])
        centroid = np.median(signatures, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm

        # Aggregate composition
        all_types: Counter = Counter()
        n_headings = 0
        n_tables = 0
        n_figures = 0
        for fp in fps:
            all_types.update(fp.type_histogram)
            n_headings += fp.n_headings
            n_tables += fp.n_tables
            n_figures += fp.n_figures

        # Generate template ID from hash of centroid
        centroid_hash = hashlib.sha256(centroid.tobytes()).hexdigest()[:8]
        tid = f"T-{centroid_hash}"
        # Sample content from first page
        sample_content = ""
        if pages and fps:
            sample_content = f"Page {pages[0]} fingerprint: {fps[0].type_histogram}"

        template = PageTemplate(
            template_id=tid,
            pages=sorted(pages),
            cluster_size=len(pages),
            centroid=centroid,
            composition=dict(all_types),
            sample_content=sample_content,
            fingerprint=fps[len(pages) // 2],  # Median page
            n_headings=n_headings // len(pages),
            n_tables=n_tables // len(pages),
            n_figures=n_figures // len(pages),
            n_blocks=sum(fp.n_elements for fp in fps) // len(pages),
        )
        return template

    # Legacy build() method
    def build(self, elements: list[GeometricElement]) -> list[PageTemplate]:
        """Legacy flat list elements clustering."""
        by_page: dict[int, list[GeometricElement]] = defaultdict(list)
        for e in elements:
            by_page[e.page].append(e)
        self.build_templates(by_page)
        return [t for t in self.templates.values() if t.cluster_size >= self.min_samples]

    # Legacy page_template() retrieval
    def page_template(self, page: int) -> PageTemplate | None:
        tid = self._page_to_tmpl.get(page)
        tmpl = self.templates.get(tid) if tid else None
        if tmpl and tmpl.cluster_size < self.min_samples:
            return None
        return tmpl

    # Legacy scoring
    def template_score(self, element: GeometricElement) -> float:
        tmpl = self.page_template(element.page)
        if tmpl is None:
            return 0.6
        is_tmpl_element = getattr(element, "is_template", False)
        if tmpl.is_dominant and is_tmpl_element:
            return 0.15   # boilerplate → suppress
        return 0.70

    # Legacy compression factor calculation
    def compression_factor(self, total_pages: int) -> float:
        if total_pages == 0:
            return 1.0
        covered = sum(t.cluster_size for t in self.templates.values())
        unique = total_pages - covered + len(self.templates)
        return unique / total_pages

    # Legacy detect & score
    def detect(self, elements: list[GeometricElement]) -> list[PageTemplate]:
        return self.build(elements)

    def score(self, query: str, elements: list[GeometricElement]) -> dict[str, float]:
        return {getattr(e, "element_id", str(i)): self.template_score(e) for i, e in enumerate(elements)}

    # ============================================================
    # 4. DUPLICATE DETECTION
    # ============================================================

    def detect_duplicates(
        self, similarity_threshold: float | None = None
    ) -> list[DuplicateGroup]:
        """
        Detect near-duplicate pages using cosine similarity.

        Two pages are duplicates if their signature similarity > threshold.
        """
        threshold = similarity_threshold or self.duplicate_threshold
        self.duplicates = []

        if len(self.fingerprints) < 2:
            return self.duplicates

        pages = sorted(self.fingerprints.keys())
        signatures = np.stack([self.fingerprints[p].signature for p in pages])

        # Compute pairwise similarity
        norms = np.linalg.norm(signatures, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normalized = signatures / norms
        sim_matrix = normalized @ normalized.T

        # Find connected components of duplicates
        n = len(pages)
        visited = [False] * n
        groups: list[DuplicateGroup] = []
        for i in range(n):
            if visited[i]:
                continue
            component = [i]
            similarities = []
            queue = [i]
            visited[i] = True
            while queue:
                curr = queue.pop(0)
                for j in range(n):
                    if visited[j] or j == curr:
                        continue
                    if sim_matrix[curr, j] >= threshold:
                        component.append(j)
                        similarities.append(float(sim_matrix[curr, j]))
                        visited[j] = True
                        queue.append(j)
            if len(component) >= 2:
                gid = f"D-{len(groups) + 1}"
                group_pages = sorted([pages[idx] for idx in component])
                rep_page = group_pages[0]
                rep_fp = self.fingerprints[rep_page]
                groups.append(DuplicateGroup(
                    group_id=gid,
                    pages=group_pages,
                    similarity_scores=similarities,
                    representative_page=rep_page,
                    content_hash=rep_fp.content_hash,
                ))
        self.duplicates = groups
        return groups

    def find_exact_duplicates(self) -> list[DuplicateGroup]:
        """Find pages with identical content (exact match)."""
        groups: list[DuplicateGroup] = []
        hash_to_pages: dict[str, list[int]] = defaultdict(list)
        for page, fp in self.fingerprints.items():
            hash_to_pages[fp.content_hash].append(page)
        for content_hash, pages in hash_to_pages.items():
            if len(pages) >= 2:
                gid = f"D-exact-{len(groups) + 1}"
                groups.append(DuplicateGroup(
                    group_id=gid,
                    pages=sorted(pages),
                    similarity_scores=[1.0] * (len(pages) - 1),
                    representative_page=pages[0],
                    content_hash=content_hash,
                ))
        return groups

    def find_similar_templates(
        self, template: PageTemplate, top_k: int = 3
    ) -> list[tuple[PageTemplate, float]]:
        """Find templates similar to a given template."""
        target_centroid = template.centroid if template.centroid is not None else template.signature
        if target_centroid is None:
            return []
        similarities = []
        for tid, other in self.templates.items():
            other_centroid = other.centroid if other.centroid is not None else other.signature
            if tid == template.template_id or other_centroid is None:
                continue
            sim = float(
                np.dot(target_centroid, other_centroid) /
                (np.linalg.norm(target_centroid) * np.linalg.norm(other_centroid) + 1e-9)
            )
            similarities.append((other, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    # ============================================================
    # QUERIES
    # ============================================================

    def get_template(self, template_id: str) -> PageTemplate | None:
        """Get template by ID."""
        return self.templates.get(template_id)

    def get_templates_for_page(self, page: int) -> list[PageTemplate]:
        """Get templates containing a specific page."""
        return [t for t in self.templates.values() if page in t.pages]

    def get_dominant_templates(self) -> list[PageTemplate]:
        """Get templates appearing 3+ times (dominant)."""
        return [t for t in self.templates.values() if t.is_dominant]

    def get_template_by_page_signature(
        self, signature: np.ndarray
    ) -> PageTemplate | None:
        """Find best matching template for a signature."""
        best_match = None
        best_sim = -1.0
        for t in self.templates.values():
            t_centroid = t.centroid if t.centroid is not None else t.signature
            if t_centroid is None:
                continue
            sim = float(
                np.dot(signature, t_centroid) /
                (np.linalg.norm(signature) * np.linalg.norm(t_centroid) + 1e-9)
            )
            if sim > best_sim:
                best_sim = sim
                best_match = t
        return best_match

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self) -> TemplateStats:
        """Get overall template statistics."""
        if not self.templates:
            return TemplateStats()
        template_pages = sum(t.cluster_size for t in self.templates.values())
        n_templates = len(self.templates)
        naive_storage = template_pages
        compressed_storage = n_templates + template_pages * 0.1  # refs
        cr = compressed_storage / max(1, naive_storage)
        sizes = [t.cluster_size for t in self.templates.values()]
        return TemplateStats(
            n_pages=template_pages,
            n_templates=n_templates,
            n_dominant_templates=sum(1 for t in self.templates.values() if t.is_dominant),
            n_template_pages=template_pages,
            avg_cluster_size=template_pages / max(1, n_templates),
            max_cluster_size=max(sizes) if sizes else 0,
            compression_ratio=cr,
            n_duplicates=len(self.duplicates),
        )

    def compression_report(self) -> dict:
        """Detailed compression analysis."""
        stats = self.statistics()
        if stats.n_pages == 0:
            return {"compression_ratio": 1.0, "savings_pct": 0.0}
        template_savings = []
        for t in self.templates.values():
            template_savings.append({
                "template_id": t.template_id,
                "pages": len(t.pages),
                "compression": t.compression_ratio,
                "savings_pct": (1.0 - t.compression_ratio) * 100.0,
            })
        return {
            "overall_compression": stats.compression_ratio,
            "overall_savings_pct": (1.0 - stats.compression_ratio) * 100.0,
            "n_pages": stats.n_pages,
            "n_templates": stats.n_templates,
            "templates": sorted(
                template_savings,
                key=lambda x: x["savings_pct"],
                reverse=True,
            ),
        }

    def clear(self) -> None:
        """Clear all data."""
        self.templates.clear()
        self.fingerprints.clear()
        self.duplicates.clear()
        self._page_to_tmpl.clear()
