"""
Consolidated Security Audit: Cross-Tenant Isolation & IDOR Defense (SEC-006)
"""

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import DOCUMENT_STORE, EvaluationDocument


def test_tenant_001_cross_tenant_document_inspection_denied(client: TestClient, keypair):
    """SEC-006.1: Evaluator attempting to access another tenant's document returns HTTP 404."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    # Store foreign tenant document
    DOCUMENT_STORE["foreign-doc-999"] = EvaluationDocument(
        doc_id="foreign-doc-999",
        license_id="lic-other-foreign-tenant",
        filename="confidential_contracts.pdf",
        content_type="application/pdf",
        text="Top secret foreign tenant data",
    )

    # Attempt to read foreign doc
    res_doc = client.get("/v1/evaluation/documents/foreign-doc-999", headers=headers)
    assert res_doc.status_code == 404
    assert res_doc.json()["error"] == "DOCUMENT_NOT_FOUND"


def test_tenant_002_forged_tenant_header_ignored(client: TestClient, keypair):
    """SEC-006.2: Attacker sending X-Tenant-Override header cannot escape license tenant boundary."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    headers = {
        "Authorization": f"Bearer {at}",
        "X-Tenant-Override": "tenant-evil-corporation",
        "X-Tenant-Id": "tenant-evil-corporation",
    }

    # Listing documents reflects only current evaluator license
    list_res = client.get("/v1/evaluation/documents", headers=headers)
    assert list_res.status_code == 200
    for doc in list_res.json()["items"]:
        assert doc.get("license_id") != "lic-other-foreign-tenant"


def test_tenant_003_document_list_filtered_strictly_by_license(client: TestClient, keypair):
    """SEC-006.3: Document catalog returns strictly documents uploaded by current license."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    # Own document
    DOCUMENT_STORE["my-doc-1"] = EvaluationDocument(
        doc_id="my-doc-1",
        license_id=lic_id,
        filename="my_resume.txt",
        content_type="text/plain",
        text="My own text",
    )
    # Foreign document
    DOCUMENT_STORE["other-doc-2"] = EvaluationDocument(
        doc_id="other-doc-2",
        license_id="foreign-lic-abc",
        filename="other_file.txt",
        content_type="text/plain",
        text="Other text",
    )

    list_res = client.get("/v1/evaluation/documents", headers=headers)
    assert list_res.status_code == 200
    doc_ids = [d["document_id"] for d in list_res.json()["items"]]
    assert "my-doc-1" in doc_ids
    assert "other-doc-2" not in doc_ids
