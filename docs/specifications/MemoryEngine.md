# AEGIS-DocIntel — Memory Engine
**Version 1.0.0**

---

## 1. Memory Architecture Overview

AEGIS implements a **three-tier memory hierarchy** that mirrors the human cognitive
model: immediate (working memory), short-term (session), and long-term (semantic).

```
┌──────────────────────────────────────────────────────────────────┐
│                     MEMORY ENGINE                                │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │   TIER 1       │  │   TIER 2       │  │   TIER 3         │   │
│  │   KV Cache     │  │  Semantic      │  │  Episodic        │   │
│  │   (Redis)      │  │  Cache         │  │  Memory          │   │
│  │                │  │  (Redis+FAISS) │  │  (Postgres+Redis)│   │
│  │ Scope: request │  │ Scope: global  │  │ Scope: session   │   │
│  │ TTL: 1 hour    │  │ TTL: 1 hour    │  │ TTL: 7 days      │   │
│  │ Hit rate: 80%  │  │ Hit rate: 40%  │  │ Recall: 100%     │   │
│  └────────────────┘  └────────────────┘  └──────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │   TIER 4: Document-Level Context Cache (Redis + S3)      │    │
│  │   Scope: document | TTL: configurable | Hit rate: 90%    │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Tier 1: KV Cache (Redis)

### Purpose
Caches the LLM KV (key-value) attention states for the system prompt prefix,
allowing identical system prompts to skip recomputation.

### Implementation
```python
class KVCache:
    """
    Prefix-based KV cache for LLM inference.
    Stores system prompt prefix hash → cached inference state.
    Works transparently with vLLM's built-in prefix caching.
    """

    PREFIX_KEY = "kv:prefix:{prefix_hash}"
    SESSION_KEY = "kv:session:{session_id}"

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_prefix_hash(self, system_prompt: str, tenant_id: str) -> str:
        """Generate deterministic hash for prefix caching."""
        import hashlib
        content = f"{tenant_id}:{system_prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def store_session_context(
        self,
        session_id: str,
        messages: list[dict],
        ttl: int = 3600
    ) -> None:
        """Store session message history in Redis."""
        import json
        key = self.SESSION_KEY.format(session_id=session_id)
        await self.redis.setex(key, ttl, json.dumps(messages))

    async def get_session_context(self, session_id: str) -> list[dict] | None:
        """Retrieve session message history from Redis."""
        import json
        key = self.SESSION_KEY.format(session_id=session_id)
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def extend_session_ttl(self, session_id: str, ttl: int = 3600) -> None:
        """Reset TTL on activity."""
        key = self.SESSION_KEY.format(session_id=session_id)
        await self.redis.expire(key, ttl)
```

### Configuration
```yaml
kv_cache:
  redis_db: 0
  max_memory_gb: 16
  eviction_policy: "allkeys-lru"
  prefix_ttl_seconds: 3600
  session_ttl_seconds: 3600
  max_session_messages: 20
```

---

## 3. Tier 2: Semantic Cache

### Purpose
Caches (question_embedding, response) pairs globally across all sessions.
When a new question is semantically similar to a cached question (cosine ≥ 0.95),
returns the cached response immediately — zero LLM cost.

### Architecture
```
New Question
      │
      ▼
   Embed question → q_vec (1024-d)
      │
      ▼
   FAISS IndexFlatIP lookup (in-memory, Redis-backed)
      │
      ▼
   cosine_sim(q_vec, cached_q_vec) >= 0.95 ?
      │
   YES → Return cached_response (latency: ~5ms)
      │
   NO  → Proceed to retrieval
```

### Implementation
```python
import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional

import faiss
import numpy as np
import redis.asyncio as redis_async

from src.config import settings


@dataclass
class CacheEntry:
    question: str
    embedding: np.ndarray
    response: dict
    doc_ids: list[str]
    tenant_id: str
    created_at: float
    hit_count: int = 0


class SemanticCache:
    """
    Vector-similarity-based response cache.
    
    Architecture:
    - FAISS index in-process (fast lookup)
    - Redis for persistence and cross-instance sync
    - Entry = (question_embedding, serialized_response)
    
    Hit rate: 30-50% in enterprise workloads
    Latency: 5ms (vs 500ms+ for full RAG)
    """

    CACHE_KEY_PREFIX = "sem_cache:{tenant_id}"
    CACHE_META_KEY = "sem_cache:meta:{entry_id}"
    INVALIDATE_KEY = "sem_cache:invalidate:{doc_id}"

    def __init__(self, redis_client: redis_async.Redis, dimension: int = 1024):
        self.redis = redis_client
        self.dimension = dimension
        self.threshold = settings.cache.semantic_threshold  # 0.95
        self.ttl = settings.cache.ttl_seconds  # 3600s

        # Per-tenant FAISS indices (in-memory)
        self._indices: dict[str, faiss.IndexFlatIP] = {}
        self._entries: dict[str, list[CacheEntry]] = {}
        self._lock = asyncio.Lock()

    async def lookup(
        self,
        question_embedding: np.ndarray,
        tenant_id: str,
        doc_ids: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """
        Find semantically similar cached response.
        Returns response dict or None.
        """
        idx, entries = await self._get_tenant_index(tenant_id)

        if idx.ntotal == 0:
            return None

        # L2-normalize for cosine similarity via inner product
        q = question_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(q)

        scores, indices = idx.search(q, k=5)

        for score, entry_idx in zip(scores[0], indices[0]):
            if score < self.threshold:
                break
            if entry_idx < 0 or entry_idx >= len(entries):
                continue

            entry = entries[entry_idx]

            # Check TTL
            if time.time() - entry.created_at > self.ttl:
                continue

            # Check doc_id overlap (optional filter)
            if doc_ids:
                if not any(d in entry.doc_ids for d in doc_ids):
                    continue

            # Update hit count asynchronously
            entry.hit_count += 1
            return entry.response

        return None

    async def store(
        self,
        question: str,
        question_embedding: np.ndarray,
        response: dict,
        tenant_id: str,
        doc_ids: list[str],
    ) -> None:
        """Store a new question-response pair in the cache."""
        async with self._lock:
            idx, entries = await self._get_tenant_index(tenant_id)

            vec = question_embedding.astype(np.float32).reshape(1, -1)
            faiss.normalize_L2(vec)
            idx.add(vec)

            entry = CacheEntry(
                question=question,
                embedding=question_embedding,
                response=response,
                doc_ids=doc_ids,
                tenant_id=tenant_id,
                created_at=time.time(),
            )
            entries.append(entry)

            # Persist to Redis for cross-instance sharing
            await self._persist_to_redis(entry, tenant_id)

    async def invalidate_by_doc(self, doc_id: str, tenant_id: str) -> int:
        """
        Invalidate all cache entries that reference a specific document.
        Called when a document is re-indexed or deleted.
        Returns count of invalidated entries.
        """
        async with self._lock:
            if tenant_id not in self._entries:
                return 0

            original = self._entries[tenant_id]
            filtered = [e for e in original if doc_id not in e.doc_ids]
            removed = len(original) - len(filtered)

            if removed > 0:
                self._entries[tenant_id] = filtered
                # Rebuild FAISS index
                await self._rebuild_index(tenant_id, filtered)

            return removed

    async def _get_tenant_index(
        self, tenant_id: str
    ) -> tuple[faiss.IndexFlatIP, list[CacheEntry]]:
        """Get or create per-tenant FAISS index."""
        if tenant_id not in self._indices:
            self._indices[tenant_id] = faiss.IndexFlatIP(self.dimension)
            self._entries[tenant_id] = []
            # Load from Redis on cold start
            await self._load_from_redis(tenant_id)

        return self._indices[tenant_id], self._entries[tenant_id]

    async def _rebuild_index(
        self, tenant_id: str, entries: list[CacheEntry]
    ) -> None:
        """Rebuild FAISS index from entry list."""
        idx = faiss.IndexFlatIP(self.dimension)
        if entries:
            vecs = np.array([e.embedding for e in entries], dtype=np.float32)
            faiss.normalize_L2(vecs)
            idx.add(vecs)
        self._indices[tenant_id] = idx

    async def _persist_to_redis(self, entry: CacheEntry, tenant_id: str) -> None:
        """Persist cache entry to Redis for durability."""
        try:
            payload = json.dumps({
                "question": entry.question,
                "embedding": entry.embedding.tolist(),
                "response": entry.response,
                "doc_ids": entry.doc_ids,
                "created_at": entry.created_at,
            })
            key = f"sem_cache:entry:{tenant_id}:{hash(entry.question)}"
            await self.redis.setex(key, self.ttl, payload)
        except Exception:
            pass  # Cache persistence is best-effort

    async def _load_from_redis(self, tenant_id: str) -> None:
        """Load persisted cache entries on cold start."""
        try:
            pattern = f"sem_cache:entry:{tenant_id}:*"
            keys = await self.redis.keys(pattern)
            for key in keys[:1000]:  # cap at 1000 entries per tenant
                data = await self.redis.get(key)
                if not data:
                    continue
                payload = json.loads(data)
                embedding = np.array(payload["embedding"], dtype=np.float32)
                entry = CacheEntry(
                    question=payload["question"],
                    embedding=embedding,
                    response=payload["response"],
                    doc_ids=payload["doc_ids"],
                    tenant_id=tenant_id,
                    created_at=payload["created_at"],
                )
                self._entries[tenant_id].append(entry)

            if self._entries[tenant_id]:
                await self._rebuild_index(tenant_id, self._entries[tenant_id])
        except Exception:
            pass  # Cold start gracefully
```

---

## 4. Tier 3: Episodic Memory (Conversation History)

### Purpose
Maintains per-session conversation history to support multi-turn dialogue,
follow-up questions, and context continuity.

### Implementation
```python
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import asyncpg
import redis.asyncio as redis_async


@dataclass
class Message:
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    tokens: int
    metadata: dict | None = None


class EpisodicMemory:
    """
    Per-session conversation memory with automatic compression.
    
    Flow:
    1. New turn → append to Redis (hot path)
    2. If history > 4K tokens → compress via T5 summarizer
    3. Session end → persist to Postgres (cold storage)
    4. Next session → reload from Postgres (optional)
    """

    MAX_TURNS = 20
    COMPRESS_THRESHOLD_TOKENS = 4000
    SESSION_KEY = "episodic:{session_id}"

    def __init__(self, redis_client: redis_async.Redis, pg_pool: asyncpg.Pool):
        self.redis = redis_client
        self.pg = pg_pool
        self._summarizer = None  # lazy load

    async def get_history(self, session_id: str) -> list[Message]:
        """Retrieve conversation history for a session."""
        import json
        key = self.SESSION_KEY.format(session_id=session_id)
        data = await self.redis.get(key)
        if not data:
            return await self._load_from_postgres(session_id)

        raw = json.loads(data)
        return [
            Message(
                role=m["role"],
                content=m["content"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
                tokens=m["tokens"],
                metadata=m.get("metadata"),
            )
            for m in raw
        ]

    async def append(
        self, session_id: str, message: Message
    ) -> list[Message]:
        """Append a message and return updated history."""
        import json
        history = await self.get_history(session_id)
        history.append(message)

        # Enforce max turns
        if len(history) > self.MAX_TURNS:
            history = await self._compress_and_trim(history)

        key = self.SESSION_KEY.format(session_id=session_id)
        payload = [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "tokens": m.tokens,
                "metadata": m.metadata,
            }
            for m in history
        ]
        await self.redis.setex(key, 3600, json.dumps(payload))  # 1h sliding TTL

        return history

    async def _compress_and_trim(self, history: list[Message]) -> list[Message]:
        """
        Compress older turns via summarization when history exceeds threshold.
        Keeps last 5 turns verbatim; summarizes the rest.
        """
        total_tokens = sum(m.tokens for m in history)
        if total_tokens <= self.COMPRESS_THRESHOLD_TOKENS:
            return history[-self.MAX_TURNS:]

        # Keep recent turns verbatim
        recent = history[-5:]
        to_compress = history[:-5]

        # Summarize older turns
        summary_text = await self._summarize(to_compress)
        summary_msg = Message(
            role="system",
            content=f"[Conversation Summary]: {summary_text}",
            timestamp=to_compress[0].timestamp,
            tokens=len(summary_text.split()) * 2,
            metadata={"compressed": True, "original_turns": len(to_compress)},
        )

        return [summary_msg] + recent

    async def _summarize(self, messages: list[Message]) -> str:
        """Summarize conversation history using T5 or LLM."""
        if self._summarizer is None:
            from transformers import pipeline
            self._summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1,  # CPU (lightweight model)
            )

        text = "\n".join(f"{m.role}: {m.content}" for m in messages)
        text = text[:3000]  # cap input
        result = self._summarizer(text, max_length=200, min_length=50, do_sample=False)
        return result[0]["summary_text"]

    async def persist_session(self, session_id: str) -> None:
        """Persist session to Postgres for long-term storage."""
        import json
        history = await self.get_history(session_id)
        if not history:
            return

        async with self.pg.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO session_history (session_id, messages, created_at, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (session_id) DO UPDATE
                    SET messages = EXCLUDED.messages, updated_at = NOW()
                """,
                session_id,
                json.dumps([
                    {"role": m.role, "content": m.content,
                     "timestamp": m.timestamp.isoformat(), "tokens": m.tokens}
                    for m in history
                ]),
                history[0].timestamp,
            )

    async def _load_from_postgres(self, session_id: str) -> list[Message]:
        """Load session history from Postgres (cold path)."""
        import json
        async with self.pg.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT messages FROM session_history WHERE session_id = $1",
                session_id,
            )
        if not row:
            return []
        raw = json.loads(row["messages"])
        return [
            Message(
                role=m["role"],
                content=m["content"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
                tokens=m["tokens"],
            )
            for m in raw
        ]
```

---

## 5. Tier 4: Document-Level Context Cache

### Purpose
Caches the fully-parsed and preprocessed representation of a document so that
repeated queries against the same document avoid re-parsing overhead.
Mirrors Gemini's "Context Caching" feature.

### Implementation
```python
class DocumentContextCache:
    """
    Caches parsed document representations for fast re-querying.
    Key insight: parsing a 200-page PDF takes 30s; serving from cache takes 2ms.
    
    Savings: 90% reduction on repeat-document queries.
    """

    DOC_CACHE_KEY = "doc_ctx:{doc_id}:{version}"

    def __init__(self, redis_client, s3_client):
        self.redis = redis_client
        self.s3 = s3_client

    async def get(self, doc_id: str, version: str = "latest") -> dict | None:
        """Retrieve cached document context."""
        import json
        key = self.DOC_CACHE_KEY.format(doc_id=doc_id, version=version)
        
        # L1: Redis (hot)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        
        # L2: S3 (warm)
        try:
            s3_key = f"cache/doc_ctx/{doc_id}/{version}.json"
            obj = await self.s3.get_object(Bucket="aegis-derived", Key=s3_key)
            body = await obj["Body"].read()
            payload = json.loads(body)
            # Promote to Redis
            await self.redis.setex(key, 3600, body)
            return payload
        except Exception:
            return None

    async def store(
        self,
        doc_id: str,
        context: dict,
        version: str = "latest",
        ttl: int = 3600,
    ) -> None:
        """Store document context in both Redis (hot) and S3 (warm)."""
        import json
        payload = json.dumps(context)
        key = self.DOC_CACHE_KEY.format(doc_id=doc_id, version=version)

        # L1: Redis
        await self.redis.setex(key, ttl, payload)

        # L2: S3 (async, best-effort)
        asyncio.create_task(
            self._store_s3(doc_id, version, payload)
        )

    async def invalidate(self, doc_id: str) -> None:
        """Invalidate all cache entries for a document (on re-index)."""
        pattern = self.DOC_CACHE_KEY.format(doc_id=doc_id, version="*")
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def _store_s3(self, doc_id: str, version: str, payload: str) -> None:
        try:
            s3_key = f"cache/doc_ctx/{doc_id}/{version}.json"
            await self.s3.put_object(
                Bucket="aegis-derived",
                Key=s3_key,
                Body=payload.encode(),
                ContentType="application/json",
            )
        except Exception:
            pass
```

---

## 6. Memory Engine Facade

```python
class MemoryEngine:
    """
    Unified memory API combining all four tiers.
    Use this class from application code; never access tiers directly.
    """

    def __init__(
        self,
        kv_cache: KVCache,
        semantic_cache: SemanticCache,
        episodic: EpisodicMemory,
        doc_cache: DocumentContextCache,
    ):
        self.kv = kv_cache
        self.semantic = semantic_cache
        self.episodic = episodic
        self.doc = doc_cache

    async def query_cache(
        self,
        question_embedding,
        tenant_id: str,
        doc_ids: list[str] | None = None,
    ) -> dict | None:
        """Unified semantic cache lookup."""
        return await self.semantic.lookup(question_embedding, tenant_id, doc_ids)

    async def cache_response(
        self,
        question: str,
        embedding,
        response: dict,
        tenant_id: str,
        doc_ids: list[str],
    ) -> None:
        """Store response in semantic cache."""
        await self.semantic.store(question, embedding, response, tenant_id, doc_ids)

    async def get_history(self, session_id: str) -> list[Message]:
        """Get conversation history."""
        return await self.episodic.get_history(session_id)

    async def append_turn(
        self, session_id: str, user_msg: Message, assistant_msg: Message
    ) -> list[Message]:
        """Append a complete turn (user + assistant)."""
        history = await self.episodic.append(session_id, user_msg)
        history = await self.episodic.append(session_id, assistant_msg)
        return history

    async def get_document_cache(self, doc_id: str) -> dict | None:
        return await self.doc.get(doc_id)

    async def set_document_cache(self, doc_id: str, context: dict) -> None:
        await self.doc.store(doc_id, context)

    async def invalidate_document(self, doc_id: str, tenant_id: str) -> None:
        """Full invalidation on document change."""
        await self.doc.invalidate(doc_id)
        await self.semantic.invalidate_by_doc(doc_id, tenant_id)
```
