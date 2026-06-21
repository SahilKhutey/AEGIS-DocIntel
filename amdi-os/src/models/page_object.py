"""
AEGIS-AMDI-OS — Page Object Schema
====================================
Represents a single page in a document.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field, model_validator


class PageLayout(str, Enum):
    """Detected page layout."""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PageOrientation(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    SQUARE = "square"


class PageObject(BaseModel):
    """
    A single page in a document.

    Contains blocks, dimensions, layout info, and page-level metadata.
    """

    # ===== Identity =====
    page_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    page_number: int = Field(..., ge=1)

    # ===== Dimensions =====
    width: float = Field(..., gt=0, description="Page width in points")
    height: float = Field(..., gt=0, description="Page height in points")
    dpi: int = 200

    # ===== Layout =====
    layout: PageLayout = PageLayout.UNKNOWN
    orientation: PageOrientation = PageOrientation.PORTRAIT
    n_columns: int = 1
    is_scanned: bool = False

    # ===== Content =====
    raw_text: str = ""
    blocks: list[str] = Field(default_factory=list)  # Block IDs
    tables: list[str] = Field(default_factory=list)  # Table IDs
    figures: list[str] = Field(default_factory=list)  # Figure IDs

    # ===== Images =====
    page_image: bytes | None = None  # Rendered page image
    thumbnail: bytes | None = None

    # ===== Metadata =====
    margins: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ===== Computed =====
    @computed_field
    @property
    def aspect_ratio(self) -> float:
        """Width / height."""
        return self.width / self.height

    @computed_field
    @property
    def area(self) -> float:
        """Page area in square points."""
        return self.width * self.height

    @computed_field
    @property
    def text_density(self) -> float:
        """Characters per unit area."""
        return len(self.raw_text) / self.area if self.area > 0 else 0

    # ===== Validators =====
    @model_validator(mode="after")
    def check_dimensions(self) -> "PageObject":
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Page dimensions must be positive")
        return self

    model_config = {"json_schema_extra": {
        "example": {
            "doc_id": "doc-123",
            "page_number": 1,
            "width": 612,
            "height": 792,
            "layout": "single_column",
        }
    }}
