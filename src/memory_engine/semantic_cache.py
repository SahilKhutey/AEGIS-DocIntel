"""
AEGIS-DocIntel — Semantic Cache
================================
Redis-backed + FAISS in-memory semantic cache.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

import numpy as np

from src.config import settings


class SemanticCache:
    """
    Cross-session semantic response cache.
    Hit when cosine(q, cached_q) >= threshold (default 0.95).
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.threshold = settings.cache.semantic_threshold
        self.ttl = settings.cache.ttl_seconds
        self._indices: dict = {}
        self._entries: dict = {}
        self._lock = asyncio.Lock()

    async def query_cache(
        self,
        question_embedding: np.ndarray,
        tenant_id: str,
        doc_ids: Optional[list] = None,
    ) -> Optional[dict]:
        """Lookup cached response by semantic similarity."""
        try:
            import faiss
        except ImportError:
            return None

        entries = self._entries.get(tenant_id, [])
        idx = self._indices.get(tenant_id)
        if not idx or idx.ntotal == 0:
            return None

        q = question_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(q)
        scores, indices = idx.search(q, k=3)

        for score, eidx in zip(scores[0], indices[0]):
            if score < self.threshold or eidx < 0 or eidx >= len(entries):
                break
            entry = entries[eidx]
            if time.time() - entry.get("ts", 0) > self.ttl:
                continue
            if doc_ids and not any(d in entry.get("doc_ids", []) for d in doc_ids):
                continue
            return entry.get("response")

        return None

    async def cache_response(
        self,
        question: str,
        embedding: np.ndarray,
        response: dict,
        tenant_id: str,
        doc_ids: list,
    ) -> None:
        """Store a response in the semantic cache."""
        try:
            import faiss
        except ImportError:
            return

        async with self._lock:
            if tenant_id not in self._indices:
                self._indices[tenant_id] = faiss.IndexFlatIP(settings.embeddings.dimension)
                self._entries[tenant_id] = []

            idx = self._indices[tenant_id]
            entries = self._entries[tenant_id]

            vec = embedding.astype(np.float32).reshape(1, -1)
            faiss.normalize_L2(vec)
            idx.add(vec)
            entries.append({
                "question": question,
                "response": response,
                "doc_ids": doc_ids,
                "ts": time.time(),
            })

    async def invalidate_by_doc(self, doc_id: str, tenant_id: str) -> int:
        """Remove cache entries referencing a document."""
        try:
            import faiss
        except ImportError:
            return 0

        async with self._lock:
            if tenant_id not in self._entries:
                return 0
            before = len(self._entries[tenant_id])
            self._entries[tenant_id] = [
                e for e in self._entries[tenant_id]
                if doc_id not in e.get("doc_ids", [])
            ]
            after = len(self._entries[tenant_id])
            # Rebuild index
            if before != after and self._entries[tenant_id]:
                idx = faiss.IndexFlatIP(settings.embeddings.dimension)
                self._indices[tenant_id] = idx
            return before - after

    async def get_history(self, session_id: str) -> list:
        """Retrieve conversation history (from Redis)."""
        try:
            key = f"session:{session_id}"
            data = await self.redis.get(key)
            if data:
                raw = json.loads(data)
                return [type("Msg", (), m)() for m in raw]
        except Exception:
            pass
        return []
