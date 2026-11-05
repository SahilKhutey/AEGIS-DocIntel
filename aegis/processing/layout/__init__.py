"""
aegis.processing.layout
=======================
Layout analysis package supporting region classification, IoU/mAP evaluation,
and visual overlay debugging.
"""

from aegis.processing.layout.detector import LayoutDetector
from aegis.processing.layout.evaluator import ClassMetric, LayoutEvaluationReport, LayoutEvaluator
from aegis.processing.layout.regions import (
    compute_iou,
    normalize_region_type,
    to_normalized_coordinates,
)
from aegis.processing.layout.visualizer import LayoutVisualizer

__all__ = [
    "LayoutDetector",
    "LayoutEvaluator",
    "LayoutEvaluationReport",
    "ClassMetric",
    "LayoutVisualizer",
    "compute_iou",
    "normalize_region_type",
    "to_normalized_coordinates",
]
