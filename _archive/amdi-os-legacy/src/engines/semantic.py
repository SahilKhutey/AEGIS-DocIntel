"""Alias for easy importing."""
from src.engines.semantic.semantic_engine import (
    SemanticEngine, EmbeddingService,
    SemanticElement, Entity, Keyphrase, Topic, SentimentScore,
    EntityType, SemanticStats, SemanticResult,
)

__all__ = [
    "SemanticEngine", "EmbeddingService",
    "SemanticElement", "Entity", "Keyphrase", "Topic", "SentimentScore",
    "EntityType", "SemanticStats", "SemanticResult",
]
