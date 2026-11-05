"""
aegis.processing.layout.detector
================================
Heuristic and geometric layout detector partitioning document pages into classified regions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import fitz

from aegis.processing.layout.regions import normalize_region_type, to_normalized_coordinates
from aegis.processing.models import CoordinateSystem, LayoutRegion, PageTextExtraction, RegionType


class LayoutDetector:
    """Detects layout regions (headings, paragraphs, headers, footers, tables) from page blocks."""

    def __init__(
        self,
        header_breakpoint: float = 0.08,
        footer_breakpoint: float = 0.92,
        heading_height_thresholds: tuple[float, float] = (20.0, 13.0)
    ):
        self.header_breakpoint = header_breakpoint
        self.footer_breakpoint = footer_breakpoint
        self.h_thresh_high, self.h_thresh_mid = heading_height_thresholds

    def detect_regions(
        self,
        page_extraction: PageTextExtraction,
        page_width: float = 612.0,
        page_height: float = 792.0
    ) -> List[LayoutRegion]:
        """Classify extraction blocks into canonical layout regions."""
        regions: List[LayoutRegion] = []
        doc_id = page_extraction.document_id
        page_num = page_extraction.page_number

        coord_sys = CoordinateSystem(
            units="normalized",
            origin="top_left",
            page_width=page_width,
            page_height=page_height,
        )

        for idx, block in enumerate(page_extraction.blocks):
            x0, y0, x1, y1 = block.bbox
            norm_bbox = to_normalized_coordinates(block.bbox, page_width, page_height)
            height = y1 - y0
            rel_y_top = norm_bbox[1]
            rel_y_bottom = norm_bbox[3]

            # Classification rules:
            if rel_y_bottom <= self.header_breakpoint:
                rtype = RegionType.HEADER
            elif rel_y_top >= self.footer_breakpoint:
                rtype = RegionType.FOOTER
            elif height >= self.h_thresh_high:
                rtype = RegionType.TITLE
            elif height >= self.h_thresh_mid:
                rtype = RegionType.SECTION_HEADER
            elif "table" in block.text.lower() and len(block.text.split("\n")) > 2:
                rtype = RegionType.TABLE
            else:
                rtype = RegionType.PARAGRAPH

            regions.append(
                LayoutRegion(
                    region_id=f"REGION-{page_num:03d}-{idx:04d}",
                    document_id=doc_id,
                    page_number=page_num,
                    region_type=rtype,
                    bbox=norm_bbox,
                    coordinate_system=coord_sys,
                    text_reference=block.block_id,
                    confidence=0.85,
                )
            )

        return regions
