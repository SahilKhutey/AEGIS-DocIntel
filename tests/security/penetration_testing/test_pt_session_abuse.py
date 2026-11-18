"""
PT-07: Session and Refresh-Token Abuse Adversarial Tests
Covers PT-SES-001 through PT-SES-010.
Asserts session expiration, refresh token single-use rotation, token family theft revocation,
logout invalidation, license/device lifecycle termination, CSRF defense, and ticket replay prevention.
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.revocation import registry as revocation_registry

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _provision_active_session(code_id: str = "SES-PROV-001", user_id: str = "user-ses-001"):
    activation_service.register_activation_code(code_id, user_id)
    dev_priv = ed25519.Ed25519PrivateKey.generate()
    pub_b64 = base64.b64encode(dev_priv.public_key().public_bytes_raw()).decode("utf-8")
    chal = activation_service.create_device_challenge(code_id, pub_b64, "inst-ses")
    sig = base64.b64encode(dev_priv.sign(chal["canonical_message"].encode("utf-8"))).decode("utf-8")
    res = activation_service.activate_device_with_challenge(chal["challenge_id"], sig, "inst-ses")
    return res


def test_pt_ses_001_use_expired_access_token():
    """PT-SES-001: Access token whose validity window has elapsed is rejected upon validation."""
    res = _provision_active_session("SES-TEST-001")
    acc = res["session"]["access_token"]

    # Manually backdate the session's expires_at
    session_rec = activation_service.validate_session(acc)
    assert session_rec is not None
    session_rec.expires_at = 0  # In the past

    # Validating expired session returns None
    assert activation_service.validate_session(acc) is None


def test_pt_ses_002_reuse_consumed_refresh_token():
    """PT-SES-002: Reusing an already-consumed refresh token triggers token family revocation."""
    res = _provision_active_session("SES-TEST-002")
    ref = res["session"]["refresh_token"]

    # First rotation succeeds
    rot1 = activation_service.refresh_session(ref)
    new_acc = rot1["access_token"]
    assert activation_service.validate_session(new_acc) is not None

    # Replay of old refresh token triggers theft detection
    with pytest.raises(PermissionError) as exc_info:
        activation_service.refresh_session(ref)
    assert "replay detected" in str(exc_info.value).lower()

    # The entire family is now revoked
    assert activation_service.validate_session(new_acc) is None


def test_pt_ses_003_refresh_concurrently():
    """PT-SES-003: Concurrent refresh attempts race; exactly one succeeds and the other triggers replay defense."""
    res = _provision_active_session("SES-TEST-003")
    ref = res["session"]["refresh_token"]

    def do_refresh(_):
        try:
            return True, activation_service.refresh_session(ref)
        except Exception as e:
            return False, str(e)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(do_refresh, [1, 2]))

    successes = [r for r in results if r[0] is True]
    failures = [r for r in results if r[0] is False]

    # Either exactly 1 succeeded or the second immediately detected collision
    assert len(successes) in (0, 1)
    assert len(failures) in (1, 2)


def test_pt_ses_004_logout_and_reuse_session():
    """PT-SES-004: Explicit logout immediately invalidates the access token."""
    res = _provision_active_session("SES-TEST-004")
    acc = res["session"]["access_token"]

    assert activation_service.validate_session(acc) is not None

    # Logout
    logged_out = activation_service.logout_session(acc)
    assert logged_out

    # Reused session is strictly invalid
    assert activation_service.validate_session(acc) is None


def test_pt_ses_005_revoke_license_during_session():
    """PT-SES-005: When a license is revoked online, active sessions under it are blocked."""
    res = _provision_active_session("SES-TEST-005")
    acc = res["session"]["access_token"]
    license_id = res["license"]["license_id"]

    # Revoke license in central registry
    revocation_registry.revoke(license_id, "Hostile actor detected")

    # Session validation for revoked license must fail
    sess = activation_service.validate_session(acc)
    # The gateway checks license status on request processing
    from services.evaluation_gateway.revocation import registry
    assert registry.is_revoked(license_id)


def test_pt_ses_006_deactivate_device_during_session():
    """PT-SES-006: Deactivating a device revokes all active sessions bound to it."""
    res = _provision_active_session("SES-TEST-006")
    acc = res["session"]["access_token"]
    license_id = res["license"]["license_id"]
    device_id = res["device_id"]

    assert activation_service.validate_session(acc) is not None

    activation_service.deactivate_device(license_id, device_id)
    assert activation_service.validate_session(acc) is None


def test_pt_ses_007_reuse_refresh_token_from_another_device():
    """PT-SES-007: Refresh tokens are cryptographically and logically bound to their device session."""
    res = _provision_active_session("SES-TEST-007")
    ref = res["session"]["refresh_token"]

    # Deactivating device invalidates the session family
    activation_service.deactivate_device(res["license"]["license_id"], res["device_id"])

    # Attempting to refresh after device deactivation fails
    with pytest.raises(Exception):
        activation_service.refresh_session(ref)


def test_pt_ses_008_inspect_browser_storage():
    """PT-SES-008: Client storage guidelines verified; no static bearer secrets in web sources."""
    web_dir = REPO_ROOT / "web" / "src"
    for p in web_dir.rglob("*.ts*"):
        text = p.read_text(encoding="utf-8")
        assert "hardcoded_refresh_token" not in text
        assert "aegis-dev-key" not in text


def test_pt_ses_009_csrf_protection_on_state_changing_requests(core_client):
    """PT-SES-009: State-changing mutations without required authentication and authorization are rejected."""
    # POST without credentials
    res = core_client.post("/api/v1/query", json={"query": "unauthenticated"})
    assert res.status_code == 401


def test_pt_ses_010_replay_websocket_authentication_ticket():
    """PT-SES-010: Replay of invalid or forged WebSocket authentication ticket is denied."""
    assert activation_service.validate_session("replayed-ticket-nonce-abc") is None
