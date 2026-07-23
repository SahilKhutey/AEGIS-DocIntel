"""
AMDI-OS Memory Engine Orchestrator
===================================
Main orchestrator for L0-L5 hierarchical memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .cache import CachePolicy
from .evictor import EvictionPolicy
from .exceptions import MemoryEngineError
from .hierarchical_memory import HierarchicalMemory, MemoryStats
from .levels import MemoryLevel, LevelMetadata
from .promoter import PromotionDecision, PromotionPolicy
from .retriever import RetrievalResult
from .store import StorageBackend, StoredItem


@dataclass
class MemoryReport:
    """
    Comprehensive report of the memory engine state.
    """

    stats: MemoryStats
    cache_policy: str
    cache_capacity: int
    active_levels: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stats": self.stats.to_dict(),
            "cache_policy": self.cache_policy,
            "cache_capacity": self.cache_capacity,
            "active_levels": self.active_levels,
            "metadata": self.metadata,
        }


class MemoryEngine:
    """
    Main orchestrator for L0-L5 Hierarchical Memory Engine.
    Combines cache, levels, promoters, evictors, and retrievers.
    """

    def __init__(
        self,
        storage_backend: StorageBackend | str = StorageBackend.IN_MEMORY,
        cache_capacity: int = 1000,
        cache_policy: CachePolicy = CachePolicy.LRU,
        promotion_policy: PromotionPolicy = PromotionPolicy.HYBRID,
        eviction_policy: EvictionPolicy = EvictionPolicy.HYBRID,
        level_config: Optional[Dict[MemoryLevel, LevelMetadata]] = None,
        enable_cache: bool = True,
    ) -> None:
        self.memory = HierarchicalMemory(
            storage_backend=storage_backend,
            cache_capacity=cache_capacity,
            cache_policy=cache_policy,
            promotion_policy=promotion_policy,
            eviction_policy=eviction_policy,
            level_config=level_config,
            enable_cache=enable_cache,
        )

    async def connect(self) -> None:
        """Connect to external storage databases."""
        await self.memory.connect()

    async def close(self) -> None:
        """Close storage connections."""
        await self.memory.close()

    def store(
        self,
        item_id: str,
        level: MemoryLevel,
        data: Any,
        importance: float = 0.5,
        force: bool = False,
    ) -> StoredItem:
        """Store an item at a level."""
        return self.memory.store(
            item_id=item_id,
            level=level,
            data=data,
            importance=importance,
            force=force,
        )

    def store_multi(
        self,
        items: List[Dict[str, Any]],
        default_level: MemoryLevel = MemoryLevel.L0_RAW,
    ) -> List[StoredItem]:
        """Store multiple items."""
        return self.memory.store_multi(items=items, default_level=default_level)

    def get(self, level_or_key: int | str | MemoryLevel, key: Optional[str] = None) -> Optional[Any]:
        """Get an item from cache or hierarchical storage."""
        return self.memory.get(level_or_key, key)

    def set(
        self,
        key: str,
        value: Any,
        level: int | MemoryLevel = MemoryLevel.L5_SUMMARIES,
        importance: float = 0.5,
    ) -> None:
        """Set/cache an item under key."""
        self.memory.set(key, value, level=level, importance=importance)

    async def put(
        self,
        key: str,
        value: Any,
        level: int | MemoryLevel = MemoryLevel.L5_SUMMARIES,
        importance: float = 0.5,
    ) -> None:
        """Store/cache an item asynchronously (compatibility alias)."""
        await self.memory.put(key, value, level=level, importance=importance)

    def retrieve(
        self,
        query: str,
        target_levels: Optional[List[MemoryLevel]] = None,
        top_k: int = 10,
        embedding: Optional[Any] = None,
    ) -> RetrievalResult:
        """Retrieve items from memory."""
        return self.memory.retrieve(
            query=query,
            target_levels=target_levels,
            top_k=top_k,
            embedding=embedding,
        )

    def retrieve_by_id(
        self,
        item_id: str,
        levels: Optional[List[MemoryLevel]] = None,
    ) -> Optional[Any]:
        """Retrieve an item by ID."""
        return self.memory.retrieve_by_id(item_id, levels=levels)

    def cache_get(self, key: str) -> Optional[Any]:
        """Retrieve from cache directly."""
        return self.memory.cache_get(key)

    def cache_put(self, key: str, value: Any) -> None:
        """Put in cache directly."""
        self.memory.cache_put(key, value)

    def cache_invalidate(self, key: str) -> bool:
        """Remove a key from cache."""
        return self.memory.cache_invalidate(key)

    def cache_clear(self) -> None:
        """Clear cache."""
        self.memory.cache_clear()

    def promote(self, item_id: str, level: MemoryLevel) -> Optional[PromotionDecision]:
        """Promote an item to the next level if threshold met."""
        return self.memory.promote(item_id, level)

    def evict(self, level: MemoryLevel, n: int = 1) -> List[str]:
        """Evict items from a level."""
        return self.memory.evict(level, n=n)

    def clear_all(self) -> None:
        """Clear all storage and caches."""
        self.memory.clear_all()

    def invalidate(self, doc_id: str) -> int:
        """Invalidate all items matching doc_id."""
        return self.memory.invalidate(doc_id)

    def get_stats(self) -> MemoryStats:
        """Get statistics of the memory system."""
        return self.memory.get_stats()

    def statistics(self) -> Dict[str, Any]:
        """Get stats in dict format."""
        return self.memory.statistics()

    def generate_report(self, metadata: Optional[Dict[str, Any]] = None) -> MemoryReport:
        """Generate a complete memory report."""
        stats = self.get_stats()
        active_levels = [lvl.name_long for lvl in MemoryLevel]
        cache_policy = self.memory.cache.policy.value if self.memory.cache is not None else "disabled"
        cache_capacity = self.memory.cache.capacity if self.memory.cache is not None else 0
        return MemoryReport(
            stats=stats,
            cache_policy=cache_policy,
            cache_capacity=cache_capacity,
            active_levels=active_levels,
            metadata=metadata or {},
        )
