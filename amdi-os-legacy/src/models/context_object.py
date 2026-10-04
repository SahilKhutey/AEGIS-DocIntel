"""
AEGIS-AMDI-OS — Context Object Schema
=======================================
Built context for LLM consumption.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field


class ContextSource(str, Enum):
    """Source of a context piece."""
    TEXT = "text"
    TABLE = "table"
    GRAPH_NODE = "graph_node"
    TEMPLATE = "template"
    SEMANTIC = "semantic"
    MEMORY = "memory"
    EXTERNAL = "external"


class ContextPiece(BaseModel):
    """A single piece of context."""

    piece_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    source: ContextSource = ContextSource.TEXT
    source_id: str = ""

    # Relevance
    relevance_score: float = 0.0
    layer_scores: dict[str, float] = Field(default_factory=dict)

    # Position
    page: int = 0
    section: str | None = None

    # Tokens
    token_count: int = 0

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextBudget(BaseModel):
    """Token budget for context building."""

    total: int = 6000
    system: int = 800
    context: int = 4000
    question: int = 300
    output: int = 1500
    safety_margin: int = 200

    @computed_field
    @property
    def used(self) -> int:
        return self.system + self.context + self.question

    @computed_field
    @property
    def remaining(self) -> int:
        return self.context - self.used + self.system + self.question

    @computed_field
    @property
    def utilization(self) -> float:
        if self.context == 0:
            return 0.0
        return self.used / self.context


class Citation(BaseModel):
    """A citation reference."""
    element_id: str
    page: int
    section: str | None = None
    snippet: str = ""
    confidence: float = 0.0
    bbox: list[float] | None = None


class ContextObject(BaseModel):
    """
    Built context ready for LLM consumption.

    Includes system prompt, assembled context, citations, and metadata.
    """

    # ===== Identity =====
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str

    # ===== Query =====
    query: str
    query_type: str = "unknown"

    # ===== System prompt =====
    system_prompt: str = ""

    # ===== Context pieces =====
    pieces: list[ContextPiece] = Field(default_factory=list)
    assembled_context: str = ""

    # ===== Citations =====
    citations: list[Citation] = Field(default_factory=list)

    # ===== Budget =====
    budget: ContextBudget = Field(default_factory=ContextBudget)

    # ===== Metrics =====
    tokens_used: int = 0
    pieces_included: int = 0
    pieces_excluded: int = 0

    # ===== Layer weights used =====
    layer_weights: dict[str, float] = Field(default_factory=dict)
    dominant_layer: str = ""

    # ===== Confidence =====
    confidence: float = 0.0

    # ===== Metadata =====
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""

    # ===== Computed =====
    @computed_field
    @property
    def efficiency(self) -> float:
        """Tokens per source element."""
        if not self.pieces:
            return 0.0
        return self.tokens_used / len(self.pieces)

    @computed_field
    @property
    def avg_relevance(self) -> float:
        if not self.pieces:
            return 0.0
        return sum(p.relevance_score for p in self.pieces) / len(self.pieces)

    @computed_field
    @property
    def citation_count(self) -> int:
        return len(self.citations)

    # ===== Methods =====
    def to_llm_messages(self) -> list[dict[str, str]]:
        """Format as OpenAI-style messages."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"CONTEXT:\n{self.assembled_context}\n\nQUESTION: {self.query}\n\nANSWER:"},
        ]

    def add_citation(self, citation: Citation) -> None:
        self.citations.append(citation)

    model_config = {"json_schema_extra": {
        "example": {
            "doc_id": "doc-123",
            "query": "What is the total revenue?",
            "query_type": "aggregate",
            "tokens_used": 3500,
            "dominant_layer": "matrix",
        }
    }}
