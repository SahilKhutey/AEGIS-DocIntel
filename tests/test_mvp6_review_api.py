"""
tests/test_mvp6_review_api.py
=============================
Integration and contract tests for Review Governance API endpoints.
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


@pytest.fixture
def governance_app(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_api_gov.db"
    review_db = tmp_path / "test_review_api.db"

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
    return app, client, container


def test_api_anonymous_request_rejected(governance_app):
    _, client, _ = governance_app
    resp = client.get("/v1/reviews")
    assert resp.status_code == 401


def test_api_review_lifecycle_and_idempotency(governance_app):
    _, client, container = governance_app
    svc: ReviewService = container.review_service

    # Seed a candidate fact into review queue
    span = EvidenceSpan(
        document_id="doc-api-1",
        tenant_id="default-tenant",
        chunk_id="c1",
        quoted_text="liability shall not exceed $1,000,000 USD",
    )
    fact = ExtractedFact(
        fact_id="fact-api-1",
        tenant_id="default-tenant",
        document_id="doc-api-1",
        subject="contract",
        attribute="liability_cap",
        value=1000000.0,
        raw_value="$1,000,000",
        value_type="decimal",
        unit="USD",
        evidence=(span,),
    )
    item = svc.create_review_from_fact("default-tenant", fact)

    # 1. GET /v1/reviews - list queue
    list_resp = client.get("/v1/reviews", headers=AUTH_DEV)
    assert list_resp.status_code == 200
    queue_data = list_resp.json()
    assert len(queue_data["items"]) >= 1
    review_ids = [i["review_id"] for i in queue_data["items"]]
    assert item.review_id in review_ids

    # Also test /api/v1/reviews alias
    alias_resp = client.get("/api/v1/reviews", headers=AUTH_DEV)
    assert alias_resp.status_code == 200

    # 2. GET /v1/reviews/{id} - get item detail
    detail_resp = client.get(f"/v1/reviews/{item.review_id}", headers=AUTH_DEV)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["review_id"] == item.review_id

    # 3. POST /v1/reviews/{id}/claim - claim item
    claim_resp = client.post(
        f"/v1/reviews/{item.review_id}/claim",
        json={"expected_version": 1},
        headers=AUTH_DEV,
    )
    assert claim_resp.status_code == 200
    assert claim_resp.json()["status"] == "in_review"
    assert claim_resp.json()["version"] == 2

    # 4. POST /v1/reviews/{id}/decisions - submit correction with Idempotency-Key
    headers_idem = dict(AUTH_DEV)
    headers_idem["Idempotency-Key"] = "idem-api-test-001"

    decision_payload = {
        "action": "correct",
        "expected_version": 2,
        "rationale": "Corrected aggregate limit representation",
        "corrected_value": 2500000.0,
        "corrected_type": "decimal",
        "unit": "USD",
        "evidence_quote": "liability shall not exceed $1,000,000 USD",
    }
    dec_resp = client.post(
        f"/v1/reviews/{item.review_id}/decisions",
        json=decision_payload,
        headers=headers_idem,
    )
    assert dec_resp.status_code == 200
    dec_data = dec_resp.json()
    assert dec_data["item"]["status"] == "corrected"
    assert dec_data["item"]["version"] == 3
    assert dec_data["decision"]["action"] == "correct"

    # 5. Replay with same Idempotency-Key returns cached response
    replay_resp = client.post(
        f"/v1/reviews/{item.review_id}/decisions",
        json=decision_payload,
        headers=headers_idem,
    )
    assert replay_resp.status_code == 200
    assert replay_resp.json()["item"]["version"] == 3

    # 6. GET /v1/reviews/{id}/history - inspect audit trail
    hist_resp = client.get(f"/v1/reviews/{item.review_id}/history", headers=AUTH_DEV)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 3  # create, claim, correct
    assert history[2]["action"] == "correct"

    # 7. POST /v1/reviews/{id}/feedback - record structured feedback
    fb_resp = client.post(
        f"/v1/reviews/{item.review_id}/feedback",
        json={
            "category": "wrong_value",
            "notes": "Extracted amount was missing amendment clause",
            "corrected_reference": "2500000.0",
        },
        headers=AUTH_DEV,
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["status"] == "recorded"

    # 8. GET /v1/reviews/approved-facts - verify approved facts retrieval
    approved_resp = client.get("/v1/reviews/approved-facts", headers=AUTH_DEV)
    assert approved_resp.status_code == 200
    approved_facts = approved_resp.json()
    assert len(approved_facts) == 1
    assert approved_facts[0]["value"] == 2500000.0
    assert approved_facts[0]["is_corrected"] is True

    # 9. GET /v1/reviews/metrics - get governance metrics
    metrics_resp = client.get("/v1/reviews/metrics", headers=AUTH_DEV)
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_items"] >= 1
    assert metrics["correction_rate"] == 1.0

    # 10. POST /v1/reviews/{id}/reopen - reopen review
    reopen_resp = client.post(
        f"/v1/reviews/{item.review_id}/reopen",
        json={
            "expected_version": 3,
            "rationale": "Administrative re-check required by compliance officer",
        },
        headers=AUTH_DEV,
    )
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["item"]["status"] == "in_review"
    assert reopen_resp.json()["item"]["version"] == 4
