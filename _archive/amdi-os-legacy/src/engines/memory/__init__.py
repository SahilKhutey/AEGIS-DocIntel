"""
AMDI-OS Hierarchical Memory Engine
====================================

Six-level hierarchical memory for AMDI-OS:

    L0 Raw        — original document content (bytes / strings)
    L1 Templates  — extracted templates & fingerprints
    L2 Structures — graph / topological / tensor structures
    L3 Tables     — matrix / tabular representations
    L4 Semantic   — embeddings & semantic vectors
    L5 Summaries  — compressed summaries

Operations:
    Store     — write to a level
    Cache     — promote fast-access data to a faster level
    Promote   — move data to higher-priority level (L5 ← L0)
    Evict     — remove data based on policy (LRU / LFU / ARC)
    Retrieve  — query memory at any level

Mathematical Foundation:
    Level priority:  L5 > L4 > L3 > L2 > L1 > L0
    Promotion rule:  if access_count(v) ≥ θ_p → promote
    Eviction rule:   if memory_full(level) → evict lowest score
    Score(v)         = α·recency + β·frequency + γ·importance

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .memory_engine import MemoryEngine, MemoryReport
from .hierarchical_memory import HierarchicalMemory, MemoryStats
from .levels import MemoryLevel, LevelMetadata
from .store import StorageManager, StorageBackend
from .cache import CacheManager, CachePolicy
from .promoter import Promoter, PromotionPolicy
from .evictor import Evictor, EvictionPolicy
from .retriever import MemoryRetriever, RetrievalQuery, RetrievalResult
from .access_tracker import AccessTracker, AccessRecord
from .exceptions import (
    MemoryEngineError,
    LevelNotFoundError,
    CapacityExceededError,
    EvictionError,
    PromotionError,
)

__all__ = [
    "MemoryEngine",
    "MemoryReport",
    "HierarchicalMemory",
    "MemoryStats",
    "MemoryLevel",
    "LevelMetadata",
    "StorageManager",
    "StorageBackend",
    "CacheManager",
    "CachePolicy",
    "Promoter",
    "PromotionPolicy",
    "Evictor",
    "EvictionPolicy",
    "MemoryRetriever",
    "RetrievalQuery",
    "RetrievalResult",
    "AccessTracker",
    "AccessRecord",
    "MemoryEngineError",
    "LevelNotFoundError",
    "CapacityExceededError",
    "EvictionError",
    "PromotionError",
]

__version__ = "1.0.0"
