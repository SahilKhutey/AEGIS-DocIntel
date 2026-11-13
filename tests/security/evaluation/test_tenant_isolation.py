"""
AEGIS Evaluation Security Tests — Tenant & Evaluation Isolation (PROT-04 WP-04.09)
Tests:
- TENANT-001: Cross-tenant document access returns 404 (IDOR immunity)
- TENANT-002: Forged tenant and workspace headers have no effect on data partitioning
"""

import io
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.license import issue_evaluation_license, export_license_token


def test_tenant_001_cross_tenant_document_access_denied(client: TestClient):
    """TENANT-001: Evaluator A cannot read or compare documents uploaded by Evaluator B."""
    # Tenant A
    lic_a = issue_evaluation_license(user_id="evaluator-alice")
    token_a = export_license_token(lic_a)
    headers_a = {"X-Evaluation-License": token_a}

    # Tenant B
    lic_b = issue_evaluation_license(user_id="evaluator-bob")
    token_b = export_license_token(lic_b)
    headers_b = {"X-Evaluation-License": token_b}

    # Alice uploads a document
    file_content = b"Confidential Alice Document"
    res_upload = client.post(
        "/v1/evaluation/documents",
        headers=headers_a,
        files={"file": ("alice_doc.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert res_upload.status_code == 200
    doc_id_a = res_upload.json()["document_id"]

    # Bob attempts to fetch Alice's document directly (IDOR probe)
    res_bob_fetch = client.get(f"/v1/evaluation/documents/{doc_id_a}", headers=headers_b)
    # Server must return 404 to avoid leaking existence
    assert res_bob_fetch.status_code == 404
    assert res_bob_fetch.json()["error"] == "DOCUMENT_NOT_FOUND"


def test_tenant_002_forged_tenant_header_denied(client: TestClient):
    """TENANT-002: Passing forged headers (X-Tenant-ID: victim) does not breach license boundary."""
    lic_attacker = issue_evaluation_license(user_id="evaluator-attacker")
    token_attacker = export_license_token(lic_attacker)
    headers_attacker = {
        "X-Evaluation-License": token_attacker,
        "X-Tenant-ID": "enterprise-victim-corp",
        "X-Workspace-ID": "ws-victim-production",
    }

    # Fetching documents only returns attacker's documents (empty)
    res = client.get("/v1/evaluation/documents", headers=headers_attacker)
    assert res.status_code == 200
    assert res.json()["total"] == 0
