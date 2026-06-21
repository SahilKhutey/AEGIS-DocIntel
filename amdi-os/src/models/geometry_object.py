"""
AEGIS-AMDI-OS — Geometry Object Schema
=======================================
e_i = (x_i, y_i, w_i, h_i, p_i, θ_i, t_i, c_i)

Spatial coordinate representation for every element.
"""
from __future__ import annotations

import math
import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field, model_validator


class ElementType(str, Enum):
    """Types of geometric elements."""
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TITLE = "title"
    SUBTITLE = "subtitle"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    FORMULA = "formula"
    HEADER = "header"
    FOOTER = "footer"
    CAPTION = "caption"
    LIST = "list_item"
    QUOTE = "quote"
    CODE = "code"
    REFERENCE = "reference"
    OTHER = "other"


class BoundingBox(BaseModel):
    """
    Normalized bounding box.
    All coordinates in [0, 1].
    """
    x0: float = Field(0.0, ge=0, le=1)
    y0: float = Field(0.0, ge=0, le=1)
    x1: float = Field(1.0, ge=0, le=1)
    y1: float = Field(1.0, ge=0, le=1)

    @computed_field
    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @computed_field
    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

    @computed_field
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def iou(self, other: "BoundingBox") -> float:
        """Intersection over Union."""
        ix0 = max(self.x0, other.x0)
        iy0 = max(self.y0, other.y0)
        ix1 = min(self.x1, other.x1)
        iy1 = min(self.y1, other.y1)
        iw = max(0.0, ix1 - ix0)
        ih = max(0.0, iy1 - iy0)
        intersection = iw * ih
        union = self.area + other.area - intersection
        return intersection / union if union > 0 else 0.0

    def distance_to(self, other: "BoundingBox") -> float:
        """Euclidean distance between centers."""
        ax, ay = self.center
        bx, by = other.center
        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

    @model_validator(mode="after")
    def check_valid(self) -> "BoundingBox":
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError(f"Invalid bbox: x1<x0 or y1<y0: {self}")
        return self


class GeometryObject(BaseModel):
    """
    e_i = (x_i, y_i, w_i, h_i, p_i, θ_i, t_i, c_i)

    Geometric representation of a document element.
    """

    # ===== Identity =====
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    page_id: str | None = None

    # ===== Position =====
    page: int = Field(..., ge=1)
    bbox: BoundingBox

    # ===== Orientation =====
    rotation: float = Field(0.0, ge=0, lt=2 * math.pi, description="Rotation in radians")

    # ===== Type & Content =====
    type: ElementType = ElementType.TEXT
    content: str = ""
    section: str | None = None
    section_level: int = 0

    # ===== Importance & Frequency =====
    frequency: int = 1
    importance_weight: float = 1.0
    recurrence_id: str | None = None

    # ===== Entropy =====
    entropy: float = 0.0

    # ===== Metadata =====
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ===== Computed =====
    @computed_field
    @property
    def x_center(self) -> float:
        return self.bbox.center[0]

    @computed_field
    @property
    def y_center(self) -> float:
        return self.bbox.center[1]

    @computed_field
    @property
    def area_ratio(self) -> float:
        """Fraction of page area covered."""
        return self.bbox.area

    # ===== Methods =====
    def distance_to(self, other: "GeometryObject") -> float:
        """Geometric distance with page penalty."""
        d = self.bbox.distance_to(other.bbox)
        page_penalty = abs(self.page - other.page) * 1.5
        return d + page_penalty

    def alignment_with(self, other: "GeometryObject") -> float:
        """Alignment score A(i, j) ∈ [0, 1]."""
        a_x = max(0.0, 1.0 - abs(self.x_center - other.x_center))
        a_y = max(0.0, 1.0 - abs(self.y_center - other.y_center))
        return (a_x + a_y) / 2

    model_config = {"json_schema_extra": {
        "example": {
            "doc_id": "doc-123",
            "page": 1,
            "bbox": {"x0": 0.1, "y0": 0.1, "x1": 0.9, "y1": 0.2},
            "type": "heading",
            "content": "Executive Summary",
        }
    }}
