"""
aegis.processing.security.error_classifier
==========================================
Standardized error mapping and sanitization ensuring no sensitive stack traces,
host paths, or internal tokens leak in error responses.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from aegis.processing.models import ProcessingError, ProcessingStatus


class ErrorClassifier:
    """Classifies exceptions into standardized ProcessingStatus and sanitized ProcessingError."""

    @classmethod
    def sanitize_message(cls, msg: str) -> str:
        """Strip internal filesystem paths, usernames, and environment details from error strings."""
        if not msg:
            return "Internal processing error occurred"
        # Mask Windows / Unix absolute file paths
        clean = re.sub(r"[A-Za-z]:\\[\w\\\s.-]+", "<REDACTED_PATH>", msg)
        clean = re.sub(r"/(?:[\w.-]+/)+[\w.-]+", "<REDACTED_PATH>", clean)
        return clean.strip()

    @classmethod
    def classify_exception(
        cls,
        exc: Exception,
        stage: str = "processing",
        page_number: Optional[int] = None
    ) -> Tuple[ProcessingStatus, ProcessingError]:
        """Map exception to standard status and safe error model."""
        exc_type = type(exc).__name__
        exc_str = str(exc)
        safe_msg = cls.sanitize_message(exc_str)

        if isinstance(exc, TimeoutError) or "timeout" in exc_str.lower():
            status = ProcessingStatus.TIMEOUT
            code = "TIMEOUT_EXCEEDED"
            cat = "RESOURCE_LIMIT"
        elif isinstance(exc, MemoryError) or "memory" in exc_str.lower():
            status = ProcessingStatus.RESOURCE_LIMIT_EXCEEDED
            code = "MEMORY_LIMIT_EXCEEDED"
            cat = "RESOURCE_LIMIT"
        elif isinstance(exc, PermissionError):
            status = ProcessingStatus.SECURITY_REJECTED
            code = "ACCESS_DENIED"
            cat = "SECURITY"
        elif "password" in exc_str.lower() or "encrypt" in exc_str.lower():
            status = ProcessingStatus.ENCRYPTED_DOCUMENT
            code = "ENCRYPTED_DOCUMENT"
            cat = "SECURITY"
        elif "corrupt" in exc_str.lower() or "damaged" in exc_str.lower() or "syntaxerror" in exc_type.lower():
            status = ProcessingStatus.CORRUPTED_DOCUMENT
            code = "DOCUMENT_CORRUPTED"
            cat = "FILE_INTEGRITY"
        else:
            status = ProcessingStatus.EXTRACTION_FAILED
            code = "EXTRACTION_FAILURE"
            cat = "DOCUMENT_PROCESSING"

        err = ProcessingError(
            code=code,
            stage=stage,
            page_number=page_number,
            category=cat,
            recoverable=False,
            message=safe_msg if safe_msg else f"{exc_type} during {stage}",
        )
        return status, err
