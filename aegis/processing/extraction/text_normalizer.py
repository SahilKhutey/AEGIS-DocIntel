"""
aegis.processing.extraction.text_normalizer
===========================================
Unicode and typographic text normalization preserving content semantics.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


# Common ligatures and their decomposition
LIGATURE_MAP = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}


class TextNormalizer:
    """Normalizes extracted text while retaining raw content integrity."""

    @staticmethod
    def normalize_unicode(text: str, form: str = "NFC") -> str:
        """Apply Unicode normalization (NFC, NFKC, NFD, NFKD)."""
        if not text:
            return ""
        return unicodedata.normalize(form, text)

    @staticmethod
    def decompose_ligatures(text: str) -> str:
        """Decompose typographic ligatures (fi, fl, ffi, etc.)."""
        if not text:
            return ""
        for lig, repl in LIGATURE_MAP.items():
            text = text.replace(lig, repl)
        return text

    @staticmethod
    def normalize_hyphens(text: str) -> str:
        """Standardize dash variants (en-dash, em-dash, non-breaking hyphen)."""
        if not text:
            return ""
        # Preserve em-dash/en-dash if semantic, but standardize soft hyphen and non-breaking hyphen
        text = text.replace("\u00ad", "")  # remove soft hyphen
        text = text.replace("\u2011", "-")  # non-breaking hyphen
        return text

    @staticmethod
    def normalize_whitespace(text: str, preserve_newlines: bool = True) -> str:
        """Normalize excessive whitespace while optionally preserving paragraph breaks."""
        if not text:
            return ""
        # Replace non-breaking spaces
        text = text.replace("\u00a0", " ").replace("\u202f", " ")
        if preserve_newlines:
            lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
            return "\n".join(lines).strip()
        else:
            return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def clean(cls, text: str, preserve_newlines: bool = True) -> str:
        """Full standard pipeline for extracted text normalization."""
        if not text:
            return ""
        t = cls.normalize_unicode(text, "NFC")
        t = cls.decompose_ligatures(t)
        t = cls.normalize_hyphens(t)
        t = cls.normalize_whitespace(t, preserve_newlines=preserve_newlines)
        return t
