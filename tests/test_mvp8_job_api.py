"""
tests/test_mvp8_job_api.py
==========================
Integration tests for the Operational Jobs API endpoints (/v1/jobs).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.operations.job_contracts import JobStatus, JobType
from src.operations.job_repository import JobRepository
from src.operations.job_service import JobService
from src.services.container import ServiceContainer
from src.config import settings

AUTH_TENANT_A = {"Authorization": "Bearer dev-tenant-a"}
AUTH_TENANT_B = {"Authorization": "Bearer dev-tenant-b"}


@pytest.fixture
def jobs_app(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_api_jobs.db"

    app = create_app()
    container = ServiceContainer(settings)
    container._started = True
    repo = JobRepository(db_path=str(db_file))
    service = JobService(repository=repo)

    container.job_repository = repo
    container.job_service = service

    app.state.container = container
    app.state.job_repository = repo
    app.state.job_service = service

    client = TestClient(app)
    return app, client, service, repo


def test_api_anonymous_request_rejected(jobs_app):
    _, client, _, _ = jobs_app
    resp = client.get("/v1/jobs")
    assert resp.status_code == 401


def test_submit_job_and_idempotency(jobs_app):
    _, client, _, _ = jobs_app

    # 1. Submit valid job
    payload = {
        "job_type": "ingest_document",
        "resource_id": "doc-abc-123",
        "payload": {"source": "upload"},
        "max_attempts": 3,
    }
    headers = {**AUTH_TENANT_A, "Idempotency-Key": "idem-key-100"}

    resp1 = client.post("/v1/jobs", json=payload, headers=headers)
    assert resp1.status_code == 202
    data1 = resp1.json()
    assert data1["job_id"].startswith("job-")
    assert data1["status"] == "queued"
    assert data1["tenant_id"] == "tenant-a"
    assert f"/v1/jobs/{data1['job_id']}" in resp1.headers["Location"]

    # 2. Idempotent replay: same key, same payload -> returns 200 or 202 with same job
    resp2 = client.post("/v1/jobs", json=payload, headers=headers)
    assert resp2.status_code in (200, 202)
    data2 = resp2.json()
    assert data2["job_id"] == data1["job_id"]

    # 3. Idempotency conflict: same key, different payload -> 409 Conflict
    conflicting_payload = {
        "job_type": "index_document",
        "resource_id": "doc-different",
        "payload": {},
    }
    resp3 = client.post("/v1/jobs", json=conflicting_payload, headers=headers)
    assert resp3.status_code == 409
    assert "reused with different input fingerprint" in resp3.json()["detail"]


def test_get_and_list_jobs_with_tenant_isolation(jobs_app):
    _, client, _, _ = jobs_app

    # Submit job as Tenant A
    resp_a = client.post(
        "/v1/jobs",
        json={"job_type": "extract_facts", "resource_id": "doc-a"},
        headers=AUTH_TENANT_A,
    )
    job_a_id = resp_a.json()["job_id"]

    # Submit job as Tenant B
    resp_b = client.post(
        "/v1/jobs",
        json={"job_type": "extract_facts", "resource_id": "doc-b"},
        headers=AUTH_TENANT_B,
    )
    job_b_id = resp_b.json()["job_id"]

    # Tenant A lists jobs -> only sees job_a
    list_a = client.get("/v1/jobs", headers=AUTH_TENANT_A)
    assert list_a.status_code == 200
    items_a = list_a.json()["items"]
    assert any(j["job_id"] == job_a_id for j in items_a)
    assert not any(j["job_id"] == job_b_id for j in items_a)

    # Tenant A gets job_a -> 200
    get_a = client.get(f"/v1/jobs/{job_a_id}", headers=AUTH_TENANT_A)
    assert get_a.status_code == 200
    assert get_a.json()["job_id"] == job_a_id

    # Tenant B tries to get job_a -> 404
    get_cross = client.get(f"/v1/jobs/{job_a_id}", headers=AUTH_TENANT_B)
    assert get_cross.status_code == 404


def test_cancel_and_retry_lifecycle(jobs_app):
    _, client, _, repo = jobs_app

    # Submit job as Tenant A
    resp = client.post(
        "/v1/jobs",
        json={"job_type": "compare_documents", "resource_id": "doc-cmp"},
        headers=AUTH_TENANT_A,
    )
    job_id = resp.json()["job_id"]

    # Cancel job
    cancel_resp = client.post(f"/v1/jobs/{job_id}/cancel", headers=AUTH_TENANT_A)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Retry cancelled job
    retry_resp = client.post(f"/v1/jobs/{job_id}/retry", headers=AUTH_TENANT_A)
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] == "queued"

    # Check events timeline
    events_resp = client.get(f"/v1/jobs/{job_id}/events", headers=AUTH_TENANT_A)
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert isinstance(events, list)
    assert len(events) >= 3  # queued -> cancelled -> queued (retry)
    statuses = [e["to_status"] for e in events]
    assert "cancelled" in statuses
