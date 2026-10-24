"""
AEGIS-DocIntel — Webhook Security & SSRF Protection Tests
=========================================================
Verifies:
- Outbound URL validation blocks localhost, RFC 1918 private nets, and cloud metadata
- Non-HTTP/HTTPS schemes rejected
- HMAC-SHA256 signature generation and validation
- Replay attack mitigation via timestamp tolerance window
- Webhook subscription route RBAC enforcement
"""
import pytest
import time
from unittest.mock import patch

from src.core.webhook_security import (
    is_safe_webhook_url,
    generate_webhook_signature,
    verify_webhook_signature,
)
from src.core.security_context import (
    TenantContext,
    ROLE_VIEWER,
    ROLE_TENANT_ADMIN,
)
from src.api.routers.webhooks import _check_webhook_admin
from fastapi import HTTPException


def test_is_safe_webhook_url_valid_public():
    # Public domain names should resolve to safe IPs
    safe, msg = is_safe_webhook_url("https://example.com/webhook")
    assert safe is True
    assert msg == ""


def test_is_safe_webhook_url_rejects_schemes():
    safe, msg = is_safe_webhook_url("ftp://example.com/webhook")
    assert safe is False
    assert "Invalid scheme" in msg

    safe, msg = is_safe_webhook_url("file:///etc/passwd")
    assert safe is False
    assert "Invalid scheme" in msg


def test_is_safe_webhook_url_rejects_localhost_and_loopback():
    safe, msg = is_safe_webhook_url("http://localhost:8000/webhook")
    assert safe is False
    assert "Localhost destinations are forbidden" in msg

    safe, msg = is_safe_webhook_url("http://127.0.0.1:8000/webhook")
    assert safe is False
    assert "loopback address" in msg


def test_is_safe_webhook_url_rejects_cloud_metadata():
    safe, msg = is_safe_webhook_url("http://169.254.169.254/latest/meta-data")
    assert safe is False
    assert "cloud metadata" in msg or "link-local" in msg


def test_is_safe_webhook_url_rejects_private_ips():
    # 10.0.0.1
    safe, msg = is_safe_webhook_url("http://10.0.0.1/hook")
    assert safe is False
    assert "private network" in msg

    # 192.168.1.1
    safe, msg = is_safe_webhook_url("http://192.168.1.1/hook")
    assert safe is False
    assert "private network" in msg


def test_is_safe_webhook_url_allow_private_flag():
    # With explicit allow_private_for_tests
    safe, _ = is_safe_webhook_url("http://127.0.0.1:8000/webhook", allow_private_for_tests=True)
    assert safe is True


def test_webhook_hmac_signatures():
    payload = b'{"event":"document.indexed","doc_id":"doc-123"}'
    secret = "super_secret_webhook_key_42"
    now_ts = int(time.time())

    # Generate signature
    sig = generate_webhook_signature(payload, secret, now_ts)
    assert isinstance(sig, str)
    assert len(sig) == 64  # sha256 hex string

    # Verify signature
    assert verify_webhook_signature(payload, secret, sig, now_ts, now=now_ts) is True

    # Tampered payload fails
    tampered_payload = b'{"event":"document.indexed","doc_id":"doc-666"}'
    assert verify_webhook_signature(tampered_payload, secret, sig, now_ts, now=now_ts) is False

    # Tampered secret fails
    assert verify_webhook_signature(payload, "wrong_secret", sig, now_ts, now=now_ts) is False

    # Replay attack: timestamp expired (> 300 seconds) fails
    old_ts = now_ts - 600
    old_sig = generate_webhook_signature(payload, secret, old_ts)
    assert verify_webhook_signature(payload, secret, old_sig, old_ts, now=now_ts) is False


def test_webhook_rbac_enforcement():
    viewer_context = TenantContext(
        tenant_id="tenant-alpha",
        principal_id="user-viewer",
        roles=frozenset([ROLE_VIEWER]),
    )
    admin_context = TenantContext(
        tenant_id="tenant-alpha",
        principal_id="user-admin",
        roles=frozenset([ROLE_TENANT_ADMIN]),
    )

    # Viewer should be blocked
    with pytest.raises(HTTPException) as exc_info:
        _check_webhook_admin(viewer_context)
    assert exc_info.value.status_code == 403
    assert "tenant_admin role" in exc_info.value.detail

    # Admin should pass without exception
    _check_webhook_admin(admin_context)
