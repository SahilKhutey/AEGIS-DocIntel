"""
AEGIS-AMDI-OS — Document Object Schema
=========================================
Universal input container for any document format.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, computed_field


class DocumentFormat(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    IMAGE = "image"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    CSV = "csv"
    JSON = "json"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Processing status."""
    PENDING = "pending"
    INGESTING = "ingesting"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentSource(str, Enum):
    """How the document was obtained."""
    UPLOAD = "upload"
    URL = "url"
    S3 = "s3"
    EMAIL = "email"
    API = "api"
    GENERATED = "generated"


class DocumentObject(BaseModel):
    """
    Universal document input container.

    Supports PDF, DOCX, PPTX, XLSX, images, and more.
    """

    # ===== Identity =====
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = Field(..., min_length=1, max_length=512)
    format: DocumentFormat = DocumentFormat.UNKNOWN
    status: DocumentStatus = DocumentStatus.PENDING
    source: DocumentSource = DocumentSource.UPLOAD

    # ===== Content =====
    raw_bytes: bytes = b""
    raw_path: str | None = None
    text_content: str | None = None
    markdown_content: str | None = None

    # ===== Metadata =====
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = Field(default_factory=list)
    language: str = "en"
    page_count: int = 0
    word_count: int = 0
    char_count: int = 0

    # ===== Custom metadata =====
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ===== Multi-tenancy =====
    tenant_id: str = "default"
    user_id: str | None = None

    # ===== Timestamps =====
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    indexed_at: datetime | None = None

    # ===== Tags =====
    tags: list[str] = Field(default_factory=list)
    collections: list[str] = Field(default_factory=list)

    # ===== Computed =====
    @computed_field
    @property
    def size_bytes(self) -> int:
        """Document size in bytes."""
        return len(self.raw_bytes)

    @computed_field
    @property
    def content_hash(self) -> str:
        """SHA-256 hash of content."""
        return hashlib.sha256(self.raw_bytes).hexdigest()

    @computed_field
    @property
    def short_hash(self) -> str:
        """First 16 chars of hash."""
        return self.content_hash[:16]

    @computed_field
    @property
    def is_scanned(self) -> bool:
        """Whether document is image-based (requires OCR)."""
        return self.metadata.get("scanned", False) or self.format == DocumentFormat.IMAGE

    # ===== Validators =====
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Ensure language is a valid ISO 639-1 code."""
        return v.lower()[:2] if v else "en"

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Strip path components from filename."""
        return v.split("/")[-1].split("\\")[-1]

    # ===== Methods =====
    def to_metadata_dict(self) -> dict:
        """Export metadata as a flat dict (for embedding)."""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "format": self.format.value,
            "title": self.title or self.filename,
            "author": self.author,
            "language": self.language,
            "page_count": self.page_count,
            "tags": ",".join(self.tags),
            "tenant_id": self.tenant_id,
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "annual_report_2024.pdf",
                "format": "pdf",
                "tenant_id": "acme_corp",
                "tags": ["financial", "2024"],
            }
        }
    }
