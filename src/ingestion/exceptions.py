"""
AEGIS-AMDI-OS — Ingestion & Parser Error Hierarchy
===================================================
Strict typed exceptions for all document ingestion, parsing, and extraction failures.
Zero silent failures: any parsing issue is represented by a specific, typed error.
All errors inherit from IngestionError and LoaderError for full backwards compatibility.
"""
from __future__ import annotations


class IngestionError(Exception):
    """Base exception for all ingestion, loading, and parsing errors."""

    def __init__(self, message: str, filename: str = "", details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.filename = filename
        self.details = details or {}

    def __str__(self) -> str:
        ctx = f" (file: {self.filename})" if self.filename else ""
        return f"{self.__class__.__name__}: {self.message}{ctx}"


class LoaderError(IngestionError):
    """Base loader error, inherits from IngestionError."""
    pass


class DocumentCorruptError(LoaderError):
    """Raised when a document has an invalid, truncated, or corrupted binary structure."""
    pass


class EncryptedDocumentError(LoaderError):
    """Raised when a document requires password authentication or is DRM/encryption protected."""
    pass


class UnsupportedFormatError(LoaderError):
    """Raised when the document format is unrecognized or not supported by any loader."""
    pass


class ProcessingTimeoutError(LoaderError):
    """Raised when ingestion or parsing exceeds the configured processing timeout."""
    pass


class ExtractionError(LoaderError):
    """Raised when a loader or extractor encounters an unrecoverable error during content parsing."""
    pass


class SizeLimitError(LoaderError):
    """Raised when document file size exceeds the configured maximum threshold."""
    pass


class FormatError(DocumentCorruptError):
    """Legacy format error, inherits from DocumentCorruptError and LoaderError."""
    pass
