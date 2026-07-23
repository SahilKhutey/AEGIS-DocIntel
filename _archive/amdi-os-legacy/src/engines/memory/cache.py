"""
Cache Manager
=============

Caches frequently-accessed items for fast retrieval.

Policies:
- LRU  (Least Recently Used)
- LFU  (Least Frequently Used)
- ARC  (Adaptive Replacement Cache)
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import CapacityExceededError


class CachePolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    ARC = "arc"


@dataclass
class CacheEntry:
    """A cached item."""

    key: str
    value: Any
    frequency: int = 0
    last_access_order: int = 0


class CacheManager:
    """
    In-memory cache with configurable eviction policy.
    """

    def __init__(
        self,
        capacity: int = 1000,
        policy: CachePolicy = CachePolicy.LRU,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive.")
        self.capacity = capacity
        self.policy = policy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.freq_index: Dict[str, int] = {}
        self._access_counter = 0
        # ARC: separate T1 (recent) and T2 (frequent) lists
        self._arc_t1: OrderedDict[str, Any] = OrderedDict()
        self._arc_t2: OrderedDict[str, Any] = OrderedDict()
        self._arc_b1: OrderedDict[str, Any] = OrderedDict()
        self._arc_b2: OrderedDict[str, Any] = OrderedDict()
        self._arc_p = 0  # adaptation parameter

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache; updates access stats."""
        if self.policy == CachePolicy.LRU:
            return self._lru_get(key)
        if self.policy == CachePolicy.LFU:
            return self._lfu_get(key)
        if self.policy == CachePolicy.ARC:
            return self._arc_get(key)
        return None

    def put(self, key: str, value: Any) -> None:
        """Put a value into the cache."""
        if self.policy == CachePolicy.LRU:
            self._lru_put(key, value)
        elif self.policy == CachePolicy.LFU:
            self._lfu_put(key, value)
        elif self.policy == CachePolicy.ARC:
            self._arc_put(key, value)

    def invalidate(self, key: str) -> bool:
        """Remove a key from the cache."""
        removed = False
        if key in self.cache:
            del self.cache[key]
            self.freq_index.pop(key, None)
            removed = True
        for d in (self._arc_t1, self._arc_t2, self._arc_b1, self._arc_b2):
            if key in d:
                del d[key]
                removed = True
        return removed

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.freq_index.clear()
        self._arc_t1.clear()
        self._arc_t2.clear()
        self._arc_b1.clear()
        self._arc_b2.clear()
        self._arc_p = 0

    def size(self) -> int:
        if self.policy == CachePolicy.ARC:
            return len(self._arc_t1) + len(self._arc_t2)
        return len(self.cache)

    def keys(self) -> List[str]:
        if self.policy == CachePolicy.ARC:
            return list(self._arc_t1.keys()) + list(self._arc_t2.keys())
        return list(self.cache.keys())

    # ========================================================================
    # LRU
    # ========================================================================

    def _lru_get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        entry = self.cache[key]
        # move to end (most recent)
        self.cache.move_to_end(key)
        entry.frequency += 1
        self._access_counter += 1
        entry.last_access_order = self._access_counter
        return entry.value

    def _lru_put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key].value = value
            self.cache[key].frequency += 1
            return
        if len(self.cache) >= self.capacity:
            # evict LRU = first item
            self.cache.popitem(last=False)
        self._access_counter += 1
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            frequency=1,
            last_access_order=self._access_counter,
        )

    # ========================================================================
    # LFU
    # ========================================================================

    def _lfu_get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        entry = self.cache[key]
        entry.frequency += 1
        return entry.value

    def _lfu_put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache[key].value = value
            self.cache[key].frequency += 1
            return
        if len(self.cache) >= self.capacity:
            # evict least frequent (ties broken by insertion order)
            victim = min(self.cache.values(), key=lambda e: (e.frequency, e.last_access_order))
            del self.cache[victim.key]
            self.freq_index.pop(victim.key, None)
        self._access_counter += 1
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            frequency=1,
            last_access_order=self._access_counter,
        )

    # ========================================================================
    # ARC (Adaptive Replacement Cache)
    # ========================================================================

    def _arc_get(self, key: str) -> Optional[Any]:
        if key in self._arc_t1:
            # promote to T2
            val = self._arc_t1.pop(key)
            self._arc_t2[key] = val
            return val
        if key in self._arc_t2:
            # move to end of T2 (most recent)
            self._arc_t2.move_to_end(key)
            return self._arc_t2[key]
        return None

    def _arc_put(self, key: str, value: Any) -> None:
        c = self.capacity
        if key in self._arc_t1 or key in self._arc_t2:
            # Update value and move to T2
            if key in self._arc_t1:
                self._arc_t1.pop(key)
            else:
                self._arc_t2.pop(key)
            self._arc_t2[key] = value
            return

        in_b1 = key in self._arc_b1
        in_b2 = key in self._arc_b2

        if in_b1:
            # adapt: increase p
            delta = max(1, len(self._arc_b2) // max(len(self._arc_b1), 1))
            self._arc_p = min(self._arc_p + delta, c)
            self._replace(key, self._arc_p)
            self._arc_b1.pop(key)
            self._arc_t2[key] = value
            return

        if in_b2:
            # adapt: decrease p
            delta = max(1, len(self._arc_b1) // max(len(self._arc_b2), 1))
            self._arc_p = max(self._arc_p - delta, 0)
            self._replace(key, self._arc_p)
            self._arc_b2.pop(key)
            self._arc_t2[key] = value
            return

        # key is not in T1, T2, B1, or B2
        t1_size = len(self._arc_t1)
        b1_size = len(self._arc_b1)
        t2_size = len(self._arc_t2)
        b2_size = len(self._arc_b2)

        if t1_size + b1_size == c:
            if t1_size < c:
                self._arc_b1.popitem(last=False)
                self._replace(key, self._arc_p)
            else:
                self._arc_t1.popitem(last=False)
        elif t1_size + b1_size < c:
            total_size = t1_size + t2_size + b1_size + b2_size
            if total_size >= c:
                if total_size == 2 * c:
                    self._arc_b2.popitem(last=False)
                self._replace(key, self._arc_p)

        self._arc_t1[key] = value

    def _replace(self, key: str, p: float) -> None:
        """ARC replacement decision."""
        t1_size = len(self._arc_t1)
        if t1_size > 0 and (t1_size > p or (key in self._arc_b2 and t1_size == p)):
            # Evict LRU from T1, move to B1 (ghost)
            k, v = self._arc_t1.popitem(last=False)
            self._arc_b1[k] = True
        else:
            # Evict LRU from T2, move to B2 (ghost)
            if len(self._arc_t2) > 0:
                k, v = self._arc_t2.popitem(last=False)
                self._arc_b2[k] = True
