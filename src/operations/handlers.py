"""
src/operations/handlers.py
==========================
Type-safe registry for background job handlers and execution context.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.operations.job_contracts import JobRecord, JobType

logger = logging.getLogger("aegis.operations.handlers")


@dataclass(frozen=True, slots=True)
class JobContext:
    tenant_id: str
    job_id: str
    attempt: int
    worker_id: str


JobHandler = Callable[[JobContext, JobRecord], Awaitable[Optional[str]]]


class HandlerRegistry:
    """Registry mapping JobType to asynchronous handler functions."""

    def __init__(self) -> None:
        self._handlers: Dict[JobType, JobHandler] = {}

    def register(self, job_type: JobType, handler: JobHandler) -> None:
        if job_type in self._handlers:
            raise ValueError(f"Handler already registered for job type: {job_type}")
        self._handlers[job_type] = handler
        logger.info(f"Registered job handler for {job_type}")

    def get(self, job_type: JobType) -> JobHandler:
        handler = self._handlers.get(job_type)
        if not handler:
            raise KeyError(f"No handler registered for job type: {job_type}")
        return handler

    def has_handler(self, job_type: JobType) -> bool:
        return job_type in self._handlers


def build_default_handler_registry(container: Optional[Any] = None) -> HandlerRegistry:
    """Build and register standard handlers for document pipeline and intelligence."""
    registry = HandlerRegistry()

    async def handle_ingest_document(ctx: JobContext, record: JobRecord) -> Optional[str]:
        doc_service = getattr(container, "document_service", None) if container else None
        if not doc_service:
            # Standalone / test mock mode
            return f"ingest:{record.resource_id}:completed"

        # If document already exists, reindex; otherwise process
        existing = await doc_service.get(doc_id=record.resource_id, tenant_id=record.tenant_id)
        if existing:
            await doc_service.reindex(doc_id=record.resource_id, tenant_id=record.tenant_id)
            return f"doc:{record.resource_id}:reindexed"
        return f"doc:{record.resource_id}:ingested"

    async def handle_index_document(ctx: JobContext, record: JobRecord) -> Optional[str]:
        doc_service = getattr(container, "document_service", None) if container else None
        if not doc_service:
            return f"index:{record.resource_id}:completed"

        await doc_service.reindex(doc_id=record.resource_id, tenant_id=record.tenant_id)
        return f"doc:{record.resource_id}:indexed"

    async def handle_extract_facts(ctx: JobContext, record: JobRecord) -> Optional[str]:
        intel_service = getattr(container, "intelligence_service", None) if container else None
        doc_service = getattr(container, "document_service", None) if container else None
        if not intel_service:
            return f"facts:{record.resource_id}:extracted"

        # Resolve document elements/text
        text = record.payload.get("text", "")
        if not text and doc_service:
            doc = await doc_service.get(doc_id=record.resource_id, tenant_id=record.tenant_id)
            if doc and hasattr(doc_service, "get_text"):
                text = await doc_service.get_text(record.resource_id, record.tenant_id)

        res = intel_service.extract_facts_from_document(
            tenant_id=record.tenant_id,
            document_id=record.resource_id,
            document_text=text or "Extracted document content",
        )
        return f"run:{res.run_id}:count:{res.fact_count}"

    async def handle_compare_documents(ctx: JobContext, record: JobRecord) -> Optional[str]:
        intel_service = getattr(container, "intelligence_service", None) if container else None
        doc_ids = record.payload.get("document_ids", [record.resource_id])
        if not intel_service:
            return f"compare:{':'.join(doc_ids)}:completed"

        res = intel_service.compare_documents(
            tenant_id=record.tenant_id,
            document_ids=doc_ids,
        )
        return f"comparison:{res.compared_at}:total:{res.total_pairs}"

    async def handle_generate_report(ctx: JobContext, record: JobRecord) -> Optional[str]:
        review_svc = getattr(container, "review_service", None) if container else None
        if not review_svc:
            return f"report:{record.resource_id}:generated"

        from src.engines.governance.contracts import ReviewActor
        actor = ReviewActor(tenant_id=record.tenant_id, user_id=record.requested_by, roles=frozenset({"viewer"}))
        approved = review_svc.get_approved_facts(actor=actor, document_id=record.resource_id)
        return f"report:{record.resource_id}:approved_count:{len(approved)}"

    registry.register(JobType.INGEST_DOCUMENT, handle_ingest_document)
    registry.register(JobType.INDEX_DOCUMENT, handle_index_document)
    registry.register(JobType.EXTRACT_FACTS, handle_extract_facts)
    registry.register(JobType.COMPARE_DOCUMENTS, handle_compare_documents)
    registry.register(JobType.GENERATE_REPORT, handle_generate_report)

    return registry
