"""
AEGIS-AMDI-OS — Text Loader
============================
Loader for plain text, Markdown, HTML, and JSON documents with encoding recovery.
"""
from __future__ import annotations

import logging
from typing import Any

from src.core.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader
from src.ingestion.exceptions import FormatError, SizeLimitError

logger = logging.getLogger(__name__)


class TextLoader(BaseLoader):
    """Loader for UTF-8 / plain text / Markdown / HTML / JSON documents."""

    FORMAT_NAME = "text"
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm", ".json", ".csv"}

    def __init__(self, max_size_mb: int = 50, **options):
        super().__init__(**options)
        self.max_size_mb = max_size_mb

    def validate(self, raw_bytes: bytes) -> bool:
        """Validate if bytes can be read as text."""
        if not raw_bytes:
            return True
        # Check for binary null bytes
        if b"\x00" in raw_bytes[:1024]:
            return False
        return True

    async def load(self, source, filename: str = "") -> DocumentObject:
        """Load text document with encoding detection."""
        raw_bytes, name = self.read_source(source)
        if filename:
            name = filename
        if not name:
            name = "document.txt"

        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise SizeLimitError(f"Text document too large: {size_mb:.1f}MB", filename=name)

        if not self.validate(raw_bytes):
            raise FormatError(f"File contains binary null characters: {name}", filename=name)

        # Decoding
        try:
            text = raw_bytes.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("latin-1")
                encoding = "latin-1"
            except Exception as exc:
                raise FormatError(f"Failed to decode text: {exc}", filename=name) from exc

        word_count = len(text.split()) if text else 0
        metadata: dict[str, Any] = {
            "encoding": encoding,
            "char_count": len(text),
            "line_count": len(text.splitlines()),
        }

        # Resolve format
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else "txt"
        fmt = DocumentFormat.TEXT
        if ext in ("md", "markdown"):
            fmt = DocumentFormat.MARKDOWN
        elif ext in ("html", "htm"):
            fmt = DocumentFormat.HTML

        return DocumentObject(
            filename=name,
            format=fmt,
            raw_bytes=raw_bytes,
            metadata=metadata,
            page_count=max(1, (word_count // 400) + (1 if word_count % 400 else 0)) if word_count > 0 else 1,
            word_count=word_count,
            text_content=text,
        )
