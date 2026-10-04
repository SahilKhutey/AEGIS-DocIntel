"""
AEGIS-AMDI-OS — File-Type Sniffing Module
=========================================
Deep byte-level inspection and magic byte sniffing for accurate document format identification.
Does not rely solely on file extensions.
"""
from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import zipfile

from src.models.document_object import DocumentFormat

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SniffResult:
    """Result of sniffing a byte payload."""
    format: DocumentFormat
    mime_type: str
    confidence: float
    is_binary: bool
    details: str = ""


# Magic byte signatures
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_87A = b"GIF87a"
_GIF_89A = b"GIF89a"
_TIFF_LE = b"II*\x00"
_TIFF_BE = b"MM\x00*"
_BMP_MAGIC = b"BM"
_FLAC_MAGIC = b"fLaC"
_OGG_MAGIC = b"OggS"
_MP3_ID3 = b"ID3"


def sniff_format(raw_bytes: bytes, filename: str = "") -> SniffResult:
    """
    Sniff document format from binary content with extension fallback.

    Args:
        raw_bytes: Binary contents (at least first 2048 bytes recommended)
        filename: Optional filename to resolve ties or extension hints

    Returns:
        SniffResult containing detected DocumentFormat, MIME type, and confidence.
    """
    if not raw_bytes:
        return SniffResult(
            format=DocumentFormat.UNKNOWN,
            mime_type="application/octet-stream",
            confidence=0.0,
            is_binary=False,
            details="Empty byte payload",
        )

    header = raw_bytes[:64]

    # 1. PDF detection
    if header.startswith(_PDF_MAGIC):
        return SniffResult(
            format=DocumentFormat.PDF,
            mime_type="application/pdf",
            confidence=1.0,
            is_binary=True,
            details="PDF magic bytes (%PDF) matched",
        )

    # 2. Image detection
    if header.startswith(_PNG_MAGIC) or header.startswith(b"\x89PNG"):
        return SniffResult(
            format=DocumentFormat.IMAGE,
            mime_type="image/png",
            confidence=1.0,
            is_binary=True,
            details="PNG magic bytes matched",
        )

    if header.startswith(_JPEG_MAGIC):
        return SniffResult(
            format=DocumentFormat.IMAGE,
            mime_type="image/jpeg",
            confidence=1.0,
            is_binary=True,
            details="JPEG magic bytes matched",
        )

    if header.startswith(_GIF_87A) or header.startswith(_GIF_89A):
        return SniffResult(
            format=DocumentFormat.IMAGE,
            mime_type="image/gif",
            confidence=1.0,
            is_binary=True,
            details="GIF magic bytes matched",
        )

    if header.startswith(_TIFF_LE) or header.startswith(_TIFF_BE):
        return SniffResult(
            format=DocumentFormat.IMAGE,
            mime_type="image/tiff",
            confidence=1.0,
            is_binary=True,
            details="TIFF magic bytes matched",
        )

    if header.startswith(_BMP_MAGIC) and len(raw_bytes) >= 14:
        return SniffResult(
            format=DocumentFormat.IMAGE,
            mime_type="image/bmp",
            confidence=0.9,
            is_binary=True,
            details="BMP header matched",
        )

    # WebP: starts with 'RIFF' and has 'WEBP' at offset 8..12
    if len(raw_bytes) >= 12 and header.startswith(b"RIFF") and raw_bytes[8:12] == b"WEBP":
        return SniffResult(
            format=DocumentFormat.IMAGE,
            mime_type="image/webp",
            confidence=1.0,
            is_binary=True,
            details="WebP container matched",
        )

    # 3. Audio detection
    if len(raw_bytes) >= 12 and header.startswith(b"RIFF") and raw_bytes[8:12] == b"WAVE":
        return SniffResult(
            format=DocumentFormat.SPEECH,
            mime_type="audio/wav",
            confidence=1.0,
            is_binary=True,
            details="RIFF WAVE container matched",
        )

    if header.startswith(_FLAC_MAGIC):
        return SniffResult(
            format=DocumentFormat.SPEECH,
            mime_type="audio/flac",
            confidence=1.0,
            is_binary=True,
            details="FLAC magic matched",
        )

    if header.startswith(_OGG_MAGIC):
        return SniffResult(
            format=DocumentFormat.SPEECH,
            mime_type="audio/ogg",
            confidence=1.0,
            is_binary=True,
            details="OGG container matched",
        )

    if header.startswith(_MP3_ID3) or (len(raw_bytes) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        return SniffResult(
            format=DocumentFormat.SPEECH,
            mime_type="audio/mpeg",
            confidence=0.95,
            is_binary=True,
            details="MP3 header matched",
        )

    # 4. ZIP-based Office formats (DOCX, XLSX, PPTX)
    if header.startswith(_ZIP_MAGIC):
        office_res = _sniff_zip_structure(raw_bytes, filename)
        if office_res:
            return office_res

    # 5. Text-based detection (HTML, JSON, Markdown, CSV, plain text)
    text_res = _sniff_text_format(raw_bytes, filename)
    if text_res:
        return text_res

    # 6. Extension fallback if still unknown
    ext = Path(filename).suffix.lower() if filename else ""
    ext_map = {
        ".pdf": (DocumentFormat.PDF, "application/pdf"),
        ".docx": (DocumentFormat.DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ".pptx": (DocumentFormat.PPTX, "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ".xlsx": (DocumentFormat.XLSX, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ".png": (DocumentFormat.IMAGE, "image/png"),
        ".jpg": (DocumentFormat.IMAGE, "image/jpeg"),
        ".jpeg": (DocumentFormat.IMAGE, "image/jpeg"),
        ".tiff": (DocumentFormat.IMAGE, "image/tiff"),
        ".tif": (DocumentFormat.IMAGE, "image/tiff"),
        ".webp": (DocumentFormat.IMAGE, "image/webp"),
        ".bmp": (DocumentFormat.IMAGE, "image/bmp"),
        ".wav": (DocumentFormat.SPEECH, "audio/wav"),
        ".mp3": (DocumentFormat.SPEECH, "audio/mpeg"),
        ".flac": (DocumentFormat.SPEECH, "audio/flac"),
        ".ogg": (DocumentFormat.SPEECH, "audio/ogg"),
        ".html": (DocumentFormat.HTML, "text/html"),
        ".htm": (DocumentFormat.HTML, "text/html"),
        ".md": (DocumentFormat.MARKDOWN, "text/markdown"),
        ".txt": (DocumentFormat.TEXT, "text/plain"),
        ".csv": (DocumentFormat.TEXT, "text/csv"),
        ".json": (DocumentFormat.TEXT, "application/json"),
    }
    if ext in ext_map:
        fmt, mime = ext_map[ext]
        return SniffResult(
            format=fmt,
            mime_type=mime,
            confidence=0.5,
            is_binary=fmt in (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.PPTX, DocumentFormat.XLSX, DocumentFormat.IMAGE, DocumentFormat.SPEECH),
            details=f"Fallback to file extension '{ext}'",
        )

    return SniffResult(
        format=DocumentFormat.UNKNOWN,
        mime_type="application/octet-stream",
        confidence=0.0,
        is_binary=True,
        details="Unrecognized binary signature",
    )


def _sniff_zip_structure(raw_bytes: bytes, filename: str) -> Optional[SniffResult]:
    """Inspect ZIP file structure to distinguish DOCX, XLSX, PPTX, or generic zip."""
    ext = Path(filename).suffix.lower() if filename else ""

    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
            names = set(z.namelist())

            # Word document
            if any(name.startswith("word/") for name in names) or "word/document.xml" in names:
                return SniffResult(
                    format=DocumentFormat.DOCX,
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    confidence=1.0,
                    is_binary=True,
                    details="OpenXML WordprocessingML structure confirmed",
                )

            # Excel spreadsheet
            if any(name.startswith("xl/") for name in names) or "xl/workbook.xml" in names:
                return SniffResult(
                    format=DocumentFormat.XLSX,
                    mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    confidence=1.0,
                    is_binary=True,
                    details="OpenXML SpreadsheetML structure confirmed",
                )

            # PowerPoint presentation
            if any(name.startswith("ppt/") for name in names) or "ppt/presentation.xml" in names:
                return SniffResult(
                    format=DocumentFormat.PPTX,
                    mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    confidence=1.0,
                    is_binary=True,
                    details="OpenXML PresentationML structure confirmed",
                )

            # Check [Content_Types].xml
            if "[Content_Types].xml" in names:
                try:
                    ct_content = z.read("[Content_Types].xml").decode("utf-8", errors="ignore")
                    if "wordprocessingml" in ct_content:
                        return SniffResult(
                            format=DocumentFormat.DOCX,
                            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            confidence=0.95,
                            is_binary=True,
                            details="[Content_Types].xml specifies wordprocessingml",
                        )
                    if "spreadsheetml" in ct_content:
                        return SniffResult(
                            format=DocumentFormat.XLSX,
                            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            confidence=0.95,
                            is_binary=True,
                            details="[Content_Types].xml specifies spreadsheetml",
                        )
                    if "presentationml" in ct_content:
                        return SniffResult(
                            format=DocumentFormat.PPTX,
                            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            confidence=0.95,
                            is_binary=True,
                            details="[Content_Types].xml specifies presentationml",
                        )
                except Exception:
                    pass

    except zipfile.BadZipFile:
        # Broken or truncated zip file
        logger.debug("Sniffer encountered corrupt zip payload")
    except Exception as exc:
        logger.debug(f"Zip inspection failed: {exc}")

    # If ZIP inspection couldn't be parsed but extension indicates Office format
    if ext == ".docx":
        return SniffResult(
            format=DocumentFormat.DOCX,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            confidence=0.6,
            is_binary=True,
            details="ZIP header with .docx extension",
        )
    if ext == ".xlsx":
        return SniffResult(
            format=DocumentFormat.XLSX,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            confidence=0.6,
            is_binary=True,
            details="ZIP header with .xlsx extension",
        )
    if ext == ".pptx":
        return SniffResult(
            format=DocumentFormat.PPTX,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            confidence=0.6,
            is_binary=True,
            details="ZIP header with .pptx extension",
        )

    return None


def _sniff_text_format(raw_bytes: bytes, filename: str) -> Optional[SniffResult]:
    """Test if bytes represent text and identify HTML, JSON, Markdown, or plain text."""
    sample = raw_bytes[:4096]

    # Check for null bytes (typical binary signature)
    if b"\x00" in sample:
        return None

    # Try decoding sample as UTF-8
    try:
        text = sample.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = sample.decode("latin-1")
        except Exception:
            return None

    stripped = text.strip()
    if not stripped:
        return SniffResult(
            format=DocumentFormat.TEXT,
            mime_type="text/plain",
            confidence=0.5,
            is_binary=False,
            details="Empty text document",
        )

    # HTML
    lower_text = stripped[:256].lower()
    if lower_text.startswith("<!doctype html") or lower_text.startswith("<html") or "<head>" in lower_text:
        return SniffResult(
            format=DocumentFormat.HTML,
            mime_type="text/html",
            confidence=0.95,
            is_binary=False,
            details="HTML declaration detected",
        )

    # JSON
    if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
        try:
            json.loads(text)
            return SniffResult(
                format=DocumentFormat.TEXT,
                mime_type="application/json",
                confidence=0.95,
                is_binary=False,
                details="Valid JSON text",
            )
        except Exception:
            pass

    # Markdown
    ext = Path(filename).suffix.lower() if filename else ""
    if ext in (".md", ".markdown"):
        return SniffResult(
            format=DocumentFormat.MARKDOWN,
            mime_type="text/markdown",
            confidence=0.9,
            is_binary=False,
            details="Markdown extension and valid text",
        )

    # Check if text contains markdown markers
    if any(line.startswith(("# ", "## ", "### ", "- ", "* ")) for line in stripped.splitlines()[:10]):
        return SniffResult(
            format=DocumentFormat.MARKDOWN,
            mime_type="text/markdown",
            confidence=0.75,
            is_binary=False,
            details="Markdown syntax detected",
        )

    ext = Path(filename).suffix.lower() if filename else ""
    if ext in (".txt", ".text", ".csv", ".tsv", ".log", ""):
        return SniffResult(
            format=DocumentFormat.TEXT,
            mime_type="text/plain",
            confidence=0.8,
            is_binary=False,
            details="Decodable text payload",
        )

    return None

