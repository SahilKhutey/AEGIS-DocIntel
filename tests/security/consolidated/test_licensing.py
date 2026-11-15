"""
Consolidated Security Audit: Cryptographic License Validation & Revocation (SEC-007, SEC-008)
"""

import pytest
from services.evaluation_gateway.license import (
    issue_evaluation_license,
    verify_license,
    LicenseSignatureError,
    LicenseVerificationError,
    LicenseRevokedError,
)
from services.evaluation_gateway.revocation import registry as revocation_registry
from src.services.security_operations.key_rotation_service import key_rotation_service


def test_lic_001_valid_ed25519_signed_license_verified():
    """SEC-007.1: Valid Ed25519 signed license passes authoritative verification."""
    lic = issue_evaluation_license("eval-valid-001", duration_days=14)
    payload = verify_license(lic)
    assert payload["sub"] == "eval-valid-001"
    assert payload["tier"] == "evaluation"


def test_lic_002_tampered_license_payload_fails_signature():
    """SEC-007.2: Tampering with license payload attributes triggers LicenseSignatureError."""
    lic = issue_evaluation_license("eval-tamper-002", duration_days=14)
    lic["payload"]["tier"] = "enterprise_unlimited"
    with pytest.raises(LicenseSignatureError):
        verify_license(lic)


def test_lic_003_corrupted_signature_fails_validation():
    """SEC-007.3: Forged or corrupted signature string triggers LicenseSignatureError."""
    lic = issue_evaluation_license("eval-tamper-003", duration_days=14)
    lic["signature"] = "corrupted_signature_bytes_base64=="
    with pytest.raises(LicenseSignatureError):
        verify_license(lic)


def test_lic_004_unknown_key_id_rejected():
    """SEC-007.4: Unknown signing key ID rejected with LicenseVerificationError."""
    lic = issue_evaluation_license("eval-tamper-004", duration_days=14)
    lic["header"]["kid"] = "unknown-unregistered-kid-2099"
    with pytest.raises(LicenseVerificationError):
        verify_license(lic)


def test_lic_005_revoked_license_denied_access():
    """SEC-008.1: License recorded in revocation registry is strictly denied."""
    lic = issue_evaluation_license("eval-revoked-005", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    revocation_registry.revoke(lic_id, "Non-payment violation")

    with pytest.raises(LicenseRevokedError):
        verify_license(lic)


def test_lic_006_key_rotation_and_emergency_compromise():
    """SEC-007.5: Key rotation preserves existing licenses; key compromise immediately invalidates."""
    old_lic = issue_evaluation_license("eval-rot-006", duration_days=14)
    new_kid, _ = key_rotation_service.rotate_license_signing_key()
    new_lic = issue_evaluation_license("eval-rot-007", duration_days=14)

    # Both old and new licenses verify cleanly
    assert verify_license(old_lic)["sub"] == "eval-rot-006"
    assert verify_license(new_lic)["sub"] == "eval-rot-007"

    # Emergency compromise of old key invalidates old license
    old_kid = old_lic["header"]["kid"]
    key_rotation_service.emergency_compromise_key(old_kid)

    with pytest.raises(LicenseVerificationError):
        verify_license(old_lic)

    # New license remains unaffected
    assert verify_license(new_lic)["sub"] == "eval-rot-007"
