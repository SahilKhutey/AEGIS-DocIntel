"""
AEGIS-AMDI — Hierarchical Memory Engine
==========================================
Cold → Warm → Hot tiered memory model.

Level 0  Cold:  Raw pages (disk / object storage)
Level 1  Cold:  Templates (compressed, disk)
Level 2  Warm:  Structures (compressed, in-process)
Level 3  Warm:  Tables / matrices (structured store)
Level 4  Hot:   Semantic chunks (in-memory, vector-ready)
Level 5  Hot:   Summaries + keyphrases (in-memory, instant)

Eviction: LRU per tier, size-capped.
Retrieval: cache-hit at highest hot tier → falls back to warm/cold.
"""
from __future__ import annotations

import json
import logging
import time
import zlib
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

log = logging.getLogger("amdi.memory")


# ─────────────────────────────────────────────────────────────────
# Memory Tiers
# ─────────────────────────────────────────────────────────────────

class MemoryTier(int, Enum):
    RAW       = 0   # Raw page data     (cold)
    TEMPLATE  = 1   # Template store    (cold)
    STRUCTURE = 2   # Structural graph  (warm)
    TABLE     = 3   # Matrix store      (warm)
    CHUNK     = 4   # Semantic chunks   (hot)
    SUMMARY   = 5   # Summaries+KP      (hot)


@dataclass
class MemoryEntry:
    key:         str
    value:       Any
    tier:        MemoryTier
    doc_id:      str
    size_bytes:  int        = 0
    access_count: int       = 0
    created_at:  float      = field(default_factory=time.time)
    accessed_at: float      = field(default_factory=time.time)
    compressed:  bool       = False

    def touch(self) -> None:
        self.accessed_at = time.time()
        self.access_count += 1


# ─────────────────────────────────────────────────────────────────
# LRU Cache (per tier)
# ─────────────────────────────────────────────────────────────────

class LRUCache:
    def __init__(self, max_size_mb: float = 256.0):
        self._max_bytes = int(max_size_mb * 1024 * 1024)
        self._store:    OrderedDict[str, MemoryEntry] = OrderedDict()
        self._bytes:    int = 0

    def get(self, key: str) -> Optional[MemoryEntry]:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        entry = self._store[key]
        entry.touch()
        return entry

    def put(self, entry: MemoryEntry) -> None:
        if entry.key in self._store:
            self._bytes -= self._store[entry.key].size_bytes
            del self._store[entry.key]
        # Evict LRU until we have room
        while self._bytes + entry.size_bytes > self._max_bytes and self._store:
            _, evicted = self._store.popitem(last=False)
            self._bytes -= evicted.size_bytes
            log.debug("Evicted: %s (%d B)", evicted.key, evicted.size_bytes)
        self._store[entry.key] = entry
        self._bytes += entry.size_bytes

    def __len__(self) -> int:
        return len(self._store)

    def stats(self) -> dict:
        return {
            "entries":    len(self._store),
            "used_mb":    round(self._bytes / 1024 / 1024, 2),
            "max_mb":     round(self._max_bytes / 1024 / 1024, 2),
            "utilization": round(self._bytes / max(1, self._max_bytes) * 100, 1),
        }


# ─────────────────────────────────────────────────────────────────
# Hierarchical Memory Engine
# ─────────────────────────────────────────────────────────────────

class MemoryEngine:
    """
    Tiered memory with LRU eviction.

    HOT (L4 + L5): semantic chunks + summaries → instant access
    WARM (L2 + L3): structures + tables → fast access
    COLD (L0 + L1): raw + templates → slow access (disk simulation)

    Public API:
        store(key, value, tier, doc_id)
        retrieve(key)
        promote(key)         — move entry to hotter tier
        invalidate(doc_id)   — evict all entries for a document
        prefetch(doc_id)     — warm up L4/L5 for a document
    """

    TIER_SIZES_MB: dict[MemoryTier, float] = {
        MemoryTier.SUMMARY:   32.0,
        MemoryTier.CHUNK:    256.0,
        MemoryTier.TABLE:    128.0,
        MemoryTier.STRUCTURE: 64.0,
        MemoryTier.TEMPLATE:  32.0,
        MemoryTier.RAW:      512.0,
    }

    COMPRESS_TIERS = {MemoryTier.RAW, MemoryTier.TEMPLATE, MemoryTier.STRUCTURE}

    def __init__(self):
        self._caches: dict[MemoryTier, LRUCache] = {
            tier: LRUCache(mb) for tier, mb in self.TIER_SIZES_MB.items()
        }
        self._hit:  int = 0
        self._miss: int = 0

    # ──────────────────────────────────────────────────────────────
    # Store
    # ──────────────────────────────────────────────────────────────

    def store(
        self,
        key:    str,
        value:  Any,
        tier:   MemoryTier,
        doc_id: str = "",
    ) -> None:
        compress = tier in self.COMPRESS_TIERS
        stored_value, size = self._serialize(value, compress)
        entry = MemoryEntry(
            key=key, value=stored_value, tier=tier, doc_id=doc_id,
            size_bytes=size, compressed=compress,
        )
        self._caches[tier].put(entry)
        log.debug("Stored %s → tier=%s size=%dB", key, tier.name, size)

    # ──────────────────────────────────────────────────────────────
    # Retrieve
    # ──────────────────────────────────────────────────────────────

    def retrieve(self, key: str, tier: Optional[MemoryTier] = None) -> Optional[Any]:
        """
        Retrieve by key. If tier not specified, searches HOT → WARM → COLD.
        """
        search_order = (
            [tier] if tier else
            [MemoryTier.SUMMARY, MemoryTier.CHUNK, MemoryTier.TABLE,
             MemoryTier.STRUCTURE, MemoryTier.TEMPLATE, MemoryTier.RAW]
        )
        for t in search_order:
            entry = self._caches[t].get(key)
            if entry is not None:
                self._hit += 1
                return self._deserialize(entry.value, entry.compressed)
        self._miss += 1
        return None

    # ──────────────────────────────────────────────────────────────
    # Promote (move to hotter tier)
    # ──────────────────────────────────────────────────────────────

    def promote(self, key: str, from_tier: MemoryTier, to_tier: MemoryTier) -> bool:
        entry = self._caches[from_tier].get(key)
        if entry is None:
            return False
        value = self._deserialize(entry.value, entry.compressed)
        self.store(key, value, to_tier, doc_id=entry.doc_id)
        log.debug("Promoted %s: %s → %s", key, from_tier.name, to_tier.name)
        return True

    # ──────────────────────────────────────────────────────────────
    # Batch operations
    # ──────────────────────────────────────────────────────────────

    def store_document(self, doc_id: str, data: dict) -> None:
        """
        Batch-store all representations of a document.
        Expected keys: "templates", "tables", "chunks", "summaries", "graph"
        """
        if "summaries" in data:
            for k, v in data["summaries"].items():
                self.store(f"{doc_id}:summary:{k}", v, MemoryTier.SUMMARY, doc_id)
        if "chunks" in data:
            for k, v in data["chunks"].items():
                self.store(f"{doc_id}:chunk:{k}", v, MemoryTier.CHUNK, doc_id)
        if "tables" in data:
            for k, v in data["tables"].items():
                self.store(f"{doc_id}:table:{k}", v, MemoryTier.TABLE, doc_id)
        if "graph" in data:
            self.store(f"{doc_id}:graph", data["graph"], MemoryTier.STRUCTURE, doc_id)
        if "templates" in data:
            for k, v in data["templates"].items():
                self.store(f"{doc_id}:template:{k}", v, MemoryTier.TEMPLATE, doc_id)

    def invalidate_document(self, doc_id: str) -> int:
        """Evict all entries for a document across all tiers."""
        evicted = 0
        for cache in self._caches.values():
            to_remove = [k for k, e in cache._store.items() if e.doc_id == doc_id]
            for k in to_remove:
                cache._bytes -= cache._store[k].size_bytes
                del cache._store[k]
                evicted += 1
        log.info("Invalidated %d entries for doc '%s'", evicted, doc_id)
        return evicted

    def prefetch(self, doc_id: str, chunk_ids: list[str]) -> None:
        """Promote cold/warm entries to hot tier for a document."""
        for cid in chunk_ids:
            key = f"{doc_id}:chunk:{cid}"
            self.promote(key, MemoryTier.STRUCTURE, MemoryTier.CHUNK)

    # ──────────────────────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────────────────────

    @property
    def hit_rate(self) -> float:
        total = self._hit + self._miss
        return self._hit / total if total > 0 else 0.0

    def statistics(self) -> dict:
        return {
            "hit_rate": round(self.hit_rate, 3),
            "hits": self._hit, "misses": self._miss,
            "tiers": {
                tier.name: cache.stats()
                for tier, cache in self._caches.items()
            },
        }

    # ──────────────────────────────────────────────────────────────
    # Serialization
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _serialize(value: Any, compress: bool) -> tuple[Any, int]:
        try:
            raw = json.dumps(value, default=str).encode("utf-8")
        except Exception:
            raw = str(value).encode("utf-8")
        if compress:
            data = zlib.compress(raw, level=6)
        else:
            data = raw
        return data, len(data)

    @staticmethod
    def _deserialize(data: Any, compressed: bool) -> Any:
        try:
            raw = zlib.decompress(data) if compressed else data
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return data
