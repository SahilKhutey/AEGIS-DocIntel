"""
Memory Retriever
================

Multi-level retrieval from hierarchical memory.

Supports:
- Exact lookup
- Level-specific query
- Cross-level semantic search (via embeddings)
- Hybrid retrieval (across multiple levels)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .access_tracker import AccessTracker
from .cache import CacheManager
from .evictor import Evictor
from .levels import MemoryLevel
from .promoter import Promoter
from .store import StorageManager, StoredItem


@dataclass
class RetrievalQuery:
    """A retrieval query."""

    query: str
    target_levels: Optional[List[MemoryLevel]] = None
    top_k: int = 10
    embedding: Optional[np.ndarray] = None
    item_id: Optional[str] = None  # for exact lookup
    metadata_filter: Optional[Dict[str, Any]] = None


@dataclass
class RetrievedItem:
    """A single retrieved item."""

    item_id: str
    level: MemoryLevel
    data: Any
    score: float
    importance: float
    access_count: int


@dataclass
class RetrievalResult:
    """Result of a retrieval query."""

    query: str
    items: List[RetrievedItem]
    num_levels_searched: int
    total_candidates: int

    def top(self, k: int = 10) -> List[RetrievedItem]:
        return self.items[:k]

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "num_levels_searched": self.num_levels_searched,
            "total_candidates": self.total_candidates,
            "items": [
                {
                    "item_id": it.item_id,
                    "level": it.level.name_long,
                    "score": round(it.score, 6),
                    "importance": round(it.importance, 6),
                    "access_count": it.access_count,
                }
                for it in self.items
            ],
        }


class MemoryRetriever:
    """
    Multi-level memory retriever.
    """

    def __init__(
        self,
        storage: StorageManager,
        tracker: AccessTracker,
        cache: Optional[CacheManager] = None,
        cache_levels: Optional[List[MemoryLevel]] = None,
    ) -> None:
        self.storage = storage
        self.tracker = tracker
        self.cache = cache
        self.cache_levels = cache_levels or [MemoryLevel.L4_SEMANTIC, MemoryLevel.L5_SUMMARIES]

    def retrieve(
        self,
        query: RetrievalQuery,
        embedding_scorer: Optional[Any] = None,
    ) -> RetrievalResult:
        """
        Execute retrieval across target levels.

        Parameters
        ----------
        query : RetrievalQuery
        embedding_scorer : Optional[Callable]
            Function (item_embedding, query_embedding) → score.
            Used when query has an embedding.
        """
        target_levels = query.target_levels or list(MemoryLevel)
        items: List[RetrievedItem] = []
        candidates_count = 0

        for level in target_levels:
            level_items = self.storage.items_at_level(level)
            candidates_count += len(level_items)
            for item in level_items:
                score = self._score_item(item, query, embedding_scorer)
                rec = self.tracker.get(item.item_id)
                access_count = rec.access_count if rec else 0
                items.append(
                    RetrievedItem(
                        item_id=item.item_id,
                        level=level,
                        data=item.data,
                        score=score,
                        importance=item.importance,
                        access_count=access_count,
                    )
                )
                # record access
                self.tracker.record_read(item.item_id)
                # promote to cache if applicable
                if self.cache is not None and level in self.cache_levels:
                    self.cache.put(item.item_id, item.data)

        # sort by score descending
        items.sort(key=lambda x: x.score, reverse=True)
        items = items[: query.top_k]

        return RetrievalResult(
            query=query.query,
            items=items,
            num_levels_searched=len(target_levels),
            total_candidates=candidates_count,
        )

    def retrieve_by_id(
        self,
        item_id: str,
        levels: Optional[List[MemoryLevel]] = None,
    ) -> Optional[RetrievedItem]:
        """Exact lookup by item ID."""
        target_levels = levels or list(MemoryLevel)
        for level in target_levels:
            item = self.storage.get(item_id, level)
            if item is not None:
                rec = self.tracker.get(item_id)
                access_count = rec.access_count if rec else 0
                self.tracker.record_read(item_id)
                return RetrievedItem(
                    item_id=item.item_id,
                    level=level,
                    data=item.data,
                    score=1.0,
                    importance=item.importance,
                    access_count=access_count,
                )
        return None

    @staticmethod
    def _score_item(
        item: StoredItem,
        query: RetrievalQuery,
        embedding_scorer: Optional[Any],
    ) -> float:
        """Compute relevance score for an item against the query."""
        # exact match
        if query.item_id == item.item_id:
            return 1.0
        # importance baseline
        score = item.importance * 0.5
        # string match (case-insensitive substring)
        if query.query and isinstance(item.data, str):
            q_lower = query.query.lower()
            if q_lower in item.data.lower():
                score += 0.3
        # embedding similarity
        if embedding_scorer is not None and query.embedding is not None:
            try:
                item_emb = item.data.get("embedding") if isinstance(item.data, dict) else None
                if item_emb is not None:
                    sim = embedding_scorer(np.asarray(item_emb), query.embedding)
                    score += 0.5 * float(sim)
            except Exception:
                pass
        # metadata filter boost
        if query.metadata_filter and isinstance(item.data, dict):
            if all(item.data.get(k) == v for k, v in query.metadata_filter.items()):
                score += 0.2
        return min(score, 1.0)
