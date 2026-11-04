"""
tests.security.authentication.test_authentication_suite
======================================================
Tests for WP-07.01 Authentication Security Gate (AUTH-001 through AUTH-012).
"""

import pytest
from aegis.security.auth import AuthVerifier, AuthBenchmarkRunner


@pytest.fixture
def verifier():
    return AuthVerifier()


def test_auth_001_missing_credentials(verifier):
    ok, _, reason = verifier.verify_token(None)
    assert not ok
    assert "missing" in reason.lower()


def test_auth_002_valid_jwt(verifier):
    token = verifier.issue_jwt("user-1", "tenant-1", ["viewer"], expires_in_seconds=3600)
    ok, payload, reason = verifier.verify_token(token)
    assert ok
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"


def test_auth_003_invalid_api_key(verifier):
    verifier.register_api_key("valid-secret", "tenant-1", "service-1", ["viewer"])
    ok, _, reason = verifier.verify_api_key("invalid-secret")
    assert not ok
    assert "invalid" in reason.lower()


def test_auth_004_expired_token(verifier):
    token = verifier.issue_jwt("user-1", "tenant-1", ["viewer"], expires_in_seconds=-60)
    ok, _, reason = verifier.verify_token(token)
    assert not ok
    assert "expired" in reason.lower()


def test_auth_005_tampered_token(verifier):
    token = verifier.issue_jwt("user-1", "tenant-1", ["viewer"])
    parts = token.split(".")
    tampered = f"{parts[0]}.eyJzdWIiOiAiYXR0YWNrZXIifQ.{parts[2]}"
    ok, _, reason = verifier.verify_token(tampered)
    assert not ok


def test_auth_006_invalid_signature_attacker_key(verifier):
    token = verifier.issue_jwt("user-1", "tenant-1", ["viewer"], use_attacker_key=True)
    ok, _, reason = verifier.verify_token(token)
    assert not ok
    assert "signature" in reason.lower()


def test_auth_007_revoked_token(verifier):
    token = verifier.issue_jwt("user-1", "tenant-1", ["viewer"])
    verifier.revoke_token(token)
    ok, _, reason = verifier.verify_token(token)
    assert not ok
    assert "revoked" in reason.lower()


def test_auth_008_revoked_session(verifier):
    token = verifier.issue_jwt("user-1", "tenant-1", ["viewer"], custom_claims={"sid": "sess-42"})
    verifier.revoke_session("sess-42")
    ok, _, reason = verifier.verify_token(token)
    assert not ok
    assert "invalidated" in reason.lower()


def test_auth_009_failed_attempt_lockout(verifier):
    ip = "10.0.0.1"
    assert not verifier.is_locked_out(ip)
    for _ in range(4):
        verifier.record_failed_attempt(ip)
    assert not verifier.is_locked_out(ip)
    # 5th attempt locks out
    locked = verifier.record_failed_attempt(ip)
    assert locked
    assert verifier.is_locked_out(ip)


def test_auth_010_password_reset_single_use(verifier):
    token = "unique-reset-token-77"
    ok1, _ = verifier.use_password_reset_token(token)
    assert ok1
    ok2, reason = verifier.use_password_reset_token(token)
    assert not ok2
    assert "already used" in reason.lower()


def test_auth_011_disabled_account(verifier):
    token = verifier.issue_jwt("banned-user", "tenant-1", ["viewer"])
    verifier.disable_account("banned-user")
    ok, _, reason = verifier.verify_token(token)
    assert not ok
    assert "disabled" in reason.lower()


def test_auth_012_benchmark_runner_full_suite():
    runner = AuthBenchmarkRunner()
    report = runner.run_authentication_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 12
