"""
AEGIS-AMDI-OS — Universal Ingestion Service
============================================
Routes documents to the correct loader based on deep format detection.
Provides strict error handling and universal fallback recovery.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional, Union

from src.core.document_object import DocumentFormat, DocumentObject
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
from src.ingestion.ocr_engine import OCREngine
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.pptx_loader import PPTXLoader
from src.ingestion.sniff import sniff_format
from src.ingestion.speech_loader import SpeechLoader
from src.ingestion.text_loader import TextLoader
from src.ingestion.xlsx_loader import XLSXLoader

logger = logging.getLogger(__name__)

PathLike = Union[str, Path, bytes]


class IngestionService:
    """
    Universal document ingestion service.

    Auto-detects format via byte-level sniffing and routes to the appropriate loader.
    Supports timeout budgeting, strict typed exceptions, and zero-crash emergency fallback.
    """

    def __init__(self, ocr_engine: OCREngine | None = None, **loader_options):
        self.ocr = ocr_engine or OCREngine()
        self.options = loader_options
        speech_loader = SpeechLoader(**loader_options)
        text_loader = TextLoader(**loader_options)
        self.fallback_parser = FallbackParser()

        self.loaders: dict[DocumentFormat, BaseLoader] = {
            DocumentFormat.PDF: PDFLoader(ocr=self.ocr, **loader_options),
            DocumentFormat.DOCX: DOCXLoader(**loader_options),
            DocumentFormat.PPTX: PPTXLoader(**loader_options),
            DocumentFormat.XLSX: XLSXLoader(**loader_options),
            DocumentFormat.IMAGE: ImageLoader(ocr=self.ocr, **loader_options),
            DocumentFormat.SPEECH: speech_loader,
            DocumentFormat.AUDIO: speech_loader,
            DocumentFormat.TEXT: text_loader,
            DocumentFormat.MARKDOWN: text_loader,
            DocumentFormat.HTML: text_loader,
        }
        logger.info(f"IngestionService initialized with {len(self.loaders)} loaders")

    async def ingest(
        self,
        source: PathLike,
        filename: str = "",
        format: DocumentFormat | None = None,
        fallback: bool = False,
        timeout: float | None = None,
    ) -> DocumentObject:
        """
        Ingest a document from file path, Path object, or bytes.

        Args:
            source: File path, Path, or bytes
            filename: Optional filename
            format: Optional explicit format (auto-detected if None)
            fallback: If True, uses FallbackParser on errors instead of raising
            timeout: Optional processing timeout in seconds

        Returns:
            DocumentObject with content and metadata
        """
        # Read source
        if isinstance(source, bytes):
            raw_bytes = source
            if not filename:
                filename = "document"
        else:
            path = Path(source)
            try:
                raw_bytes = path.read_bytes()
            except Exception as exc:
                if fallback:
                    return self.fallback_parser.parse(b"", filename=path.name, error_context=str(exc))
                raise DocumentCorruptError(f"Failed to read file from disk: {exc}", filename=path.name) from exc
            if not filename:
                filename = path.name

        # Detect format if not explicitly provided
        detected_res = None
        if format is None:
            detected_res = self.sniff_format_result(raw_bytes, filename)
            format = detected_res.format

        # Get loader
        loader = self.loaders.get(format)
        if loader is None:
            err = UnsupportedFormatError(f"No loader for format: {format}", filename=filename)
            if fallback:
                return self.fallback_parser.parse(
                    raw_bytes,
                    filename=filename,
                    error_context=str(err),
                    original_format=format or DocumentFormat.UNKNOWN,
                )
            raise err

        # Load with timeout and error handling
        async def _load_coro() -> DocumentObject:
            return await loader.load(raw_bytes, filename)

        try:
            if timeout is not None and timeout > 0:
                doc = await asyncio.wait_for(_load_coro(), timeout=timeout)
            else:
                doc = await _load_coro()

            if detected_res and "sniff_confidence" not in doc.metadata:
                doc.metadata["sniff_confidence"] = detected_res.confidence
                doc.metadata["mime_type"] = detected_res.mime_type

            logger.info(
                f"Loaded {filename}: {format.value}, "
                f"{doc.page_count} pages, {doc.size_bytes} bytes"
            )
            return doc

        except asyncio.TimeoutError as exc:
            err = ProcessingTimeoutError(
                f"Ingestion timed out after {timeout} seconds: {filename}",
                filename=filename,
            )
            if fallback:
                return self.fallback_parser.parse(
                    raw_bytes,
                    filename=filename,
                    error_context=str(err),
                    original_format=format,
                )
            raise err from exc

        except (IngestionError, FormatError, LoaderError) as exc:
            if fallback:
                logger.warning(f"Ingestion failed for {filename} ({type(exc).__name__}: {exc}), applying fallback")
                return self.fallback_parser.parse(
                    raw_bytes,
                    filename=filename,
                    error_context=str(exc),
                    original_format=format,
                )
            raise

        except Exception as exc:
            wrapped_err = ExtractionError(f"Unexpected error parsing {filename}: {exc}", filename=filename)
            if fallback:
                logger.warning(f"Unexpected parsing error for {filename}, applying fallback: {exc}")
                return self.fallback_parser.parse(
                    raw_bytes,
                    filename=filename,
                    error_context=str(wrapped_err),
                    original_format=format,
                )
            raise wrapped_err from exc

    def detect_format(self, raw_bytes: bytes, filename: str = "") -> DocumentFormat:
        """Auto-detect document format via byte-level sniffing."""
        return sniff_format(raw_bytes, filename).format

    def sniff_format_result(self, raw_bytes: bytes, filename: str = ""):
        """Return deep sniffing result with confidence and MIME type."""
        return sniff_format(raw_bytes, filename)

    def get_supported_formats(self) -> list[DocumentFormat]:
        """Return list of supported formats."""
        return list(self.loaders.keys())

    async def ingest_batch(self, sources: list[PathLike]) -> list[DocumentObject]:
        """Ingest multiple documents in parallel."""
        tasks = [self.ingest(src, fallback=True) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        docs = []
        for r in results:
            if isinstance(r, DocumentObject):
                docs.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Batch ingest error: {r}")
        return docs


# Module-level convenience function
_DEFAULT_SERVICE: IngestionService | None = None


def get_default_service() -> IngestionService:
    """Get or create singleton IngestionService."""
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = IngestionService()
    return _DEFAULT_SERVICE


async def parse_document(
    source: PathLike,
    filename: str = "",
    format: DocumentFormat | None = None,
    fallback: bool = True,
    timeout: float | None = None,
) -> DocumentObject:
    """
    Universal entry point to parse any document.

    Guarantees:
    - With fallback=True (default): NEVER raises an unhandled exception on malformed,
      fuzzed, corrupted, or encrypted documents. Returns a valid DocumentObject.
    - With fallback=False: raises strict typed exceptions (DocumentCorruptError,
      EncryptedDocumentError, UnsupportedFormatError, ProcessingTimeoutError, SizeLimitError).
    """
    service = get_default_service()
    return await service.ingest(
        source=source,
        filename=filename,
        format=format,
        fallback=fallback,
        timeout=timeout,
    )
