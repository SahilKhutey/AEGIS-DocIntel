"""
tests/test_mvp4_api_contracts.py
================================
API contract integration tests verifying request ID, security headers,
and error response consistency on the live application factory.
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
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_api_contracts.db"

    app = create_app()
    container = ServiceContainer(settings)
    container._started = True
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    client = TestClient(app)
    return app, client, container


def test_api_contract_headers_and_request_id(api_client):
    _, client, _ = api_client
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_api_contract_health_live_probe(api_client):
    _, client, _ = api_client
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_contract_health_ready_probe(api_client):
    _, client, _ = api_client
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "dependencies" in data


def test_api_contract_unauthenticated_protected_route(api_client):
    _, client, _ = api_client
    resp = client.get("/v1/documents")
    assert resp.status_code == 401
    assert "X-Request-ID" in resp.headers


def test_api_contract_answers_route(api_client):
    _, client, _ = api_client
    headers = {"Authorization": "Bearer dev-tenant-corp"}
    resp = client.post("/v1/answers", json={"question": "What is the policy?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "answer" in data
    assert "citations" in data
    assert "warnings" in data
    assert "X-Request-ID" in resp.headers
