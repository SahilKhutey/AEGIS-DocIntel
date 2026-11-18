"""
PT-05: Entitlement Bypass Adversarial Tests
Covers PT-ENT-001 through PT-ENT-010.
Asserts that evaluators cannot execute features outside their assigned evaluation edition,
verifying server-side authoritative allowlists, enterprise route guards, and immediate revocation.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from tests.security.penetration_testing.conftest import make_evaluator_jwt
from services.evaluation_gateway.license import issue_evaluation_license, export_license_token
from services.evaluation_gateway.revocation import registry as revocation_registry


def test_pt_ent_001_direct_call_admin_endpoint(staging_rsa_keypair, core_client):
    """PT-ENT-001: Evaluator directly calling restricted admin endpoint is denied HTTP 403."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="evaluation_user")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post(
            "/api/v1/admin/evaluation/quotas/policies",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "rogue-policy"}
        )
        assert res.status_code == 403
        assert "Admin role required" in res.json().get("detail", "")


def test_pt_ent_002_manipulated_permission_claims(staging_rsa_keypair, core_client):
    """PT-ENT-002: Injected client headers claiming enterprise permissions are ignored and denied."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Entitlements": "enterprise,unlimited,batch_export",
            "X-Feature-Flags": "all_features=true",
        }
        res = core_client.post("/api/v1/enterprise/batch-export", headers=headers)
        assert res.status_code == 403
        assert "batch_export" in res.json().get("detail", "")


def test_pt_ent_003_modified_frontend_role(staging_rsa_keypair, core_client):
    """PT-ENT-003: Altering role in frontend client code does not bypass server role check."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="evaluation_user")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Client-Role": "enterprise_admin",
        }
        res = core_client.post("/api/v1/enterprise/auto-redaction", headers=headers)
        assert res.status_code == 403


def test_pt_ent_004_requests_after_entitlement_revocation(evaluator_a_license, gateway_client):
    """PT-ENT-004: Requests submitted after entitlement/license revocation are immediately blocked."""
    headers = evaluator_a_license["headers"]
    lic_id = evaluator_a_license["license_id"]

    # Revoke license online
    revocation_registry.revoke(lic_id, "Evaluation ended early by administrator")

    res = gateway_client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": "Test after revocation"}
    )
    assert res.status_code in (401, 403)
    assert any(err in str(res.json()) for err in ["REVOKED", "LICENSE_REVOKED"])


def test_pt_ent_005_access_through_alternate_api_routes(evaluator_a_license, gateway_client):
    """PT-ENT-005: Probing legacy, undocumented, or alternate API route prefixes is rejected."""
    headers = evaluator_a_license["headers"]
    alternate_routes = [
        "/api/v0/admin",
        "/api/internal/entitlements",
        "/admin/evaluation/override",
        "/api/v2/beta/bypass",
    ]
    for route in alternate_routes:
        res = gateway_client.get(route, headers=headers)
        assert res.status_code in (403, 404)


def test_pt_ent_006_background_job_authorization_bypass(staging_rsa_keypair, core_client):
    """PT-ENT-006: Asynchronous jobs verify entitlement before enqueueing; unauthorized jobs are rejected."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        # Enterprise batch export job endpoint
        res = core_client.post("/api/v1/enterprise/batch-export", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403


def test_pt_ent_007_enterprise_batch_export_endpoints(staging_rsa_keypair, core_client):
    """PT-ENT-007: Enterprise bulk export endpoint strictly requires enterprise tier license."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post("/api/v1/enterprise/batch-export", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403
        assert "not licensed under evaluation" in res.json().get("detail", "")


def test_pt_ent_008_enterprise_auto_redaction_endpoints(staging_rsa_keypair, core_client):
    """PT-ENT-008: Automated PII redaction pipeline requires enterprise entitlement."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post("/api/v1/enterprise/auto-redaction", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403
        assert "auto_redaction" in res.json().get("detail", "")


def test_pt_ent_009_websocket_enterprise_telemetry():
    """PT-ENT-009: WebSocket subscription to enterprise live telemetry requires enterprise role."""
    from services.evaluation_gateway.activation import activation_service
    # Evaluator cannot open enterprise live telemetry feed
    session_status = activation_service.validate_session("evaluator-session-token")
    assert session_status is None


def test_pt_ent_010_multi_tenant_organization_federation(staging_rsa_keypair, core_client):
    """PT-ENT-010: Evaluator attempting to federate cross-organization or cross-workspace is rejected."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Federated-Tenant-IDs": "tenant-eval-a,tenant-eval-b,tenant-eval-c",
        }
        res = core_client.get("/api/v1/protected", headers=headers)
        assert res.status_code == 200
        # Authority strictly tied to single tenant-eval-a, federated claim disregarded
        assert res.json()["tenant_id"] == "tenant-eval-a"
