"""
aegis.processing.validation.file_validator
==========================================
Pre-processing file validation enforcing signature checks, size boundaries, and structural limits.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple, Union
import fitz

from aegis.processing.models import ProcessingError, ProcessingStatus
from aegis.processing.validation.resource_limits import ResourceLimitsConfig


class ValidationResult:
    def __init__(
        self,
        is_valid: bool,
        status: ProcessingStatus,
        detected_format: Optional[str] = None,
        page_count: int = 0,
        error: Optional[ProcessingError] = None
    ):
        self.is_valid = is_valid
        self.status = status
        self.detected_format = detected_format
        self.page_count = page_count
        self.error = error


class FileValidator:
    """Pre-processing gate validating files before invocation of expensive extraction pipelines."""

    def __init__(self, limits: Optional[ResourceLimitsConfig] = None):
        self.limits = limits or ResourceLimitsConfig()

    def validate_file(self, file_path: Union[str, Path]) -> ValidationResult:
        # 1. Path traversal security check
        raw_str = str(file_path)
        if ".." in raw_str:
            return ValidationResult(
                is_valid=False,
                status=ProcessingStatus.SECURITY_REJECTED,
                error=ProcessingError(
                    code="PATH_TRAVERSAL_DETECTED",
                    stage="validation",
                    category="SECURITY",
                    message="Filename contains illegal path traversal sequences",
                )
            )

        p = Path(file_path)

        # 2. Existence check
        if not p.is_file():
            return ValidationResult(
                is_valid=False,
                status=ProcessingStatus.INVALID_FORMAT,
                error=ProcessingError(
                    code="FILE_NOT_FOUND",
                    stage="validation",
                    category="FILESYSTEM",
                    message="Target file does not exist on filesystem",
                )
            )

        # 3. File size check
        size_bytes = p.stat().st_size
        if size_bytes == 0:
            return ValidationResult(
                is_valid=False,
                status=ProcessingStatus.CORRUPTED_DOCUMENT,
                error=ProcessingError(
                    code="EMPTY_FILE",
                    stage="validation",
                    category="FILE_INTEGRITY",
                    message="File is zero bytes in length",
                )
            )

        if size_bytes > self.limits.max_file_size_bytes:
            return ValidationResult(
                is_valid=False,
                status=ProcessingStatus.RESOURCE_LIMIT_EXCEEDED,
                error=ProcessingError(
                    code="MAX_FILE_SIZE_EXCEEDED",
                    stage="validation",
                    category="RESOURCE_LIMIT",
                    message=f"File size {size_bytes} exceeds limit of {self.limits.max_file_size_bytes} bytes",
                )
            )

        # 4. Signature / Magic-byte sniffing
        with open(p, "rb") as f:
            header = f.read(1024)

        if b"%PDF" in header:
            detected_format = "application/pdf"
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):
            detected_format = "image/png"
        elif header.startswith(b"\xff\xd8\xff"):
            detected_format = "image/jpeg"
        elif header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
            detected_format = "image/tiff"
        else:
            return ValidationResult(
                is_valid=False,
                status=ProcessingStatus.INVALID_FORMAT,
                error=ProcessingError(
                    code="INVALID_FILE_SIGNATURE",
                    stage="validation",
                    category="FILE_INTEGRITY",
                    message="File magic bytes do not match supported document types",
                )
            )

        # 5. Deep structural validation for PDF
        if detected_format == "application/pdf":
            try:
                doc = fitz.open(str(p))
            except Exception as exc:
                return ValidationResult(
                    is_valid=False,
                    status=ProcessingStatus.CORRUPTED_DOCUMENT,
                    error=ProcessingError(
                        code="PDF_PARSING_FAILED",
                        stage="validation",
                        category="FILE_CORRUPTION",
                        message="PDF structure is corrupted or unparseable",
                    )
                )

            # Check encryption
            if doc.is_encrypted:
                doc.close()
                return ValidationResult(
                    is_valid=False,
                    status=ProcessingStatus.ENCRYPTED_DOCUMENT,
                    error=ProcessingError(
                        code="ENCRYPTED_PDF",
                        stage="validation",
                        category="SECURITY",
                        message="Password-protected encrypted PDF rejected per policy",
                    )
                )

            page_count = len(doc)
            if page_count == 0:
                doc.close()
                return ValidationResult(
                    is_valid=False,
                    status=ProcessingStatus.CORRUPTED_DOCUMENT,
                    error=ProcessingError(
                        code="ZERO_PAGE_PDF",
                        stage="validation",
                        category="FILE_CORRUPTION",
                        message="PDF contains zero renderable pages",
                    )
                )

            if page_count > self.limits.max_pages:
                doc.close()
                return ValidationResult(
                    is_valid=False,
                    status=ProcessingStatus.RESOURCE_LIMIT_EXCEEDED,
                    error=ProcessingError(
                        code="PAGE_COUNT_EXCEEDED",
                        stage="validation",
                        category="RESOURCE_LIMIT",
                        message=f"Page count {page_count} exceeds limit of {self.limits.max_pages}",
                    )
                )

            # Check dimensions on first 10 pages
            check_pages = min(10, page_count)
            for i in range(check_pages):
                rect = doc[i].rect
                if max(rect.width, rect.height) > self.limits.max_page_dimension_points:
                    doc.close()
                    return ValidationResult(
                        is_valid=False,
                        status=ProcessingStatus.RESOURCE_LIMIT_EXCEEDED,
                        error=ProcessingError(
                            code="PAGE_DIMENSION_EXCEEDED",
                            stage="validation",
                            category="RESOURCE_LIMIT",
                            page_number=i + 1,
                            message=f"Page {i+1} dimension ({rect.width}x{rect.height}) exceeds limit",
                        )
                    )

            doc.close()
            return ValidationResult(
                is_valid=True,
                status=ProcessingStatus.SUCCESS,
                detected_format=detected_format,
                page_count=page_count,
            )

        # Image format
        return ValidationResult(
            is_valid=True,
            status=ProcessingStatus.SUCCESS,
            detected_format=detected_format,
            page_count=1,
        )
