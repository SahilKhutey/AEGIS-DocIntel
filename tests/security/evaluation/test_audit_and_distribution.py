"""
AEGIS Evaluation Security Tests — Audit Logging & Distribution Hygiene (PROT-04 WP-04.08)
Tests:
- AUDIT-001: Failed activation security events are logged
- AUDIT-002: Revocation events are logged
- AUDIT-003: Raw tokens, activation codes, and private keys NEVER enter security logs
- DIST-001: Evaluation package contains no private signing keys
- DIST-002: Evaluation package contains no shared gateway secrets or admin passwords
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.audit import audit_service


def test_audit_001_failed_activation_recorded(client: TestClient):
    """AUDIT-001: Invalid activation codes record security audit events."""
    audit_service.clear()
    client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "INVALID-CODE-XXXX", "device_public_key": "some_key"},
    )
    events = audit_service.get_events(10)
    invalid_events = [e for e in events if e["event_type"] == "activation.invalid_code"]
    assert len(invalid_events) >= 1
    assert invalid_events[0]["status"] == "FAILURE"


def test_audit_002_revocation_recorded(client: TestClient):
    """AUDIT-002: Administrative revocation events are recorded."""
    audit_service.clear()
    client.post(
        "/v1/evaluation/admin/revoke",
        json={"license_id": "test-lic-revocation-audit-id", "reason": "security_test"},
    )
    events = audit_service.get_events(10)
    rev_events = [e for e in events if e["event_type"] == "license.revoked_by_admin"]
    assert len(rev_events) >= 1
    assert rev_events[0]["license_id"] == "test-lic-revocation-audit-id"


def test_audit_003_raw_token_never_in_logs(client: TestClient):
    """AUDIT-003: Neither raw bearer tokens, private keys, nor full activation codes appear in logs."""
    audit_service.clear()

    secret_raw_token = "aegis_eval_at_SUPERSECRETTOKEN1234567890abcdef"
    full_act_code = "AEGIS-EVAL-SECRETCODE-9999"

    audit_service.record_event(
        event_type="test.sensitive_input",
        status="TEST",
        details={
            "token": secret_raw_token,
            "access_token": secret_raw_token,
            "activation_code": full_act_code,
            "header": f"Bearer {secret_raw_token}",
        },
    )

    events = audit_service.get_events(10)
    serialized = json.dumps(events)

    assert secret_raw_token not in serialized, "Raw token leaked in audit event log!"
    assert "SECRETCODE" not in serialized, "Raw activation secret leaked in audit event log!"
    assert "[REDACTED]" in serialized or "[REDACTED_TOKEN]" in serialized


def test_dist_001_package_contains_no_private_signing_key():
    """DIST-001: The distribution release directory must never bundle private-key.pem."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    demo_pkg_dir = repo_root / "distribution" / "demo-edition"

    if demo_pkg_dir.exists():
        for p in demo_pkg_dir.rglob("*"):
            if p.is_file():
                assert "private" not in p.name.lower(), f"Private key file found in distribution: {p}"
                assert not p.name.endswith(".key"), f"Key file found in distribution: {p}"


def test_dist_002_package_contains_no_shared_gateway_secret():
    """DIST-002: Distribution files must not contain hardcoded gateway admin secrets or passwords."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    demo_pkg_dir = repo_root / "distribution" / "demo-edition"

    forbidden_tokens = [
        "ADMIN_SECRET",
        "MASTER_KEY",
        "GATEWAY_ROOT_PASSWORD",
        "SUPER_ADMIN",
    ]

    if demo_pkg_dir.exists():
        for p in demo_pkg_dir.rglob("*"):
            if p.is_file() and p.suffix in (".yaml", ".yml", ".json", ".conf", ".ps1", ".sh"):
                text = p.read_text(encoding="utf-8", errors="ignore")
                for token in forbidden_tokens:
                    assert token not in text, f"Forbidden secret token '{token}' in distribution file: {p}"
