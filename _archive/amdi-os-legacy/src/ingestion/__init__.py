"""
AEGIS-AMDI-OS — Ingestion Layer
=================================
Document loading and format detection.
"""
from src.ingestion.base import BaseLoader, LoaderError, FormatError, SizeLimitError
from src.ingestion.ocr_engine import OCREngine
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.docx_loader import DOCXLoader
from src.ingestion.pptx_loader import PPTXLoader
from src.ingestion.xlsx_loader import XLSXLoader
from src.ingestion.image_loader import ImageLoader
from src.ingestion.service import IngestionService

__all__ = [
    "BaseLoader", "LoaderError", "FormatError", "SizeLimitError",
    "OCREngine",
    "PDFLoader", "DOCXLoader", "PPTXLoader", "XLSXLoader", "ImageLoader",
    "IngestionService",
]
