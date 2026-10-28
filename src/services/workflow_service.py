"""
src/services/workflow_service.py
================================
AEGIS-DocIntel — Workflow Coordinator & Stage Orchestration Service.
Coordinates end-to-end question answering and document ingestion pipelines
through deterministic, auditable, and bounded stages.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Generic, Optional, Protocol, Sequence, Tuple, TypeVar

from src.core.observability import (
    EVENT_GENERATION_COMPLETED,
    EVENT_REQUEST_ACCEPTED,
    EVENT_REQUEST_COMPLETED,
    EVENT_RETRIEVAL_COMPLETED,
    StageTimer,
    log_event,
)
from src.engines.generation.contracts import (
    Evidence,
    GenerationPolicy,
    GenerationRequest,
    GenerationResult,
)
from src.engines.generation.service import GenerationService
from src.engines.retrieval.query_contract import validate_query
from src.services.authorization_service import (
    DocumentAuthorizationService,
    Principal,
)

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class WorkflowMetadata:
    """Audit metadata capturing execution trace and stage durations."""
    request_id: str
    workflow_name: str
    duration_ms: float
    stages_completed: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkflowResult(Generic[T]):
    """Structured workflow outcome containing strongly-typed result and metadata."""
    value: T
    metadata: WorkflowMetadata


class RetrievalProvider(Protocol):
    """Protocol for candidate evidence retrieval scoped to a tenant."""

    def retrieve_authorized(
        self,
        *,
        question: str,
        tenant_id: str,
        document_ids: Tuple[str, ...],
    ) -> Sequence[Evidence]:
        ...


class WorkflowCoordinator:
    """
    Central orchestration service for AEGIS-DocIntel pipelines.
    Enforces stage ordering, timeout budgets, authorization, and telemetry.
    """

    def __init__(
        self,
        *,
        authorization_service: DocumentAuthorizationService,
        generation_service: GenerationService,
        retrieval_provider: Optional[RetrievalProvider] = None,
        policy: Optional[GenerationPolicy] = None,
    ) -> None:
        self.authorization_service = authorization_service
        self.generation_service = generation_service
        self.retrieval_provider = retrieval_provider
        self.policy = policy or GenerationPolicy()

    def execute_answer_workflow(
        self,
        *,
        question: str,
        principal: Principal,
        document_ids: Sequence[str] = (),
        request_id: Optional[str] = None,
    ) -> WorkflowResult[GenerationResult]:
        """
        Execute deterministic 8-stage evidence-grounded answer workflow.

        Stages:
        1. validate_request
        2. authorize_documents
        3. retrieve_evidence
        4. enforce_context_limits
        5. generate_answer
        6. validate_citations
        7. recheck_citation_authorization
        8. record_telemetry
        """
        req_id = request_id or uuid.uuid4().hex
        overall_timer = StageTimer()
        stages: list[str] = []

        log_event(
            EVENT_REQUEST_ACCEPTED,
            request_id=req_id,
            fields={"workflow": "answer", "tenant_id": principal.tenant_id},
        )

        # Stage 1: Validate request query and filter boundaries
        validated_q = validate_query(
            query=question,
            tenant_id=principal.tenant_id,
            document_ids=list(document_ids),
            max_top_k=self.policy.max_evidence_items,
        )
        stages.append("validate_request")

        # Stage 2: Authorize requested document boundaries
        doc_tuple = tuple(validated_q.document_ids)
        self.authorization_service.authorize_documents(
            principal=principal,
            document_ids=doc_tuple,
        )
        stages.append("authorize_documents")

        # Stage 3: Retrieve authorized candidate evidence
        retrieval_timer = StageTimer()
        evidence_list: list[Evidence] = []
        if self.retrieval_provider is not None:
            raw_evidence = self.retrieval_provider.retrieve_authorized(
                question=validated_q.query,
                tenant_id=principal.tenant_id,
                document_ids=doc_tuple,
            )
            evidence_list.extend(raw_evidence)
        stages.append("retrieve_evidence")

        log_event(
            EVENT_RETRIEVAL_COMPLETED,
            request_id=req_id,
            fields={
                "duration_ms": retrieval_timer.elapsed_ms(),
                "result_count": len(evidence_list),
            },
        )

        # Stage 4: Enforce context and evidence limits
        bounded_evidence = tuple(evidence_list[: self.policy.max_evidence_items])
        stages.append("enforce_context_limits")

        # Stage 5 & 6: Generate candidate answer & validate schema/citations
        gen_timer = StageTimer()
        gen_request = GenerationRequest(
            question=validated_q.query,
            tenant_id=principal.tenant_id,
            evidence=bounded_evidence,
            policy=self.policy,
        )
        gen_result = self.generation_service.answer(gen_request)
        stages.append("generate_answer")
        stages.append("validate_citations")

        log_event(
            EVENT_GENERATION_COMPLETED,
            request_id=req_id,
            fields={
                "duration_ms": gen_timer.elapsed_ms(),
                "status": gen_result.status,
                "citation_count": len(gen_result.citations),
            },
        )

        # Stage 7: Recheck citation authorization before returning response
        self.authorization_service.authorize_citations(
            principal=principal,
            citations=gen_result.citations,
        )
        stages.append("recheck_citation_authorization")

        # Stage 8: Record telemetry
        duration_ms = overall_timer.elapsed_ms()
        log_event(
            EVENT_REQUEST_COMPLETED,
            request_id=req_id,
            fields={
                "workflow": "answer",
                "duration_ms": duration_ms,
                "stages_count": len(stages),
            },
        )
        stages.append("record_telemetry")

        metadata = WorkflowMetadata(
            request_id=req_id,
            workflow_name="answer_workflow",
            duration_ms=duration_ms,
            stages_completed=tuple(stages),
        )
        return WorkflowResult(value=gen_result, metadata=metadata)
