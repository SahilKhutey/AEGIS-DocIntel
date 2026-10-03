"""
AEGIS-AMDI-OS — DOCX Loader
=============================
Microsoft Word document loader using python-docx with strict error handling.
"""
from __future__ import annotations

import io
import logging
from typing import Any
import zipfile

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from src.core.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader
from src.ingestion.exceptions import (
    DocumentCorruptError,
    EncryptedDocumentError,
    FormatError,
    LoaderError,
    SizeLimitError,
)

logger = logging.getLogger(__name__)


class DOCXLoader(BaseLoader):
    """DOCX document loader."""

    FORMAT_NAME = "docx"
    SUPPORTED_EXTENSIONS = {".docx"}
    DOCX_MAGIC = b"PK\x03\x04"  # ZIP-based format

    def __init__(self, max_size_mb: int = 100, **options):
        super().__init__(**options)
        self.max_size_mb = max_size_mb

    def validate(self, raw_bytes: bytes) -> bool:
        """Check if bytes represent a valid DOCX file."""
        if not raw_bytes or len(raw_bytes) < 4:
            return False
        if raw_bytes[:4] != self.DOCX_MAGIC:
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                names = z.namelist()
                # Must be a zip file with typical Word structure or content types
                return any(n.startswith("word/") for n in names) or "[Content_Types].xml" in names
        except Exception:
            return False

    async def load(self, source, filename: str = "") -> DocumentObject:
        """Load a DOCX document with zero silent failures."""
        raw_bytes, name = self.read_source(source)
        if filename:
            name = filename
        if not name:
            name = "document.docx"

        if not raw_bytes or len(raw_bytes) < 4 or raw_bytes[:4] != self.DOCX_MAGIC:
            raise FormatError(f"Not a valid DOCX file (missing ZIP header): {name}", filename=name)

        if DocxDocument is None:
            raise LoaderError("python-docx is not installed", filename=name)

        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise SizeLimitError(f"DOCX too large: {size_mb:.1f}MB", filename=name)

        # Inspect ZIP structure for encryption or corruption
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                names = z.namelist()
                if "EncryptedPackage" in names or any("encrypted" in n.lower() for n in names):
                    raise EncryptedDocumentError(f"DOCX document is password protected or encrypted: {name}", filename=name)
                # Check for word/document.xml or [Content_Types].xml
                if not any(n.startswith("word/") for n in names) and "[Content_Types].xml" not in names:
                    raise DocumentCorruptError(f"DOCX package is missing required wordprocessingml components: {name}", filename=name)
        except zipfile.BadZipFile as exc:
            raise DocumentCorruptError(f"Corrupt or truncated DOCX zip archive: {exc}", filename=name) from exc
        except EncryptedDocumentError:
            raise
        except DocumentCorruptError:
            raise
        except Exception as exc:
            raise DocumentCorruptError(f"Failed to inspect DOCX package: {exc}", filename=name) from exc

        # Open document with python-docx
        try:
            doc = DocxDocument(io.BytesIO(raw_bytes))
        except Exception as exc:
            err_msg = str(exc).lower()
            if "password" in err_msg or "encrypted" in err_msg:
                raise EncryptedDocumentError(f"DOCX document is encrypted: {exc}", filename=name) from exc
            raise DocumentCorruptError(f"Malformed DOCX document: {exc}", filename=name) from exc

        # Extract metadata
        metadata = self._extract_metadata(doc)

        # Extract text content
        text_parts: list[str] = []
        try:
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)
        except Exception as exc:
            logger.warning(f"DOCX partial text extraction warning: {exc}")

        return DocumentObject(
            filename=name,
            format=DocumentFormat.DOCX,
            raw_bytes=raw_bytes,
            metadata=metadata,
            word_count=sum(len(t.split()) for t in text_parts),
            text_content="\n\n".join(text_parts),
        )

    def _extract_metadata(self, doc: Any) -> dict[str, Any]:
        """Extract DOCX metadata from loaded document."""
        metadata: dict[str, Any] = {}
        try:
            cp = doc.core_properties
            metadata["title"] = cp.title
            metadata["author"] = cp.author
            metadata["subject"] = cp.subject
            metadata["keywords"] = cp.keywords
            metadata["created"] = str(cp.created) if cp.created else None
            metadata["modified"] = str(cp.modified) if cp.modified else None
            metadata["last_modified_by"] = cp.last_modified_by
            metadata["revision"] = cp.revision

            # Count elements
            metadata["paragraph_count"] = len(doc.paragraphs)
            metadata["table_count"] = len(doc.tables)
            metadata["section_count"] = len(doc.sections)

            # Count images
            image_count = 0
            if hasattr(doc, "part") and hasattr(doc.part, "rels"):
                for rel in doc.part.rels.values():
                    if "image" in rel.reltype:
                        image_count += 1
            metadata["image_count"] = image_count
        except Exception as e:
            logger.warning(f"DOCX metadata extraction failed: {e}")
        return metadata
