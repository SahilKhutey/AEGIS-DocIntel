"""
AMDI-OS — Shared Element Model
================================
Universal document element used by all representation engines.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ElementType(str, Enum):
    TEXT      = "text"
    HEADING   = "heading"
    PARAGRAPH = "paragraph"
    TITLE     = "title"
    SUBTITLE  = "subtitle"
    TABLE     = "table"
    FIGURE    = "figure"
    EQUATION  = "equation"
    HEADER    = "header"
    FOOTER    = "footer"
    CAPTION   = "caption"
    LIST_ITEM = "list_item"
    FORMULA   = "formula"
    CODE      = "code"
    QUOTE     = "quote"
    REFERENCE = "reference"
    OTHER     = "other"


@dataclass(frozen=True)
class BoundingBox:
    x0: float; y0: float; x1: float; y1: float

    @property
    def width(self) -> float: return self.x1 - self.x0
    @property
    def height(self) -> float: return self.y1 - self.y0
    @property
    def area(self) -> float: return max(0., self.width) * max(0., self.height)
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def iou(self, other: "BoundingBox") -> float:
        ix0, iy0 = max(self.x0, other.x0), max(self.y0, other.y0)
        ix1, iy1 = min(self.x1, other.x1), min(self.y1, other.y1)
        inter = max(0., ix1 - ix0) * max(0., iy1 - iy0)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def to_tuple(self) -> tuple: return (self.x0, self.y0, self.x1, self.y1)
    def to_normalized(self, pw: float, ph: float) -> "BoundingBox":
        return BoundingBox(self.x0 / pw, self.y0 / ph, self.x1 / pw, self.y1 / ph)


@dataclass
class GeometricElement:
    """
    Universal element carrying all layer annotations.
    Created by the orchestrator from NormalizedBlock objects.
    """
    element_id:        str           = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id:            str           = ""
    page:              int           = 0
    type:              ElementType   = ElementType.PARAGRAPH
    content:           str           = ""
    bbox:              Optional[BoundingBox] = None
    section:           Optional[str] = None
    section_level:     int           = 0
    parent_id:         Optional[str] = None

    # Layer annotations (set by engines)
    embedding:         Optional[list[float]] = None
    importance_weight: float                 = 1.0
    frequency:         int                   = 1
    recurrence_id:     Optional[str]         = None
    is_template:       bool                  = False
    entropy:           float                 = 0.0

    # Semantic annotations
    entities:          list[tuple[str, str]] = field(default_factory=list)
    keyphrases:        list[str]             = field(default_factory=list)
    summary:           str                   = ""

    metadata:          dict[str, Any]        = field(default_factory=dict)

    @property
    def token_count(self) -> int:
        return max(1, int(len(self.content.split()) * 1.33))

    @property
    def is_structural(self) -> bool:
        return self.type in (ElementType.TABLE, ElementType.FIGURE, ElementType.EQUATION)

    def geo_vector(self) -> list[float]:
        if not self.bbox:
            return [0., 0., 0., 0., float(self.page)]
        return [self.bbox.x0, self.bbox.y0, self.bbox.width, self.bbox.height, float(self.page)]

    def to_compact(self) -> dict:
        return {
            "id": self.element_id, "type": self.type.value,
            "page": self.page, "section": self.section,
            "weight": round(self.importance_weight, 4),
            "content": self.content[:300],
            "bbox": self.bbox.to_tuple() if self.bbox else None,
        }

    def __repr__(self) -> str:
        return f"<{self.type.value} p={self.page} w={self.importance_weight:.2f} '{self.content[:40]}'>"
