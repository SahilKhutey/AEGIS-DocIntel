"""
Chart Understander
====================

Detects chart type and extracts data from chart images.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class ChartType(Enum):
    """Chart type detection."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    AREA = "area"
    HEATMAP = "heatmap"
    UNKNOWN = "unknown"


@dataclass
class ChartData:
    """Extracted chart data."""

    chart_type: ChartType
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    series: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "series": self.series,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class ChartUnderstander:
    """
    Understands chart images and extracts data.

    Production: use a vision model (CLIP, GPT-4V, or specialized).
    """

    def __init__(self) -> None:
        self.chart_keywords = {
            ChartType.BAR: ["bar", "column", "histogram"],
            ChartType.LINE: ["line", "trend", "time series"],
            ChartType.PIE: ["pie", "donut", "proportion"],
            ChartType.SCATTER: ["scatter", "correlation", "regression"],
            ChartType.HEATMAP: ["heatmap", "matrix", "correlation matrix"],
            ChartType.AREA: ["area", "stacked", "filled"],
        }

    def understand(self, chart_image: bytes) -> ChartData:
        """Understand a chart image and extract data."""
        # detect chart type (heuristic based on image properties)
        chart_type = self._detect_type(chart_image)
        # extract axis labels (OCR or vision model)
        x_label = self._extract_xlabel(chart_image)
        y_label = self._extract_ylabel(chart_image)
        # extract data series (vision model)
        series = self._extract_series(chart_image, chart_type)
        # compute confidence
        confidence = 0.85 if series else 0.3
        return ChartData(
            chart_type=chart_type,
            x_label=x_label,
            y_label=y_label,
            series=series,
            confidence=confidence,
            metadata={
                "image_size": len(chart_image),
                "extraction_method": "vision_model",
            },
        )

    def _detect_type(self, chart_image: bytes) -> ChartType:
        """Detect chart type from image bytes (heuristic)."""
        # In production: use a CNN classifier
        # Placeholder: use metadata in image bytes if present
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(chart_image))
            width, height = img.size
            aspect = width / max(height, 1)
            # Heuristic: pie charts tend to be square, bar/line wider
            if 0.8 < aspect < 1.2:
                return ChartType.PIE
            if aspect > 2.0:
                return ChartType.LINE
            return ChartType.BAR
        except Exception:
            return ChartType.UNKNOWN

    def _extract_xlabel(self, chart_image: bytes) -> str:
        """Extract X-axis label via OCR."""
        # In production: use Tesseract or vision model
        return "X-Axis"

    def _extract_ylabel(self, chart_image: bytes) -> str:
        """Extract Y-axis label via OCR."""
        return "Y-Axis"

    def _extract_series(
        self, chart_image: bytes, chart_type: ChartType
    ) -> List[Dict[str, Any]]:
        """Extract data series from chart image."""
        # In production: use vision model with structured output
        # Placeholder: return empty series
        return []

    def detect_anomalies(self, chart_data: ChartData) -> List[Dict[str, Any]]:
        """Detect anomalies in chart data (e.g., outliers)."""
        anomalies: List[Dict[str, Any]] = []
        for series in chart_data.series:
            values = [p.get("y", 0) for p in series.get("points", [])]
            if not values or len(values) < 3:
                continue
            arr = np.array(values)
            mean, std = float(arr.mean()), float(arr.std())
            if std > 0:
                for i, v in enumerate(values):
                    z = abs(v - mean) / std
                    if z > 3:
                        anomalies.append({
                            "series": series.get("name", "unknown"),
                            "index": i,
                            "value": v,
                            "z_score": z,
                        })
        return anomalies
