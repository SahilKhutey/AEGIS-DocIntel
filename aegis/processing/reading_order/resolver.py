"""
aegis.processing.reading_order.resolver
=======================================
Layout-aware reading order resolver handling multi-column documents and semantic flow.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aegis.processing.models import LayoutRegion, ReadingOrderResult, RegionType
from aegis.processing.reading_order.graph import ReadingOrderGraph


class ReadingOrderResolver:
    """Resolves logical reading sequence from geometric regions, preventing column interleaving."""

    def __init__(self, column_gap_threshold: float = 0.15):
        self.column_gap_threshold = column_gap_threshold

    def resolve(
        self,
        regions: List[LayoutRegion],
        document_id: str,
        page_number: int = 1
    ) -> ReadingOrderResult:
        """Construct reading order sequence using column-aware geometric graph sorting."""
        if not regions:
            return ReadingOrderResult(
                document_id=document_id,
                page_number=page_number,
                reading_order=[],
                ordering_method="layout_graph",
                confidence=1.0,
            )

        graph = ReadingOrderGraph()
        for r in regions:
            graph.add_node(r.region_id)

        # Separate full-width top headers, multi-column body, and footers
        headers: List[LayoutRegion] = []
        footers: List[LayoutRegion] = []
        body: List[LayoutRegion] = []

        for r in regions:
            x0, y0, x1, y1 = r.bbox
            width = x1 - x0
            if r.region_type == RegionType.HEADER or (y1 <= 0.08 and width >= 0.70):
                headers.append(r)
            elif r.region_type == RegionType.FOOTER or (y0 >= 0.92 and width >= 0.70):
                footers.append(r)
            else:
                body.append(r)

        # Sort headers top-to-bottom
        headers.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
        # Sort footers top-to-bottom
        footers.sort(key=lambda r: (r.bbox[1], r.bbox[0]))

        # Detect columns in body: cluster by x0
        body_columns: List[List[LayoutRegion]] = []
        if body:
            sorted_body = sorted(body, key=lambda r: r.bbox[0])
            current_col = [sorted_body[0]]

            for r in sorted_body[1:]:
                # If gap between x0 of current and previous block exceeds threshold, new column
                prev_x0 = current_col[-1].bbox[0]
                if abs(r.bbox[0] - prev_x0) > self.column_gap_threshold:
                    body_columns.append(current_col)
                    current_col = [r]
                else:
                    current_col.append(r)
            body_columns.append(current_col)

            # Sort each column top-to-bottom
            for col in body_columns:
                col.sort(key=lambda r: (r.bbox[1], r.bbox[0]))

        # Assemble global linear sequence: headers -> col1 -> col2 -> ... -> footers
        final_sequence: List[str] = []

        for h in headers:
            final_sequence.append(h.region_id)

        for col in body_columns:
            for b in col:
                final_sequence.append(b.region_id)

        for f in footers:
            final_sequence.append(f.region_id)

        # Add precedence edges along the computed sequence into graph
        for i in range(len(final_sequence) - 1):
            graph.add_precedence(final_sequence[i], final_sequence[i + 1])

        # Associate captions to preceding figures / tables if adjacent
        for idx, r in enumerate(regions):
            if r.region_type == RegionType.CAPTION and idx > 0:
                prev_r = regions[idx - 1]
                if prev_r.region_type in [RegionType.FIGURE, RegionType.TABLE]:
                    graph.add_relationship(
                        source_id=prev_r.region_id,
                        target_id=r.region_id,
                        relation_type="figure_to_caption" if prev_r.region_type == RegionType.FIGURE else "table_to_caption"
                    )

        sorted_order = graph.topological_sort()

        return ReadingOrderResult(
            document_id=document_id,
            page_number=page_number,
            reading_order=sorted_order,
            ordering_method="layout_graph",
            confidence=0.95,
            relationships=graph.relationships,
        )
