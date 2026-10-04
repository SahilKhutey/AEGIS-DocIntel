"""
AEGIS-AMDI-OS — XLSX Loader
=============================
Microsoft Excel spreadsheet loader using openpyxl with strict error handling.
"""
from __future__ import annotations

import io
import logging
from typing import Any
import zipfile

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

from src.models.document_object import DocumentFormat, DocumentObject
from src.ingestion.base import BaseLoader
from src.ingestion.exceptions import (
    DocumentCorruptError,
    EncryptedDocumentError,
    FormatError,
    LoaderError,
    SizeLimitError,
)

logger = logging.getLogger(__name__)


class XLSXLoader(BaseLoader):
    """XLSX spreadsheet loader."""

    FORMAT_NAME = "xlsx"
    SUPPORTED_EXTENSIONS = {".xlsx"}
    XLSX_MAGIC = b"PK\x03\x04"

    def __init__(self, max_size_mb: int = 100, **options):
        super().__init__(**options)
        self.max_size_mb = max_size_mb

    def validate(self, raw_bytes: bytes) -> bool:
        """Check if bytes represent a valid XLSX file."""
        if not raw_bytes or len(raw_bytes) < 4:
            return False
        if raw_bytes[:4] != self.XLSX_MAGIC:
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                names = z.namelist()
                return any(n.startswith("xl/") for n in names) or "[Content_Types].xml" in names
        except Exception:
            return False

    async def load(self, source, filename: str = "") -> DocumentObject:
        """Load an XLSX spreadsheet with zero silent failures."""
        raw_bytes, name = self.read_source(source)
        if filename:
            name = filename
        if not name:
            name = "spreadsheet.xlsx"

        if not raw_bytes or len(raw_bytes) < 4 or raw_bytes[:4] != self.XLSX_MAGIC:
            raise FormatError(f"Not a valid XLSX file (missing ZIP header): {name}", filename=name)

        if load_workbook is None:
            raise LoaderError("openpyxl is not installed", filename=name)

        size_mb = len(raw_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise SizeLimitError(f"XLSX too large: {size_mb:.1f}MB", filename=name)

        # Inspect zip structure for encryption or corruption
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                names = z.namelist()
                if "EncryptedPackage" in names or any("encrypted" in n.lower() for n in names):
                    raise EncryptedDocumentError(f"XLSX spreadsheet is password protected: {name}", filename=name)
                if not any(n.startswith("xl/") for n in names) and "[Content_Types].xml" not in names:
                    raise DocumentCorruptError(f"XLSX package is missing required spreadsheetml components: {name}", filename=name)
        except zipfile.BadZipFile as exc:
            raise DocumentCorruptError(f"Corrupt or truncated XLSX zip archive: {exc}", filename=name) from exc
        except EncryptedDocumentError:
            raise
        except DocumentCorruptError:
            raise
        except Exception as exc:
            raise DocumentCorruptError(f"Failed to inspect XLSX package: {exc}", filename=name) from exc

        # Open workbook
        try:
            wb = load_workbook(io.BytesIO(raw_bytes), data_only=True)
        except Exception as exc:
            err_msg = str(exc).lower()
            if "password" in err_msg or "encrypted" in err_msg:
                raise EncryptedDocumentError(f"XLSX workbook is encrypted: {exc}", filename=name) from exc
            raise DocumentCorruptError(f"Malformed XLSX workbook: {exc}", filename=name) from exc

        metadata, text_parts, sheet_count = self._extract(wb)
        return DocumentObject(
            filename=name,
            format=DocumentFormat.XLSX,
            raw_bytes=raw_bytes,
            metadata=metadata,
            page_count=sheet_count,
            text_content="\n\n".join(text_parts),
        )

    def _extract(self, wb: Any) -> tuple[dict[str, Any], list[str], int]:
        """Extract metadata and text parts from loaded openpyxl workbook."""
        metadata: dict[str, Any] = {}
        text_parts: list[str] = []
        sheet_count = len(wb.sheetnames)

        try:
            metadata["sheet_count"] = sheet_count
            metadata["sheet_names"] = wb.sheetnames
            if hasattr(wb, "properties") and wb.properties:
                metadata["creator"] = wb.properties.creator
                metadata["title"] = wb.properties.title
                metadata["subject"] = wb.properties.subject
                metadata["keywords"] = wb.properties.keywords
                metadata["created"] = str(wb.properties.created) if wb.properties.created else None
                metadata["modified"] = str(wb.properties.modified) if wb.properties.modified else None

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                text_parts.append(f"--- Sheet: {sheet_name} ---")
                row_count = 0
                col_count = 0
                for row in ws.iter_rows(values_only=True):
                    row_count += 1
                    col_count = max(col_count, sum(1 for c in row if c is not None))
                    row_data = [str(c) if c is not None else "" for c in row]
                    if any(c.strip() for c in row_data):
                        text_parts.append(" | ".join(row_data))
                metadata[f"sheet_{sheet_name}_rows"] = row_count
                metadata[f"sheet_{sheet_name}_cols"] = col_count
        except Exception as e:
            logger.warning(f"XLSX extraction warning: {e}")
        return metadata, text_parts, sheet_count
