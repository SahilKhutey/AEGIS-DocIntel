"""
AEGIS-AMDI-OS — Image Loader
=============================
Image loader with automatic OCR.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from src.core.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader, FormatError, SizeLimitError
from src.ingestion.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class ImageLoader(BaseLoader):
    """Image loader with automatic OCR."""

    FORMAT_NAME = "image"
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif"}

    # Image format magic bytes
    MAGIC_BYTES = {
        b"\x89PNG": "png",
        b"\xff\xd8\xff": "jpeg",
        b"GIF8": "gif",
        b"BM": "bmp",
        b"RIFF": "webp",
    }

    def __init__(self, ocr: OCREngine | None = None, max_size_mb: int = 50, **options):
        super().__init__(**options)
        self.ocr = ocr or OCREngine()
        self.max_size_mb = max_size_mb

    def validate(self, raw_bytes: bytes) -> bool:
        if not raw_bytes or len(raw_bytes) < 8:
            return False
        for magic, fmt in self.MAGIC_BYTES.items():
            if raw_bytes.startswith(magic):
                return True
        # TIFF magic
        if raw_bytes[:4] in (b"II*\x00", b"MM\x00*"):
            return True
        return False

    async def load(self, source, filename: str = "") -> DocumentObject:
        raw_bytes, name = self.read_source(source)
        if filename:
            name = filename
        if not name:
            name = "image.png"

        if not self.validate(raw_bytes):
            raise FormatError(f"Not a valid image: {name}")

        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise SizeLimitError(f"Image too large: {size_mb:.1f}MB")

        metadata = self._extract_metadata(raw_bytes)
        # Run OCR
        text_content = await self.ocr.recognize(raw_bytes)
        ocr_confidence = self.ocr.get_confidence(raw_bytes)
        metadata["ocr_confidence"] = ocr_confidence

        return DocumentObject(
            filename=name,
            format=DocumentFormat.IMAGE,
            raw_bytes=raw_bytes,
            metadata=metadata,
            page_count=1,
            word_count=len(text_content.split()) if text_content else 0,
            text_content=text_content,
        )

    def _extract_metadata(self, raw_bytes: bytes) -> dict[str, Any]:
        """Extract image metadata."""
        metadata: dict[str, Any] = {}
        try:
            img = Image.open(io.BytesIO(raw_bytes))
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["mode"] = img.mode
            metadata["format"] = img.format
            metadata["size_pixels"] = img.width * img.height
            # DPI
            if hasattr(img, "info") and "dpi" in img.info:
                metadata["dpi"] = img.info["dpi"]
            # EXIF (if available)
            if hasattr(img, "_getexif") and img._getexif():
                exif = img._getexif()
                if exif:
                    metadata["has_exif"] = True
        except Exception as e:
            logger.warning(f"Image metadata extraction failed: {e}")
        return metadata

    def get_dimensions(self, raw_bytes: bytes) -> tuple[int, int]:
        """Get image dimensions."""
        try:
            img = Image.open(io.BytesIO(raw_bytes))
            return img.width, img.height
        except Exception:
            return 0, 0
