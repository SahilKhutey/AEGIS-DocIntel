"""
Release Engineering Test Suite — Release Revocation & Rollback (REL-010, GATE-12)
PROT-FINAL-04: Workstream REL-10
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app as gateway_app, ADMIN_SECRET_KEY
from services.evaluation_gateway.release_policy import release_policy
from services.evaluation_gateway.revocation import registry as revocation_registry


@pytest.fixture
def client():
    return TestClient(gateway_app)


@pytest.fixture(autouse=True)
def clean_policy():
    release_policy.reset()
    yield
    release_policy.reset()


def test_rel_061_public_release_policy_endpoint(client):
    """REL-010.1: Public endpoint returns active client release policy."""
    res = client.get("/v1/evaluation/release/policy")
    assert res.status_code == 200
    data = res.json()
    assert data["minimum_supported_version"] == "1.0.0"
    assert "blocked_versions" in data
    assert data["release_channel"] == "evaluation"


def test_rel_062_supported_client_version_allowed(client):
    """REL-010.2: Supported client version header proceeds cleanly."""
    res = client.get("/health", headers={"X-Client-Version": "1.1.0"})
    assert res.status_code == 200


def test_rel_063_blocked_client_version_rejected(client):
    """REL-010.3: Explicitly blocked client version is rejected with 403 Forbidden."""
    release_policy.block_version("0.9.5-vulnerable", reason="Known security flaw")
    
    res = client.get("/health", headers={"X-Client-Version": "0.9.5-vulnerable"})
    assert res.status_code == 403
    data = res.json()
    assert "CLIENT_VERSION_BLOCKED" in (data.get("error") or data.get("detail", {}).get("error", ""))


def test_rel_064_version_below_minimum_supported_rejected(client):
    """REL-010.4: Client version below minimum supported version is rejected with 403 Forbidden."""
    release_policy.set_minimum_version("1.1.0")
    
    res = client.get("/health", headers={"X-Client-Version": "1.0.0"})
    assert res.status_code == 403
    data = res.json()
    assert "CLIENT_VERSION_UNSUPPORTED" in (data.get("error") or data.get("detail", {}).get("error", ""))


def test_rel_065_admin_block_unblock_workflow(client):
    """REL-010.5: Administrative endpoints permit dynamic blocking and unblocking of client versions."""
    admin_headers = {"X-Admin-Key": ADMIN_SECRET_KEY}
    
    # 1. Block version
    res_block = client.post(
        "/v1/admin/evaluation/release/policy/block",
        headers=admin_headers,
        json={"version": "1.0.1", "reason": "Compromised build worker"}
    )
    assert res_block.status_code == 200
    assert "1.0.1" in res_block.json()["policy"]["blocked_versions"]
    
    # Verify client is blocked
    check_blocked = client.get("/health", headers={"X-Client-Version": "1.0.1"})
    assert check_blocked.status_code == 403
    
    # 2. Unblock version
    res_unblock = client.post(
        "/v1/admin/evaluation/release/policy/unblock",
        headers=admin_headers,
        json={"version": "1.0.1"}
    )
    assert res_unblock.status_code == 200
    assert "1.0.1" not in res_unblock.json()["policy"]["blocked_versions"]
    
    # Verify client is allowed again
    check_allowed = client.get("/health", headers={"X-Client-Version": "1.0.1"})
    assert check_allowed.status_code == 200


def test_rel_066_rollback_safeguards_do_not_reactivate_revoked_licenses():
    """GATE-12: Rollback safeguards confirm that release policy adjustments cannot resurrect revoked licenses."""
    test_lic_id = "test-lic-revoked-safeguard"
    revocation_registry.revoke(test_lic_id, reason="Security revocation")
    assert revocation_registry.is_revoked(test_lic_id) is True
    
    # Adjust release policy
    release_policy.set_minimum_version("1.0.0")
    
    # License remains strictly revoked
    assert revocation_registry.is_revoked(test_lic_id) is True
