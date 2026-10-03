"""
AEGIS-AMDI-OS — Ingestion Layer
=================================
Document loading, sniffing, and format detection with zero silent failures.
"""
from src.ingestion.base import BaseLoader
from src.ingestion.docx_loader import DOCXLoader
from src.ingestion.exceptions import (
    DocumentCorruptError,
    EncryptedDocumentError,
    ExtractionError,
    FormatError,
    IngestionError,
    LoaderError,
    ProcessingTimeoutError,
    SizeLimitError,
    UnsupportedFormatError,
)
from src.ingestion.fallback_parser import FallbackParser
from src.ingestion.image_loader import ImageLoader
from src.ingestion.image_parser import AdvancedImageParser
from src.ingestion.ocr_engine import OCREngine
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.pptx_loader import PPTXLoader
from src.ingestion.service import IngestionService, get_default_service, parse_document
from src.ingestion.sniff import SniffResult, sniff_format
from src.ingestion.speech_loader import SpeechLoader
from src.ingestion.text_loader import TextLoader
from src.ingestion.xlsx_loader import XLSXLoader

__all__ = [
    "BaseLoader",
    "IngestionError",
    "DocumentCorruptError",
    "EncryptedDocumentError",
    "UnsupportedFormatError",
    "ProcessingTimeoutError",
    "ExtractionError",
    "LoaderError",
    "FormatError",
    "SizeLimitError",
    "OCREngine",
    "PDFLoader",
    "DOCXLoader",
    "PPTXLoader",
    "XLSXLoader",
    "ImageLoader",
    "SpeechLoader",
    "TextLoader",
    "AdvancedImageParser",
    "FallbackParser",
    "IngestionService",
    "get_default_service",
    "parse_document",
    "sniff_format",
    "SniffResult",
]
