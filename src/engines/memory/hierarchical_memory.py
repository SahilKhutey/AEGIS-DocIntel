"""
Hierarchical Memory
===================

The complete L0-L5 hierarchical memory system combining
storage, cache, promotion, eviction, and retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .access_tracker import AccessTracker
from .cache import CacheManager, CachePolicy
from .evictor import Evictor, EvictionPolicy
from .levels import (
    DEFAULT_LEVEL_CONFIG,
    LevelMetadata,
    MemoryLevel,
    get_level_metadata,
)
from .promoter import Promoter, PromotionPolicy, PromotionDecision
from .retriever import MemoryRetriever, RetrievalQuery, RetrievalResult
from .store import StorageBackend, StorageManager, StoredItem


@dataclass
class MemoryStats:
    """Statistics for the entire memory system."""

    total_items: int
    total_bytes: int
    items_per_level: Dict[MemoryLevel, int]
    bytes_per_level: Dict[MemoryLevel, int]
    capacity_per_level: Dict[MemoryLevel, int]
    cache_size: int
    total_accesses: int

    def to_dict(self) -> dict:
        return {
            "total_items": self.total_items,
            "total_bytes": self.total_bytes,
            "items_per_level": {
                l.name_long: self.items_per_level[l] for l in MemoryLevel
            },
            "bytes_per_level": {
                l.name_long: self.bytes_per_level[l] for l in MemoryLevel
            },
            "cache_size": self.cache_size,
            "total_accesses": self.total_accesses,
        }


class HierarchicalMemory:
    """
    The hierarchical memory system.
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
        if isinstance(storage_backend, str) and storage_backend.startswith("redis://"):
            self.redis_url = storage_backend
            self.backend_type = "redis"
            backend = StorageBackend.IN_MEMORY
        else:
            self.redis_url = None
            self.backend_type = "in_memory"
            if isinstance(storage_backend, str):
                try:
                    backend = StorageBackend(storage_backend)
                except ValueError:
                    backend = StorageBackend.IN_MEMORY
            else:
                backend = storage_backend

        self.storage = StorageManager(
            backend=backend,
            level_config=level_config,
        )
        self.tracker = AccessTracker()
        self.cache = CacheManager(capacity=cache_capacity, policy=cache_policy) if enable_cache else None
        self.promoter = Promoter(policy=promotion_policy)
        self.evictor = Evictor(policy=eviction_policy)
        self.retriever = MemoryRetriever(
            storage=self.storage,
            tracker=self.tracker,
            cache=self.cache,
        )
        self.redis: Any = None

    async def connect(self) -> None:
        """Connect to Redis if configured."""
        if self.backend_type == "redis" and self.redis_url:
            try:
                import redis.asyncio as redis_async
                self.redis = redis_async.from_url(self.redis_url, decode_responses=False)
                await self.redis.ping()
            except Exception:
                self.redis = None

    async def close(self) -> None:
        """Close connection to Redis."""
        if self.redis is not None:
            try:
                await self.redis.close()
            except Exception:
                pass
            self.redis = None

    async def put(self, key: str, value: Any, level: int | MemoryLevel = MemoryLevel.L5_SUMMARIES, importance: float = 0.5) -> None:
        """Store/cache an item under key asynchronously. Compatibility helper."""
        if isinstance(level, int):
            lvl = MemoryLevel(level)
        else:
            lvl = level
        self.store(key, lvl, value, importance=importance, force=True)
        if self.cache is not None:
            self.cache.put(key, value)

    # =========================================================================
    # Store
    # =========================================================================

    def store(
        self,
        item_id: str,
        level: MemoryLevel,
        data: Any,
        importance: float = 0.5,
        force: bool = False,
    ) -> StoredItem:
        """Store an item at a level."""
        item = self.storage.store(item_id, level, data, importance, force=force)
        self.tracker.record_write(item_id)
        return item

    def store_multi(
        self,
        items: List[Dict[str, Any]],
        default_level: MemoryLevel = MemoryLevel.L0_RAW,
    ) -> List[StoredItem]:
        """Store multiple items.

        Each item dict must contain 'item_id' and 'data'; optional 'level' and 'importance'.
        """
        results: List[StoredItem] = []
        for entry in items:
            level = entry.get("level", default_level)
            results.append(
                self.store(
                    item_id=entry["item_id"],
                    level=level,
                    data=entry["data"],
                    importance=entry.get("importance", 0.5),
                    force=entry.get("force", False),
                )
            )
        return results

    # =========================================================================
    # Retrieve & Get/Set API
    # =========================================================================

    def get(self, level_or_key: int | str | MemoryLevel, key: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve an item. Supports signatures:
        - get(level, key)
        - get(key)
        """
        if key is not None:
            if isinstance(level_or_key, int):
                level = MemoryLevel(level_or_key)
            else:
                level = level_or_key
            if self.cache is not None:
                cached = self.cache.get(key)
                if cached is not None:
                    return cached
            stored = self.storage.get(key, level)
            if stored is not None:
                self.tracker.record_read(key)
                if self.cache is not None:
                    self.cache.put(key, stored.data)
                return stored.data
            return None
        else:
            key = level_or_key
            if self.cache is not None:
                cached = self.cache.get(key)
                if cached is not None:
                    return cached
            retrieved = self.retriever.retrieve_by_id(key)
            if retrieved is not None:
                return retrieved.data
            return None

    def set(self, key: str, value: Any, level: int | MemoryLevel = MemoryLevel.L5_SUMMARIES, importance: float = 0.5) -> None:
        """Store/cache an item under key. Alias for store."""
        if isinstance(level, int):
            lvl = MemoryLevel(level)
        else:
            lvl = level
        self.store(key, lvl, value, importance=importance, force=True)
        if self.cache is not None:
            self.cache.put(key, value)

    def retrieve(
        self,
        query: str,
        target_levels: Optional[List[MemoryLevel]] = None,
        top_k: int = 10,
        embedding: Optional[Any] = None,
    ) -> RetrievalResult:
        """Retrieve items matching the query."""
        q = RetrievalQuery(
            query=query,
            target_levels=target_levels,
            top_k=top_k,
            embedding=embedding,
        )
        return self.retriever.retrieve(q)

    def retrieve_by_id(
        self,
        item_id: str,
        levels: Optional[List[MemoryLevel]] = None,
    ) -> Optional[Any]:
        """Retrieve by exact ID."""
        result = self.retriever.retrieve_by_id(item_id, levels=levels)
        return result.data if result is not None else None

    # =========================================================================
    # Cache
    # =========================================================================

    def cache_get(self, key: str) -> Optional[Any]:
        if self.cache is None:
            return None
        return self.cache.get(key)

    def cache_put(self, key: str, value: Any) -> None:
        if self.cache is not None:
            self.cache.put(key, value)

    def cache_invalidate(self, key: str) -> bool:
        if self.cache is None:
            return False
        return self.cache.invalidate(key)

    def cache_clear(self) -> None:
        if self.cache is not None:
            self.cache.clear()

    # =========================================================================
    # Promotion & Eviction
    # =========================================================================

    def promote(self, item_id: str, level: MemoryLevel) -> Optional[PromotionDecision]:
        """Decide and execute promotion for an item."""
        decision = self.promoter.should_promote(item_id, level, self.storage, self.tracker)
        if decision is not None:
            if self.storage.move(decision.item_id, level, decision.to_level):
                return decision
        return None

    def evict(self, level: MemoryLevel, n: int = 1) -> List[str]:
        """Evict N items from a level."""
        return self.evictor.evict(level, self.storage, self.tracker, n=n)

    # =========================================================================
    # Control operations
    # =========================================================================

    def clear_all(self) -> None:
        """Clear all storage and caches."""
        self.storage.clear_all()
        if self.cache is not None:
            self.cache.clear()

    def invalidate(self, doc_id: str) -> int:
        """Invalidate all items and keys matching doc_id. Legacy compat."""
        removed_count = 0
        for level in MemoryLevel:
            for item in self.storage.items_at_level(level):
                if doc_id in item.item_id:
                    self.storage.remove(item.item_id, level)
                    self.tracker.remove(item.item_id)
                    if self.cache is not None:
                        self.cache.invalidate(item.item_id)
                    removed_count += 1
        return removed_count

    def get_stats(self) -> MemoryStats:
        """Get current stats object."""
        total_items = sum(self.storage.item_count(lvl) for lvl in MemoryLevel)
        total_bytes = sum(self.storage.size_bytes(lvl) for lvl in MemoryLevel)
        items_per_level = {lvl: self.storage.item_count(lvl) for lvl in MemoryLevel}
        bytes_per_level = {lvl: self.storage.size_bytes(lvl) for lvl in MemoryLevel}
        capacity_per_level = {lvl: self.storage.capacity(lvl).capacity_items for lvl in MemoryLevel}
        cache_size = self.cache.size() if self.cache is not None else 0
        total_accesses = sum(r.access_count for r in self.tracker.records.values())

        return MemoryStats(
            total_items=total_items,
            total_bytes=total_bytes,
            items_per_level=items_per_level,
            bytes_per_level=bytes_per_level,
            capacity_per_level=capacity_per_level,
            cache_size=cache_size,
            total_accesses=total_accesses,
        )

    def statistics(self) -> Dict[str, Any]:
        """Get stats in the legacy dict format."""
        result = {}
        temps = {0: "cold", 1: "cold", 2: "warm", 3: "warm", 4: "hot", 5: "hot"}
        names = {0: "RAW", 1: "TEMPLATE", 2: "STRUCTURE", 3: "TABLE", 4: "CHUNK", 5: "SUMMARY"}
        for level in MemoryLevel:
            name = names[level.value]
            result[name] = {
                "tier": level.value,
                "temperature": temps[level.value],
                "entries": self.storage.item_count(level),
                "hit_rate": 0.0,
                "redis_backed": False,
            }
        return result
