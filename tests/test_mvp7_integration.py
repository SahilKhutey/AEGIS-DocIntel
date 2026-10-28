"""
tests/test_mvp7_integration.py
==============================
End-to-end integration and API contract tests for MVP 7 Document Workbench endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.services.container import ServiceContainer, RealDocumentService
from src.core.orchestrator import AMDIOrchestrator
from src.config import settings
from src.repositories.review_repository import ReviewRepository
from src.engines.governance.review_service import ReviewService
from src.engines.intelligence.contracts import EvidenceSpan, ExtractedFact

AUTH_DEV = {"Authorization": "Bearer dev-default-tenant"}
AUTH_OTHER = {"Authorization": "Bearer dev-other-tenant"}


@pytest.fixture
def workbench_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_api_wb.db"
    review_db = tmp_path / "test_review_wb.db"

    app = create_app()
    container = ServiceContainer(settings)
    container._started = True
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))
    container.review_repository = ReviewRepository(db_path=str(review_db))
    container.review_service = ReviewService(
        repository=container.review_repository,
        orchestrator=container.rag_engine,
    )

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    app.state.review_service = container.review_service
    client = TestClient(app)
    return client, container


def test_api_v1_documents_endpoints(workbench_client):
    client, _ = workbench_client

    # 1. Anonymous rejected
    resp_anon = client.get("/api/v1/documents")
    assert resp_anon.status_code == 401

    # 2. Authenticated lists documents
    resp = client.get("/api/v1/documents", headers=AUTH_DEV)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_api_v1_ask_endpoint(workbench_client):
    client, _ = workbench_client

    # 1. Anonymous rejected
    resp_anon = client.post("/api/v1/ask", json={"question": "What is the liability cap?"})
    assert resp_anon.status_code == 401

    # 2. Authenticated ask query
    resp = client.post(
        "/api/v1/ask",
        json={"question": "What is the liability cap?", "document_ids": []},
        headers=AUTH_DEV,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data


def test_api_v1_reviews_workbench_lifecycle(workbench_client):
    client, container = workbench_client
    svc: ReviewService = container.review_service

    # Seed candidate fact into review queue
    span = EvidenceSpan(
        document_id="doc-wb-1",
        tenant_id="default-tenant",
        chunk_id="chunk-wb-1",
        quoted_text="termination notice requires 30 days prior notice",
    )
    fact = ExtractedFact(
        fact_id="fact-wb-1",
        tenant_id="default-tenant",
        document_id="doc-wb-1",
        subject="notice",
        attribute="termination_period",
        value=30,
        raw_value="30 days",
        value_type="integer",
        unit="days",
        evidence=(span,),
    )
    item = svc.create_review_from_fact("default-tenant", fact)

    # 1. GET /api/v1/reviews
    list_resp = client.get("/api/v1/reviews", headers=AUTH_DEV)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(i["review_id"] == item.review_id for i in items)

    # Cross-tenant isolation: other tenant cannot see this item
    other_list = client.get("/api/v1/reviews", headers=AUTH_OTHER)
    assert other_list.status_code == 200
    assert not any(i["review_id"] == item.review_id for i in other_list.json()["items"])

    # 2. GET /api/v1/reviews/{id}
    detail_resp = client.get(f"/api/v1/reviews/{item.review_id}", headers=AUTH_DEV)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["review_id"] == item.review_id

    # 3. POST /api/v1/reviews/{id}/claim
    claim_resp = client.post(
        f"/api/v1/reviews/{item.review_id}/claim",
        json={"expected_version": 1},
        headers=AUTH_DEV,
    )
    assert claim_resp.status_code == 200
    assert claim_resp.json()["status"] == "in_review"

    # 4. POST /api/v1/reviews/{id}/decisions (Approve)
    dec_resp = client.post(
        f"/api/v1/reviews/{item.review_id}/decisions",
        json={
            "action": "approve",
            "expected_version": 2,
            "rationale": "Notice requirement verified against clause 12",
        },
        headers=AUTH_DEV,
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["item"]["status"] == "approved"

    # 5. GET /api/v1/reviews/{id}/history
    hist_resp = client.get(f"/api/v1/reviews/{item.review_id}/history", headers=AUTH_DEV)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 3  # create, claim, approve

    # 6. GET /api/v1/reviews/metrics
    metrics_resp = client.get("/api/v1/reviews/metrics", headers=AUTH_DEV)
    assert metrics_resp.status_code == 200
    assert metrics_resp.json()["total_items"] >= 1
