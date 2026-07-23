"""
AEGIS-AMDI-OS — PDF Loader
=============================
Handles text-based PDFs (PyMuPDF) and scanned PDFs (OCR fallback).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from src.core.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader, FormatError, SizeLimitError
from src.ingestion.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class PDFLoader(BaseLoader):
    """
    PDF document loader.

    Strategy:
    1. Try PyMuPDF for text extraction
    2. If scanned (no text), render pages as images and OCR
    3. Extract metadata (title, author, etc.)
    """

    FORMAT_NAME = "pdf"
    SUPPORTED_EXTENSIONS = {".pdf"}
    PDF_MAGIC = b"%PDF"

    def __init__(self, ocr: OCREngine | None = None, max_size_mb: int = 500, **options):
        super().__init__(**options)
        self.ocr = ocr or OCREngine()
        self.max_size_mb = max_size_mb

    def validate(self, raw_bytes: bytes) -> bool:
        """Check if bytes are a valid PDF."""
        if not raw_bytes:
            return False
        if len(raw_bytes) < 4:
            return False
        return raw_bytes.startswith(self.PDF_MAGIC)

    async def load(self, source, filename: str = "") -> DocumentObject:
        """Load a PDF document."""
        raw_bytes, name = self.read_source(source)
        if filename:
            name = filename
        if not name:
            name = "document.pdf"

        # Validate
        if not self.validate(raw_bytes):
            raise FormatError("Not a valid PDF file")

        # Size check
        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise SizeLimitError(f"PDF too large: {size_mb:.1f}MB > {self.max_size_mb}MB")

        # Extract metadata and content
        metadata = self._extract_metadata(raw_bytes)
        page_count = metadata.get("page_count", 0)
        is_scanned = metadata.get("is_scanned", False)

        # Build DocumentObject
        doc = DocumentObject(
            filename=name,
            format=DocumentFormat.PDF,
            raw_bytes=raw_bytes,
            metadata=metadata,
            page_count=page_count,
            title=metadata.get("title"),
            author=metadata.get("author"),
            subject=metadata.get("subject"),
        )
        doc.metadata["scanned"] = is_scanned
        return doc

    def _extract_metadata(self, raw_bytes: bytes) -> dict[str, Any]:
        """Extract PDF metadata and detect scanned pages."""
        metadata: dict[str, Any] = {}
        try:
            pdf = fitz.open(stream=raw_bytes, filetype="pdf")
            try:
                # Standard metadata
                meta = pdf.metadata or {}
                metadata["title"] = meta.get("title")
                metadata["author"] = meta.get("author")
                metadata["subject"] = meta.get("subject")
                metadata["keywords"] = meta.get("keywords")
                metadata["creator"] = meta.get("creator")
                metadata["producer"] = meta.get("producer")
                metadata["creation_date"] = str(meta.get("creationDate", ""))
                metadata["page_count"] = len(pdf)

                # Detect if scanned (sample first 5 pages)
                text_chars = 0
                image_count = 0
                for i in range(min(5, len(pdf))):
                    page = pdf[i]
                    text_chars += len(page.get_text().strip())
                    image_count += len(page.get_images(full=True))
                metadata["is_scanned"] = text_chars < 50 and image_count > 0
                metadata["text_chars_sample"] = text_chars
                metadata["image_count_sample"] = image_count

                # Extract outline (table of contents)
                try:
                    toc = pdf.get_toc()
                    if toc:
                        metadata["toc"] = [
                            {"level": lvl, "title": title, "page": page}
                            for lvl, title, page in toc[:50]
                        ]
                except Exception:
                    pass
            finally:
                pdf.close()
        except Exception as e:
            logger.warning(f"PDF metadata extraction failed: {e}")
            metadata["page_count"] = 0
            metadata["is_scanned"] = False
        return metadata

    def extract_pages_for_ocr(self, raw_bytes: bytes, dpi: int = 150, max_pages: int = 20) -> list[bytes]:
        """
        Render PDF pages as images for OCR processing.
        Returns list of PNG image bytes.
        """
        images = []
        try:
            pdf = fitz.open(stream=raw_bytes, filetype="pdf")
            try:
                for i in range(min(max_pages, len(pdf))):
                    page = pdf[i]
                    pix = page.get_pixmap(dpi=dpi)
                    images.append(pix.tobytes("png"))
            finally:
                pdf.close()
        except Exception as e:
            logger.error(f"Failed to render PDF pages: {e}")
        return images

    async def ocr_extract(self, raw_bytes: bytes, max_pages: int = 50) -> str:
        """OCR all pages of a scanned PDF and return combined text."""
        images = self.extract_pages_for_ocr(raw_bytes, max_pages=max_pages)
        full_text = []
        for i, img_bytes in enumerate(images):
            page_text = await self.ocr.recognize(img_bytes)
            full_text.append(f"\n--- Page {i+1} ---\n{page_text}\n")
        return "\n".join(full_text)
