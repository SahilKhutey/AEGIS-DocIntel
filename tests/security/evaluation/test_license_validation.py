"""
AEGIS Evaluation Security Tests — License Engine & Signature Cryptography (PROT-04 WP-04.04)
Tests:
- LIC-002: Forged license rejected
- LIC-003: Expired license rejected
- LIC-004: Revoked license rejected
- LIC-005: License for another product rejected
- LIC-006: Suspended license rejected
"""

import copy
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.license import (
    issue_evaluation_license,
    export_license_token,
    CANONICAL_PRODUCT,
)
from services.evaluation_gateway.revocation import registry as revocation_registry


def test_lic_002_forged_license_rejected(client: TestClient):
    """LIC-002: Altering any claim in the signed payload breaks Ed25519 signature."""
    lic = issue_evaluation_license(user_id="legit-user", duration_days=14)
    # Attacker alters duration or role in payload without private key
    lic_tampered = copy.deepcopy(lic)
    lic_tampered["payload"]["user_id"] = "attacker-escalated"
    lic_tampered["payload"]["entitlements"].append("platform.admin")
    token = export_license_token(lic_tampered)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_SIGNATURE"


def test_lic_003_expired_license_rejected(client: TestClient):
    """LIC-003: A license that has passed expires_at is rejected with HTTP 403 LICENSE_EXPIRED."""
    lic = issue_evaluation_license(user_id="expired-evaluator", duration_days=-1)
    token = export_license_token(lic)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res.status_code == 403
    assert res.json()["error"] == "LICENSE_EXPIRED"


def test_lic_004_revoked_license_rejected(client: TestClient):
    """LIC-004: A license present in the revocation list is immediately denied."""
    lic = issue_evaluation_license(user_id="revoked-user", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    token = export_license_token(lic)

    # Valid before revocation
    res1 = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res1.status_code == 200

    # Revoke
    revocation_registry.revoke(lic_id)

    # Denied after revocation
    res2 = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res2.status_code == 403
    assert res2.json()["error"] == "LICENSE_REVOKED"


def test_lic_005_license_for_another_product_rejected(client: TestClient):
    """LIC-005: License issued for an alien product (e.g., AEGIS_CORE_ENTERPRISE) is rejected."""
    lic = issue_evaluation_license(
        user_id="enterprise-evaluator",
        duration_days=14,
        product="AEGIS_UNAUTHORIZED_PRODUCT",
    )
    token = export_license_token(lic)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res.status_code == 403
    assert res.json()["error"] == "PRODUCT_MISMATCH"


def test_lic_006_suspended_license_rejected(client: TestClient):
    """LIC-006: A license marked with status 'SUSPENDED' is rejected with HTTP 403 LICENSE_SUSPENDED."""
    lic = issue_evaluation_license(
        user_id="suspended-evaluator",
        duration_days=14,
        status="SUSPENDED",
    )
    token = export_license_token(lic)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res.status_code == 403
    assert res.json()["error"] == "LICENSE_SUSPENDED"
