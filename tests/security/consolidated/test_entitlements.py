"""
Consolidated Security Audit: Server-Enforced Entitlements (SEC-011)
"""

import pytest
from fastapi.testclient import TestClient


def test_ent_001_permitted_evaluation_features_allowed(client: TestClient, keypair):
    """SEC-011.1: Permitted evaluation tier features return HTTP 200."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    assert client.get("/v1/evaluation/documents", headers=headers).status_code == 200
    assert client.get("/v1/evaluation/usage", headers=headers).status_code == 200


def test_ent_002_prohibited_enterprise_features_denied(client: TestClient, keypair):
    """SEC-011.2: Unentitled enterprise management features return HTTP 403."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    assert client.post("/v1/admin/users", json={"name": "user2"}, headers=headers).status_code == 403
    assert client.post("/v1/admin/platform/config", json={}, headers=headers).status_code == 403


def test_ent_003_admin_override_disables_feature_immediately(client: TestClient, keypair):
    """SEC-011.3: Administrative dynamic override instantly revokes feature capability."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    # Admin disables documents.compare
    ov_res = client.post(
        f"/v1/admin/evaluation/licenses/{lic_id}/override",
        json={"feature_key": "documents.compare", "override_enabled": False, "reason_code": "POLICY_REVOKE"},
        headers={"X-Admin-Key": "aegis-admin-secret-key-eval-2026"},
    )
    assert ov_res.status_code == 200

    # Evaluator attempts compare -> returns HTTP 403
    comp_res = client.post(
        "/v1/evaluation/compare",
        json={"left_document_id": "doc-1", "right_document_id": "doc-2"},
        headers=headers,
    )
    assert comp_res.status_code == 403
    assert comp_res.json()["error"] == "FEATURE_NOT_ENTITLED"


def test_ent_004_client_asserted_entitlements_ignored(client: TestClient, keypair):
    """SEC-011.4: Client sending forged X-Entitlements header receives zero elevation."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    headers = {
        "Authorization": f"Bearer {at}",
        "X-Entitlements": "users.manage,platform.admin,models.configure",
    }
    assert client.post("/v1/admin/users", json={"name": "hacked"}, headers=headers).status_code == 403
