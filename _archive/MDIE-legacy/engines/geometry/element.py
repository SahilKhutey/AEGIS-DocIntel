"""
AEGIS-MDIE — Geometric Element
================================
Atomic unit: e_i = (x_i, y_i, w_i, h_i, p_i, t_i, c_i)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ElementType(str, Enum):
    TEXT       = "text"
    HEADING    = "heading"
    PARAGRAPH  = "paragraph"
    TABLE      = "table"
    FIGURE     = "figure"
    EQUATION   = "equation"
    HEADER     = "header"       # page header
    FOOTER     = "footer"       # page footer
    CAPTION    = "caption"
    LIST_ITEM  = "list_item"
    FORMULA    = "formula"
    CODE       = "code"


@dataclass(frozen=True)
class BoundingBox:
    """Immutable 4-corner bounding box in PDF user-space coordinates."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:  return self.x1 - self.x0
    @property
    def height(self) -> float: return self.y1 - self.y0
    @property
    def area(self) -> float:   return max(0.0, self.width) * max(0.0, self.height)
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def iou(self, other: "BoundingBox") -> float:
        ix0, iy0 = max(self.x0, other.x0), max(self.y0, other.y0)
        ix1, iy1 = min(self.x1, other.x1), min(self.y1, other.y1)
        inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def contains(self, other: "BoundingBox") -> bool:
        return (self.x0 <= other.x0 and self.y0 <= other.y0
                and self.x1 >= other.x1 and self.y1 >= other.y1)

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    def to_normalized(self, pw: float, ph: float) -> "BoundingBox":
        return BoundingBox(
            self.x0 / pw, self.y0 / ph,
            self.x1 / pw, self.y1 / ph,
        )


@dataclass
class GeometricElement:
    """
    Full mathematical document element.
    e_i = (x_i, y_i, w_i, h_i, p_i, t_i, c_i)
    """
    element_id:         str            = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id:             str            = ""
    bbox:               Optional[BoundingBox] = None
    page:               int            = 0
    type:               ElementType    = ElementType.TEXT
    content:            str            = ""
    metadata:           dict[str, Any] = field(default_factory=dict)

    # Mathematical properties (set by engines)
    frequency:          int   = 1
    importance_weight:  float = 1.0
    is_template_element: bool = False
    recurrence_id:      Optional[str] = None

    # Hierarchy coordinates L = (p, s, b, l, t)
    section:            Optional[str] = None
    section_level:      int           = 0
    block_index:        int           = 0
    line_index:         int           = 0
    parent_id:          Optional[str] = None

    # Embeddings (set externally)
    embedding:          Optional[list[float]] = None

    @property
    def token_count(self) -> int:
        """Approximate token count (4/3 × word count heuristic)."""
        return max(1, int(len(self.content.split()) * 1.33))

    def geometry_vector(self) -> list[float]:
        """5-D spatial vector: [x, y, w, h, page]."""
        if not self.bbox:
            return [0.0, 0.0, 0.0, 0.0, float(self.page)]
        return [self.bbox.x0, self.bbox.y0,
                self.bbox.width, self.bbox.height, float(self.page)]

    def hierarchical_coord(self) -> tuple:
        """L = (page, section_level, block_index, line_index)"""
        return (self.page, self.section_level, self.block_index, self.line_index)

    def to_compact(self) -> dict:
        return {
            "id":      self.element_id,
            "type":    self.type.value,
            "page":    self.page,
            "bbox":    self.bbox.to_tuple() if self.bbox else None,
            "section": self.section,
            "weight":  round(self.importance_weight, 4),
            "freq":    self.frequency,
            "content": self.content[:200],
        }

    def __repr__(self) -> str:
        return (f"<{self.type.value} p={self.page} "
                f"w={self.importance_weight:.2f} '{self.content[:40]}...'>")
