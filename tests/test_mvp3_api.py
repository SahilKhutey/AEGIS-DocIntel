"""
tests/test_mvp3_api.py
======================
Integration tests for POST /v1/answers endpoint.
Covers authentication, input validation, candidate evidence retrieval,
tenant isolation, answer generation, and citation returns.
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.core.orchestrator import AMDIOrchestrator
from src.services.container import ServiceContainer, RealDocumentService
from src.config import settings


@pytest.fixture
def answers_api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_answers.db"

    app = create_app()
    container = ServiceContainer(settings)
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    client = TestClient(app)
    return app, client, container


def test_answers_endpoint_unauthenticated(answers_api_client):
    _, client, _ = answers_api_client
    resp = client.post("/v1/answers", json={"question": "What is the policy?"})
    assert resp.status_code == 401


def test_answers_endpoint_invalid_body(answers_api_client):
    _, client, _ = answers_api_client
    headers = {"Authorization": "Bearer dev-tenant-alpha"}
    resp = client.post("/v1/answers", json={"question": ""}, headers=headers)
    assert resp.status_code == 422


def test_answers_endpoint_no_documents_abstains(answers_api_client):
    _, client, _ = answers_api_client
    headers = {"Authorization": "Bearer dev-tenant-alpha"}
    resp = client.post(
        "/v1/answers",
        json={"question": "What is our Q3 cloud spending?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "insufficient_evidence"
    assert "sufficient" in data["answer"].lower()
    assert data["citations"] == []


def test_answers_endpoint_with_document_grounded_answer(answers_api_client):
    app, client, container = answers_api_client
    tenant_id = "tenant-alpha"
    headers = {"Authorization": f"Bearer dev-{tenant_id}"}

    # Ingest document for tenant-alpha
    doc_text = "Section 1. Security Policy.\n\nAll data at rest must be encrypted using AES-256-GCM."
    file_payload = {
        "file": ("policy.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain"),
    }
    upload_resp = client.post("/v1/documents/upload", files=file_payload, headers=headers)
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["doc_id"]

    # Query answers endpoint
    answer_resp = client.post(
        "/v1/answers",
        json={
            "question": "How is data at rest encrypted?",
            "document_ids": [doc_id],
        },
        headers=headers,
    )
    assert answer_resp.status_code == 200
    data = answer_resp.json()
    assert data["status"] == "answered"
    assert "AES-256-GCM" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["document_id"] == doc_id


def test_answers_endpoint_tenant_isolation(answers_api_client):
    app, client, container = answers_api_client
    tenant_alpha = "tenant-alpha"
    tenant_beta = "tenant-beta"
    headers_alpha = {"Authorization": f"Bearer dev-{tenant_alpha}"}
    headers_beta = {"Authorization": f"Bearer dev-{tenant_beta}"}

    # Tenant alpha uploads confidential document
    doc_text = "Alpha Confidential Project.\n\nProject Apollo budget is 5 million dollars."
    file_payload = {
        "file": ("apollo.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain"),
    }
    upload_resp = client.post("/v1/documents/upload", files=file_payload, headers=headers_alpha)
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["doc_id"]

    # Tenant beta attempts to query answers for Alpha's document
    answer_resp = client.post(
        "/v1/answers",
        json={
            "question": "What is the budget for Project Apollo?",
            "document_ids": [doc_id],
        },
        headers=headers_beta,
    )
    # Tenant beta cannot see Alpha's document, so orchestrator yields 0 elements, leading to abstention
    assert answer_resp.status_code == 200
    data = answer_resp.json()
    assert data["status"] == "insufficient_evidence"
    assert "sufficient" in data["answer"].lower()
    assert data["citations"] == []
