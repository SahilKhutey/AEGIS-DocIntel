"""
AEGIS-AMDI-OS — Universal Ingestion Service
============================================
Routes documents to the correct loader based on format detection.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

from src.core.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader, LoaderError
from src.ingestion.docx_loader import DOCXLoader
from src.ingestion.image_loader import ImageLoader
from src.ingestion.ocr_engine import OCREngine
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.pptx_loader import PPTXLoader
from src.ingestion.xlsx_loader import XLSXLoader

logger = logging.getLogger(__name__)

PathLike = Union[str, Path, bytes]


class IngestionService:
    """
    Universal document ingestion service.

    Auto-detects format and routes to the appropriate loader.
    """

    # Magic byte signatures
    PDF_MAGIC = b"%PDF"
    ZIP_MAGIC = b"PK\x03\x04"
    IMAGE_MAGICS = {
        b"\x89PNG": DocumentFormat.IMAGE,
        b"\xff\xd8\xff": DocumentFormat.IMAGE,
        b"GIF8": DocumentFormat.IMAGE,
        b"BM": DocumentFormat.IMAGE,
    }

    # Extension mapping
    EXT_MAP = {
        ".pdf": DocumentFormat.PDF,
        ".docx": DocumentFormat.DOCX,
        ".pptx": DocumentFormat.PPTX,
        ".xlsx": DocumentFormat.XLSX,
        ".png": DocumentFormat.IMAGE,
        ".jpg": DocumentFormat.IMAGE,
        ".jpeg": DocumentFormat.IMAGE,
        ".tiff": DocumentFormat.IMAGE,
        ".tif": DocumentFormat.IMAGE,
        ".bmp": DocumentFormat.IMAGE,
        ".webp": DocumentFormat.IMAGE,
        ".gif": DocumentFormat.IMAGE,
        ".html": DocumentFormat.HTML,
        ".htm": DocumentFormat.HTML,
        ".md": DocumentFormat.MARKDOWN,
        ".markdown": DocumentFormat.MARKDOWN,
        ".txt": DocumentFormat.TEXT,
    }

    def __init__(self, ocr_engine: OCREngine | None = None, **loader_options):
        self.ocr = ocr_engine or OCREngine()
        self.options = loader_options
        self.loaders: dict[DocumentFormat, BaseLoader] = {
            DocumentFormat.PDF: PDFLoader(ocr=self.ocr, **loader_options),
            DocumentFormat.DOCX: DOCXLoader(**loader_options),
            DocumentFormat.PPTX: PPTXLoader(**loader_options),
            DocumentFormat.XLSX: XLSXLoader(**loader_options),
            DocumentFormat.IMAGE: ImageLoader(ocr=self.ocr, **loader_options),
        }
        logger.info(f"IngestionService initialized with {len(self.loaders)} loaders")

    async def ingest(
        self,
        source: PathLike,
        filename: str = "",
        format: DocumentFormat | None = None,
    ) -> DocumentObject:
        """
        Ingest a document from file path, Path object, or bytes.

        Args:
            source: File path, Path, or bytes
            filename: Optional filename
            format: Optional explicit format (auto-detected if None)

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
            raw_bytes = path.read_bytes()
            if not filename:
                filename = path.name

        # Detect format
        if format is None:
            format = self.detect_format(raw_bytes, filename)

        # Get loader
        loader = self.loaders.get(format)
        if loader is None:
            raise LoaderError(f"No loader for format: {format}")

        # Load
        try:
            doc = await loader.load(raw_bytes, filename)
            logger.info(
                f"Loaded {filename}: {format.value}, "
                f"{doc.page_count} pages, {doc.size_bytes} bytes"
            )
            return doc
        except Exception as e:
            logger.exception(f"Failed to load {filename}")
            raise

    def detect_format(self, raw_bytes: bytes, filename: str = "") -> DocumentFormat:
        """
        Auto-detect document format from magic bytes and extension.

        Args:
            raw_bytes: First bytes of the document
            filename: Optional filename for extension hints

        Returns:
            Detected DocumentFormat
        """
        if not raw_bytes:
            return DocumentFormat.UNKNOWN

        # Check PDF magic
        if raw_bytes[:5] == self.PDF_MAGIC:
            return DocumentFormat.PDF

        # Check ZIP magic (Office formats)
        if raw_bytes[:4] == self.ZIP_MAGIC:
            ext = Path(filename).suffix.lower() if filename else ""
            zip_map = {
                ".docx": DocumentFormat.DOCX,
                ".pptx": DocumentFormat.PPTX,
                ".xlsx": DocumentFormat.XLSX,
            }
            if ext in zip_map:
                return zip_map[ext]
            # Try to detect from ZIP contents
            fmt = self._detect_office_format_from_zip(raw_bytes)
            if fmt:
                return fmt
            return DocumentFormat.UNKNOWN

        # Check image magics
        for magic, fmt in self.IMAGE_MAGICS.items():
            if raw_bytes.startswith(magic):
                return DocumentFormat.IMAGE
        # TIFF
        if raw_bytes[:4] in (b"II*\x00", b"MM\x00*"):
            return DocumentFormat.IMAGE

        # Fallback to extension
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in self.EXT_MAP:
                return self.EXT_MAP[ext]

        return DocumentFormat.UNKNOWN

    def _detect_office_format_from_zip(self, raw_bytes: bytes) -> DocumentFormat | None:
        """Detect Office format by inspecting ZIP contents."""
        try:
            import zipfile
            import io
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                names = z.namelist()
                if "[Content_Types].xml" in names:
                    content_types = z.read("[Content_Types].xml").decode("utf-8", errors="ignore")
                    if "wordprocessingml" in content_types:
                        return DocumentFormat.DOCX
                    if "presentationml" in content_types:
                        return DocumentFormat.PPTX
                    if "spreadsheetml" in content_types:
                        return DocumentFormat.XLSX
        except Exception:
            pass
        return None

    def get_supported_formats(self) -> list[DocumentFormat]:
        """Return list of supported formats."""
        return list(self.loaders.keys())

    async def ingest_batch(self, sources: list[PathLike]) -> list[DocumentObject]:
        """Ingest multiple documents in parallel."""
        import asyncio
        tasks = [self.ingest(src) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        docs = []
        for r in results:
            if isinstance(r, DocumentObject):
                docs.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Batch ingest error: {r}")
        return docs
