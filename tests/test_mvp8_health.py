"""
tests/test_mvp8_health.py
=========================
Integration tests for operations database and background worker health & readiness checks.
"""

from __future__ import annotations

import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.operations.job_repository import JobRepository
from src.services.container import ServiceContainer, RealDocumentService
from src.core.orchestrator import AMDIOrchestrator
from src.config import settings


@pytest.fixture
def health_app(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    doc_db = tmp_path / "test_doc.db"
    ops_db = tmp_path / "test_health_ops.db"

    app = create_app()
    container = ServiceContainer(settings)
    container._started = True

    orch = AMDIOrchestrator()
    container.rag_engine = orch
    container.document_service = RealDocumentService(orchestrator=orch, db_path=str(doc_db))

    repo = JobRepository(db_path=str(ops_db))
    container.job_repository = repo

    app.state.container = container
    client = TestClient(app)
    return app, client, container, repo


def test_liveness_probe_returns_ok(health_app):
    _, client, _, _ = health_app
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_probe_includes_operations_db(health_app):
    _, client, container, _ = health_app
    ready, details = await container.verify_readiness()
    assert ready is True
    assert details["operations_db"] == "ok"
    assert details["database"] == "ok"

    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
