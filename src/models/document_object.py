"""
AEGIS-AMDI-OS — Document Object Schema
=========================================
Universal input container for any document format.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


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
    SCANNED_PDF = "scanned_pdf"
    SPEECH = "speech"
    AUDIO = "audio"
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


MAGIC = {
    b"%PDF": DocumentFormat.PDF,
    b"\x89PNG": DocumentFormat.IMAGE,
    b"\xff\xd8\xff": DocumentFormat.IMAGE,
    b"GIF8": DocumentFormat.IMAGE,
    b"RIFF": DocumentFormat.SPEECH,
    b"ID3": DocumentFormat.SPEECH,
    b"OggS": DocumentFormat.SPEECH,
    b"fLaC": DocumentFormat.SPEECH,
}

EXT_MAP = {
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.DOCX,
    ".pptx": DocumentFormat.PPTX,
    ".xlsx": DocumentFormat.XLSX,
    ".md": DocumentFormat.MARKDOWN,
    ".html": DocumentFormat.HTML,
    ".htm": DocumentFormat.HTML,
    ".txt": DocumentFormat.TEXT,
    ".csv": DocumentFormat.CSV,
    ".json": DocumentFormat.JSON,
    ".png": DocumentFormat.IMAGE,
    ".jpg": DocumentFormat.IMAGE,
    ".jpeg": DocumentFormat.IMAGE,
    ".gif": DocumentFormat.IMAGE,
    ".wav": DocumentFormat.SPEECH,
    ".mp3": DocumentFormat.SPEECH,
    ".m4a": DocumentFormat.SPEECH,
    ".flac": DocumentFormat.SPEECH,
    ".ogg": DocumentFormat.SPEECH,
    ".aac": DocumentFormat.SPEECH,
}


class DocumentObject(BaseModel):
    """
    Universal document input container.

    Supports PDF, DOCX, PPTX, XLSX, images, speech/audio, and more.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        populate_by_name=True,
    )

    # ===== Identity =====
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    format: DocumentFormat = DocumentFormat.UNKNOWN
    status: DocumentStatus = DocumentStatus.PENDING
    source: DocumentSource = DocumentSource.UPLOAD

    # ===== Content =====
    raw_bytes: bytes = b""
    raw_path: Optional[str] = None
    text_content: Optional[str] = None
    markdown_content: Optional[str] = None

    # ===== Metadata =====
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    language: str = "en"
    page_count: int = 0
    word_count: int = 0
    char_count: int = 0

    # ===== Custom metadata =====
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ===== Multi-tenancy =====
    tenant_id: str = "default"
    user_id: Optional[str] = None

    # ===== Timestamps =====
    created_at: Union[datetime, float] = Field(default_factory=time.time)
    updated_at: Union[datetime, float] = Field(default_factory=time.time)
    indexed_at: Optional[Union[datetime, float]] = None

    # ===== Tags =====
    tags: list[str] = Field(default_factory=list)
    collections: list[str] = Field(default_factory=list)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            pos_keys = [
                "doc_id", "filename", "format", "raw_bytes", "raw_path",
                "text_content", "markdown_content", "title", "author", "subject",
                "page_count", "word_count", "char_count", "metadata", "tenant_id",
                "user_id", "created_at"
            ]
            for key, val in zip(pos_keys, args):
                if key not in kwargs:
                    kwargs[key] = val
        super().__init__(**kwargs)

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
        return bool(self.metadata.get("scanned", False)) or self.format in (
            DocumentFormat.IMAGE, DocumentFormat.SCANNED_PDF,
        )

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
        if not v:
            return ""
        return v.split("/")[-1].split("\\")[-1]

    @model_validator(mode="after")
    def _detect_format_if_unknown(self) -> "DocumentObject":
        if self.format == DocumentFormat.UNKNOWN or not self.format:
            detected = self._detect()
            if detected != DocumentFormat.UNKNOWN:
                self.format = detected
        return self

    # ===== Methods =====
    def _detect(self) -> DocumentFormat:
        for sig, fmt in MAGIC.items():
            if self.raw_bytes.startswith(sig):
                return fmt
        # ZIP-based (DOCX/PPTX/XLSX)
        if self.raw_bytes.startswith(b"PK\x03\x04"):
            ext = Path(self.filename).suffix.lower()
            return {
                ".docx": DocumentFormat.DOCX,
                ".pptx": DocumentFormat.PPTX,
                ".xlsx": DocumentFormat.XLSX,
            }.get(ext, DocumentFormat.UNKNOWN)
        return EXT_MAP.get(Path(self.filename).suffix.lower(), DocumentFormat.UNKNOWN)

    @classmethod
    def from_path(cls, path: str, **kwargs: Any) -> "DocumentObject":
        p = Path(path)
        raw = p.read_bytes()
        return cls(filename=p.name, raw_bytes=raw, raw_path=str(p), **kwargs)

    def to_dict(self) -> dict[str, Any]:
        fmt = self.format.value if hasattr(self.format, "value") else str(self.format)
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "format": fmt,
            "size_bytes": self.size_bytes,
            "content_hash": self.content_hash,
            "tenant_id": self.tenant_id,
        }

    def to_metadata_dict(self) -> dict[str, Any]:
        """Export metadata as a flat dict (for embedding)."""
        fmt = self.format.value if hasattr(self.format, "value") else str(self.format)
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "format": fmt,
            "title": self.title or self.filename,
            "author": self.author,
            "language": self.language,
            "page_count": self.page_count,
            "tags": ",".join(self.tags),
            "tenant_id": self.tenant_id,
        }


__all__ = [
    "DocumentObject",
    "DocumentFormat",
    "DocumentStatus",
    "DocumentSource",
    "MAGIC",
    "EXT_MAP",
]
