"""
AEGIS-DocIntel — Service Container (Dependency Injection)
==========================================================
Bootstraps and wires all system components together.
Central access point for all services.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from src.config import Settings
from src.core.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator
from src.llm_service.llm_client import LLMService
from src.services.query_service import QueryService

log = structlog.get_logger("aegis.container")


class RealDocumentService:
    """Document service that delegates to AMDIOrchestrator."""

    def __init__(self, orchestrator: AMDIOrchestrator):
        self.orchestrator = orchestrator
        self._docs: dict = {}

    async def ingest(self, file_bytes: bytes, filename: str, content_type: str, tenant_id: str):
        doc_id = str(uuid.uuid4())
        doc = DocumentObject(
            doc_id=doc_id,
            filename=filename,
            raw_bytes=file_bytes,
            tenant_id=str(tenant_id),
        )
        
        # Ingest using orchestrator
        stats = await self.orchestrator.ingest(doc)
        
        doc_info = {
            "doc_id": stats.get("doc_id", doc_id),
            "tenant_id": str(tenant_id),
            "filename": filename,
            "status": "ready",
            "page_count": stats.get("pages", 1),
            "chunk_count": stats.get("elements", 0),
            "is_scanned": False,
            "language": "en",
            "created_at": datetime.now(timezone.utc),
        }
        
        self._docs[stats.get("doc_id", doc_id)] = doc_info
        
        class _DocResp:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        return _DocResp(doc_info)

    async def get(self, doc_id: str, tenant_id: str):
        doc = self._docs.get(str(doc_id))
        if not doc:
            return None
        class _DocResp:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        return _DocResp(doc)

    async def get_status(self, doc_id: str, tenant_id: str):
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

    async def list_documents(self, tenant_id: str, page: int = 1, page_size: int = 20, status: str | None = None):
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

    async def delete(self, doc_id: str, tenant_id: str):
        if str(doc_id) in self._docs:
            self._docs.pop(str(doc_id), None)
            return True
        return False

    async def reindex(self, doc_id: str, tenant_id: str):
        return await self.get_status(doc_id, tenant_id)

    async def list_chunks(self, doc_id: str, tenant_id: str, page: int = 1, page_size: int = 50):
        elements = self.orchestrator.get_document_elements(str(doc_id))
        class _Chunk:
            def __init__(self, e):
                self.chunk_id = e.element_id
                self.doc_id = e.doc_id
                self.page_start = e.page
                self.page_end = e.page
                self.section = e.section
                self.block_type = e.type.value if hasattr(e.type, "value") else str(e.type)
                self.text = e.content
                self.token_count = e.token_count if hasattr(e, "token_count") else max(1, len(e.content.split()))
        class _ChunkList:
            items = [_Chunk(e) for e in elements]
            total = len(elements)
        return _ChunkList()

    async def batch_ingest(self, documents: list, tenant_id: str):
        class _Job:
            job_id = uuid.uuid4()
            doc_count = len(documents)
            status = "queued"
        return _Job()


class ServiceContainer:
    """
    Dependency injection container.
    Connects API gateway endpoints to real AMDI-OS orchestrator.
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

        # Pre-LLM, Compliance, Versioning, Entity & Math Services
        self.compliance_service = None
        self.entity_service = None
        self.versioning_service = None
        self.anomaly_service = None
        self.normalizer_service = None
        self.decomposer_service = None
        self.math_engine = None

    async def startup(self):
        """Initialize all services."""
        log.info("Initializing service container")

        # Config mapping for AMDIOrchestrator
        amdi_config = {
            "embedding_dim": self.settings.embeddings.dimension,
            "redis_url": self.settings.redis.url,
            "llm_provider": self.settings.llm.provider,
            "llm_model": self.settings.llm.model,
            "openai_api_key": self.settings.llm.api_key or os.environ.get("OPENAI_API_KEY", ""),
            "max_context_tokens": self.settings.llm.max_input_tokens,
        }

        # ── Embedding Model ──────────────────────────────────────────────
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(
                self.settings.embeddings.text_model,
                device=self.settings.embeddings.device,
            )
            log.info("Embedding model loaded", model=self.settings.embeddings.text_model)
        except Exception as e:
            log.warning("SentenceTransformer unavailable, fallback in orchestrator", error=str(e))
            self.embedding_model = None

        # ── LLM Service ─────────────────────────────────────────
        self.llm_service = LLMService()

        # ── Real AMDIOrchestrator ───────────────────────────────
        self.rag_engine = AMDIOrchestrator(config=amdi_config)

        # ── Memory Engine (Redis-backed Cache) ─────────────────
        self.memory_engine = await self._init_memory()

        # ── Document Service ─────────────────────────────────────
        self.document_service = RealDocumentService(self.rag_engine)

        # ── Query Service ────────────────────────────────────────
        self.query_service = QueryService(
            rag_engine=self.rag_engine,
            memory_engine=self.memory_engine,
            llm_service=self.llm_service,
            embedding_model=self.embedding_model,
        )

        # ── Advanced Submodules Wire-Up ─────────────────────────
        from src.compliance.redaction_engine import RedactionPolicy
        from src.entity.canonicalizer import cluster_into_canonical_entities
        from src.versioning.diff_engine import compute_structural_diff
        from src.ingestion.anomaly_gate import run_ingestion_gate
        from src.engines.matrix.unit_normalizer import parse_quantity
        from src.query.decomposer import build_query_dag
        from src.math_concepts.master_math_engine import MasterUnifiedMathEngine

        self.compliance_service = RedactionPolicy
        self.entity_service = cluster_into_canonical_entities
        self.versioning_service = compute_structural_diff
        self.anomaly_service = run_ingestion_gate
        self.normalizer_service = parse_quantity
        self.decomposer_service = build_query_dag
        self.math_engine = MasterUnifiedMathEngine()

        self._started = True
        log.info("Service container ready")

    async def shutdown(self):
        """Graceful shutdown of all services."""
        log.info("Shutting down service container")
        if self.rag_engine:
            await self.rag_engine.close()

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

        checks["milvus"] = "ok" if self.rag_engine and self.rag_engine._vector_store else "mock"
        checks["elasticsearch"] = "ok" if self.rag_engine and self.rag_engine._frequency else "mock"

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
            log.warning("Redis unavailable, memory cache disabled", error=str(e))
            return None
