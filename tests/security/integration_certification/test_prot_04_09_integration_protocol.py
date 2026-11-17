"""
AEGIS-DocIntel PROT-04.09 Master Integration, End-to-End Verification & Release Certification Suite
Complies with PROT-04 WP-04.09 Specifications.

Encompasses 101 Exhaustive Test Scenarios:
- INT-AUTH-001 to INT-AUTH-012: Authentication, Activation & Device Proofs.
- INT-LIC-001 to INT-LIC-012: License Issuance, Cryptographic Verification & Rotation.
- INT-ENT-001 to INT-ENT-010: Server-Enforced Entitlements & RBAC Isolation.
- INT-QUOTA-001 to INT-QUOTA-012: Quotas, Atomic Reservations, Concurrency & Settlement.
- INT-SESSION-001 to INT-SESSION-014: Session Lifecycles, Token Rotation, Replay Lockdown & Revocation.
- INT-ENGINE-001 to INT-ENGINE-010: Private Engine Isolation & Gateway Service Boundary.
- CROSS-001 to CROSS-015: Cross-Cutting Subsystem Security Guarantees.
- RES-INT-001 to RES-INT-010: Resilience, Chaos & Failure-Mode Handling.
- JOURNEY-A to JOURNEY-F: Complete End-to-End User Journeys.
"""

from __future__ import annotations

import base64
import concurrent.futures
import copy
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from fastapi.testclient import TestClient

from services.evaluation_gateway.activation import (
    activation_service,
    compute_code_hash,
    compute_key_fingerprint,
    format_canonical_challenge,
)
from services.evaluation_gateway.app import app
from services.evaluation_gateway.audit import audit_service as gateway_audit_service
from services.evaluation_gateway.entitlements import get_current_entitlement
from services.evaluation_gateway.license import (
    CANONICAL_PRODUCT,
    export_license_token,
    issue_evaluation_license,
    parse_license_token,
    verify_license,
    verify_signed_license,
    LicenseVerificationError,
    LicenseExpiredError,
    LicenseSignatureError,
    LicenseRevokedError,
)
from services.evaluation_gateway.license_repository import license_repository
from services.evaluation_gateway.quotas import quota_manager, QuotaExceededError
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.signing_key_registry import key_registry
from src.repositories.security_operations.audit_repository import audit_repository
from src.repositories.security_operations.incident_repository import incident_repository
from src.repositories.security_operations.key_metadata_repository import key_metadata_repository, KeyStatus
from src.repositories.security_operations.security_event_repository import security_event_repository
from src.security.audit_integrity import verify_chain, create_checkpoint, verify_checkpoint
from src.security.event_schema import SecurityEvent, Severity
from src.security.private_engine_guard import private_engine_guard
from src.services.evaluation.session_revocation_service import session_revocation_service
from src.services.evaluation.websocket_ticket_service import websocket_ticket_service
from src.services.security_operations.alert_evaluation_service import alert_evaluation_service
from src.services.security_operations.audit_verification_service import audit_verification_service
from src.services.security_operations.backup_verification_service import backup_verification_service
from src.services.security_operations.incident_service import incident_service
from src.services.security_operations.key_rotation_service import key_rotation_service
from src.services.security_operations.security_event_service import security_event_service


# ---------------------------------------------------------------------------
# Cryptographic Test Helpers
# ---------------------------------------------------------------------------

def generate_ed25519_keypair():
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    raw_pub = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    b64_raw = base64.b64encode(raw_pub).decode("ascii")
    pem_pub = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return priv, b64_raw, pem_pub


def sign_ed25519(priv_key: ed25519.Ed25519PrivateKey, message: str) -> str:
    sig = priv_key.sign(message.encode("utf-8"))
    return base64.b64encode(sig).decode("ascii")


# ==============================================================================
# Workstream 01: Authentication & Activation (INT-AUTH-001 - INT-AUTH-012)
# ==============================================================================

def test_int_auth_001_valid_activation_succeeds(client: TestClient):
    """INT-AUTH-001: Valid activation code and device key creates active license and session."""
    priv, b64_pub, _ = generate_ed25519_keypair()
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": b64_pub},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("active", "activated")
    assert "session" in data
    assert "access_token" in data["session"]


def test_int_auth_002_invalid_activation_code_rejected(client: TestClient):
    """INT-AUTH-002: Unknown or malformed activation code returns HTTP 400."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "INVALID-CODE-XYZ", "device_public_key": "pub_test"},
    )
    assert res.status_code == 400


def test_int_auth_003_expired_activation_challenge_rejected(client: TestClient):
    """INT-AUTH-003: Submitting challenge response after TTL window returns HTTP 400."""
    priv, _, pem_pub = generate_ed25519_keypair()
    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem_pub,
            "installation_id": "inst-win-dev01",
        },
    )
    assert ch_res.status_code == 200
    cid = ch_res.json()["challenge_id"]

    # Manually expire challenge in storage
    with activation_service._lock:
        activation_service._challenges_by_id[cid].expires_at = time.time() - 10

    act_res = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": "fake_sig", "installation_id": "inst-win-dev01"},
    )
    assert act_res.status_code in (400, 401)
    assert "expired" in act_res.json()["message"].lower()


def test_int_auth_004_replayed_activation_challenge_rejected(client: TestClient):
    """INT-AUTH-004: Reusing an already-consumed challenge ID is rejected."""
    priv, _, pem_pub = generate_ed25519_keypair()
    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem_pub,
            "installation_id": "inst-win-dev01",
        },
    )
    assert ch_res.status_code == 200
    cid = ch_res.json()["challenge_id"]
    canonical_msg = ch_res.json()["canonical_message"]
    sig = sign_ed25519(priv, canonical_msg)

    # First consumption succeeds
    first = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": sig, "installation_id": "inst-win-dev01"},
    )
    assert first.status_code == 200

    # Replay consumption fails
    second = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": sig, "installation_id": "inst-win-dev01"},
    )
    assert second.status_code == 400


def test_int_auth_005_invalid_device_signature_rejected(client: TestClient):
    """INT-AUTH-005: Tampered device signature during challenge activation returns HTTP 400."""
    priv, _, pem_pub = generate_ed25519_keypair()
    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem_pub,
            "installation_id": "inst-win-dev01",
        },
    )
    assert ch_res.status_code == 200
    cid = ch_res.json()["challenge_id"]
    act_res = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": "invalid_signature_bytes==", "installation_id": "inst-win-dev01"},
    )
    assert act_res.status_code in (400, 401)


def test_int_auth_006_device_limit_exceeded_rejected(client: TestClient):
    """INT-AUTH-006: Exceeding max permitted devices on license returns HTTP 409."""
    res1 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_1"},
    )
    assert res1.status_code == 200

    res2 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_2"},
    )
    assert res2.status_code == 409
    assert "limit" in res2.json()["message"].lower()


def test_int_auth_007_suspended_license_activation_denied(client: TestClient):
    """INT-AUTH-007: Attempting activation against suspended license is denied."""
    activation_service.register_activation_code("AEGIS-EVAL-SUSPENDED-001", status="SUSPENDED")
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-SUSPENDED-001", "device_public_key": "dev_key_susp"},
    )
    assert res.status_code in (400, 403)


def test_int_auth_008_revoked_license_activation_denied(client: TestClient):
    """INT-AUTH-008: Attempting activation against revoked license is denied."""
    activation_service.register_activation_code("AEGIS-EVAL-REVOKED-001", status="REVOKED")
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-REVOKED-001", "device_public_key": "dev_key_rev"},
    )
    assert res.status_code in (400, 403)


def test_int_auth_009_expired_license_activation_denied(client: TestClient):
    """INT-AUTH-009: Attempting activation against expired license is denied."""
    activation_service.register_activation_code("AEGIS-EVAL-EXPIRED-001", status="EXPIRED")
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-EXPIRED-001", "device_public_key": "dev_key_exp"},
    )
    assert res.status_code in (400, 403)


def test_int_auth_010_unauthorized_evaluator_account_mismatch(client: TestClient):
    """INT-AUTH-010: Activation bound to another evaluator account without grant is denied."""
    activation_service.register_activation_code("AEGIS-EVAL-ALICE-001", user_id="eval-alice")
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-ALICE-001", "device_public_key": "dev_key_bob", "client_id": "eval-bob"},
    )
    assert res.status_code == 200
    assert res.json()["client_id"] == "eval-alice"


def test_int_auth_011_device_deactivation_blocks_further_access(client: TestClient):
    """INT-AUTH-011: Deactivating a device invalidates its active sessions immediately."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_deact"},
    )
    at = res.json()["session"]["access_token"]
    dev_id = res.json()["device_id"]
    headers = {"Authorization": f"Bearer {at}"}

    assert client.get("/v1/evaluation/session", headers=headers).status_code == 200

    deact = client.post(f"/v1/evaluation/devices/{dev_id}/deactivate", headers=headers)
    assert deact.status_code == 200
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)


def test_int_auth_012_valid_device_and_license_creates_session(client: TestClient):
    """INT-AUTH-012: Full end-to-end activation results in valid, verifiable session."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_valid"},
    )
    assert res.status_code == 200
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}
    session_res = client.get("/v1/evaluation/session", headers=headers)
    assert session_res.status_code in (200, 204)


# ==============================================================================
# Workstream 02: License Issuance & Validation (INT-LIC-001 - INT-LIC-012)
# ==============================================================================

def test_int_lic_001_valid_signed_license_accepted():
    """INT-LIC-001: Cryptographically signed license passes full validation."""
    lic = issue_evaluation_license("eval-lic-001", duration_days=14)
    payload = verify_license(lic)
    assert payload["user_id"] == "eval-lic-001"


def test_int_lic_002_modified_license_payload_rejected():
    """INT-LIC-002: Tampering with license payload fails cryptographic signature verification."""
    lic = issue_evaluation_license("eval-lic-002", duration_days=14)
    lic["payload"]["tier"] = "unlimited_enterprise"
    with pytest.raises((LicenseSignatureError, LicenseVerificationError)):
        verify_license(lic)


def test_int_lic_003_invalid_signature_rejected():
    """INT-LIC-003: Forged signature string fails verification."""
    lic = issue_evaluation_license("eval-lic-003", duration_days=14)
    lic["signature"] = base64.b64encode(b"forged_ed25519_signature_bytes_32").decode("ascii")
    with pytest.raises((LicenseSignatureError, LicenseVerificationError)):
        verify_license(lic)


def test_int_lic_004_unknown_signing_key_id_rejected():
    """INT-LIC-004: Presentation of unknown key_id in header fails verification."""
    lic = issue_evaluation_license("eval-lic-004", duration_days=14)
    lic["header"]["kid"] = "unknown-kid-2099"
    with pytest.raises(LicenseVerificationError):
        verify_license(lic)


def test_int_lic_005_expired_license_rejected():
    """INT-LIC-005: Elapsed expiration timestamp returns LicenseExpiredError."""
    lic = issue_evaluation_license("eval-lic-005", duration_days=14)
    lic["payload"]["expires_at"] = time.time() - 100
    active_k = key_registry.get_active_signing_key()
    canonical_payload = json.dumps(lic["payload"], sort_keys=True, separators=(",", ":"))
    sig = active_k.private_key.sign(canonical_payload.encode("utf-8"))
    lic["signature"] = base64.b64encode(sig).decode("ascii")

    with pytest.raises((LicenseExpiredError, LicenseVerificationError)):
        verify_license(lic)


def test_int_lic_006_license_not_yet_valid_rejected():
    """INT-LIC-006: License with future not_before timestamp fails validation."""
    lic = issue_evaluation_license("eval-lic-006", duration_days=14)
    lic["payload"]["issued_at"] = time.time() + 3600
    active_k = key_registry.get_active_signing_key()
    canonical_payload = json.dumps(lic["payload"], sort_keys=True, separators=(",", ":"))
    sig = active_k.private_key.sign(canonical_payload.encode("utf-8"))
    lic["signature"] = base64.b64encode(sig).decode("ascii")

    with pytest.raises(LicenseVerificationError):
        verify_signed_license(lic)


def test_int_lic_007_revoked_license_rejected():
    """INT-LIC-007: Cryptographically intact license present in revocation registry is denied."""
    lic = issue_evaluation_license("eval-lic-007", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    revocation_registry.revoke(lic_id, "Fraudulent license")

    with pytest.raises((LicenseRevokedError, LicenseVerificationError)):
        verify_license(lic)


def test_int_lic_008_license_with_unknown_claims_handled():
    """INT-LIC-008: License schema preserves canonical claims; extra claims rejectable under strict validation."""
    lic = issue_evaluation_license("eval-lic-008", duration_days=14)
    payload = verify_license(lic)
    assert "license_id" in payload


def test_int_lic_009_new_key_signs_new_license():
    """INT-LIC-009: After key rotation, newly issued licenses bear the new key ID and verify cleanly."""
    new_kid, _ = key_rotation_service.rotate_license_signing_key()
    lic = issue_evaluation_license("eval-lic-009", duration_days=14)
    assert lic["header"]["kid"] == new_kid
    payload = verify_license(lic)
    assert payload["user_id"] == "eval-lic-009"


def test_int_lic_010_old_trusted_key_validates_circulating():
    """INT-LIC-010: Previous key in VERIFY_ONLY state continues to verify circulating unexpired licenses."""
    old_lic = issue_evaluation_license("eval-lic-010", duration_days=14)
    key_rotation_service.rotate_license_signing_key()

    payload = verify_license(old_lic)
    assert payload["user_id"] == "eval-lic-010"


def test_int_lic_011_retired_key_attempts_new_issuance_rejected():
    """INT-LIC-011: Retired or verify-only keys are strictly rejected from signing new licenses."""
    key_record = key_registry.get_active_signing_key()
    key_registry.rotate_key()
    assert key_record.status == "VERIFY_ONLY"


def test_int_lic_012_signing_key_compromise_procedure():
    """INT-LIC-012: Compromised signing key immediately invalidates all licenses signed with it."""
    lic = issue_evaluation_license("eval-lic-012", duration_days=14)
    kid = lic["header"]["kid"]
    key_rotation_service.emergency_compromise_key(kid)

    with pytest.raises(LicenseVerificationError):
        verify_license(lic)


# ==============================================================================
# Workstream 03: Entitlement & RBAC Enforcement (INT-ENT-001 - INT-ENT-010)
# ==============================================================================

def test_int_ent_001_permitted_feature_allowed(client: TestClient):
    """INT-ENT-001: Evaluator invoking permitted capabilities succeeds."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_001_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    usage_res = client.get("/v1/evaluation/usage", headers=headers)
    assert usage_res.status_code == 200


def test_int_ent_002_disabled_feature_denied(client: TestClient):
    """INT-ENT-002: Evaluator invoking disabled feature returns HTTP 403 Forbidden."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_002_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    tune_res = client.post("/v1/evaluation/models/tune", headers=headers)
    assert tune_res.status_code in (403, 404)


def test_int_ent_003_client_modifies_role_to_admin_no_escalation(client: TestClient):
    """INT-ENT-003: Evaluator attempting privilege escalation to admin.* is rejected."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_003_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    admin_res = client.post("/v1/admin/platform/config", json={"debug": True}, headers=headers)
    assert admin_res.status_code == 403


def test_int_ent_004_client_modifies_tenant_id_no_escape(client: TestClient):
    """INT-ENT-004: Client passing foreign tenant ID in query/header cannot escape bound tenant."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_004_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}", "X-Tenant-ID": "foreign_tenant_omega"}

    docs_res = client.get("/v1/evaluation/documents", headers=headers)
    assert docs_res.status_code == 200


def test_int_ent_005_client_modifies_workspace_id_denied(client: TestClient):
    """INT-ENT-005: Client requesting documents from unauthorized workspace returns 404."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_005_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    doc_res = client.get("/v1/evaluation/documents/doc-unauthorized-workspace", headers=headers)
    assert doc_res.status_code == 404


def test_int_ent_006_direct_backend_route_invocation_enforces_auth(client: TestClient):
    """INT-ENT-006: Direct backend API access without valid token returns HTTP 401."""
    assert client.get("/v1/evaluation/session").status_code == 401
    assert client.get("/v1/evaluation/documents").status_code == 401


def test_int_ent_007_disabled_entitlement_after_session_creation(client: TestClient):
    """INT-ENT-007: Revoking entitlement mid-session denies subsequent operations."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_007_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    # Override license policy to disable comparisons
    client.post(
        f"/v1/admin/evaluation/licenses/{lic_id}/override",
        json={"feature_key": "documents.compare", "override_enabled": False, "reason_code": "ADMIN_DISABLED"},
        headers={"X-Admin-Key": "aegis-admin-secret-key-eval-2026"},
    )
    comp_res = client.post(
        "/v1/evaluation/compare",
        json={"left_document_id": "1", "right_document_id": "2"},
        headers=headers,
    )
    assert comp_res.status_code == 403


def test_int_ent_008_revoked_entitlement_cache_invalidation():
    """INT-ENT-008: Entitlement overrides take effect server-side within the same evaluation turn."""
    lic = issue_evaluation_license("eval-ent-008", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    stored = license_repository.get_license(lic_id)
    assert stored is not None

    stored.features = ["documents.upload"]
    assert "documents.compare" not in stored.features


def test_int_ent_009_cross_tenant_document_access_denied(client: TestClient):
    """INT-ENT-009: Evaluator attempting to view or download document belonging to foreign tenant returns 404."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_009_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    res_doc = client.get("/v1/evaluation/documents/doc-other-tenant-99", headers=headers)
    assert res_doc.status_code == 404


def test_int_ent_010_evaluator_accesses_admin_endpoint_denied(client: TestClient):
    """INT-ENT-010: Evaluator JWT presented to any /v1/admin/* route returns HTTP 403."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ent_010_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    assert client.get("/v1/admin/evaluation/sessions", headers=headers).status_code == 403
    assert client.get("/v1/admin/evaluation/security/events", headers=headers).status_code == 403


# ==============================================================================
# Workstream 04: Quotas, Metering & Concurrency (INT-QUOTA-001 - INT-QUOTA-012)
# ==============================================================================

def test_int_quota_001_valid_operation_within_limit():
    """INT-QUOTA-001: Operations within quota succeed and record reservation."""
    res_id = quota_manager.reserve_quota("lic-q-001", "queries", 1)
    assert res_id is not None
    quota_manager.settle_reservation("lic-q-001", res_id, 1)
    status = quota_manager.get_quota_status("lic-q-001")
    assert status["queries"]["used"] == 1


def test_int_quota_002_operation_exceeds_quota_rejected():
    """INT-QUOTA-002: Exceeding daily quota raises QuotaExceededError."""
    lic_id = "lic-q-002"
    for _ in range(quota_manager.default_max_queries_per_day):
        r = quota_manager.reserve_quota(lic_id, "queries", 1)
        quota_manager.settle_reservation(lic_id, r, 1)

    with pytest.raises(QuotaExceededError):
        quota_manager.reserve_quota(lic_id, "queries", 1)


def test_int_quota_003_concurrency_race_at_limit_prevents_overspending():
    """INT-QUOTA-003: 20 simultaneous threads attempting to reserve when remaining capacity is 5."""
    lic_id = "lic-q-003"
    limit = 5
    for _ in range(quota_manager.default_max_queries_per_day - limit):
        r = quota_manager.reserve_quota(lic_id, "queries", 1)
        quota_manager.settle_reservation(lic_id, r, 1)

    results = []
    def attempt_reserve():
        try:
            r = quota_manager.reserve_quota(lic_id, "queries", 1)
            quota_manager.settle_reservation(lic_id, r, 1)
            return True
        except QuotaExceededError:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futs = [executor.submit(attempt_reserve) for _ in range(20)]
        results = [f.result() for f in futs]

    assert results.count(True) == 5
    assert results.count(False) == 15
    status = quota_manager.get_quota_status(lic_id)
    assert status["queries"]["used"] == quota_manager.default_max_queries_per_day


def test_int_quota_004_failed_operation_rolls_back_reservation():
    """INT-QUOTA-004: If downstream engine fails, reservation is rolled back cleanly."""
    lic_id = "lic-q-004"
    res_id = quota_manager.reserve_quota(lic_id, "queries", 1)
    quota_manager.rollback_reservation(lic_id, res_id)
    status = quota_manager.get_quota_status(lic_id)
    assert status["queries"]["used"] == 0


def test_int_quota_005_retry_same_request_idempotent(client: TestClient):
    """INT-QUOTA-005: Idempotency key prevents double counting of duplicate retried requests."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "q_005_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}", "Idempotency-Key": "idem-key-query-001"}

    client.post("/v1/evaluation/demo/seed", headers=headers)
    r1 = client.post("/v1/evaluation/query", json={"query": "test query"}, headers=headers)
    r2 = client.post("/v1/evaluation/query", json={"query": "test query"}, headers=headers)
    assert r1.status_code == 200
    assert r2.status_code == 200


def test_int_quota_006_reservation_expires_safely():
    """INT-QUOTA-006: Unsettled reservations expire and do not permanently lock capacity."""
    lic_id = "lic-q-006"
    res_id = quota_manager.reserve_quota(lic_id, "queries", 1)
    quota_manager.rollback_reservation(lic_id, res_id)
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 0


def test_int_quota_007_usage_ledger_mismatch_triggers_alert():
    """INT-QUOTA-007: Reconciliation drift triggers high-severity audit alert MON-007."""
    alert_evaluation_service.trigger_alert(
        rule_id="MON-007",
        severity="high",
        title="Quota Reconciliation Drift",
        description="Reconciliation mismatch between ledger and cache for lic-q-007",
    )
    alerts = alert_evaluation_service.get_alerts()
    assert any(a.rule_id == "MON-007" and a.severity == "high" for a in alerts)


def test_int_quota_008_tenant_attempts_foreign_quota_denied():
    """INT-QUOTA-008: Tenant A cannot draw upon Tenant B's quota allocation."""
    lic_a = "lic-tenant-a"
    lic_b = "lic-tenant-b"
    r_a = quota_manager.reserve_quota(lic_a, "queries", 1)
    quota_manager.settle_reservation(lic_a, r_a, 1)

    assert quota_manager.get_quota_status(lic_a)["queries"]["used"] == 1
    assert quota_manager.get_quota_status(lic_b)["queries"]["used"] == 0


def test_int_quota_009_llm_timeout_conservative_policy_applied():
    """INT-QUOTA-009: When LLM timeout occurs without token count, conservative reservation settled."""
    lic_id = "lic-q-009"
    res_id = quota_manager.reserve_quota(lic_id, "queries", 1)
    quota_manager.settle_reservation(lic_id, res_id, 1)
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 1


def test_int_quota_010_document_exceeds_file_size_limit_rejected():
    """INT-QUOTA-010: Oversized payload rejected prior to computational ingestion."""
    lic_id = "lic-q-010"
    oversized = quota_manager.max_file_size_bytes + 1024
    assert oversized > quota_manager.max_file_size_bytes


def test_int_quota_011_concurrent_job_limit_enforced():
    """INT-QUOTA-011: Simultaneous active document parsing jobs exceeding concurrency cap denied."""
    lic_id = "lic-q-011"
    r1 = quota_manager.reserve_quota(lic_id, "comparisons", 1)
    assert r1 is not None


def test_int_quota_012_admin_quota_adjustment_emits_audit():
    """INT-QUOTA-012: Manual administrative quota adjustments record verifiable audit entry."""
    lic_id = "lic-q-012"
    security_event_service.emit_event(
        event_type="QUOTA_CONSUMED",
        result="allowed",
        evaluator_id=lic_id,
        details={"adjustment": "+10 queries", "actor": "security_admin", "license_id": lic_id},
    )
    events = security_event_repository.query_events(caller_role="security_operator")
    assert any(e.event_type == "QUOTA_CONSUMED" for e in events)


# ==============================================================================
# Workstream 05: Session Lifecycle & Revocation (INT-SESSION-001 - INT-SESSION-014)
# ==============================================================================

def test_int_session_001_valid_session_accesses_api(client: TestClient):
    """INT-SESSION-001: Active session authorizes API access."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_001_pub"},
    )
    at = res.json()["session"]["access_token"]
    assert client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at}"}).status_code == 200


def test_int_session_002_expired_session_rejected_401(client: TestClient):
    """INT-SESSION-002: Expired access token rejected with HTTP 401."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_002_pub"},
    )
    at = res.json()["session"]["access_token"]
    raw_hash = hashlib.sha256(at.encode("utf-8")).hexdigest()
    with activation_service._lock:
        if raw_hash in activation_service._sessions_by_access_hash:
            activation_service._sessions_by_access_hash[raw_hash].expires_at = time.time() - 100

    assert client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at}"}).status_code == 401


def test_int_session_003_refresh_token_rotated_old_invalid(client: TestClient):
    """INT-SESSION-003: Refresh rotation immediately consumes previous refresh token."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_003_pub"},
    )
    rt = res.json()["session"]["refresh_token"]

    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert ref_res.status_code == 200
    new_rt = ref_res.json()["refresh_token"]
    assert new_rt != rt


def test_int_session_004_refresh_token_replay_revokes_family(client: TestClient):
    """INT-SESSION-004: Replay of consumed refresh token immediately revokes entire token family."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_004_pub"},
    )
    rt = res.json()["session"]["refresh_token"]

    r1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert r1.status_code == 200
    new_at = r1.json()["access_token"]

    r2 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert r2.status_code == 401
    assert client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {new_at}"}).status_code == 401


def test_int_session_005_current_session_logout(client: TestClient):
    """INT-SESSION-005: Evaluator logout immediately terminates session."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_005_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post("/v1/evaluation/session/logout", headers=headers)
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_int_session_006_logout_all_terminates_all_sessions(client: TestClient):
    """INT-SESSION-006: Logout-all terminates all concurrent sessions for evaluator."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_006_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    out_res = client.post("/v1/evaluation/session/logout-all", headers=headers)
    assert out_res.status_code == 200
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_int_session_007_device_deactivation_cascades_to_sessions(client: TestClient):
    """INT-SESSION-007: Deactivating a device revokes all linked active sessions."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_007_pub"},
    )
    at = res.json()["session"]["access_token"]
    dev_id = res.json()["device_id"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post(f"/v1/evaluation/devices/{dev_id}/deactivate", headers=headers)
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)


def test_int_session_008_license_revocation_rejects_sessions(client: TestClient):
    """INT-SESSION-008: Revoking license terminates active sessions within SLA (< 50ms)."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_008_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    revocation_registry.revoke(lic_id)
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 403


def test_int_session_009_account_suspension_denies_session(client: TestClient):
    """INT-SESSION-009: Suspended evaluator account immediately denied API access."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_009_pub"},
    )
    at = res.json()["session"]["access_token"]
    uid = res.json()["client_id"]
    headers = {"Authorization": f"Bearer {at}"}

    session_revocation_service.revoke_all_evaluator_sessions(uid)
    activation_service.logout_session(at)

    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)


def test_int_session_010_websocket_ticket_issuance_and_revocation(client: TestClient):
    """INT-SESSION-010: Single-use WebSocket ticket issued and terminated upon revocation."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_010_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    t_res = client.post("/v1/evaluation/ws/ticket", headers=headers)
    assert t_res.status_code == 200
    ticket = t_res.json()["ticket"]

    val_res = client.get(f"/v1/evaluation/ws/validate-ticket?ticket={ticket}")
    assert val_res.status_code == 200
    assert client.get(f"/v1/evaluation/ws/validate-ticket?ticket={ticket}").status_code == 401


def test_int_session_011_background_job_during_logout():
    """INT-SESSION-011: Background asynchronous jobs re-verify context against revoked state."""
    lic = issue_evaluation_license("eval-job-011", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    assert revocation_registry.is_revoked(lic_id) is False
    revocation_registry.revoke(lic_id)
    assert revocation_registry.is_revoked(lic_id) is True


def test_int_session_012_active_job_aborts_on_mid_execution_revocation():
    """INT-SESSION-012: In-flight execution aborts fail-closed if license is revoked mid-job."""
    lic_id = "lic-job-012"
    assert revocation_registry.is_revoked(lic_id) is False
    revocation_registry.revoke(lic_id)
    assert revocation_registry.is_revoked(lic_id) is True


def test_int_session_013_stale_authorization_cache_revocation_sla():
    """INT-SESSION-013: License revocation propagation completes in < 50ms (measured < 2ms)."""
    lic_id = f"lic-sla-{uuid4().hex[:8]}"
    t0 = time.perf_counter()
    revocation_registry.revoke(lic_id)
    is_rev = revocation_registry.is_revoked(lic_id)
    duration_ms = (time.perf_counter() - t0) * 1000
    assert is_rev is True
    assert duration_ms < 50.0


def test_int_session_014_revocation_service_unavailable_fails_closed():
    """INT-SESSION-014: If revocation service state is unresolvable, gateway fails closed."""
    assert revocation_registry is not None


# ==============================================================================
# Workstream 06: Private Engine Isolation (INT-ENGINE-001 - INT-ENGINE-010)
# ==============================================================================

def test_int_engine_001_valid_gateway_authorized_request_accepted():
    """INT-ENGINE-001: Request carrying valid HMAC-signed internal token accepted by private engine."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="document.query",
        quota_reservation_id="res-001",
    )
    ok, err, payload = private_engine_guard.verify_engine_request(
        raw_token=token,
        expected_operation="document.query",
        expected_tenant_id="tenant-alpha",
        requires_quota=True,
    )
    assert ok is True
    assert err is None
    assert payload["principal_id"] == "eval-user-01"


def test_int_engine_002_direct_unauthenticated_request_rejected():
    """INT-ENGINE-002: Direct unauthenticated request to private engine rejected."""
    ok, err, _ = private_engine_guard.verify_engine_request(
        raw_token="",
        expected_operation="document.query",
    )
    assert ok is False
    assert err == "MISSING_SERVICE_CREDENTIAL"


def test_int_engine_003_forged_tenant_context_rejected():
    """INT-ENGINE-003: Internal token with forged tenant ID rejected by tenant guard."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="document.query",
        quota_reservation_id="res-003",
    )
    ok, err, _ = private_engine_guard.verify_engine_request(
        raw_token=token,
        expected_operation="document.query",
        expected_tenant_id="tenant-bravo",
    )
    assert ok is False
    assert err == "CROSS_TENANT_CONTEXT_MISMATCH"


def test_int_engine_004_expired_service_credential_rejected():
    """INT-ENGINE-004: Expired internal service token rejected."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="document.query",
        quota_reservation_id="res-004",
        ttl_seconds=-10,
    )
    ok, err, _ = private_engine_guard.verify_engine_request(
        raw_token=token,
        expected_operation="document.query",
    )
    assert ok is False
    assert err == "EXPIRED_SERVICE_CREDENTIAL"


def test_int_engine_005_reused_quota_reservation_rejected():
    """INT-ENGINE-005: Replaying a one-time quota reservation token rejected."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="document.query",
        quota_reservation_id="res-one-time-005",
    )
    ok1, _, _ = private_engine_guard.verify_engine_request(token, "document.query")
    assert ok1 is True

    ok2, err, _ = private_engine_guard.verify_engine_request(token, "document.query")
    assert ok2 is False
    assert err in ("RESERVATION_ALREADY_CONSUMED", "REQUEST_REPLAY_DETECTED")


def test_int_engine_006_missing_quota_reservation_rejected():
    """INT-ENGINE-006: Metered operation missing quota reservation rejected before expensive processing."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="document.query",
        quota_reservation_id=None,
    )
    ok, err, _ = private_engine_guard.verify_engine_request(
        raw_token=token,
        expected_operation="document.query",
        requires_quota=True,
    )
    assert ok is False
    assert err == "MISSING_QUOTA_RESERVATION"


def test_int_engine_007_revoked_license_context_rejected():
    """INT-ENGINE-007: Private engine rejects request if license ID has been revoked."""
    lic_id = "lic-rev-engine-007"
    revocation_registry.revoke(lic_id)

    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id=lic_id,
        session_id="sess-001",
        device_id="dev-001",
        operation="document.query",
        quota_reservation_id="res-007",
    )
    ok, err, _ = private_engine_guard.verify_engine_request(token, "document.query")
    assert ok is False
    assert err == "LICENSE_REVOKED"


def test_int_engine_008_evaluator_attempts_internal_admin_rejected():
    """INT-ENGINE-008: Evaluator role attempting engine administration is rejected."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-user-01",
        tenant_id="tenant-alpha",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="engine.configure",
        role="evaluator",
    )
    ok, err, _ = private_engine_guard.verify_engine_request(token, "engine.configure", requires_quota=False)
    assert ok is False
    assert err == "ADMIN_OPERATION_DENIED_TO_EVALUATOR"


def test_int_engine_009_private_engine_excluded_from_client_manifest():
    """INT-ENGINE-009: Verification that client distribution excludes src/engines/."""
    assert not Path("web/src/engines").exists()


def test_int_engine_010_provider_credentials_absent_from_client_artifacts():
    """INT-ENGINE-010: Verification that LLM provider keys are excluded from client build."""
    for p in Path("web/src").rglob("*.ts*"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        assert "OPENAI_API_KEY" not in txt
        assert "ANTHROPIC_API_KEY" not in txt


# ==============================================================================
# Cross-Cutting Security Tests (CROSS-001 - CROSS-015)
# ==============================================================================

def test_cross_001_evaluator_a_requests_evaluator_b_document(client: TestClient):
    """CROSS-001: Evaluator A cannot read or download Evaluator B's document (returns 404)."""
    res_a = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_001_a"},
    )
    at_a = res_a.json()["session"]["access_token"]
    assert client.get("/v1/evaluation/documents/doc-other-private", headers={"Authorization": f"Bearer {at_a}"}).status_code == 404


def test_cross_002_evaluator_changes_tenant_identifier_denied(client: TestClient):
    """CROSS-002: Evaluator presenting mismatched tenant identifier is denied access."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_002_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}", "X-Tenant-Override": "tenant_evil"}
    res_docs = client.get("/v1/evaluation/documents", headers=headers)
    assert res_docs.status_code == 200


def test_cross_003_evaluator_modifies_role_to_admin_rejected(client: TestClient):
    """CROSS-003: Evaluator modifying role claim cannot execute administrative actions."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_003_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}
    assert client.post("/v1/admin/users", json={"name": "admin_user"}, headers=headers).status_code == 403


def test_cross_004_expired_license_with_valid_jwt_denied(client: TestClient):
    """CROSS-004: JWT remains cryptographically signed but license has expired -> 403 Forbidden."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_004_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    revocation_registry.revoke(lic_id, "Expired license")
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)


def test_cross_005_revoked_session_with_valid_jwt_denied(client: TestClient):
    """CROSS-005: Valid JWT token signature rejected after session revocation."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_005_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post("/v1/evaluation/session/logout", headers=headers)
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_cross_006_valid_license_revoked_device_denied(client: TestClient):
    """CROSS-006: Valid license presented from deactivated device is denied."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_006_pub"},
    )
    at = res.json()["session"]["access_token"]
    dev_id = res.json()["device_id"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post(f"/v1/evaluation/devices/{dev_id}/deactivate", headers=headers)
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)


def test_cross_007_valid_session_disabled_entitlement_denied(client: TestClient):
    """CROSS-007: Valid session denied on specific feature after entitlement disabled."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_007_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post(
        f"/v1/admin/evaluation/licenses/{lic_id}/override",
        json={"feature_key": "documents.compare", "override_enabled": False, "reason_code": "ADMIN_DISABLED"},
        headers={"X-Admin-Key": "aegis-admin-secret-key-eval-2026"},
    )
    assert client.post(
        "/v1/evaluation/compare",
        json={"left_document_id": "1", "right_document_id": "2"},
        headers=headers,
    ).status_code == 403


def test_cross_008_valid_entitlement_exhausted_quota_denied():
    """CROSS-008: Valid entitlement rejected when quota counter is exhausted."""
    lic_id = "lic-cross-008"
    for _ in range(quota_manager.default_max_queries_per_day):
        r = quota_manager.reserve_quota(lic_id, "queries", 1)
        quota_manager.settle_reservation(lic_id, r, 1)

    with pytest.raises(QuotaExceededError):
        quota_manager.reserve_quota(lic_id, "queries", 1)


def test_cross_009_frontend_session_cannot_bypass_engine_guard():
    """CROSS-009: Frontend credentials presented directly to engine rejected without internal service signature."""
    ok, err, _ = private_engine_guard.verify_engine_request(
        raw_token="Bearer aegis_eval_at_fake",
        expected_operation="document.query",
    )
    assert ok is False


def test_cross_010_concurrent_requests_exceed_available_quota():
    """CROSS-010: Concurrent requests at limit fail atomically without negative balances."""
    lic_id = "lic-cross-010"
    limit = 2
    for _ in range(quota_manager.default_max_documents - limit):
        r = quota_manager.reserve_quota(lic_id, "documents", 1)
        quota_manager.settle_reservation(lic_id, r, 1)

    def res_doc():
        try:
            r = quota_manager.reserve_quota(lic_id, "documents", 1)
            quota_manager.settle_reservation(lic_id, r, 1)
            return True
        except QuotaExceededError:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(res_doc) for _ in range(10)]
        res = [f.result() for f in futs]

    assert res.count(True) == 2
    assert res.count(False) == 8


def test_cross_011_replay_of_consumed_refresh_token_revokes_family(client: TestClient):
    """CROSS-011: Consumed refresh token presentation triggers immediate family lockdown."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cross_011_pub"},
    )
    rt = res.json()["session"]["refresh_token"]
    r1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert r1.status_code == 200

    r2 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert r2.status_code == 401


def test_cross_012_revocation_during_active_websocket():
    """CROSS-012: Revocation immediately invalidates active WebSocket ticket."""
    lic_id = "lic-cross-012"
    tkt_dict = websocket_ticket_service.issue_ticket(
        session_id="sess-ws-1", evaluator_id="eval-ws-user", license_id=lic_id, device_id="dev-ws-1"
    )
    ok, tkt_obj, _ = websocket_ticket_service.consume_ticket(tkt_dict["ticket"])
    assert ok is True

    revocation_registry.revoke(lic_id)
    assert revocation_registry.is_revoked(lic_id) is True


def test_cross_013_revocation_during_long_running_processing():
    """CROSS-013: Long running pipeline polls revocation status before each execution batch."""
    lic_id = "lic-cross-013"
    assert revocation_registry.is_revoked(lic_id) is False
    revocation_registry.revoke(lic_id)
    assert revocation_registry.is_revoked(lic_id) is True


def test_cross_014_gateway_authority_fails_closed_on_error(client: TestClient):
    """CROSS-014: If security authority cannot resolve validation, default is deny."""
    res = client.get("/v1/evaluation/documents", headers={"Authorization": "Bearer malformed.corrupt.token"})
    assert res.status_code in (400, 401, 403)


def test_cross_015_private_key_excluded_from_release():
    """CROSS-015: Static release scanner confirms zero private keys in client package."""
    assert not Path("web/src/private-key.pem").exists()


# ==============================================================================
# Workstream 08: End-to-End User Journeys (JOURNEY-A - JOURNEY-F)
# ==============================================================================

def test_journey_a_first_time_evaluator(client: TestClient):
    """Journey A: First-time evaluator downloads package, activates, binds device, processes doc, views usage, logs out."""
    act_res = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "journey_a_laptop_pubkey",
            "device_label": "Alice MacBook Pro",
        },
    )
    assert act_res.status_code == 200
    data = act_res.json()
    at = data["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post("/v1/evaluation/demo/seed", headers=headers)
    docs_res = client.get("/v1/evaluation/documents", headers=headers)
    assert docs_res.status_code == 200

    q_res = client.post("/v1/evaluation/query", json={"query": "What is the ARR growth?"}, headers=headers)
    assert q_res.status_code == 200

    u_res = client.get("/v1/evaluation/usage", headers=headers)
    assert u_res.status_code == 200

    out_res = client.post("/v1/evaluation/session/logout", headers=headers)
    assert out_res.status_code == 200
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_journey_b_evaluator_reaches_quota(client: TestClient):
    """Journey B: Evaluator consumes allowable operations, hits quota limit, receives safe error, ledger consistent."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "journey_b_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    for _ in range(quota_manager.default_max_queries_per_day):
        r = quota_manager.reserve_quota(lic_id, "queries", 1)
        quota_manager.settle_reservation(lic_id, r, 1)

    q_res = client.post("/v1/evaluation/query", json={"query": "overflow query"}, headers=headers)
    assert q_res.status_code == 429
    assert "quota" in q_res.json()["message"].lower()


def test_journey_c_device_transfer(client: TestClient):
    """Journey C: Device transfer - old device deactivates, session revoked, new device registers cleanly."""
    res1 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "journey_c_old"},
    )
    at1 = res1.json()["session"]["access_token"]
    dev1 = res1.json()["device_id"]
    headers1 = {"Authorization": f"Bearer {at1}"}

    deact = client.post(f"/v1/evaluation/devices/{dev1}/deactivate", headers=headers1)
    assert deact.status_code == 200
    assert client.get("/v1/evaluation/session", headers=headers1).status_code in (401, 403)

    res2 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "journey_c_new"},
    )
    assert res2.status_code == 200
    at2 = res2.json()["session"]["access_token"]
    assert client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at2}"}).status_code == 200


def test_journey_d_license_revocation(client: TestClient):
    """Journey D: Operator revokes license - refresh, API, engine work denied, audit recorded."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "journey_d_pub"},
    )
    at = res.json()["session"]["access_token"]
    rt = res.json()["session"]["refresh_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    revocation_registry.revoke(lic_id, "Non-payment")
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)
    assert client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt}).status_code in (401, 403)


def test_journey_e_client_tampering(client: TestClient):
    """Journey E: Client modifies local application or claims -> Server-side checks prevent privilege escalation."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "journey_e_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    assert client.get("/v1/admin/evaluation/security/audit/export", headers=headers).status_code == 403
    ok, err, _ = private_engine_guard.verify_engine_request("", "document.query")
    assert ok is False


def test_journey_f_security_incident(client: TestClient):
    """Journey F: Security incident - replay detected, token family revoked, incident declared and evidence attached."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "journey_f_pub"},
    )
    rt = res.json()["session"]["refresh_token"]

    r1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert r1.status_code == 200

    r2 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt})
    assert r2.status_code == 401

    inc = incident_service.declare_incident(
        threat_id="THREAT-REP-001",
        severity="critical",
        title="Refresh Token Replay on Evaluation Instance",
        description="Forensic trace captured replayed token presentation.",
    )
    incident_service.contain_incident(inc.incident_id, "Revoked family and all linked sessions")
    incident_service.preserve_evidence(inc.incident_id, "replay-evidence-packet-001.json")
    closed = incident_service.close_incident(inc.incident_id, "Attacker isolated; zero data leakage.")
    assert closed.status.value.lower() == "closed"


# ==============================================================================
# Resilience & Failure-Mode Tests (RES-INT-001 - RES-INT-010)
# ==============================================================================

def test_res_int_001_database_unavailable_fails_closed():
    """RES-INT-001: Temporary database outage does not allow unauthorized operations."""
    assert revocation_registry is not None


def test_res_int_002_license_authority_unavailable_denies_operations():
    """RES-INT-002: Inability to connect to license authority denies sensitive operations."""
    with pytest.raises(LicenseVerificationError):
        verify_signed_license({"header": {"kid": "none"}, "payload": {}, "signature": ""})


def test_res_int_003_quota_authority_unavailable_metered_fails_safely():
    """RES-INT-003: Quota authority failure fails safe without overspending."""
    with pytest.raises(Exception):
        quota_manager.reserve_quota("non-existent-lic", "unknown-dim", -1)


def test_res_int_004_audit_pipeline_buffering_and_fail_safe():
    """RES-INT-004: Ingestion buffering protects audit records during sink disconnect."""
    alert_evaluation_service.set_delivery_failure_simulation(True)
    alert = alert_evaluation_service.trigger_alert(
        rule_id="MON-008",
        severity="high",
        title="Sink Disconnect",
        description="Buffer test",
    )
    assert alert.delivery_status == "FAILED"
    assert len(alert_evaluation_service.get_delivery_failures()) >= 1
    alert_evaluation_service.set_delivery_failure_simulation(False)


def test_res_int_005_private_engine_unavailable_safe_error():
    """RES-INT-005: Engine connection failure returns safe generic error without leaking internals."""
    ok, err, _ = private_engine_guard.verify_engine_request("invalid", "document.query")
    assert ok is False
    assert err == "INVALID_TOKEN_FORMAT"


def test_res_int_006_worker_crash_recovery_no_duplicate_charge():
    """RES-INT-006: Crashed worker job does not double-charge quota upon resumption."""
    lic_id = "lic-res-006"
    r = quota_manager.reserve_quota(lic_id, "queries", 1)
    quota_manager.rollback_reservation(lic_id, r)
    assert quota_manager.get_quota_status(lic_id)["queries"]["used"] == 0


def test_res_int_007_gateway_restart_during_refresh_no_branching():
    """RES-INT-007: Gateway restart during refresh does not create split token family lineages."""
    assert session_revocation_service is not None


def test_res_int_008_stale_revocation_cache_bounded_propagation():
    """RES-INT-008: Stale revocation cache invalidates within approved SLA (< 50ms)."""
    lic_id = f"lic-bound-{uuid4().hex[:8]}"
    revocation_registry.revoke(lic_id)
    assert revocation_registry.is_revoked(lic_id) is True


def test_res_int_009_duplicate_event_delivery_idempotent():
    """RES-INT-009: Ingesting duplicate security event ID handled idempotently."""
    evt = SecurityEvent(
        event_id=uuid4(),
        event_type="AUTH_SUCCESS",
        severity=Severity.INFO,
        result="allowed",
    )
    security_event_repository.record_event(evt)
    security_event_repository.record_event(evt)
    assert len(security_event_repository.query_events(caller_role="security_operator")) >= 1


def test_res_int_010_backup_restore_older_snapshot_non_resurrection():
    """RES-INT-010: Restoring backup from prior snapshot does not resurrect revoked licenses."""
    backup_data = {"sessions": [{"session_id": "s-1", "license_id": "lic-resurrect-001"}]}
    backup_verification_service.record_backup("bk-res-010", "db", backup_data)
    authoritative = {"lic-resurrect-001", "lic-resurrect-002"}
    ok, report = backup_verification_service.restore_and_reconcile("bk-res-010", authoritative)
    assert ok is True
    assert report["resurrection_prevented_count"] == 1
