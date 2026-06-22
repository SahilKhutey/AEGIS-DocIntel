"""
AMDI-OS Advanced Analytics
==========================

A suite of enterprise-grade analytical tools supporting similarity search,
knowledge graph networks, trend prediction, user feedback metrics, and cost tuning.
"""

from .similarity_search import (
    SimilaritySearcher,
    cosine_similarity,
    compute_centroid,
)
from .knowledge_graph import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
)
from .trend_analyzer import (
    TrendAnalyzer,
)
from .user_behavior import (
    BehaviorAnalyticsManager,
    SearchQueryLog,
    SessionLog,
)
from .cost_optimizer import (
    CostOptimizer,
    QueryCostRecord,
)
from .analytics_engine import (
    AnalyticsEngine,
)

__all__ = [
    "SimilaritySearcher",
    "cosine_similarity",
    "compute_centroid",
    "KnowledgeGraph",
    "GraphNode",
    "GraphEdge",
    "TrendAnalyzer",
    "BehaviorAnalyticsManager",
    "SearchQueryLog",
    "SessionLog",
    "CostOptimizer",
    "QueryCostRecord",
    "AnalyticsEngine",
]
