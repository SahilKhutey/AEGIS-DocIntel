"""
aegis.processing.reading_order
==============================
Document reading order resolution, graph construction, topological sorting,
and ranking evaluation (Kendall's tau).
"""

from aegis.processing.reading_order.evaluator import (
    ReadingOrderEvaluationReport,
    ReadingOrderEvaluator,
)
from aegis.processing.reading_order.graph import ReadingOrderGraph
from aegis.processing.reading_order.resolver import ReadingOrderResolver

__all__ = [
    "ReadingOrderGraph",
    "ReadingOrderResolver",
    "ReadingOrderEvaluator",
    "ReadingOrderEvaluationReport",
]
