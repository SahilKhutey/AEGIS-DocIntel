"""
AEGIS-AMDI-OS — PDF Loader
=============================
Handles text-based PDFs (PyMuPDF) and scanned PDFs (OCR fallback).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from src.models.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader
from src.ingestion.exceptions import (
    DocumentCorruptError,
    EncryptedDocumentError,
    FormatError,
    LoaderError,
    SizeLimitError,
)
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
        """Check if bytes are a valid PDF.

        Scans the first 1024 bytes rather than requiring the magic bytes at
        position 0, so that Ghostscript-generated PDFs (which prepend a
        version comment before the ``%PDF-`` marker) are accepted.
        """
        if not raw_bytes or len(raw_bytes) < 4:
            return False
        return self.PDF_MAGIC in raw_bytes[:1024]

    async def load(self, source, filename: str = "") -> DocumentObject:
        """Load a PDF document."""
        raw_bytes, name = self.read_source(source)
        if filename:
            name = filename
        if not name:
            name = "document.pdf"

        # Validate format
        if not self.validate(raw_bytes):
            raise FormatError(f"Invalid PDF file format: {name}", filename=name)

        if fitz is None:
            raise LoaderError("PyMuPDF (fitz) is not installed", filename=name)

        # Size check
        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise SizeLimitError(f"PDF too large: {size_mb:.1f}MB > {self.max_size_mb}MB", filename=name)

        # Open and inspect
        try:
            pdf = fitz.open(stream=raw_bytes, filetype="pdf")
        except Exception as exc:
            err_msg = str(exc).lower()
            if "password" in err_msg or "encrypted" in err_msg:
                raise EncryptedDocumentError(f"PDF is encrypted: {exc}", filename=name) from exc
            raise DocumentCorruptError(f"Malformed PDF file: {exc}", filename=name) from exc

        try:
            if getattr(pdf, "is_encrypted", False):
                # Try authenticate with empty password just in case
                if not pdf.authenticate(""):
                    raise EncryptedDocumentError(f"PDF is password-protected: {name}", filename=name)

            # Extract text from all pages in a single pass — used both for
            # content and for scanned-page detection in _extract_metadata.
            # This avoids a redundant fitz pass over the first 5 pages that
            # previously occurred when _extract_metadata called get_text()
            # independently before load() collected text_parts.
            page_count = len(pdf)
            text_parts = [page.get_text() for page in pdf]
            metadata = self._extract_metadata(pdf, text_parts=text_parts)
            is_scanned = metadata.get("is_scanned", False)
            text_content = "\n\n".join(t for t in text_parts if t.strip())
            char_count = sum(len(t) for t in text_parts)
            word_count = sum(len(t.split()) for t in text_parts)
        finally:
            pdf.close()

        # Build DocumentObject
        doc = DocumentObject(
            filename=name,
            format=DocumentFormat.PDF,
            raw_bytes=raw_bytes,
            metadata=metadata,
            page_count=page_count,
            char_count=char_count,
            word_count=word_count,
            text_content=text_content,
            title=metadata.get("title"),
            author=metadata.get("author"),
            subject=metadata.get("subject"),
        )
        doc.metadata["scanned"] = is_scanned
        return doc

    def _extract_metadata(self, pdf: Any, text_parts: list[str] | None = None) -> dict[str, Any]:
        """Extract PDF metadata and detect scanned pages from open pdf.

        Parameters
        ----------
        pdf:
            An open ``fitz.Document`` object.
        text_parts:
            Optional pre-extracted per-page text (list indexed by page number).
            When supplied, scanned-page detection reuses these strings instead
            of calling ``page.get_text()`` a second time.  Pass this whenever
            ``load()`` has already extracted the full text to avoid a redundant
            fitz pass over the first five pages.
        """
        metadata: dict[str, Any] = {}
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

            # Detect if scanned (sample first 5 pages).
            # Reuse pre-extracted text_parts when provided to avoid a
            # second fitz get_text() pass over already-read pages.
            text_chars = 0
            image_count = 0
            for i in range(min(5, len(pdf))):
                page = pdf[i]
                if text_parts is not None and i < len(text_parts):
                    page_text = text_parts[i]
                else:
                    page_text = page.get_text()
                text_chars += len(page_text.strip())
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
        except Exception as e:
            logger.warning(f"PDF metadata extraction failed: {e}")
            metadata["page_count"] = len(pdf) if pdf else 0
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
