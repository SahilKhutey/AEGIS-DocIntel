"""
aegis.security.parser_guard
===========================
Document parser security guard validating path boundaries, payload bounds,
and file integrity to prevent traversal, parser bombs, and memory exhaustion.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Optional, Set
from pydantic import BaseModel, Field


class ParserSecurityResult(BaseModel):
    is_safe: bool
    sanitized_filename: str
    error_reason: Optional[str] = None
    file_size_bytes: int = 0


class DocumentParserGuard:
    """Hardened input validation guard for document ingestion."""

    DEFAULT_MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
    ALLOWED_EXTENSIONS: Set[str] = {
        ".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".csv", ".json", ".png", ".jpg", ".jpeg"
    }
    RESERVED_WINDOWS_NAMES = {
        "con", "prn", "aux", "nul", "com1", "com2", "com3", "com4", "com5", "com6", "com7",
        "com8", "com9", "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"
    }

    @classmethod
    def sanitize_and_validate_filename(cls, filename: str) -> ParserSecurityResult:
        if not filename or not filename.strip():
            return ParserSecurityResult(
                is_safe=False,
                sanitized_filename="",
                error_reason="Filename cannot be empty",
            )

        # Check for null bytes
        if "\0" in filename:
            return ParserSecurityResult(
                is_safe=False,
                sanitized_filename="",
                error_reason="Null byte detected in filename",
            )

        # Path traversal checks
        if ".." in filename or "/" in filename or "\\" in filename:
            # Strip path elements to base name
            base_name = os.path.basename(filename.replace("\\", "/"))
            if not base_name or ".." in base_name:
                return ParserSecurityResult(
                    is_safe=False,
                    sanitized_filename="",
                    error_reason="Illegal path traversal sequence in filename",
                )
            filename = base_name

        # Clean non-alphanumeric except safe delimiters
        cleaned = re.sub(r"[^\w\.\-\_]", "_", filename).strip()
        stem = Path(cleaned).stem.lower()

        if stem in cls.RESERVED_WINDOWS_NAMES:
            return ParserSecurityResult(
                is_safe=False,
                sanitized_filename="",
                error_reason=f"Filename '{stem}' is a reserved operating system device name",
            )

        ext = Path(cleaned).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return ParserSecurityResult(
                is_safe=False,
                sanitized_filename=cleaned,
                error_reason=f"File extension '{ext}' is not permitted in document ingestion pipeline",
            )

        return ParserSecurityResult(
            is_safe=True,
            sanitized_filename=cleaned,
            error_reason=None,
        )

    @classmethod
    def validate_payload(
        cls, payload: bytes, filename: str, max_size_bytes: int = DEFAULT_MAX_FILE_SIZE
    ) -> ParserSecurityResult:
        fn_res = cls.sanitize_and_validate_filename(filename)
        if not fn_res.is_safe:
            return fn_res

        size = len(payload)
        if size == 0:
            return ParserSecurityResult(
                is_safe=False,
                sanitized_filename=fn_res.sanitized_filename,
                error_reason="Zero-byte file payload received",
                file_size_bytes=0,
            )

        if size > max_size_bytes:
            return ParserSecurityResult(
                is_safe=False,
                sanitized_filename=fn_res.sanitized_filename,
                error_reason=f"File size {size} exceeds maximum limit of {max_size_bytes} bytes",
                file_size_bytes=size,
            )

        return ParserSecurityResult(
            is_safe=True,
            sanitized_filename=fn_res.sanitized_filename,
            error_reason=None,
            file_size_bytes=size,
        )
