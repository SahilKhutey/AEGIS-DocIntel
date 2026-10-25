"""
Tests for cross-tenant query isolation and data separation.
Permanent regression tests for the tenant-isolation fixes in AMDIOrchestrator.
"""
from __future__ import annotations

import pytest

from src.core.orchestrator import AMDIOrchestrator
from src.models.document_object import DocumentFormat, DocumentObject


def make_document(
    tenant_id: str,
    filename: str = "doc.txt",
    content: str = "Confidential tenant content data payload.",
) -> DocumentObject:
    return DocumentObject(
        filename=filename,
        raw_bytes=content.encode("utf-8"),
        format=DocumentFormat.TEXT,
        tenant_id=tenant_id,
    )


@pytest.mark.asyncio
async def test_cross_tenant_query_isolation():
    """
    Regression test for the fix noted in orchestrator.py: a query must
    never return another tenant's document, whether or not a doc_id is
    supplied.
    """
    orch = AMDIOrchestrator()
    try:
        doc_a = await orch.ingest(
            make_document(tenant_id="tenant-a", filename="doc_a.txt", content="Tenant A quarterly earnings")
        )
        doc_b = await orch.ingest(
            make_document(tenant_id="tenant-b", filename="doc_b.txt", content="Tenant B secret merger info")
        )

        # No doc_id supplied — must not silently return the most-recent
        # document regardless of which tenant is asking.
        result = await orch.query("earnings query", tenant_id="tenant-a")
        assert result.doc_id != doc_b.doc_id

        # Explicit doc_id belonging to a different tenant must be rejected,
        # not silently honored.
        with pytest.raises(PermissionError):
            await orch.query("test query", tenant_id="tenant-a", doc_id=doc_b.doc_id)

        # Direct accessor calls for a different tenant's doc_id must also raise PermissionError
        with pytest.raises(PermissionError):
            orch.get_document_elements(doc_b.doc_id, tenant_id="tenant-a")

        with pytest.raises(PermissionError):
            orch.get_document_tables(doc_b.doc_id, tenant_id="tenant-a")

        with pytest.raises(PermissionError):
            orch.get_master_state(doc_b.doc_id, tenant_id="tenant-a")

        # Owner can access their own document state
        state_a = orch.get_master_state(doc_a.doc_id, tenant_id="tenant-a")
        assert state_a is not None
        assert state_a.doc_id == doc_a.doc_id
    finally:
        await orch.close()


def test_cross_tenant_query_api_returns_404(monkeypatch):
    """
    HTTP API integration test: a tenant querying another tenant's document
    via POST /v1/query returns 404 Not Found (not 200 with phantom citations,
    nor 500 error).
    """
    from fastapi.testclient import TestClient
    from src.main import app

    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    tenant_a_headers = {"Authorization": "Bearer dev-tenant-alpha"}
    tenant_b_headers = {"Authorization": "Bearer dev-tenant-bravo"}

    with TestClient(app, raise_server_exceptions=False) as client:
        # Ingest document as tenant A
        r = client.post(
            "/v1/ingest",
            headers=tenant_a_headers,
            files={"file": ("alpha_secret.md", b"# Secret\n\nConfidential Alpha Financial Plan.", "text/markdown")},
        )
        assert r.status_code == 201, r.text
        doc_id = r.json()["doc_id"]

        # Tenant A can query their own document
        r_owner = client.post(
            "/v1/query",
            headers=tenant_a_headers,
            json={"question": "What is the secret?", "doc_ids": [doc_id]},
        )
        assert r_owner.status_code == 200, r_owner.text

        # Tenant B queries tenant A's doc_id with doc_ids list -> 404
        r_cross = client.post(
            "/v1/query",
            headers=tenant_b_headers,
            json={"question": "What is the secret?", "doc_ids": [doc_id]},
        )
        assert r_cross.status_code == 404, f"Expected 404, got {r_cross.status_code}: {r_cross.text}"

        # Tenant B queries tenant A's doc_id with doc_id scalar -> 404
        r_cross_scalar = client.post(
            "/v1/query",
            headers=tenant_b_headers,
            json={"question": "What is the secret?", "doc_id": doc_id},
        )
        assert r_cross_scalar.status_code == 404, f"Expected 404, got {r_cross_scalar.status_code}: {r_cross_scalar.text}"

        # Tenant B attempts to export tenant A's document -> 404
        r_cross_export = client.get(
            f"/v1/documents/{doc_id}/export?format=json",
            headers=tenant_b_headers,
        )
        assert r_cross_export.status_code == 404, f"Expected 404, got {r_cross_export.status_code}"


def test_cross_tenant_document_lifecycle_idor_attacks(monkeypatch):
    """
    Verify that across all document lifecycle operations (GET, DELETE, CHUNKS, LIST),
    cross-tenant resource probing yields non-disclosing 404 responses (IDOR defense).
    """
    from fastapi.testclient import TestClient
    from src.main import app

    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    tenant_a_headers = {"Authorization": "Bearer dev-tenant-alpha"}
    tenant_b_headers = {"Authorization": "Bearer dev-tenant-bravo"}

    with TestClient(app, raise_server_exceptions=False) as client:
        # 1. Ingest document as tenant A via /v1/documents/upload
        r = client.post(
            "/v1/documents/upload",
            headers=tenant_a_headers,
            files={"file": ("alpha_secret_lifecycle.pdf", b"%PDF-1.7 Confidential Alpha Data", "application/pdf")},
        )
        assert r.status_code == 202, r.text
        doc_id = r.json()["doc_id"]

        # 2. Tenant B GET /v1/documents/{doc_id} -> 404
        r_get = client.get(f"/v1/documents/{doc_id}", headers=tenant_b_headers)
        assert r_get.status_code == 404, f"Expected 404 on get, got {r_get.status_code}"

        # 3. Tenant B GET /v1/documents/{doc_id}/status -> 404
        r_status = client.get(f"/v1/documents/{doc_id}/status", headers=tenant_b_headers)
        assert r_status.status_code == 404, f"Expected 404 on status, got {r_status.status_code}"

        # 4. Tenant B GET /v1/documents/{doc_id}/chunks -> 404
        r_chunks = client.get(f"/v1/documents/{doc_id}/chunks", headers=tenant_b_headers)
        assert r_chunks.status_code == 404, f"Expected 404 on chunks, got {r_chunks.status_code}"

        # 5. Tenant B DELETE /v1/documents/{doc_id} -> 404
        r_del = client.delete(f"/v1/documents/{doc_id}", headers=tenant_b_headers)
        assert r_del.status_code == 404, f"Expected 404 on delete, got {r_del.status_code}"

        # 6. Document still exists for Tenant A
        r_owner = client.get(f"/v1/documents/{doc_id}", headers=tenant_a_headers)
        assert r_owner.status_code == 200, f"Expected 200 for owner, got {r_owner.status_code}"

        # 7. List documents for Tenant B must not contain Tenant A doc
        r_list = client.get("/v1/documents", headers=tenant_b_headers)
        assert r_list.status_code == 200
        items = r_list.json().get("items", [])
        assert all(i.get("doc_id") != doc_id for i in items)

        # 8. Tenant A can delete their own document
        r_del_owner = client.delete(f"/v1/documents/{doc_id}", headers=tenant_a_headers)
        assert r_del_owner.status_code == 204
