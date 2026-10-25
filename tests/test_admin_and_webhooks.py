"""
AEGIS-DocIntel — Admin, Webhooks, and Chunk Inspection Integration Tests
=======================================================================
Verifies RBAC access controls, tenant-scoped admin statistics, token usage metrics,
webhook subscriptions lifecycle, and paginated document chunk inspection with
post-restart re-hydration from SQLite.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.core.orchestrator import AMDIOrchestrator
from src.services.container import ServiceContainer, RealDocumentService
from src.config import settings


@pytest.fixture
def app_and_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_admin.db"

    app = create_app()
    container = ServiceContainer(settings)
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    client = TestClient(app)
    return app, client, container


def test_admin_stats_rbac_and_data(app_and_client):
    app, client, container = app_and_client

    # 1. Anonymous request rejected with 401
    resp_anon = client.get("/v1/admin/stats")
    assert resp_anon.status_code == 401

    admin_headers = {"Authorization": "Bearer dev-tenant-alpha"}
    
    # Ingest document under tenant-alpha
    doc_id = str(uuid.uuid4())
    doc_info = {
        "doc_id": doc_id,
        "tenant_id": "tenant-alpha",
        "filename": "financial_report.pdf",
        "status": "ready",
        "page_count": 5,
        "chunk_count": 24,
        "is_scanned": False,
        "language": "en",
        "created_at": None,
    }
    container.document_service._docs[doc_id] = doc_info

    # 2. Admin request succeeds and returns aggregated TenantStats
    resp_admin = client.get("/v1/admin/stats", headers=admin_headers)
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert data["tenant_id"] == "tenant-alpha"
    assert data["doc_count"] == 1
    assert data["chunk_count"] == 24
    assert data["total_tokens_used"] == 24 * 128
    assert data["total_cost_usd"] > 0


def test_admin_token_usage(app_and_client):
    app, client, container = app_and_client
    admin_headers = {"Authorization": "Bearer dev-tenant-beta"}

    doc_id = str(uuid.uuid4())
    container.document_service._docs[doc_id] = {
        "doc_id": doc_id,
        "tenant_id": "tenant-beta",
        "filename": "contract.pdf",
        "status": "ready",
        "page_count": 2,
        "chunk_count": 10,
        "is_scanned": False,
        "language": "en",
        "created_at": None,
    }

    resp = client.get("/v1/admin/token-usage", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "month-to-date"
    assert data["total_in_tokens"] == 10 * 128
    assert data["total_out_tokens"] == int(10 * 128 * 0.25)
    assert data["query_count"] >= 1


def test_webhook_subscriptions_crud(app_and_client):
    app, client, _ = app_and_client
    headers_a = {"Authorization": "Bearer dev-tenant-1"}
    headers_b = {"Authorization": "Bearer dev-tenant-2"}

    # 1. Unauthenticated creation rejected
    resp_anon = client.post("/v1/webhooks/subscriptions", json={"url": "https://example.com/test", "secret_token": "sec123"})
    assert resp_anon.status_code == 401

    # 2. Create subscription under tenant-1
    resp_create = client.post(
        "/v1/webhooks/subscriptions",
        headers=headers_a,
        json={"url": "https://example.com/test", "secret_token": "sec123", "topic_pattern": "document.*"},
    )
    assert resp_create.status_code == 201
    created = resp_create.json()
    sub_id = created["subscription_id"]
    assert created["tenant_id"] == "tenant-1"
    assert created["is_active"] is True

    # 3. List under tenant-1 has 1 item, tenant-2 has 0 items
    list_a = client.get("/v1/webhooks/subscriptions", headers=headers_a).json()
    assert len(list_a) == 1
    assert list_a[0]["subscription_id"] == sub_id

    list_b = client.get("/v1/webhooks/subscriptions", headers=headers_b).json()
    assert len(list_b) == 0

    # 4. Deleting under foreign tenant-2 returns 404
    del_foreign = client.delete(f"/v1/webhooks/subscriptions/{sub_id}", headers=headers_b)
    assert del_foreign.status_code == 404

    # 5. Deleting under owner tenant-1 succeeds
    del_owner = client.delete(f"/v1/webhooks/subscriptions/{sub_id}", headers=headers_a)
    assert del_owner.status_code == 200
    assert del_owner.json()["deleted"] is True


@pytest.mark.asyncio
async def test_document_chunks_pagination_and_rehydration(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_chunks.db"

    app = create_app()
    container = ServiceContainer(settings)
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    client = TestClient(app)

    auth_headers = {"Authorization": "Bearer dev-tenant-corp"}

    # Ingest real document with multi-element text
    raw_content = b"Paragraph One: Core architecture overview.\n\nParagraph Two: Mathematical proofs.\n\nParagraph Three: Benchmarks."
    ingest_resp = await container.document_service.ingest(
        file_bytes=raw_content,
        filename="overview.txt",
        content_type="text/plain",
        tenant_id="tenant-corp",
    )
    doc_id = ingest_resp.doc_id

    # 1. Fetch chunks page 1 with page_size=2
    resp_p1 = client.get(f"/v1/documents/{doc_id}/chunks?page=1&page_size=2", headers=auth_headers)
    assert resp_p1.status_code == 200
    p1_data = resp_p1.json()
    assert p1_data["total"] >= 2
    assert len(p1_data["items"]) <= 2

    # 2. Simulate server restart: wipe orchestrator memory
    container.rag_engine._doc_state.clear()
    assert doc_id not in container.rag_engine._doc_state

    # 3. Fetch chunks after restart: auto-hydrates from SQLite
    resp_rehydrated = client.get(f"/v1/documents/{doc_id}/chunks", headers=auth_headers)
    assert resp_rehydrated.status_code == 200
    rehydrated_data = resp_rehydrated.json()
    assert rehydrated_data["total"] >= 2
    assert len(rehydrated_data["items"]) >= 2
    assert doc_id in container.rag_engine._doc_state

    # 4. Cross-tenant access returns 404
    foreign_headers = {"Authorization": "Bearer dev-foreign-tenant"}
    resp_foreign = client.get(f"/v1/documents/{doc_id}/chunks", headers=foreign_headers)
    assert resp_foreign.status_code == 404
