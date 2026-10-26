"""
tests/security/test_tenant_route_isolation.py
=============================================
Phase 3.1 Security Acceptance Suite — Cross-Tenant Route Isolation & IDOR Defense:
- Proving that cross-tenant resource access across all document, query, chunk, and export
  endpoints yields non-disclosing 404 responses.
- Verifying database and orchestrator level separation between tenants.
"""
from __future__ import annotations

import os
import uuid
import pytest
from fastapi.testclient import TestClient

from src.core.orchestrator import AMDIOrchestrator
from src.main import create_app
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
async def test_orchestrator_cross_tenant_isolation():
    """Verify that AMDIOrchestrator prevents cross-tenant access at engine level."""
    orch = AMDIOrchestrator()
    try:
        doc_a = await orch.ingest(
            make_document(tenant_id="tenant-alpha", filename="doc_a.txt", content="Alpha confidential earnings")
        )
        doc_b = await orch.ingest(
            make_document(tenant_id="tenant-bravo", filename="doc_b.txt", content="Bravo confidential roadmap")
        )

        # Cross-tenant query by doc_id must raise PermissionError
        with pytest.raises(PermissionError):
            await orch.query("earnings report", tenant_id="tenant-alpha", doc_id=doc_b.doc_id)

        # Direct accessor calls must raise PermissionError
        with pytest.raises(PermissionError):
            orch.get_document_elements(doc_b.doc_id, tenant_id="tenant-alpha")

        with pytest.raises(PermissionError):
            orch.get_document_tables(doc_b.doc_id, tenant_id="tenant-alpha")

        with pytest.raises(PermissionError):
            orch.get_master_state(doc_b.doc_id, tenant_id="tenant-alpha")

        # Owner can access their own document
        state_a = orch.get_master_state(doc_a.doc_id, tenant_id="tenant-alpha")
        assert state_a is not None
        assert state_a.doc_id == doc_a.doc_id
    finally:
        await orch.close()


def test_http_api_cross_tenant_lifecycle_idor_defense(monkeypatch):
    """
    HTTP API verification: Tenant Bravo probing Tenant Alpha's resources across
    GET, POST, DELETE, status, chunks, and export endpoints yields non-disclosing 404s.
    """
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    headers_alpha = {"Authorization": "Bearer dev-tenant-alpha"}
    headers_bravo = {"Authorization": "Bearer dev-tenant-bravo"}

    app = create_app()
    with TestClient(app) as client:
        # 1. Ingest document as Tenant Alpha
        res_upload = client.post(
            "/v1/documents/upload",
            headers=headers_alpha,
            files={"file": ("alpha_confidential.pdf", b"%PDF-1.7 Confidential Alpha Data", "application/pdf")},
        )
        assert res_upload.status_code == 202, res_upload.text
        doc_id = res_upload.json()["doc_id"]

        # 2. Tenant Bravo GET /v1/documents/{doc_id} -> 404
        assert client.get(f"/v1/documents/{doc_id}", headers=headers_bravo).status_code == 404

        # 3. Tenant Bravo GET /v1/documents/{doc_id}/status -> 404
        assert client.get(f"/v1/documents/{doc_id}/status", headers=headers_bravo).status_code == 404

        # 4. Tenant Bravo GET /v1/documents/{doc_id}/chunks -> 404
        assert client.get(f"/v1/documents/{doc_id}/chunks", headers=headers_bravo).status_code == 404

        # 5. Tenant Bravo GET /v1/documents/{doc_id}/export -> 404
        assert client.get(f"/v1/documents/{doc_id}/export?format=json", headers=headers_bravo).status_code == 404

        # 6. Tenant Bravo POST /v1/query with doc_id -> 404
        res_query = client.post(
            "/v1/query",
            headers=headers_bravo,
            json={"question": "What is the secret?", "doc_ids": [doc_id]},
        )
        assert res_query.status_code == 404

        # 7. Tenant Bravo DELETE /v1/documents/{doc_id} -> 404
        assert client.delete(f"/v1/documents/{doc_id}", headers=headers_bravo).status_code == 404

        # 8. Tenant Bravo GET /v1/documents list -> must NOT leak Alpha doc_id
        res_list = client.get("/v1/documents", headers=headers_bravo)
        assert res_list.status_code == 200
        items = res_list.json().get("items", [])
        assert all(item.get("doc_id") != doc_id for item in items)

        # 9. Tenant Alpha can access their own document
        assert client.get(f"/v1/documents/{doc_id}", headers=headers_alpha).status_code == 200

        # 10. Tenant Alpha can delete their own document
        assert client.delete(f"/v1/documents/{doc_id}", headers=headers_alpha).status_code == 204
