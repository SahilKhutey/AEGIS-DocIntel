"""
AEGIS-AMDI-OS — Universal Fallback Parser
=========================================
Robust emergency text extractor for malformed, corrupted, or unsupported documents.
Guaranteed NEVER to raise an unhandled exception.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Tuple

from src.core.document_object import DocumentFormat, DocumentObject

logger = logging.getLogger(__name__)

# Printable ASCII characters regex (words with spaces/punctuation)
_PRINTABLE_RE = re.compile(rb"[\x20-\x7e\t\n\r]{4,}")


class FallbackParser:
    """
    Universal fallback parser with robust multi-pass encoding recovery.
    Always yields a valid DocumentObject with whatever salvageable text is present.
    """

    def parse(
        self,
        raw_bytes: bytes,
        filename: str = "fallback_document.txt",
        error_context: str | None = None,
        original_format: DocumentFormat = DocumentFormat.UNKNOWN,
    ) -> DocumentObject:
        """
        Extract text from raw bytes using multi-tier encoding recovery.

        Args:
            raw_bytes: Source byte stream (can be arbitrary binary or corrupted data)
            filename: Name of the file
            error_context: Description of why fallback was invoked
            original_format: Format originally expected

        Returns:
            DocumentObject containing recovered text content and diagnostic metadata.
        """
        recovered_text, encoding_used = self._recover_text(raw_bytes)
        word_count = len(recovered_text.split()) if recovered_text else 0

        metadata: dict[str, Any] = {
            "recovered_via_fallback": True,
            "fallback_encoding": encoding_used,
            "original_format": original_format.value if hasattr(original_format, "value") else str(original_format),
            "error_context": error_context or "Primary parser failed or file corrupted",
            "is_corrupt_recovery": bool(error_context),
            "byte_size": len(raw_bytes),
        }

        return DocumentObject(
            filename=filename or "document.txt",
            format=DocumentFormat.TEXT,
            raw_bytes=raw_bytes,
            metadata=metadata,
            page_count=max(1, (word_count // 400) + (1 if word_count % 400 else 0)) if word_count > 0 else 1,
            word_count=word_count,
            text_content=recovered_text,
        )

    def _recover_text(self, raw_bytes: bytes) -> Tuple[str, str]:
        """Attempt text decoding across encodings with binary strings fallback."""
        if not raw_bytes:
            return "", "empty"

        # Tier 1: UTF-8 standard
        try:
            text = raw_bytes.decode("utf-8")
            clean = self._clean_text(text)
            if clean:
                return clean, "utf-8"
        except UnicodeDecodeError:
            pass

        # Tier 2: UTF-8 with BOM
        try:
            text = raw_bytes.decode("utf-8-sig")
            clean = self._clean_text(text)
            if clean:
                return clean, "utf-8-sig"
        except UnicodeDecodeError:
            pass

        # Tier 3: UTF-16 if BOM is present or alternate bytes are nulls
        has_utf16_bom = raw_bytes.startswith((b"\xff\xfe", b"\xfe\xff"))
        has_alternate_nulls = len(raw_bytes) >= 4 and (
            raw_bytes[1::2].count(0) > len(raw_bytes) // 4 or raw_bytes[0::2].count(0) > len(raw_bytes) // 4
        )
        if has_utf16_bom or has_alternate_nulls:
            for enc in ("utf-16", "utf-16-le", "utf-16-be"):
                try:
                    text = raw_bytes.decode(enc)
                    clean = self._clean_text(text)
                    if clean and not clean.startswith("\x00"):
                        return clean, enc
                except (UnicodeDecodeError, ValueError):
                    pass

        # Tier 4: Latin-1 (decodes every byte 0..255)
        try:
            latin_text = raw_bytes.decode("latin-1")
            printable_ratio = sum(c.isprintable() or c in "\n\r\t " for c in latin_text) / max(1, len(latin_text))
            if printable_ratio > 0.65:
                clean = self._clean_text(latin_text)
                if clean:
                    return clean, "latin-1"
        except Exception:
            pass


        # Tier 5: Windows-1252 with replace
        try:
            text = raw_bytes.decode("cp1252", errors="replace")
            printable_ratio = sum(c.isprintable() or c in "\n\r\t " for c in text) / max(1, len(text))
            if printable_ratio > 0.7:
                clean = self._clean_text(text)
                if clean:
                    return clean, "cp1252"
        except Exception:
            pass

        # Tier 6: Binary strings extraction (regex match on ASCII printable blocks)
        try:
            chunks = _PRINTABLE_RE.findall(raw_bytes)
            if chunks:
                extracted = " ".join(c.decode("ascii", errors="ignore").strip() for c in chunks)
                clean = self._clean_text(extracted)
                if clean:
                    return clean, "binary-ascii-strings"
        except Exception as exc:
            logger.warning(f"Binary strings recovery failed: {exc}")

        # Tier 7: Ultimate UTF-8 with replace
        try:
            fallback = raw_bytes.decode("utf-8", errors="replace")
            clean = "".join(c for c in fallback if c.isprintable() or c in "\n\r\t ")
            return clean.strip(), "utf-8-replace"
        except Exception:
            return "", "failed"

    @staticmethod
    def _clean_text(text: str) -> str:
        """Strip non-printable control characters while preserving layout spacing."""
        if not text:
            return ""
        # Remove null bytes and non-printable control characters below ASCII 32 except tab, newline, CR
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return cleaned.strip()
