"""Deterministic, provenance-preserving context chunking for AEGIS-DocIntel.

Offsets are zero-based, half-open character offsets into the normalized source
text. This module does not perform OCR, semantic retrieval, or persistence.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.normalized_document import NormalizedDocument


@dataclass(frozen=True, slots=True)
class ContextChunk:
    chunk_id: str
    document_id: str
    index: int
    text: str
    char_start: int
    char_end: int
    page_start: int | None = None
    page_end: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ContextResult:
    document_id: str
    text_length: int
    chunk_count: int
    chunks: tuple[ContextChunk, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "text_length": self.text_length,
            "chunk_count": self.chunk_count,
            "chunks": [c.to_dict() for c in self.chunks],
        }


def normalize_text(text: str) -> str:
    """Normalize line endings and outer whitespace while preserving paragraph breaks."""
    if not text:
        return ""
    # Standardize CRLF and CR to LF
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip()


def chunk_text(
    document_id: str,
    text: str,
    max_chars: int = 1800,
    overlap_chars: int = 200,
    page_spans: Sequence[tuple[int, int, int]] | None = None,
) -> ContextResult:
    """Split text into bounded chunks with deterministic identifiers and overlap.

    Parameters
    ----------
    document_id:
        Identifier of the document.
    text:
        Raw or normalized input text. Passed through normalize_text.
    max_chars:
        Maximum allowed character length per chunk (must be > 0).
    overlap_chars:
        Maximum character overlap between successive chunks (must be >= 0 and < max_chars).
    page_spans:
        Optional sequence of (page_number, span_start, span_end) half-open intervals
        in the normalized text used to calculate page_start and page_end.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be non-negative")
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be strictly less than max_chars")

    norm_text = normalize_text(text)
    total_len = len(norm_text)
    if total_len == 0:
        return ContextResult(
            document_id=document_id,
            text_length=0,
            chunk_count=0,
            chunks=(),
        )

    chunks: list[ContextChunk] = []
    step = max_chars - overlap_chars
    start = 0
    idx = 0

    while start < total_len:
        end = min(start + max_chars, total_len)
        chunk_text_slice = norm_text[start:end]

        p_start: int | None = None
        p_end: int | None = None
        if page_spans:
            overlapping_pages = [
                p_num for p_num, p_s, p_e in page_spans
                if max(start, p_s) < min(end, p_e)
            ]
            if overlapping_pages:
                p_start = min(overlapping_pages)
                p_end = max(overlapping_pages)

        chunk_id = f"{document_id}:chunk:{idx:04d}"
        chunks.append(
            ContextChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                index=idx,
                text=chunk_text_slice,
                char_start=start,
                char_end=end,
                page_start=p_start,
                page_end=p_end,
            )
        )
        idx += 1

        if end >= total_len:
            break
        start += step

    return ContextResult(
        document_id=document_id,
        text_length=total_len,
        chunk_count=len(chunks),
        chunks=tuple(chunks),
    )


def build_context_for_normalized_text(
    *,
    document_id: str,
    normalized_text: str,
    max_chars: int = 1800,
    overlap_chars: int = 200,
) -> ContextResult:
    """Build deterministic context from the canonical normalized text."""
    return chunk_text(
        document_id=document_id,
        text=normalized_text,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )


def build_context_from_normalized_document(
    doc: NormalizedDocument,
    max_chars: int = 1800,
    overlap_chars: int = 200,
) -> ContextResult:
    """Build deterministic context chunks from a NormalizedDocument preserving page provenance."""
    page_spans: list[tuple[int, int, int]] = []
    text_parts: list[str] = []
    current_offset = 0

    for page in doc.pages:
        page_text = page.text
        if not page_text:
            continue
        p_start = current_offset
        text_parts.append(page_text)
        current_offset += len(page_text)
        p_end = current_offset
        page_spans.append((page.page_number, p_start, p_end))
        current_offset += 2  # Account for "\n\n" between pages

    full_text = "\n\n".join(text_parts)
    return chunk_text(
        document_id=doc.doc_id,
        text=full_text,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
        page_spans=page_spans if page_spans else None,
    )
