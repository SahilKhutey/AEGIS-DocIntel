"""
tests/test_mvp4_workflows.py
============================
Unit and integration tests for WorkflowCoordinator stage execution, timing, and failure gating.
"""

from __future__ import annotations

import json
import pytest
from src.engines.generation.contracts import (
    Evidence,
    GenerationPolicy,
    GenerationResult,
)
from src.engines.generation.generator import AnswerGenerator
from src.engines.generation.service import GenerationService
from src.services.authorization_service import (
    DocumentAuthorizationService,
    InMemoryDocumentAccessRepository,
)
from src.services.workflow_service import (
    WorkflowCoordinator,
    WorkflowResult,
)


class MockPrincipal:
    def __init__(self, tenant_id: str, subject_id: str) -> None:
        self.tenant_id = tenant_id
        self.subject_id = subject_id


class MockRetrievalProvider:
    def __init__(self, evidence_map: dict[str, list[Evidence]]) -> None:
        self.evidence_map = evidence_map

    def retrieve_authorized(self, *, question: str, tenant_id: str, document_ids: tuple[str, ...]) -> list[Evidence]:
        results: list[Evidence] = []
        for doc_id in document_ids:
            results.extend(self.evidence_map.get(doc_id, []))
        return results


class MockModel:
    def generate(self, *, system_prompt: str, user_prompt: str, temperature: float, max_output_tokens: int) -> str:
        return json.dumps({
            "status": "answered",
            "answer": "Data is encrypted using AES-256-GCM at rest.",
            "claims": [
                {
                    "text": "Data is encrypted using AES-256-GCM at rest.",
                    "evidence_ids": ["chunk-1"],
                }
            ],
            "warnings": [],
        })


def test_complete_answer_workflow_success():
    principal = MockPrincipal(tenant_id="tenant-alpha", subject_id="user-1")
    repo = InMemoryDocumentAccessRepository({"doc-1": "tenant-alpha"})
    auth_service = DocumentAuthorizationService(repo)

    ev = Evidence(
        chunk_id="chunk-1",
        document_id="doc-1",
        tenant_id="tenant-alpha",
        text="All customer data at rest is encrypted using AES-256-GCM.",
        score=1.0,
    )
    retrieval_provider = MockRetrievalProvider({"doc-1": [ev]})
    generator = AnswerGenerator(MockModel())
    gen_service = GenerationService(generator)

    coordinator = WorkflowCoordinator(
        authorization_service=auth_service,
        generation_service=gen_service,
        retrieval_provider=retrieval_provider,
    )

    result = coordinator.execute_answer_workflow(
        question="What encryption is used at rest?",
        principal=principal,
        document_ids=("doc-1",),
        request_id="test-req-001",
    )

    assert isinstance(result, WorkflowResult)
    assert result.value.status == "answered"
    assert "AES-256-GCM" in result.value.answer
    assert len(result.value.citations) == 1
    assert result.value.citations[0].document_id == "doc-1"

    # Verify metadata and stage completeness
    assert result.metadata.request_id == "test-req-001"
    assert result.metadata.workflow_name == "answer_workflow"
    assert result.metadata.duration_ms >= 0.0
    expected_stages = (
        "validate_request",
        "authorize_documents",
        "retrieve_evidence",
        "enforce_context_limits",
        "generate_answer",
        "validate_citations",
        "recheck_citation_authorization",
        "record_telemetry",
    )
    assert result.metadata.stages_completed == expected_stages


def test_workflow_halts_early_on_authorization_failure():
    principal = MockPrincipal(tenant_id="tenant-alpha", subject_id="user-1")
    # doc-secret belongs to tenant-beta
    repo = InMemoryDocumentAccessRepository({"doc-secret": "tenant-beta"})
    auth_service = DocumentAuthorizationService(repo)

    generator = AnswerGenerator(MockModel())
    gen_service = GenerationService(generator)
    coordinator = WorkflowCoordinator(
        authorization_service=auth_service,
        generation_service=gen_service,
    )

    with pytest.raises(PermissionError, match="not authorized"):
        coordinator.execute_answer_workflow(
            question="What is the secret?",
            principal=principal,
            document_ids=("doc-secret",),
        )


def test_workflow_safe_abstention_on_empty_retrieved_evidence():
    principal = MockPrincipal(tenant_id="tenant-alpha", subject_id="user-1")
    repo = InMemoryDocumentAccessRepository({"doc-empty": "tenant-alpha"})
    auth_service = DocumentAuthorizationService(repo)

    retrieval_provider = MockRetrievalProvider({"doc-empty": []})
    generator = AnswerGenerator(MockModel())
    gen_service = GenerationService(generator)
    coordinator = WorkflowCoordinator(
        authorization_service=auth_service,
        generation_service=gen_service,
        retrieval_provider=retrieval_provider,
    )

    result = coordinator.execute_answer_workflow(
        question="What is the answer?",
        principal=principal,
        document_ids=("doc-empty",),
    )
    assert result.value.status == "insufficient_evidence"
    assert "sufficient" in result.value.answer.lower()
    assert result.value.citations == ()
