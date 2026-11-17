"""
Consolidated Security Audit: Private Engine Isolation & Boundary Defense (SEC-003, SEC-016)
"""

import json
from pathlib import Path
import pytest
from src.security.private_engine_guard import private_engine_guard
from services.evaluation_gateway.revocation import registry as revocation_registry


def test_engine_001_gateway_authorized_token_accepted():
    """SEC-016.1: Gateway-issued HMAC token is accepted by Private Engine Guard."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-001",
        tenant_id="tenant-001",
        license_id="lic-001",
        session_id="sess-001",
        device_id="dev-001",
        operation="documents.compare",
        quota_reservation_id="res-eng-001",
    )
    ok, err, ctx = private_engine_guard.verify_engine_request(token, expected_operation="documents.compare")
    assert ok is True
    assert err is None
    assert ctx["license_id"] == "lic-001"
    assert ctx["operation"] == "documents.compare"


def test_engine_002_unauthenticated_direct_call_rejected():
    """SEC-016.2: Direct call to private engine without HMAC token returns HTTP 401."""
    ok, err, _ = private_engine_guard.verify_engine_request("", expected_operation="documents.compare")
    assert ok is False
    assert "MISSING_SERVICE_CREDENTIAL" in err


def test_engine_003_tampered_payload_or_signature_rejected():
    """SEC-016.3: Modified internal token fails cryptographic HMAC validation."""
    token = private_engine_guard.create_authorized_token(
        principal_id="eval-003",
        tenant_id="tenant-003",
        license_id="lic-003",
        session_id="sess-003",
        device_id="dev-003",
        operation="documents.query",
        quota_reservation_id="res-eng-003",
    )
    doc = json.loads(token)
    doc["signature"] = "forged_hmac_signature_hex"
    tampered_token = json.dumps(doc)
    ok, err, _ = private_engine_guard.verify_engine_request(tampered_token, expected_operation="documents.query")
    assert ok is False
    assert "TAMPERED_SERVICE_SIGNATURE" in err


def test_engine_004_reused_quota_reservation_rejected():
    """SEC-016.4: Presenting an already-consumed quota reservation ID is rejected."""
    token1 = private_engine_guard.create_authorized_token(
        principal_id="eval-004",
        tenant_id="tenant-004",
        license_id="lic-004",
        session_id="sess-004",
        device_id="dev-004",
        operation="documents.query",
        quota_reservation_id="res-single-use-004",
    )
    ok1, _, _ = private_engine_guard.verify_engine_request(token1, expected_operation="documents.query")
    assert ok1 is True

    # Attempt second request reusing identical reservation ID
    token2 = private_engine_guard.create_authorized_token(
        principal_id="eval-004",
        tenant_id="tenant-004",
        license_id="lic-004",
        session_id="sess-004",
        device_id="dev-004",
        operation="documents.query",
        quota_reservation_id="res-single-use-004",
    )
    ok2, err2, _ = private_engine_guard.verify_engine_request(token2, expected_operation="documents.query")
    assert ok2 is False
    assert "RESERVATION_ALREADY_CONSUMED" in err2


def test_engine_005_revoked_license_denied_engine_execution():
    """SEC-016.5: Engine execution immediately denied if target license is revoked."""
    lic_id = "lic-rev-engine-005"
    revocation_registry.revoke(lic_id, "Critical compromise")

    token = private_engine_guard.create_authorized_token(
        principal_id="eval-005",
        tenant_id="tenant-005",
        license_id=lic_id,
        session_id="sess-005",
        device_id="dev-005",
        operation="documents.query",
        quota_reservation_id="res-eng-005",
    )
    ok, err, _ = private_engine_guard.verify_engine_request(token, expected_operation="documents.query")
    assert ok is False
    assert "LICENSE_REVOKED" in err


def test_engine_006_no_private_engine_code_in_client_artifacts():
    """SEC-003.1: Static verification confirms private engine directory absent from web client."""
    assert not Path("web/src/private_engine").exists()
    assert not Path("web/src/core/private_engine").exists()
    assert not Path("web/public/engine").exists()
