"""
Consolidated Security Audit: Authorization & RBAC Isolation (SEC-004)
"""

import pytest
from fastapi.testclient import TestClient


def test_authz_001_evaluator_calling_admin_users_endpoint_denied(client: TestClient, keypair):
    """SEC-004.1: Evaluator calling user management admin endpoint returns HTTP 403."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    res_admin = client.post("/v1/admin/users", json={"name": "attacker"}, headers=headers)
    assert res_admin.status_code == 403


def test_authz_002_evaluator_calling_platform_config_denied(client: TestClient, keypair):
    """SEC-004.2: Evaluator calling platform configuration returns HTTP 403."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    res_admin = client.post("/v1/admin/platform/config", json={"setting": "danger"}, headers=headers)
    assert res_admin.status_code == 403


def test_authz_003_evaluator_jwt_claim_tampering_no_elevation(client: TestClient, keypair):
    """SEC-004.3: Evaluator modifying local JWT role to admin is rejected server-side."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]

    # Even if attacker constructs a header with elevated role assertion
    headers = {
        "Authorization": f"Bearer {at}",
        "X-User-Role": "admin",
        "X-Admin-Role": "superuser",
    }
    assert client.post("/v1/admin/users", json={"name": "escalated"}, headers=headers).status_code == 403


def test_authz_004_admin_endpoint_with_valid_admin_secret_succeeds(client: TestClient):
    """SEC-004.4: Authoritative admin key grants access to admin routes."""
    headers = {"X-Admin-Key": "aegis-admin-secret-key-eval-2026"}
    res = client.get("/v1/admin/evaluation/policies", headers=headers)
    assert res.status_code == 200
