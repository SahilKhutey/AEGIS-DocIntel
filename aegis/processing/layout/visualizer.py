"""
aegis.processing.layout.visualizer
==================================
Generates visual SVG overlays for layout bounding box debugging and error inspection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from aegis.processing.layout.evaluator import LayoutEvaluationReport
from aegis.processing.models import LayoutRegion


class LayoutVisualizer:
    """Renders visual SVG overlays comparing ground truth and predicted layout regions."""

    @staticmethod
    def render_svg_overlay(
        predictions: List[LayoutRegion],
        ground_truths: List[LayoutRegion],
        evaluation_report: LayoutEvaluationReport,
        page_width: float = 612.0,
        page_height: float = 792.0
    ) -> str:
        """Generate an SVG string illustrating matched, missed, and false-positive layout regions."""
        matched_gt_ids = {m["gt_id"] for m in evaluation_report.matched_pairs}
        matched_pred_ids = {m["pred_id"] for m in evaluation_report.matched_pairs}

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {page_width} {page_height}" width="{page_width}" height="{page_height}">',
            f'  <rect width="100%" height="100%" fill="#fafafa" stroke="#cccccc" stroke-width="1"/>',
            f'  <defs>',
            f'    <style>',
            f'      .gt-matched {{ fill: rgba(46, 204, 113, 0.15); stroke: #27ae60; stroke-width: 2; }}',
            f'      .gt-missed {{ fill: rgba(230, 126, 34, 0.15); stroke: #d35400; stroke-width: 2; stroke-dasharray: 4,4; }}',
            f'      .pred-fp {{ fill: rgba(231, 76, 60, 0.15); stroke: #c0392b; stroke-width: 2; }}',
            f'      .label {{ font-family: sans-serif; font-size: 10px; font-weight: bold; fill: #2c3e50; }}',
            f'    </style>',
            f'  </defs>',
        ]

        # Draw Ground Truths
        for gt in ground_truths:
            x0, y0, x1, y1 = gt.bbox
            # If normalized, scale to page dimensions
            if gt.coordinate_system.units == "normalized":
                x0 *= page_width
                y0 *= page_height
                x1 *= page_width
                y1 *= page_height
            w = max(1.0, x1 - x0)
            h = max(1.0, y1 - y0)

            cls_name = "gt-matched" if gt.region_id in matched_gt_ids else "gt-missed"
            svg_lines.append(
                f'  <rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" class="{cls_name}"/>'
            )
            svg_lines.append(
                f'  <text x="{x0 + 4:.1f}" y="{y0 + 12:.1f}" class="label">{gt.region_type.value} [{gt.region_id}]</text>'
            )

        # Draw False Positive Predictions
        for p in predictions:
            if p.region_id not in matched_pred_ids:
                x0, y0, x1, y1 = p.bbox
                if p.coordinate_system.units == "normalized":
                    x0 *= page_width
                    y0 *= page_height
                    x1 *= page_width
                    y1 *= page_height
                w = max(1.0, x1 - x0)
                h = max(1.0, y1 - y0)
                svg_lines.append(
                    f'  <rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" class="pred-fp"/>'
                )
                svg_lines.append(
                    f'  <text x="{x0 + 4:.1f}" y="{y0 + 12:.1f}" class="label" fill="#c0392b">FP: {p.region_type.value}</text>'
                )

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    @classmethod
    def export_overlay(
        cls,
        predictions: List[LayoutRegion],
        ground_truths: List[LayoutRegion],
        evaluation_report: LayoutEvaluationReport,
        output_file: Path | str,
        page_width: float = 612.0,
        page_height: float = 792.0
    ) -> Path:
        """Export SVG overlay to a file path."""
        p = Path(output_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        svg_content = cls.render_svg_overlay(
            predictions, ground_truths, evaluation_report, page_width, page_height
        )
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg_content)
        return p
