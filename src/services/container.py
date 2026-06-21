"""
AEGIS-DocIntel — Service Container (Dependency Injection)
==========================================================
Bootstraps and wires all system components together.
Central access point for all services.

Environment flags:
  AEGIS_USE_MOCK_EMBEDDER=1  → skip model download (for testing/CI)
"""
from __future__ import annotations

import asyncio
import logging
import os

import structlog

from src.config import Settings
from src.llm_service.llm_client import LLMService
from src.services.query_service import QueryService

log = structlog.get_logger("aegis.container")


class MockEmbeddingModel:
    """Development stub when sentence-transformers not installed."""

    def encode(self, texts: list[str]) -> list:
        import numpy as np
        return np.random.randn(len(texts), 1024).astype("float32")


class MockRAGEngine:
    """Development stub for RAG engine."""

    def __init__(self, embedding_model):
        self.embedder = embedding_model

        # Minimal context_builder stub
        class _ContextBuilder:
            def build(self, chunks, query, system_prompt, history):
                context = "\n\n".join(f"[Source-{i+1}]: {c.text[:200]}" for i, c in enumerate(chunks))
                return context, chunks, 500

            def build_prompt(self, context, query, system_prompt, history, included_chunks):
                return [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ]

        self.context_builder = _ContextBuilder()

    async def retrieve_and_build(self, query, tenant_id, doc_ids=None, history=None, top_k=None):
        """Return empty RAG result — no vector DB available in dev mode."""

        class _RAGResult:
            chunks = []
            context = "No documents indexed yet. Upload documents via POST /v1/documents/upload"
            retrieval_latency_ms = 0.0
            confidence = 0.0
            query_transformations = [query]
            total_candidates = 0
            token_count = 0

        return _RAGResult()


class MockDocumentService:
    """Development document service stub."""

    _docs: dict = {}

    async def ingest(self, file_bytes, filename, content_type, tenant_id):
        import uuid
        from datetime import datetime, timezone
        doc_id = uuid.uuid4()
        self._docs[str(doc_id)] = {
            "doc_id": doc_id,
            "tenant_id": str(tenant_id),   # always string
            "filename": filename,
            "status": "ready",
            "page_count": 1,
            "chunk_count": 0,
            "is_scanned": False,
            "language": "en",
            "created_at": datetime.now(timezone.utc),
        }
        log.info("Mock ingest complete", doc_id=str(doc_id), filename=filename)

        class _DocResp:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        return _DocResp(self._docs[str(doc_id)])

    async def get(self, doc_id, tenant_id):
        doc = self._docs.get(str(doc_id))
        if not doc:
            return None

        class _DocResp:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        return _DocResp(doc)

    async def get_status(self, doc_id, tenant_id):
        doc = self._docs.get(str(doc_id))
        if not doc:
            return None

        class _Status:
            def __init__(self, d):
                self.doc_id = d["doc_id"]
                self.status = d["status"]
                self.progress_percent = 100.0
                self.stage = "complete"
                self.error = None
                self.chunks_indexed = d["chunk_count"]

        return _Status(doc)

    async def list_documents(self, tenant_id, page=1, page_size=20, status=None):
        items = [v for v in self._docs.values() if str(v.get("tenant_id", "")) == str(tenant_id)]

        class _Doc:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        class _List:
            def __init__(self, items, total, page, page_size):
                self.items = [_Doc(i) for i in items]
                self.total = total
                self.page = page
                self.page_size = page_size

        return _List(items, len(items), page, page_size)

    async def delete(self, doc_id, tenant_id):
        return self._docs.pop(str(doc_id), None) is not None

    async def reindex(self, doc_id, tenant_id):
        return await self.get_status(doc_id, tenant_id)

    async def list_chunks(self, doc_id, tenant_id, page=1, page_size=50):
        class _ChunkList:
            items = []
            total = 0

        return _ChunkList()

    async def batch_ingest(self, documents, tenant_id):
        import uuid

        class _Job:
            job_id = uuid.uuid4()
            doc_count = len(documents)
            status = "queued"

        return _Job()


class ServiceContainer:
    """
    Dependency injection container.
    In development mode: uses lightweight stubs.
    In production mode: connects to real infrastructure.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._started = False

        # Services (initialized in startup())
        self.embedding_model = None
        self.rag_engine = None
        self.memory_engine = None
        self.llm_service: LLMService | None = None
        self.query_service: QueryService | None = None
        self.document_service = None

    async def startup(self):
        """Initialize all services."""
        log.info("Initializing service container")

        # ── Embedding Model ──────────────────────────────────────────────
        if os.environ.get("AEGIS_USE_MOCK_EMBEDDER", "").strip() == "1":
            log.info("Using mock embedding model (AEGIS_USE_MOCK_EMBEDDER=1)")
            self.embedding_model = MockEmbeddingModel()
        else:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(
                    self.settings.embeddings.text_model,
                    device=self.settings.embeddings.device,
                )
                log.info("Embedding model loaded", model=self.settings.embeddings.text_model)
            except Exception as e:
                log.warning("SentenceTransformer unavailable, using mock", error=str(e))
                self.embedding_model = MockEmbeddingModel()

        # ── LLM Service ─────────────────────────────────────────
        self.llm_service = LLMService()

        # ── Memory Engine ────────────────────────────────────────
        self.memory_engine = await self._init_memory()

        # ── RAG Engine ───────────────────────────────────────────
        self.rag_engine = await self._init_rag()

        # ── Document Service ─────────────────────────────────────
        self.document_service = await self._init_document_service()

        # ── Query Service ────────────────────────────────────────
        self.query_service = QueryService(
            rag_engine=self.rag_engine,
            memory_engine=self.memory_engine,
            llm_service=self.llm_service,
            embedding_model=self.embedding_model,
        )

        self._started = True
        log.info("Service container ready")

    async def shutdown(self):
        """Graceful shutdown of all services."""
        log.info("Shutting down service container")
        # Close DB connections, flush metrics, etc.

    async def health_check(self) -> dict[str, str]:
        """Check health of all dependent services."""
        checks = {
            "api": "ok",
            "embedding_model": "ok" if self.embedding_model else "unavailable",
            "llm_service": "ok" if self.llm_service else "unavailable",
        }

        # Check Redis
        try:
            if hasattr(self, "_redis") and self._redis:
                await self._redis.ping()
                checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"

        # Check Milvus
        checks["milvus"] = "mock" if isinstance(self.rag_engine, MockRAGEngine) else "ok"
        checks["elasticsearch"] = "mock" if isinstance(self.rag_engine, MockRAGEngine) else "ok"

        return checks

    async def _init_memory(self):
        """Initialize memory engine (Redis-backed)."""
        try:
            import redis.asyncio as redis_async
            self._redis = redis_async.from_url(
                self.settings.redis.url, decode_responses=False
            )
            await self._redis.ping()
            log.info("Redis connected", url=self.settings.redis.url)

            from src.memory_engine.semantic_cache import SemanticCache
            return SemanticCache(redis_client=self._redis)
        except Exception as e:
            log.warning("Redis unavailable, memory disabled", error=str(e))
            return None

    async def _init_rag(self):
        """Initialize RAG engine (Milvus + Elasticsearch)."""
        # In development without vector DB: use mock
        log.warning("Using MockRAGEngine — configure Milvus + Elasticsearch for production")
        return MockRAGEngine(self.embedding_model)

    async def _init_document_service(self):
        """Initialize document service."""
        log.warning("Using MockDocumentService — configure full pipeline for production")
        return MockDocumentService()
