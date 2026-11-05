"""
aegis.processing.layout.regions
===============================
Layout region taxonomy, bounding box operations, and coordinate transformations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from aegis.processing.models import CoordinateSystem, LayoutRegion, RegionType


TAXONOMY_MAP = {
    "text": RegionType.PARAGRAPH,
    "paragraph": RegionType.PARAGRAPH,
    "title": RegionType.TITLE,
    "section-header": RegionType.SECTION_HEADER,
    "section_header": RegionType.SECTION_HEADER,
    "table": RegionType.TABLE,
    "picture": RegionType.FIGURE,
    "figure": RegionType.FIGURE,
    "caption": RegionType.CAPTION,
    "list-item": RegionType.LIST,
    "list": RegionType.LIST,
    "page-header": RegionType.HEADER,
    "header": RegionType.HEADER,
    "page-footer": RegionType.FOOTER,
    "footer": RegionType.FOOTER,
    "footnote": RegionType.FOOTNOTE,
    "formula": RegionType.FORMULA,
    "form_field": RegionType.FORM_FIELD,
}


def normalize_region_type(raw_type: str) -> RegionType:
    """Map external dataset category strings to AEGIS canonical RegionType."""
    clean = raw_type.strip().lower().replace(" ", "_")
    return TAXONOMY_MAP.get(clean, RegionType.PARAGRAPH)


def compute_iou(bbox_a: List[float], bbox_b: List[float]) -> float:
    """Compute Intersection over Union (IoU) between two bounding boxes [x0, y0, x1, y1]."""
    x0_a, y0_a, x1_a, y1_a = bbox_a
    x0_b, y0_b, x1_b, y1_b = bbox_b

    # Intersection coordinates
    inter_x0 = max(x0_a, x0_b)
    inter_y0 = max(y0_a, y0_b)
    inter_x1 = min(x1_a, x1_b)
    inter_y1 = min(y1_a, y1_b)

    inter_w = max(0.0, inter_x1 - inter_x0)
    inter_h = max(0.0, inter_y1 - inter_y0)
    inter_area = inter_w * inter_h

    # Union area
    area_a = max(0.0, x1_a - x0_a) * max(0.0, y1_a - y0_a)
    area_b = max(0.0, x1_b - x0_b) * max(0.0, y1_b - y0_b)
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def to_normalized_coordinates(
    bbox: List[float],
    page_width: float,
    page_height: float
) -> List[float]:
    """Convert absolute point/pixel coordinates to normalized [0.0..1.0]."""
    if page_width <= 0 or page_height <= 0:
        return [0.0, 0.0, 1.0, 1.0]
    return [
        round(max(0.0, min(1.0, bbox[0] / page_width)), 4),
        round(max(0.0, min(1.0, bbox[1] / page_height)), 4),
        round(max(0.0, min(1.0, bbox[2] / page_width)), 4),
        round(max(0.0, min(1.0, bbox[3] / page_height)), 4),
    ]
