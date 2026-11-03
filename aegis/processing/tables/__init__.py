"""
aegis.processing.tables
=======================
Table structure extraction, grid validation, TEDS evaluation, and canonical reconstruction.
"""

from aegis.processing.tables.detector import TableExtractor
from aegis.processing.tables.evaluator import TableEvaluationReport, TableEvaluator
from aegis.processing.tables.structure import TableGridValidator

__all__ = [
    "TableExtractor",
    "TableEvaluator",
    "TableEvaluationReport",
    "TableGridValidator",
]
