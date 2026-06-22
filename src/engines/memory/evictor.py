"""
Evictor
=======

Removes items from memory levels based on policies:
- LRU  (Least Recently Used)
- LFU  (Least Frequently Used)
- IMPORTANCE  (lowest importance first)
- HYBRID      (weighted combination)

Mathematical Foundation:
-----------------------
Eviction score (lower = evict first):
    E(v) = α · recency(v) + β · frequency(v) + γ · importance(v)

where recency, frequency, importance are normalized to [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .access_tracker import AccessTracker
from .levels import MemoryLevel
from .store import StorageManager, StoredItem


class EvictionPolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    IMPORTANCE = "importance"
    HYBRID = "hybrid"


@dataclass
class EvictionCandidate:
    """An item selected for eviction."""

    item_id: str
    level: MemoryLevel
    score: float
    reason: str


class Evictor:
    """
    Selects and removes items based on policy.
    """

    def __init__(
        self,
        policy: EvictionPolicy = EvictionPolicy.HYBRID,
        recency_weight: float = 0.4,
        frequency_weight: float = 0.4,
        importance_weight: float = 0.2,
        # higher level = evict more conservatively
        level_protection: Optional[Dict[MemoryLevel, float]] = None,
    ) -> None:
        self.policy = policy
        s = recency_weight + frequency_weight + importance_weight
        self.recency_weight = recency_weight / s
        self.frequency_weight = frequency_weight / s
        self.importance_weight = importance_weight / s
        self.level_protection = level_protection or {
            MemoryLevel.L5_SUMMARIES: 0.95,
            MemoryLevel.L4_SEMANTIC: 0.85,
            MemoryLevel.L3_TABLES: 0.75,
            MemoryLevel.L2_STRUCTURES: 0.65,
            MemoryLevel.L1_TEMPLATES: 0.5,
            MemoryLevel.L0_RAW: 0.3,
        }

    def _score(self, item: StoredItem, rec: Optional[Any]) -> float:
        """Compute eviction score (higher = keep, lower = evict)."""
        if self.policy == EvictionPolicy.LRU:
            return -rec.recency_seconds if rec else -1e9
        if self.policy == EvictionPolicy.LFU:
            return rec.frequency if rec else 0
        if self.policy == EvictionPolicy.IMPORTANCE:
            return item.importance
        # HYBRID
        recency = 1.0 / (1.0 + rec.recency_seconds) if rec else 0.0
        frequency = min(rec.frequency / 100.0, 1.0) if rec else 0.0
        importance = item.importance
        return (
            self.recency_weight * recency
            + self.frequency_weight * frequency
            + self.importance_weight * importance
        )

    def select_victims(
        self,
        level: MemoryLevel,
        storage: StorageManager,
        tracker: AccessTracker,
        n: int = 1,
    ) -> List[EvictionCandidate]:
        """
        Select N items to evict from `level`.

        Items below the level protection threshold are not evicted.
        """
        items = storage.items_at_level(level)
        if not items:
            return []
        candidates: List[EvictionCandidate] = []
        for item in items:
            rec = tracker.get(item.item_id)
            score = self._score(item, rec)
            candidates.append(
                EvictionCandidate(
                    item_id=item.item_id,
                    level=level,
                    score=score,
                    reason=f"score={score:.3f}",
                )
            )
        # sort by score ascending (lowest score = first evicted)
        candidates.sort(key=lambda c: c.score)
        return candidates[:n]

    def evict(
        self,
        level: MemoryLevel,
        storage: StorageManager,
        tracker: AccessTracker,
        n: int = 1,
    ) -> List[str]:
        """
        Evict N items and return their IDs.
        """
        victims = self.select_victims(level, storage, tracker, n=n)
        evicted_ids: List[str] = []
        for v in victims:
            if storage.remove(v.item_id, level):
                tracker.remove(v.item_id)
                evicted_ids.append(v.item_id)
        return evicted_ids

    def free_space(
        self,
        level: MemoryLevel,
        bytes_needed: int,
        storage: StorageManager,
        tracker: AccessTracker,
    ) -> int:
        """
        Evict items until `bytes_needed` is freed.
        Returns number of bytes actually freed.
        """
        current = storage.size_bytes(level)
        target = storage.capacity(level).capacity_bytes
        free = target - current
        freed = 0
        while free < bytes_needed:
            victims = self.select_victims(level, storage, tracker, n=1)
            if not victims:
                break
            v = victims[0]
            item = storage.get(v.item_id, level)
            if item is None:
                break
            if storage.remove(v.item_id, level):
                tracker.remove(v.item_id)
                freed += item.size_bytes
                free += item.size_bytes
        return freed
