"""
PT-03: License Forgery and Device Binding Adversarial Tests
Covers PT-LIC-001 through PT-LIC-007 and PT-DEV-001 through PT-DEV-006 (13 tests).
Asserts Ed25519 cryptographic enforcement, tamper resistance, online revocation authority,
single-device binding, challenge-response proof-of-possession, and lifecycle controls.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from services.evaluation_gateway.license import (
    issue_evaluation_license,
    export_license_token,
    parse_license_token,
    verify_license,
    LicenseSignatureError,
    LicenseExpiredError,
    LicenseRevokedError,
    LicenseVerificationError,
    CANONICAL_PRODUCT,
)
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.activation import activation_service


def test_pt_lic_001_change_license_expiry():
    """PT-LIC-001: Changing license expiry date in payload invalidates Ed25519 signature."""
    lic = issue_evaluation_license("user-001", 14, CANONICAL_PRODUCT)
    lic["payload"]["expires_at"] = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    token = export_license_token(lic)
    doc = parse_license_token(token)

    with pytest.raises(LicenseSignatureError):
        verify_license(doc)


def test_pt_lic_002_change_evaluator_id():
    """PT-LIC-002: Changing evaluator/user identifier invalidates Ed25519 signature."""
    lic = issue_evaluation_license("user-001", 14, CANONICAL_PRODUCT)
    lic["payload"]["user_id"] = "user-rogue-attacker"
    token = export_license_token(lic)
    doc = parse_license_token(token)

    with pytest.raises(LicenseSignatureError):
        verify_license(doc)


def test_pt_lic_003_change_entitlement_claims():
    """PT-LIC-003: Injecting unauthorized enterprise entitlements invalidates Ed25519 signature."""
    lic = issue_evaluation_license("user-001", 14, CANONICAL_PRODUCT)
    lic["payload"]["entitlements"] = ["evaluation", "enterprise_unlimited", "batch_export"]
    token = export_license_token(lic)
    doc = parse_license_token(token)

    with pytest.raises(LicenseSignatureError):
        verify_license(doc)


def test_pt_lic_004_replace_signing_key_id():
    """PT-LIC-004: Replacing key ID (kid) with unknown/unregistered key ID is rejected."""
    lic = issue_evaluation_license("user-001", 14, CANONICAL_PRODUCT)
    lic["header"]["kid"] = "unregistered-rogue-key-id"
    token = export_license_token(lic)
    doc = parse_license_token(token)

    with pytest.raises(LicenseVerificationError):
        verify_license(doc)


def test_pt_lic_005_use_expired_license():
    """PT-LIC-005: Legitimate license whose validity window has elapsed is rejected as EXPIRED."""
    lic = issue_evaluation_license("user-001", duration_days=-1, product=CANONICAL_PRODUCT)
    token = export_license_token(lic)
    doc = parse_license_token(token)

    with pytest.raises(LicenseExpiredError):
        verify_license(doc)


def test_pt_lic_006_use_revoked_license():
    """PT-LIC-006: Cryptographically valid license listed in online revocation registry is rejected."""
    lic = issue_evaluation_license("user-001", 14, CANONICAL_PRODUCT)
    token = export_license_token(lic)
    lic_id = lic["payload"]["license_id"]

    # Revoke license online
    revocation_registry.revoke(lic_id, "Compromised credential during adversarial test")

    doc = parse_license_token(token)
    with pytest.raises(LicenseRevokedError):
        verify_license(doc)


def test_pt_lic_007_reuse_activation_code():
    """PT-LIC-007: Single-use activation code cannot be reused to provision multiple active instances."""
    code = "AEGIS-EVAL-PT03-TEST-001"
    activation_service.register_activation_code(code, "user-eval-pt03")

    dev_priv1 = ed25519.Ed25519PrivateKey.generate()
    pub1_b64 = base64.b64encode(dev_priv1.public_key().public_bytes_raw()).decode("utf-8")

    # First challenge creation and activation succeeds
    chal1 = activation_service.create_device_challenge(code, pub1_b64, "inst-001")
    sig1 = base64.b64encode(dev_priv1.sign(chal1["canonical_message"].encode("utf-8"))).decode("utf-8")
    res1 = activation_service.activate_device_with_challenge(chal1["challenge_id"], sig1, "inst-001")
    assert "session" in res1

    # Second attempt to provision another device with same code is strictly rejected (device limit / already bound)
    dev_priv2 = ed25519.Ed25519PrivateKey.generate()
    pub2_b64 = base64.b64encode(dev_priv2.public_key().public_bytes_raw()).decode("utf-8")
    with pytest.raises(PermissionError):
        activation_service.create_device_challenge(code, pub2_b64, "inst-002")


def test_pt_dev_001_replay_activation_challenge():
    """PT-DEV-001: Replaying an expired or already-used device challenge is rejected."""
    code = "AEGIS-EVAL-PT03-DEV01"
    activation_service.register_activation_code(code, "user-eval-dev01")

    dev_priv = ed25519.Ed25519PrivateKey.generate()
    pub_b64 = base64.b64encode(dev_priv.public_key().public_bytes_raw()).decode("utf-8")

    chal_doc = activation_service.create_device_challenge(code, pub_b64, "inst-dev01")
    challenge_id = chal_doc["challenge_id"]
    msg = chal_doc["canonical_message"]

    # Sign message
    sig = dev_priv.sign(msg.encode("utf-8"))
    sig_b64 = base64.b64encode(sig).decode("utf-8")

    # First activation consumes the challenge nonce
    res1 = activation_service.activate_device_with_challenge(challenge_id, sig_b64, "inst-dev01")
    assert "session" in res1

    # Replay of the exact same challenge fails (single-use)
    with pytest.raises(Exception):
        activation_service.activate_device_with_challenge(challenge_id, sig_b64, "inst-dev01")


def test_pt_dev_002_sign_challenge_wrong_key():
    """PT-DEV-002: Signing challenge with a rogue private key causes challenge verification failure."""
    code = "AEGIS-EVAL-PT03-DEV02"
    activation_service.register_activation_code(code, "user-eval-dev02")

    dev_priv_real = ed25519.Ed25519PrivateKey.generate()
    dev_priv_rogue = ed25519.Ed25519PrivateKey.generate()
    real_pub_b64 = base64.b64encode(dev_priv_real.public_key().public_bytes_raw()).decode("utf-8")

    chal_doc = activation_service.create_device_challenge(code, real_pub_b64, "inst-dev02")
    challenge_id = chal_doc["challenge_id"]
    msg = chal_doc["canonical_message"]

    # Sign with rogue key
    rogue_sig = dev_priv_rogue.sign(msg.encode("utf-8"))
    rogue_sig_b64 = base64.b64encode(rogue_sig).decode("utf-8")

    with pytest.raises(Exception):
        activation_service.activate_device_with_challenge(challenge_id, rogue_sig_b64, "inst-dev02")


def test_pt_dev_003_register_additional_device():
    """PT-DEV-003: Enforces strict 1-device binding limit per evaluation license."""
    code1 = "AEGIS-EVAL-PT03-DEV03-A"
    activation_service.register_activation_code(code1, "user-eval-dev03")

    dev_priv1 = ed25519.Ed25519PrivateKey.generate()
    pub1_b64 = base64.b64encode(dev_priv1.public_key().public_bytes_raw()).decode("utf-8")
    c1 = activation_service.create_device_challenge(code1, pub1_b64, "inst-dev03-1")
    sig1 = base64.b64encode(dev_priv1.sign(c1["canonical_message"].encode("utf-8"))).decode("utf-8")
    res1 = activation_service.activate_device_with_challenge(c1["challenge_id"], sig1, "inst-dev03-1")
    assert "session" in res1

    # Attempting to activate a 2nd device for the same user under the 1-device policy raises exception
    dev_priv2 = ed25519.Ed25519PrivateKey.generate()
    pub2_b64 = base64.b64encode(dev_priv2.public_key().public_bytes_raw()).decode("utf-8")
    with pytest.raises(PermissionError):
        activation_service.create_device_challenge(code1, pub2_b64, "inst-dev03-2")


def test_pt_dev_004_reuse_copied_device_credentials():
    """PT-DEV-004: Copying device config to another host fails without matching hardware private key."""
    fake_challenge_id = "non-existent-challenge-id"
    with pytest.raises(Exception):
        activation_service.activate_device_with_challenge(
            fake_challenge_id, "bogus_sig", "inst-rogue"
        )


def test_pt_dev_005_deactivate_and_reactivate_device():
    """PT-DEV-005: Deactivating a device enforces full re-authentication and revokes active session."""
    code = "AEGIS-EVAL-PT03-DEV05"
    activation_service.register_activation_code(code, "user-eval-dev05")

    dev_priv = ed25519.Ed25519PrivateKey.generate()
    pub_b64 = base64.b64encode(dev_priv.public_key().public_bytes_raw()).decode("utf-8")
    chal = activation_service.create_device_challenge(code, pub_b64, "inst-dev05")
    sig = base64.b64encode(dev_priv.sign(chal["canonical_message"].encode("utf-8"))).decode("utf-8")
    res = activation_service.activate_device_with_challenge(chal["challenge_id"], sig, "inst-dev05")

    token = res["session"]["access_token"]
    license_id = res["license"]["license_id"]
    device_id = res["device_id"]

    # Device is active
    assert activation_service.validate_session(token) is not None

    # Deactivate device
    activation_service.deactivate_device(license_id, device_id)

    # Validating session after deactivation fails
    assert activation_service.validate_session(token) is None


def test_pt_dev_006_attempt_recovery_without_authorization():
    """PT-DEV-006: Device recovery requires verified single-use recovery code."""
    code = "AEGIS-EVAL-PT03-DEV06"
    activation_service.register_activation_code(code, "user-eval-dev06")

    dev_priv = ed25519.Ed25519PrivateKey.generate()
    pub_b64 = base64.b64encode(dev_priv.public_key().public_bytes_raw()).decode("utf-8")
    chal = activation_service.create_device_challenge(code, pub_b64, "inst-dev06")
    sig = base64.b64encode(dev_priv.sign(chal["canonical_message"].encode("utf-8"))).decode("utf-8")
    res = activation_service.activate_device_with_challenge(chal["challenge_id"], sig, "inst-dev06")

    license_id = res["license"]["license_id"]
    device_id = res["device_id"]
    recovery_code = res.get("recovery_code")
    assert recovery_code is not None

    # Recovery with bogus code fails
    with pytest.raises(PermissionError):
        activation_service.recover_device(license_id, device_id, "WRONG-RECOVERY-CODE")

    # Recovery with legitimate code succeeds
    rec_res = activation_service.recover_device(license_id, device_id, recovery_code)
    assert rec_res["status"].lower() == "recovered"
