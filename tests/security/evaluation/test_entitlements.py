"""
AEGIS Evaluation Security Tests — Server-Side Entitlement Enforcement (PROT-04 WP-04.05)
Tests:
- ENT-001: Allowed document read accepted
- ENT-002: Disallowed user administration returns 403 Forbidden
- ENT-003: Disallowed platform administration returns 403 Forbidden
- ENT-004: Client header 'X-User-Role: admin' fails to escalate privileges
- ENT-005: Client tampering with entitlement claims has no effect on server enforcement
"""

import pytest
from fastapi.testclient import TestClient


def test_ent_001_allowed_document_read(client: TestClient, valid_eval_license):
    """ENT-001: Evaluation license allows reading documents."""
    headers = valid_eval_license["headers"]
    res = client.get("/v1/evaluation/documents", headers=headers)
    assert res.status_code == 200
    assert "items" in res.json()


def test_ent_002_disallowed_user_administration_forbidden(client: TestClient, valid_eval_license):
    """ENT-002: Attempting to call user administration endpoint fails with 403 Forbidden."""
    headers = valid_eval_license["headers"]
    res = client.post("/v1/admin/users", headers=headers, json={"user_id": "new-user"})
    assert res.status_code == 403
    assert res.json()["error"] == "FEATURE_NOT_ENTITLED"


def test_ent_003_disallowed_platform_administration_forbidden(client: TestClient, valid_eval_license):
    """ENT-003: Attempting to modify platform configuration fails with 403 Forbidden."""
    headers = valid_eval_license["headers"]
    res = client.post("/v1/admin/platform/config", headers=headers, json={"debug_mode": True})
    assert res.status_code == 403
    assert res.json()["error"] == "FEATURE_NOT_ENTITLED"


def test_ent_004_client_changes_its_role_to_admin_no_escalation(client: TestClient, valid_eval_license):
    """ENT-004: Spoofing headers like X-User-Role: admin or Role: admin does not grant admin access."""
    headers = dict(valid_eval_license["headers"])
    headers["X-User-Role"] = "admin"
    headers["X-Role"] = "admin"
    headers["X-Tenant-Role"] = "platform_admin"

    res = client.post("/v1/admin/platform/config", headers=headers, json={"telemetry": "disabled"})
    assert res.status_code == 403
    assert res.json()["error"] == "FEATURE_NOT_ENTITLED"


def test_ent_005_client_modifies_entitlement_response_no_escalation(client: TestClient, valid_eval_license):
    """ENT-005: The server does not accept client-provided entitlement objects; server state is authoritative."""
    headers = dict(valid_eval_license["headers"])
    headers["X-Client-Entitlements"] = '{"platform.admin": true, "users.manage": true}'

    res = client.post("/v1/admin/users", headers=headers, json={"email": "attacker@evil.com"})
    assert res.status_code == 403
