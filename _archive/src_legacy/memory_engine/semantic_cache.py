"""
AEGIS-DocIntel — Semantic Cache
================================
Redis-backed + FAISS (or NumPy fallback) in-memory semantic cache.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

import numpy as np

from src.config import settings

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    _FAISS_AVAILABLE = False


class _NumpyIndexFlatIP:
    """Pure NumPy fallback for FAISS IndexFlatIP when faiss is not installed."""

    def __init__(self, d: int) -> None:
        self.d = d
        self.vectors: list[np.ndarray] = []

    @property
    def ntotal(self) -> int:
        return len(self.vectors)

    def add(self, x: np.ndarray) -> None:
        for v in x:
            self.vectors.append(v.copy().astype(np.float32))

    def search(self, q: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        if not self.vectors:
            return np.array([[]], dtype=np.float32), np.array([[]], dtype=np.int64)
        matrix = np.vstack(self.vectors)
        q_vec = q.reshape(-1)
        scores = np.dot(matrix, q_vec)
        top_k = min(k, len(self.vectors))
        top_indices = np.argsort(scores)[::-1][:top_k]
        top_scores = scores[top_indices]
        return top_scores.reshape(1, -1), top_indices.reshape(1, -1)


def _create_index(dim: int):
    if _FAISS_AVAILABLE and faiss is not None:
        return faiss.IndexFlatIP(dim)
    return _NumpyIndexFlatIP(dim)


def _normalize_L2(x: np.ndarray) -> None:
    if _FAISS_AVAILABLE and faiss is not None:
        faiss.normalize_L2(x)
    else:
        norm = np.linalg.norm(x, axis=1, keepdims=True)
        norm = np.where(norm < 1e-12, 1.0, norm)
        x /= norm


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
        entries = self._entries.get(tenant_id, [])
        idx = self._indices.get(tenant_id)
        if not idx or idx.ntotal == 0:
            return None

        q = question_embedding.astype(np.float32).reshape(1, -1)
        _normalize_L2(q)
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

    def _purge_expired_locked(self, tenant_id: str) -> int:
        """Remove TTL-expired entries for a tenant and rebuild its FAISS
        index from survivors. Caller must already hold ``self._lock``.
        """
        entries = self._entries.get(tenant_id, [])
        if not entries:
            return 0
        now = time.time()
        surviving = [e for e in entries if now - e.get("ts", 0) <= self.ttl]
        removed = len(entries) - len(surviving)
        if removed:
            self._entries[tenant_id] = surviving
            idx = _create_index(settings.embeddings.dimension)
            if surviving:
                vecs = np.stack([e["_embedding"] for e in surviving]).astype(np.float32)
                idx.add(vecs)
            self._indices[tenant_id] = idx
        return removed

    async def purge_expired(self, tenant_id: str) -> int:
        """Public, lock-acquiring entry point for callers (e.g. a scheduled
        maintenance task) that want to purge expired entries for a tenant
        without waiting for the next cache_response() write to do it
        opportunistically."""
        async with self._lock:
            return self._purge_expired_locked(tenant_id)

    async def cache_response(
        self,
        question: str,
        embedding: np.ndarray,
        response: dict,
        tenant_id: str,
        doc_ids: list,
    ) -> None:
        """Store a response in the semantic cache."""
        async with self._lock:
            if tenant_id not in self._indices:
                self._indices[tenant_id] = _create_index(settings.embeddings.dimension)
                self._entries[tenant_id] = []

            self._purge_expired_locked(tenant_id)

            idx = self._indices[tenant_id]
            entries = self._entries[tenant_id]

            vec = embedding.astype(np.float32).reshape(1, -1)
            _normalize_L2(vec)
            idx.add(vec)
            entries.append({
                "question": question,
                "response": response,
                "doc_ids": doc_ids,
                "ts": time.time(),
                "_embedding": vec.reshape(-1),
            })

    async def invalidate_by_doc(self, doc_id: str, tenant_id: str) -> int:
        """Remove cache entries referencing a document."""
        async with self._lock:
            if tenant_id not in self._entries:
                return 0
            before = len(self._entries[tenant_id])
            surviving = [
                e for e in self._entries[tenant_id]
                if doc_id not in e.get("doc_ids", [])
            ]
            after = len(surviving)
            self._entries[tenant_id] = surviving

            if before != after:
                idx = _create_index(settings.embeddings.dimension)
                if surviving:
                    vecs = np.stack([e["_embedding"] for e in surviving]).astype(np.float32)
                    idx.add(vecs)
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
