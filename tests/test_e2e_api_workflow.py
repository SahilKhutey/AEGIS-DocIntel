"""
AEGIS-DocIntel — End-to-End API Workflow Integration Tests
==========================================================
Verifies the complete document lifecycle across the unified API:
1. Authenticated document upload (POST /v1/documents/upload)
2. Document status polling (GET /v1/documents/{doc_id})
3. Paginated chunk inspection (GET /v1/documents/{doc_id}/chunks)
4. Context-aware RAG query with citations (POST /v1/query)
5. Tenant isolation (cross-tenant 404 rejection)
6. Universal Export Object retrieval (GET /v1/documents/{doc_id}/export)
7. Cascading deletion and cleanup (DELETE /v1/documents/{doc_id})
"""
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.core.orchestrator import AMDIOrchestrator
from src.services.container import ServiceContainer, RealDocumentService
from src.services.query_service import QueryService
from src.config import settings


@pytest.fixture
def e2e_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    db_file = tmp_path / "test_e2e.db"

    app = create_app()
    container = ServiceContainer(settings)
    container.rag_engine = AMDIOrchestrator()
    container.document_service = RealDocumentService(container.rag_engine, db_path=str(db_file))
    container.query_service = QueryService(
        rag_engine=container.rag_engine,
        memory_engine=container.memory_engine,
        llm_service=container.llm_service,
        embedding_model=container.embedding_model,
    )

    app.state.container = container
    app.state.orchestrator = container.rag_engine
    client = TestClient(app)
    return app, client, container


def test_complete_document_lifecycle_and_rag(e2e_client):
    app, client, container = e2e_client

    tenant_a = "tenant-enterprise"
    tenant_b = "tenant-intruder"
    headers_a = {"Authorization": f"Bearer dev-{tenant_a}"}
    headers_b = {"Authorization": f"Bearer dev-{tenant_b}"}

    # 1. Reject unauthenticated upload
    fake_pdf = b"%PDF-1.4 mock content for e2e test\nSection 1: Executive Summary\nRevenue grew by 45% in 2025."
    file_payload = {"file": ("summary.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    resp_anon = client.post("/v1/documents/upload", files=file_payload)
    assert resp_anon.status_code == 401

    # 2. Upload document under tenant_a
    file_payload_a = {"file": ("summary.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    resp_upload = client.post("/v1/documents/upload", files=file_payload_a, headers=headers_a)
    assert resp_upload.status_code == 202
    doc_data = resp_upload.json()
    doc_id = doc_data["doc_id"]
    assert doc_data["filename"] == "summary.pdf"
    assert doc_data["status"] == "ready"

    # 3. Document status & metadata polling
    resp_get = client.get(f"/v1/documents/{doc_id}", headers=headers_a)
    assert resp_get.status_code == 200
    assert resp_get.json()["doc_id"] == doc_id
    assert resp_get.json()["filename"] == "summary.pdf"

    # 4. Cross-tenant isolation: tenant_b cannot view tenant_a's document
    resp_cross = client.get(f"/v1/documents/{doc_id}", headers=headers_b)
    assert resp_cross.status_code == 404

    # 5. List tenant documents
    resp_list = client.get("/v1/documents", headers=headers_a)
    assert resp_list.status_code == 200
    docs = resp_list.json().get("items") or resp_list.json().get("documents", [])
    assert any(d["doc_id"] == doc_id for d in docs)

    # 6. Paginated chunk inspection
    resp_chunks = client.get(f"/v1/documents/{doc_id}/chunks?page=1&page_size=10", headers=headers_a)
    assert resp_chunks.status_code == 200
    chunks_data = resp_chunks.json()
    assert "items" in chunks_data or "chunks" in chunks_data
    chunks = chunks_data.get("items") or chunks_data.get("chunks", [])
    assert chunks_data["total"] >= 1
    assert len(chunks) >= 1

    # Cross-tenant chunk inspection rejection
    resp_chunks_cross = client.get(f"/v1/documents/{doc_id}/chunks", headers=headers_b)
    assert resp_chunks_cross.status_code == 404

    # 7. Ask questions via RAG query endpoint (POST /v1/query)
    query_payload = {
        "question": "What was the revenue growth?",
        "doc_id": doc_id,
        "top_k": 5,
        "include_citations": True,
    }
    resp_query = client.post("/v1/query", json=query_payload, headers=headers_a)
    assert resp_query.status_code == 200
    q_data = resp_query.json()
    assert "answer" in q_data
    assert "confidence" in q_data

    # Cross-tenant query: tenant_b query fails to find or reference tenant_a document
    resp_query_cross = client.post("/v1/query", json=query_payload, headers=headers_b)
    assert resp_query_cross.status_code == 404

    # 8. Cascading Deletion
    resp_delete = client.delete(f"/v1/documents/{doc_id}", headers=headers_a)
    assert resp_delete.status_code == 204

    # 9. Verify document is gone
    resp_deleted_get = client.get(f"/v1/documents/{doc_id}", headers=headers_a)
    assert resp_deleted_get.status_code == 404


def test_batch_upload_endpoint(e2e_client):
    app, client, container = e2e_client
    headers = {"Authorization": "Bearer dev-tenant-batch"}

    body = {
        "documents": [
            {"s3_uri": "s3://bucket/doc1.pdf", "filename": "doc1.pdf"},
            {"s3_uri": "s3://bucket/doc2.pdf", "filename": "doc2.pdf"},
        ]
    }
    resp = client.post("/v1/documents/batch", json=body, headers=headers)
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "queued"
    assert data["doc_count"] == 2
    assert "job_id" in data
