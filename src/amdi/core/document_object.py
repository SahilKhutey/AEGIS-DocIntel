"""
AMDI-OS — Document Object
==========================
Universal input container for any document format.
"""
from __future__ import annotations
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    IMAGE = "image"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    SCANNED_PDF = "scanned_pdf"
    SPEECH = "speech"
    AUDIO = "audio"
    UNKNOWN = "unknown"


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
    ".pdf": DocumentFormat.PDF, ".docx": DocumentFormat.DOCX,
    ".pptx": DocumentFormat.PPTX, ".xlsx": DocumentFormat.XLSX,
    ".md": DocumentFormat.MARKDOWN, ".html": DocumentFormat.HTML,
    ".htm": DocumentFormat.HTML, ".txt": DocumentFormat.TEXT,
    ".png": DocumentFormat.IMAGE, ".jpg": DocumentFormat.IMAGE,
    ".jpeg": DocumentFormat.IMAGE, ".gif": DocumentFormat.IMAGE,
    ".wav": DocumentFormat.SPEECH, ".mp3": DocumentFormat.SPEECH,
    ".m4a": DocumentFormat.SPEECH, ".flac": DocumentFormat.SPEECH,
    ".ogg": DocumentFormat.SPEECH, ".aac": DocumentFormat.SPEECH,
}


@dataclass
class DocumentObject:
    """
    Universal input container produced by the API layer.
    """
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    format: DocumentFormat = DocumentFormat.UNKNOWN
    raw_bytes: bytes = b""
    raw_path: Optional[str] = None
    text_content: Optional[str] = None
    markdown_content: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    page_count: int = 0
    word_count: int = 0
    char_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    tenant_id: str = "default"
    user_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.format == DocumentFormat.UNKNOWN:
            self.format = self._detect()

    def _detect(self) -> DocumentFormat:
        for sig, fmt in MAGIC.items():
            if self.raw_bytes.startswith(sig):
                return fmt
        # ZIP-based (DOCX/PPTX/XLSX)
        if self.raw_bytes.startswith(b"PK\x03\x04"):
            ext = Path(self.filename).suffix.lower()
            return {'.docx': DocumentFormat.DOCX, '.pptx': DocumentFormat.PPTX,
                    '.xlsx': DocumentFormat.XLSX}.get(ext, DocumentFormat.UNKNOWN)
        return EXT_MAP.get(Path(self.filename).suffix.lower(), DocumentFormat.UNKNOWN)

    @property
    def size_bytes(self) -> int:
        return len(self.raw_bytes)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.raw_bytes).hexdigest()

    @classmethod
    def from_path(cls, path: str, **kwargs) -> "DocumentObject":
        p = Path(path)
        raw = p.read_bytes()
        return cls(filename=p.name, raw_bytes=raw, raw_path=str(p), **kwargs)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id, "filename": self.filename,
            "format": self.format.value, "size_bytes": self.size_bytes,
            "content_hash": self.content_hash, "tenant_id": self.tenant_id,
        }
