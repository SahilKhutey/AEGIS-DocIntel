"""
AEGIS-DocIntel — API Data Models (Pydantic v2)
===============================================
Request/Response schemas for all API endpoints.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────

class DocumentStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    REINDEXING = "reindexing"


class BlockTypeEnum(str, Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    HEADER = "header"
    FOOTER = "footer"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ─────────────────────────────────────────────────────────────────
# Document Models
# ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    doc_id: UUID
    tenant_id: str                       # str: supports both UUID and dev-mode IDs
    filename: str
    status: DocumentStatus
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    is_scanned: bool = False
    language: str = "en"
    created_at: datetime
    indexed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class BatchUploadRequest(BaseModel):
    documents: list[dict[str, str]] = Field(
        ...,
        description="List of {s3_uri, doc_id?, priority} entries",
        max_length=10000,
    )


class BatchUploadResponse(BaseModel):
    job_id: UUID
    doc_count: int
    status: str = "queued"


class IngestionStatusResponse(BaseModel):
    doc_id: UUID
    status: DocumentStatus
    progress_percent: Optional[float] = None
    stage: Optional[str] = None
    error: Optional[str] = None
    chunks_indexed: int = 0


# ─────────────────────────────────────────────────────────────────
# Query Models
# ─────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    doc_ids: Optional[list[UUID]] = Field(
        default=None,
        description="Filter to specific documents. None = all tenant docs.",
    )
    top_k: Optional[int] = Field(default=None, ge=1, le=50)
    session_id: Optional[UUID] = None
    include_citations: bool = True
    stream: bool = False
    block_types: Optional[list[BlockTypeEnum]] = None
    language: Optional[str] = None

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class CitationModel(BaseModel):
    source_num: int
    chunk_id: str
    doc_id: str
    filename: Optional[str] = None
    page: int
    section: Optional[str] = None
    snippet: str
    confidence: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationModel] = []
    confidence: ConfidenceLevel
    confidence_score: float
    session_id: UUID
    tokens_used: dict[str, int]  # {"input": N, "output": N, "total": N}
    retrieval_latency_ms: float
    total_latency_ms: float
    cached: bool = False
    model: str


class StreamChunk(BaseModel):
    """Streaming response chunk for SSE."""
    type: str  # "token" | "citation" | "done" | "error"
    content: Optional[str] = None
    citations: Optional[list[CitationModel]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────
# Chunk Models
# ─────────────────────────────────────────────────────────────────

class ChunkResponse(BaseModel):
    chunk_id: str
    doc_id: str
    page_start: int
    page_end: int
    section: Optional[str] = None
    block_type: BlockTypeEnum
    text: str
    token_count: int


class ChunkListResponse(BaseModel):
    items: list[ChunkResponse]
    total: int


# ─────────────────────────────────────────────────────────────────
# Admin Models
# ─────────────────────────────────────────────────────────────────

class TenantStats(BaseModel):
    tenant_id: UUID
    doc_count: int
    chunk_count: int
    total_tokens_used: int
    total_cost_usd: float
    cache_hit_rate: float
    avg_query_latency_ms: float


class TokenUsageResponse(BaseModel):
    period: str
    total_in_tokens: int
    total_out_tokens: int
    total_cost_usd: float
    query_count: int
    cache_hits: int
    avg_latency_ms: float


# ─────────────────────────────────────────────────────────────────
# System Models
# ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    checks: dict[str, str]


class ErrorResponse(BaseModel):
    detail: str
    request_id: Optional[str] = None
    code: Optional[str] = None
