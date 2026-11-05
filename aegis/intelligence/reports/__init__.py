"""
aegis.intelligence.reports
==========================
Report generation, pre-render validation, and multi-format rendering.
"""

from aegis.intelligence.reports.benchmark import run_report_generation_benchmark
from aegis.intelligence.reports.content_builder import ReportContentBuilder
from aegis.intelligence.reports.renderer import ReportRenderer
from aegis.intelligence.reports.validator import ReportValidator

__all__ = [
    "ReportContentBuilder",
    "ReportRenderer",
    "ReportValidator",
    "run_report_generation_benchmark",
]
