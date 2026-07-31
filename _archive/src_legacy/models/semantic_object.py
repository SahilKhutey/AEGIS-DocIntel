"""
AEGIS-AMDI-OS — Semantic Object Schema
========================================
Embeddings, NER, keyphrases, and metadata.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field


class EntityType(str, Enum):
    """Named entity types."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    PERCENT = "percent"
    PRODUCT = "product"
    EVENT = "event"
    QUANTITY = "quantity"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    OTHER = "other"


class Entity(BaseModel):
    """A named entity extracted from text."""
    text: str
    type: EntityType = EntityType.OTHER
    page: int = 0
    confidence: float = Field(1.0, ge=0, le=1)
    start_offset: int = 0
    end_offset: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Keyphrase(BaseModel):
    """An extracted keyphrase."""
    text: str
    score: float = Field(0.0, ge=0, le=1)
    frequency: int = 1
    page: int = 0


class Topic(BaseModel):
    """A topic/theme in the document."""
    name: str
    weight: float = Field(1.0, ge=0)
    pages: list[int] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class SentimentScore(BaseModel):
    """Sentiment analysis result."""
    positive: float = 0.0
    neutral: float = 1.0
    negative: float = 0.0
    compound: float = 0.0

    @computed_field
    @property
    def label(self) -> str:
        if self.compound > 0.05:
            return "positive"
        elif self.compound < -0.05:
            return "negative"
        return "neutral"


class EmbeddingInfo(BaseModel):
    """Metadata about embeddings."""
    model: str = "BAAI/bge-large-en-v1.5"
    dimension: int = 1024
    normalized: bool = True
    device: str = "cpu"


class SemanticObject(BaseModel):
    """
    Semantic representation of a document element.

    Includes embeddings, NER, keyphrases, and topic analysis.
    """

    # ===== Identity =====
    semantic_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    element_id: str | None = None
    page: int = 0

    # ===== Text =====
    text: str = ""

    # ===== Embeddings =====
    embedding: list[float] | None = None
    embedding_info: EmbeddingInfo = Field(default_factory=EmbeddingInfo)

    # ===== Entities =====
    entities: list[Entity] = Field(default_factory=list)

    # ===== Keyphrases =====
    keyphrases: list[Keyphrase] = Field(default_factory=list)

    # ===== Topics =====
    topics: list[Topic] = Field(default_factory=list)

    # ===== Sentiment =====
    sentiment: SentimentScore = Field(default_factory=SentimentScore)

    # ===== Summary =====
    summary: str = ""
    summary_length: int = 0

    # ===== Statistics =====
    token_count: int = 0
    char_count: int = 0
    language: str = "en"

    # ===== Metadata =====
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ===== Computed =====
    @computed_field
    @property
    def n_entities(self) -> int:
        return len(self.entities)

    @computed_field
    @property
    def n_keyphrases(self) -> int:
        return len(self.keyphrases)

    @computed_field
    @property
    def has_embedding(self) -> bool:
        return self.embedding is not None and len(self.embedding) > 0

    # ===== Methods =====
    def to_vector(self) -> list[float] | None:
        """Get embedding as vector."""
        return self.embedding

    def top_entities(self, n: int = 5) -> list[Entity]:
        """Get top N entities by confidence."""
        return sorted(self.entities, key=lambda e: e.confidence, reverse=True)[:n]

    def top_keyphrases(self, n: int = 5) -> list[Keyphrase]:
        """Get top N keyphrases by score."""
        return sorted(self.keyphrases, key=lambda k: k.score, reverse=True)[:n]

    model_config = {"json_schema_extra": {
        "example": {
            "doc_id": "doc-123",
            "text": "Revenue was $1.2B in Q4 2024.",
            "entities": [{"text": "Q4 2024", "type": "date", "confidence": 0.95}],
            "keyphrases": [{"text": "revenue", "score": 0.9}],
        }
    }}
