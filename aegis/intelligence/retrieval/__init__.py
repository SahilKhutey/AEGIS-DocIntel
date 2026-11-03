"""
aegis.intelligence.retrieval
============================
Retrieval module providing Lexical (BM25), Semantic, Structured, and Hybrid (RRF) retrievers.
"""

from aegis.intelligence.retrieval.base import BaseRetriever
from aegis.intelligence.retrieval.evaluator import RetrievalEvaluator, RetrievalMetrics
from aegis.intelligence.retrieval.hybrid import HybridRetriever
from aegis.intelligence.retrieval.lexical import LexicalRetriever
from aegis.intelligence.retrieval.semantic import SemanticRetriever
from aegis.intelligence.retrieval.structured import StructuredRetriever

__all__ = [
    "BaseRetriever",
    "HybridRetriever",
    "LexicalRetriever",
    "RetrievalEvaluator",
    "RetrievalMetrics",
    "SemanticRetriever",
    "StructuredRetriever",
]
