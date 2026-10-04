"""
AEGIS-AMDI-OS — Geometry Engine
==================================
e_i = (x_i, y_i, w_i, h_i, p_i, θ_i, t_i, c_i)

Mathematical operations on document spatial coordinates:
- Coordinate extraction from PDFs
- Coordinate normalization (page-invariant)
- Bounding box operations (IoU, area, center)
- Alignment detection (A_x, A_y)
- Distance calculation (Euclidean + page penalty)
- Reading order reconstruction (RO = (y, x))
- Area ratio (importance proxy)
- Spatial neighbors (above/below/left/right)
- Information field on spatial grid

Theorem 4.1 (Scale Invariance):
    Normalized distance is invariant to uniform page scaling.

Theorem 5.1 (Metric Properties):
    d satisfies triangle inequality for same-page elements.
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional, Any

import numpy as np

from src.engines.geometry.element import BoundingBox, ElementType, GeometricElement

logger = logging.getLogger("amdi.geometry")


@dataclass
class SpatialStats:
    """Statistics about geometric elements."""
    n_elements: int = 0
    n_pages: int = 0
    n_types: int = 0
    mean_area: float = 0.0
    mean_x: float = 0.5
    mean_y: float = 0.5
    x_range: tuple = (0.0, 1.0)
    y_range: tuple = (0.0, 1.0)
    max_elements_page: int = 0
    avg_elements_per_page: float = 0.0

    # Backwards compatibility dictionary interface
    def __getitem__(self, key: str) -> Any:
        mapping = {
            "total_pages": self.n_pages,
            "total_elements": self.n_elements,
            "avg_elements_per_page": self.avg_elements_per_page,
            "max_elements_page": self.max_elements_page,
        }
        if key in mapping:
            return mapping[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class SpatialIndex:
    """Per-page spatial index."""
    page: int
    width: float
    height: float
    elements: list[GeometricElement] = field(default_factory=list)

    def elements_in_region(
        self,
        x0: float, y0: float, x1: float, y1: float,
    ) -> list[GeometricElement]:
        region = BoundingBox(x0, y0, x1, y1)
        return [e for e in self.elements if e.bbox and region.iou(e.bbox) > 0]

    def elements_near(
        self, bbox: BoundingBox, max_distance: float = 0.1,
    ) -> list[GeometricElement]:
        """Find elements within max_distance (normalized) of bbox."""
        result = []
        for e in self.elements:
            if not e.bbox or e.bbox is bbox:
                continue
            # Vertical gap
            if e.bbox.y1 < bbox.y0:
                gap = bbox.y0 - e.bbox.y1
            elif bbox.y1 < e.bbox.y0:
                gap = e.bbox.y0 - bbox.y1
            else:
                gap = 0.0
            if gap <= max_distance:
                result.append(e)
        return result


class GeometryEngine:
    """
    Phase 06: Geometry Engine.

    Stores elements with their spatial coordinates and provides
    mathematical operations: distance, alignment, IoU, reading order, etc.
    """

    # Cross-page distance penalty
    PAGE_PENALTY = 1.5

    def __init__(self):
        self.elements: dict[str, GeometricElement] = {}
        self._by_page: dict[int, list[str]] = defaultdict(list)
        self._by_type: dict[str, list[str]] = defaultdict(list)
        self._by_section: dict[str, list[str]] = defaultdict(list)
        self._page_dims: dict[int, tuple[float, float]] = {}

        # Backwards compatibility state variables
        self._pages: dict[int, SpatialIndex] = {}
        self._all: list[GeometricElement] = []

    # ============================================================
    # 1. COORDINATE EXTRACTION
    # ============================================================

    def extract_geometry(self, page_dict: dict, page_number: int, page_width: float, page_height: float) -> list[GeometricElement]:
        """
        Extract geometric elements from a PDF page dictionary.

        Args:
            page_dict: PyMuPDF page.get_text("dict") output
            page_number: 1-indexed page number
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of GeometricElement objects (without normalization yet)
        """
        elements = []
        for block in page_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                elements.extend(self._extract_text_block(block, page_number, page_height))
            elif block.get("type") == 1:  # Image block
                elements.append(self._extract_image_block(block, page_number))
        return elements

    def _extract_text_block(self, block: dict, page: int, page_height: float = 792) -> list[GeometricElement]:
        """Extract text block as one or more geometric elements."""
        elements = []
        bbox = block.get("bbox", (0, 0, 0, 0))
        text = self._reconstruct_text(block)
        if not text.strip():
            return elements
        btype = self._classify_text(text, bbox, page_height)
        elements.append(GeometricElement(
            content=text,
            page=page,
            bbox=BoundingBox(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]),
            type=btype,
        ))
        return elements

    def _extract_image_block(self, block: dict, page: int) -> GeometricElement:
        """Extract image block as a figure element."""
        bbox = block.get("bbox", (0, 0, 0, 0))
        return GeometricElement(
            content="",
            page=page,
            bbox=BoundingBox(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]),
            type=ElementType.FIGURE,
        )

    @staticmethod
    def _reconstruct_text(block: dict) -> str:
        """Reconstruct text from a PDF text block."""
        lines = []
        for line in block.get("lines", []):
            spans = [s.get("text", "") for s in line.get("spans", [])]
            text = "".join(spans).strip()
            if text:
                lines.append(text)
        return "\n".join(lines)

    @staticmethod
    def _classify_text(text: str, bbox: tuple, page_height: float = 792) -> ElementType:
        """Classify text block by position and content."""
        if not bbox or len(bbox) < 4:
            return ElementType.TEXT
        # Header heuristic: top 5% of page
        if bbox[1] < page_height * 0.05:
            return ElementType.HEADER
        # Footer heuristic: bottom 5%
        if bbox[3] > page_height * 0.95:
            return ElementType.FOOTER
        # Title: short, all-caps
        if text.strip().isupper() and len(text.split()) < 15:
            return ElementType.TITLE
        # Single line at top = heading
        if len(text.splitlines()) == 1 and len(text) < 100:
            return ElementType.HEADING
        return ElementType.TEXT

    # ============================================================
    # 2. COORDINATE NORMALIZATION
    # ============================================================

    def normalize_coordinates(self, page: int, page_width: float, page_height: float) -> None:
        """
        Normalize all coordinates on a page to [0, 1].

        Applies: x̃ = x / W, ỹ = y / H, w̃ = w / W, h̃ = h / H

        Theorem 4.1: This makes the distance metric invariant to
        uniform page scaling.

        Args:
            page: Page number to normalize
            page_width: Page width in points
            page_height: Page height in points
        """
        if page_width <= 0 or page_height <= 0:
            logger.warning(f"Invalid page dimensions for page {page}")
            return

        self._page_dims[page] = (page_width, page_height)
        if page in self._pages:
            self._pages[page].width = page_width
            self._pages[page].height = page_height

        for eid in self._by_page.get(page, []):
            e = self.elements[eid]
            if e.bbox is None:
                continue
            e.bbox = BoundingBox(
                x0=e.bbox.x0 / page_width,
                y0=e.bbox.y0 / page_height,
                x1=e.bbox.x1 / page_width,
                y1=e.bbox.y1 / page_height,
            )

    def normalize_all(self, page_dims: Optional[dict[int, tuple[float, float]]] = None) -> None:
        """Normalize all pages."""
        if page_dims:
            for page, (w, h) in page_dims.items():
                self.normalize_coordinates(page, w, h)
        else:
            for page, (w, h) in list(self._page_dims.items()):
                self.normalize_coordinates(page, w, h)

    def denormalize_bbox(self, bbox: BoundingBox, page: int) -> BoundingBox:
        """Convert normalized bbox back to raw coordinates."""
        if page not in self._page_dims:
            return bbox
        w, h = self._page_dims[page]
        return BoundingBox(
            x0=bbox.x0 * w, y0=bbox.y0 * h,
            x1=bbox.x1 * w, y1=bbox.y1 * h,
        )

    # ============================================================
    # 3. BOUNDING BOXES (operations on BoundingBox)
    # ============================================================

    @staticmethod
    def iou(box_a: BoundingBox, box_b: BoundingBox) -> float:
        """
        Compute Intersection over Union of two bounding boxes.

        IoU(A, B) = |A ∩ B| / |A ∪ B|

        Returns value in [0, 1].
        """
        if box_a is None or box_b is None:
            return 0.0
        return box_a.iou(box_b)

    @staticmethod
    def contains(outer: BoundingBox, inner: BoundingBox) -> bool:
        """Check if outer box contains inner box."""
        if outer is None or inner is None:
            return False
        return (outer.x0 <= inner.x0 and outer.y0 <= inner.y0
                and outer.x1 >= inner.x1 and outer.y1 >= inner.y1)

    @staticmethod
    def bbox_area(bbox: BoundingBox) -> float:
        """Area of a bounding box."""
        return bbox.area if bbox else 0.0

    @staticmethod
    def bbox_center(bbox: BoundingBox) -> tuple[float, float]:
        """Center (cx, cy) of a bounding box."""
        if bbox is None:
            return (0.5, 0.5)
        return bbox.center

    @staticmethod
    def bbox_overlap_area(box_a: BoundingBox, box_b: BoundingBox) -> float:
        """Compute overlap area between two bounding boxes."""
        if box_a is None or box_b is None:
            return 0.0
        ix0 = max(box_a.x0, box_b.x0)
        iy0 = max(box_a.y0, box_b.y0)
        ix1 = min(box_a.x1, box_b.x1)
        iy1 = min(box_a.y1, box_b.y1)
        iw = max(0.0, ix1 - ix0)
        ih = max(0.0, iy1 - iy0)
        return iw * ih

    # ============================================================
    # 4. ALIGNMENT DETECTION
    # ============================================================

    def calculate_alignment(self, a: GeometricElement, b: GeometricElement) -> float:
        """
        Calculate alignment score between two elements.

        A(i, j) = (A_x(i, j) + A_y(i, j)) / 2

        where:
            A_x = 1 - |x_i - x_j| / W  (horizontal alignment)
            A_y = 1 - |y_i - y_j| / H  (vertical alignment)

        Returns value in [0, 1]. A=1 means perfectly aligned.
        """
        if a.bbox is None or b.bbox is None:
            return 0.0
        return (self._alignment_x(a, b) + self._alignment_y(a, b)) / 2.0

    def _alignment_x(self, a: GeometricElement, b: GeometricElement) -> float:
        """Horizontal alignment score A_x ∈ [0, 1]."""
        ax = a.bbox.center[0]
        bx = b.bbox.center[0]
        return max(0.0, 1.0 - abs(ax - bx))

    def _alignment_y(self, a: GeometricElement, b: GeometricElement) -> float:
        """Vertical alignment score A_y ∈ [0, 1]."""
        ay = a.bbox.center[1]
        by = b.bbox.center[1]
        return max(0.0, 1.0 - abs(ay - by))

    def calculate_alignment_batch(self, elements: list[GeometricElement]) -> np.ndarray:
        """Compute alignment matrix for all pairs (NxN)."""
        n = len(elements)
        if n == 0:
            return np.zeros((0, 0))
        alignments = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    alignments[i, j] = self.calculate_alignment(elements[i], elements[j])
        return alignments

    # ============================================================
    # 5. DISTANCE CALCULATION
    # ============================================================

    def calculate_distance(self, a: GeometricElement, b: GeometricElement,
                          cross_page_weight: float = 1.5) -> float:
        """
        Calculate Euclidean distance between two elements with cross-page penalty.

        d(i, j) = √[(x_i - x_j)² + (y_i - y_j)²] + λ_page · |p_i - p_j|

        Theorem 5.1: For same-page elements, this satisfies the triangle inequality.
        """
        if a.bbox is None or b.bbox is None:
            return float("inf")
        ax, ay = a.bbox.center
        bx, by = b.bbox.center
        spatial_dist = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
        page_dist = abs(a.page - b.page) * cross_page_weight
        return spatial_dist + page_dist

    def distance_matrix(self, elements: list[GeometricElement]) -> np.ndarray:
        """Compute pairwise distance matrix (NxN)."""
        n = len(elements)
        if n == 0:
            return np.zeros((0, 0))
        D = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = self.calculate_distance(elements[i], elements[j])
                D[i, j] = d
                D[j, i] = d
        return D

    def find_nearest(self, target: GeometricElement, k: int = 5,
                     same_page_only: bool = False) -> list[tuple[GeometricElement, float]]:
        """Find k nearest neighbors to target element."""
        candidates = [
            e for eid, e in self.elements.items()
            if eid != target.element_id
            and (not same_page_only or e.page == target.page)
        ]
        candidates_with_dist = [
            (e, self.calculate_distance(target, e)) for e in candidates
        ]
        candidates_with_dist.sort(key=lambda x: x[1])
        return candidates_with_dist[:k]

    # ============================================================
    # 6. READING ORDER
    # ============================================================

    def get_reading_order(self, elements: list[GeometricElement]) -> list[GeometricElement]:
        """
        Sort elements by reading order: RO(e_i) = (y_i, x_i).

        Primary sort: top-to-bottom (y ascending in normalized coords).
        Secondary sort: left-to-right (x ascending).
        Then by page number.
        """
        return sorted(
            elements,
            key=lambda e: (
                e.page,
                e.bbox.y0 if e.bbox else 0,
                e.bbox.x0 if e.bbox else 0,
            ),
        )

    def get_reading_order_indices(self, elements: list[GeometricElement]) -> list[int]:
        """Get indices in reading order."""
        order = self.get_reading_order(elements)
        index_map = {id(e): i for i, e in enumerate(elements)}
        return [index_map[id(e)] for e in order]

    # ============================================================
    # BONUS: AREA IMPORTANCE
    # ============================================================

    def area_importance(self, e: GeometricElement) -> float:
        """
        Area ratio AR(e) = w_e × h_e ∈ [0, 1].

        Larger elements → higher visual importance.
        """
        if e.bbox is None:
            return 0.0
        return e.bbox.width * e.bbox.height

    def area_importance_weighted(self, elements: list[GeometricElement]) -> np.ndarray:
        """Normalized area importance for all elements."""
        areas = np.array([self.area_importance(e) for e in elements])
        total = areas.sum()
        if total > 0:
            return areas / total
        return np.zeros(len(elements))

    # ============================================================
    # BONUS: SPATIAL NEIGHBORS
    # ============================================================

    def elements_above(self, element: GeometricElement, k: int = 5) -> list[GeometricElement]:
        """Get k elements geometrically above the given element on same page."""
        if element.bbox is None:
            return []
        same_page = self.get_by_page(element.page)
        above = [
            e for e in same_page
            if e.element_id != element.element_id and e.bbox and e.bbox.y1 <= element.bbox.y0
        ]
        above.sort(key=lambda e: element.bbox.y0 - e.bbox.y1)
        return above[:k]

    def elements_below(self, element: GeometricElement, k: int = 5) -> list[GeometricElement]:
        """Get k elements geometrically below the given element."""
        if element.bbox is None:
            return []
        same_page = self.get_by_page(element.page)
        below = [
            e for e in same_page
            if e.element_id != element.element_id and e.bbox and e.bbox.y0 >= element.bbox.y1
        ]
        below.sort(key=lambda e: e.bbox.y0 - element.bbox.y1)
        return below[:k]

    def elements_left_right(self, element: GeometricElement) -> tuple[list[GeometricElement], list[GeometricElement]]:
        """Get elements to the left and right of the given element."""
        if element.bbox is None:
            return [], []
        cx = element.bbox.center[0]
        same_page = self.get_by_page(element.page)
        left = [e for e in same_page if e.element_id != element.element_id and e.bbox and e.bbox.center[0] < cx]
        right = [e for e in same_page if e.element_id != element.element_id and e.bbox and e.bbox.center[0] > cx]
        return left, right

    # ============================================================
    # BONUS: INFORMATION FIELD ON SPATIAL GRID
    # ============================================================

    def spatial_density_field(
        self,
        elements: list[GeometricElement],
        grid_size: int = 32,
    ) -> np.ndarray:
        """
        Compute spatial density field on a grid.

        For each grid cell, sum the area_importance of elements that overlap.
        Returns a (grid_size, grid_size) array.
        """
        field = np.zeros((grid_size, grid_size))
        for e in elements:
            if e.bbox is None:
                continue
            x0_idx = int(e.bbox.x0 * grid_size)
            x1_idx = int(e.bbox.x1 * grid_size) + 1
            y0_idx = int(e.bbox.y0 * grid_size)
            y1_idx = int(e.bbox.y1 * grid_size) + 1
            importance = self.area_importance(e)
            field[
                max(0, y0_idx):min(grid_size, y1_idx),
                max(0, x0_idx):min(grid_size, x1_idx),
            ] += importance
        # Normalize
        if field.max() > 0:
            field = field / field.max()
        return field

    # ============================================================
    # BACKWARDS COMPATIBILITY METHODS
    # ============================================================

    def set_page_dims(self, page: int, width: float, height: float) -> None:
        self._page_dims[page] = (width, height)
        if page not in self._pages:
            self._pages[page] = SpatialIndex(page=page, width=width, height=height)
        else:
            self._pages[page].width = width
            self._pages[page].height = height

    def page_elements(self, page: int) -> list[GeometricElement]:
        return self.get_by_page(page)

    def all_elements(self) -> list[GeometricElement]:
        return self._all

    def elements_near(
        self, element: GeometricElement, max_distance: float = 0.1,
    ) -> list[GeometricElement]:
        if not element.bbox:
            return []
        idx = self._pages.get(element.page)
        return idx.elements_near(element.bbox, max_distance) if idx else []

    def column_count(self, page: int) -> int:
        """Estimate number of text columns on a page."""
        elems = self.page_elements(page)
        xs = [e.bbox.x0 for e in elems if e.bbox]
        if len(xs) < 4:
            return 1
        xs_sorted = sorted(xs)
        gaps = [xs_sorted[i + 1] - xs_sorted[i] for i in range(len(xs_sorted) - 1)]
        big = sum(1 for g in gaps if g > 0.2)
        return 1 + big

    def geometry_relevance(
        self,
        query_pages: Optional[list[int]],
        element: GeometricElement,
        section_hint: Optional[str] = None,
    ) -> float:
        """
        G(q, e) ∈ [0, 1]
        """
        score = 0.5  # base

        # Page match
        if query_pages:
            if element.page in query_pages:
                score += 0.3
            elif any(abs(element.page - p) == 1 for p in query_pages):
                score += 0.1

        # Section match
        if section_hint and element.section:
            if section_hint.lower() in element.section.lower():
                score += 0.2

        # Structural bonus
        if element.type in (ElementType.TABLE, ElementType.FIGURE, ElementType.EQUATION):
            score += 0.1

        # Central position bonus (avoid headers/footers)
        if element.bbox:
            cy = (element.bbox.y0 + element.bbox.y1) / 2
            if 0.1 < cy < 0.9:
                score += 0.05

        return min(1.0, score)

    def score(
        self,
        query: str,
        elements: list[GeometricElement],
        query_pages: Optional[list[int]] = None,
    ) -> dict[str, float]:
        return {e.element_id: self.geometry_relevance(query_pages, e) for e in elements}

    def analyze(self, elements: list[GeometricElement]) -> None:
        self.add_many(elements)
        self.normalize_all()

    # ============================================================
    # INDEXING / MANAGEMENT
    # ============================================================

    def add(self, element: GeometricElement) -> None:
        """Add an element to the index."""
        self.elements[element.element_id] = element
        self._by_page[element.page].append(element.element_id)
        self._by_type[element.type.value].append(element.element_id)
        if element.section:
            self._by_section[element.section].append(element.element_id)

        # Backwards compatibility sync
        self._all.append(element)
        page = element.page
        if page not in self._pages:
            w, h = self._page_dims.get(page, (1.0, 1.0))
            self._pages[page] = SpatialIndex(page=page, width=w, height=h)
        self._pages[page].elements.append(element)

    def add_many(self, elements: Iterable[GeometricElement]) -> None:
        """Add multiple elements."""
        for e in elements:
            self.add(e)

    def get(self, element_id: str) -> Optional[GeometricElement]:
        """Get element by ID."""
        return self.elements.get(element_id)

    def get_by_page(self, page: int) -> list[GeometricElement]:
        """Get all elements on a page."""
        return [self.elements[eid] for eid in self._by_page.get(page, [])]

    def get_by_type(self, element_type: ElementType) -> list[GeometricElement]:
        """Get all elements of a specific type."""
        return [self.elements[eid] for eid in self._by_type.get(element_type.value, [])]

    def get_by_section(self, section: str) -> list[GeometricElement]:
        """Get all elements in a section."""
        return [self.elements[eid] for eid in self._by_section.get(section, [])]

    def statistics(self) -> SpatialStats:
        """Get spatial statistics."""
        if not self.elements:
            return SpatialStats()
        areas = [self.area_importance(e) for e in self.elements.values()]
        xs = [e.bbox.center[0] for e in self.elements.values() if e.bbox]
        ys = [e.bbox.center[1] for e in self.elements.values() if e.bbox]

        counts = {p: len(idx.elements) for p, idx in self._pages.items()}
        avg_val = round(sum(counts.values()) / max(1, len(counts)), 1) if counts else 0.0
        max_val = max(counts.values()) if counts else 0

        return SpatialStats(
            n_elements=len(self.elements),
            n_pages=len(self._by_page),
            n_types=len(self._by_type),
            mean_area=float(np.mean(areas)) if areas else 0,
            mean_x=float(np.mean(xs)) if xs else 0.5,
            mean_y=float(np.mean(ys)) if ys else 0.5,
            x_range=(min(xs), max(xs)) if xs else (0, 1),
            y_range=(min(ys), max(ys)) if ys else (0, 1),
            max_elements_page=max_val,
            avg_elements_per_page=avg_val,
        )

    def clear(self) -> None:
        """Clear all data."""
        self.elements.clear()
        self._by_page.clear()
        self._by_type.clear()
        self._by_section.clear()
        self._page_dims.clear()
        self._pages.clear()
        self._all.clear()
