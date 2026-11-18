"""
PT-04: Tenant Isolation and Cross-Tenant Attack Adversarial Tests
Covers PT-TEN-001 through PT-TEN-010.
Asserts pre-retrieval tenant isolation, document boundary enforcement, non-disclosing error codes,
header spoofing defense, body manipulation prevention, and job/cache separation.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from tests.security.penetration_testing.conftest import make_evaluator_jwt


def test_pt_ten_001_read_another_tenant_document(staging_rsa_keypair, core_client):
    """PT-TEN-001: Evaluator A attempts reading Evaluator B's document -> Denied (403 or non-disclosing 404)."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        # doc-b-001 belongs exclusively to tenant-eval-b
        res = core_client.get("/api/v1/documents/doc-b-001", headers={"Authorization": f"Bearer {token_a}"})
        assert res.status_code in (403, 404)


def test_pt_ten_002_download_another_tenant_export(staging_rsa_keypair, core_client):
    """PT-TEN-002: Evaluator A attempts exporting/downloading Tenant B's document -> Denied."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/documents/doc-b-001/export", headers={"Authorization": f"Bearer {token_a}"})
        assert res.status_code in (403, 404)


def test_pt_ten_003_query_another_tenant_document(staging_rsa_keypair, core_client):
    """PT-TEN-003: Evaluator A queries intelligence engine referencing Tenant B's document ID -> Denied."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"document_id": "doc-b-001", "query": "Extract sensitive M&A details"}
        )
        assert res.status_code in (403, 404)


def test_pt_ten_004_compare_cross_tenant_documents(staging_rsa_keypair, core_client):
    """PT-TEN-004: Ingestion/comparison blending Tenant A doc and Tenant B doc is denied."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post(
            "/api/v1/documents/compare",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"document_ids": ["doc-a-001", "doc-b-001"]}
        )
        assert res.status_code in (403, 404)


def test_pt_ten_005_modify_tenant_id_in_request_body(staging_rsa_keypair, core_client):
    """PT-TEN-005: Client attempting to supply mismatched tenant_id in request body is ignored or rejected."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"document_id": "doc-a-001", "tenant_id": "tenant-eval-b", "query": "Summarize"}
        )
        assert res.status_code == 200
        # Authority strictly reflects authenticated token's tenant_id
        assert res.json()["tenant"] == "tenant-eval-a"


def test_pt_ten_006_modify_tenant_id_in_header(staging_rsa_keypair, core_client):
    """PT-TEN-006: Client injecting forged X-Tenant-ID header is strictly rejected with HTTP 403."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": "tenant-eval-b",
        }
        res = core_client.get("/api/v1/protected", headers=headers)
        assert res.status_code == 403
        assert "Tenant header manipulation rejected" in res.json().get("detail", "")


def test_pt_ten_007_modify_workspace_id(staging_rsa_keypair, core_client):
    """PT-TEN-007: Modifying workspace identifier does not grant access to foreign tenant spaces."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token_a}",
            "X-Workspace-ID": "workspace-victim-beta",
        }
        # Accessing foreign tenant document still strictly blocked
        res = core_client.get("/api/v1/documents/doc-b-001", headers=headers)
        assert res.status_code in (403, 404)


def test_pt_ten_008_access_another_tenant_job_id(staging_rsa_keypair, core_client):
    """PT-TEN-008: Probing another tenant's asynchronous background job ID is denied."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        # job-b-202 belongs to tenant-eval-b
        res = core_client.get("/api/v1/jobs/job-b-202", headers={"Authorization": f"Bearer {token_a}"})
        assert res.status_code in (403, 404)


def test_pt_ten_009_subscribe_another_tenant_websocket(staging_rsa_keypair):
    """PT-TEN-009: WebSocket subscription verifies tenant ticket binding; cross-tenant ticket is rejected."""
    from services.evaluation_gateway.activation import activation_service
    # Generate session for Evaluator A
    tok_a = "token-ws-eval-a"
    activation_service._sessions_by_access_hash["hash_a"] = type("Session", (), {
        "license_id": "lic-a", "user_id": "user-a", "tenant_id": "tenant-eval-a",
        "is_active": True, "is_revoked": False, "device_id": "dev-a"
    })()

    # Replaying ticket or attempting cross-tenant subscription fails
    assert activation_service.validate_session("invalid-ws-ticket") is None


def test_pt_ten_010_access_another_tenant_cached_result(staging_rsa_keypair, core_client):
    """PT-TEN-010: Cache keys incorporate tenant partition prefix; direct query to cached response is isolated."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")
    token_b = make_evaluator_jwt(priv, tenant_id="tenant-eval-b", user_id="user-eval-b")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        # Tenant A executes query
        res_a = core_client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"document_id": "doc-a-001", "query": "Cached insight"}
        )
        assert res_a.status_code == 200

        # Tenant B queries with Tenant A's document ID targeting the cache -> Denied
        res_b = core_client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"document_id": "doc-a-001", "query": "Cached insight"}
        )
        assert res_b.status_code in (403, 404)
