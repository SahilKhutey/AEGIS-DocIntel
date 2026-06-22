"""
Caption Generator
==================

Generates captions for images, tables, and charts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional


class CaptionStyle(Enum):
    """Caption style."""

    DESCRIPTIVE = "descriptive"  # What is shown
    ANALYTICAL = "analytical"    # What it means
    CONCISE = "concise"          # Brief description


class CaptionGenerator:
    """
    Generates captions for visual content.

    Production: use BLIP-2, LLaVA, or GPT-4V.
    """

    def __init__(self, default_style: CaptionStyle = CaptionStyle.DESCRIPTIVE) -> None:
        self.default_style = default_style

    def generate(
        self,
        image_data: bytes,
        style: Optional[CaptionStyle] = None,
        context: Optional[str] = None,
    ) -> str:
        """Generate a caption for an image."""
        style = style or self.default_style
        # In production: use vision-language model
        # Placeholder: generate based on heuristics
        if style == CaptionStyle.CONCISE:
            return "An image from the document."
        if style == CaptionStyle.ANALYTICAL:
            return (
                "This image illustrates key concepts from the document. "
                "It provides visual context that complements the surrounding text."
            )
        # DESCRIPTIVE
        return (
            "A figure showing important visual information. "
            "Refer to the accompanying text for detailed interpretation."
        )

    def generate_table_caption(self, table_structure: Any) -> str:
        """Generate a caption for a table."""
        if not hasattr(table_structure, "headers") or not table_structure.headers:
            return "A data table."
        return (
            f"A table with {table_structure.row_count} rows and "
            f"{table_structure.col_count} columns, showing "
            f"{', '.join(table_structure.headers[:3])}{'...' if len(table_structure.headers) > 3 else ''}."
        )

    def generate_chart_caption(self, chart_data: Any) -> str:
        """Generate a caption for a chart."""
        chart_type = (
            chart_data.chart_type.value
            if hasattr(chart_data, "chart_type")
            else "chart"
        )
        title = (
            chart_data.title if hasattr(chart_data, "title") and chart_data.title else ""
        )
        prefix = f"{title}: " if title else ""
        return (
            f"{prefix}A {chart_type} chart visualizing the relationship "
            f"between {chart_data.x_label if hasattr(chart_data, 'x_label') else 'X'} "
            f"and {chart_data.y_label if hasattr(chart_data, 'y_label') else 'Y'}."
        )

    def generate_batch(
        self,
        images: List[bytes],
        style: Optional[CaptionStyle] = None,
    ) -> List[str]:
        """Generate captions for a batch of images."""
        return [self.generate(img, style) for img in images]
