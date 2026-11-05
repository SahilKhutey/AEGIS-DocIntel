"""
aegis.processing.extraction
===========================
Text extraction subsystems including native PDF parsing, OCR pipelines,
text normalization, and confidence evaluation.
"""

from aegis.processing.extraction.confidence import CalibrationReport, ConfidenceEvaluator
from aegis.processing.extraction.native_pdf import NativePDFExtractor
from aegis.processing.extraction.ocr import OCRExtractor
from aegis.processing.extraction.text_normalizer import TextNormalizer

__all__ = [
    "NativePDFExtractor",
    "OCRExtractor",
    "TextNormalizer",
    "ConfidenceEvaluator",
    "CalibrationReport",
]
