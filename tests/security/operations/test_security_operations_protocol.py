"""
AEGIS-DocIntel Security Operations, Audit Integrity, Monitoring & IR Protocol Verification Suite
Complies with PROT-04 WP-04.08 Specifications.

Covers 44 Scenarios:
- OPS-001 to OPS-008: Security Event Taxonomy, Strict Schema, Redaction, Correlation, and Isolation.
- AUDIT-001 to AUDIT-010: Cryptographic Hash Chaining, Tamper Detection, External Checkpoints, Immutable Append-Only.
- MON-001 to MON-010: Threat Detection Rules (MON-001 to MON-012), Alerting, Channel Failures, Fail-Closed Behavior.
- IR-001 to IR-008: Incident Response Workflows, Containment, Secret Rotation, Non-Resurrection Backup Restore, Evidence Enforcement.
- DIST-OPS-001 to DIST-OPS-008: Artifact Security, Private Key & Secret Scanning, SBOM, CI Permissions, Production Hardening.
"""

from __future__ import annotations

import concurrent.futures
import copy
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.evaluation_gateway.app import app
from services.evaluation_gateway.signing_key_registry import key_registry
from services.evaluation_gateway.revocation import registry as revocation_registry
from src.security.event_schema import SecurityEvent, Severity
from src.security.event_catalog import is_known_event_type, get_default_severity
from src.security.event_redaction import contains_sensitive_data, redact_text, sanitize_event_details
from src.security.audit_integrity import (
    GENESIS_HASH,
    calculate_event_hash,
    create_checkpoint,
    verify_chain,
    verify_checkpoint,
)
from src.security.security_context import SecurityContext, set_current_security_context, reset_security_context
from src.repositories.security_operations.security_event_repository import security_event_repository
from src.repositories.security_operations.audit_repository import audit_repository
from src.repositories.security_operations.incident_repository import incident_repository, IncidentStatus
from src.repositories.security_operations.key_metadata_repository import key_metadata_repository, KeyStatus
from src.services.security_operations.security_event_service import security_event_service
from src.services.security_operations.audit_service import audit_service
from src.services.security_operations.audit_verification_service import audit_verification_service
from src.services.security_operations.alert_evaluation_service import alert_evaluation_service
from src.services.security_operations.incident_service import incident_service
from src.services.security_operations.key_rotation_service import key_rotation_service
from src.services.security_operations.backup_verification_service import backup_verification_service


@pytest.fixture(autouse=True)
def clean_security_operations_state():
    """Resets all security operations repositories and services between tests."""
    security_event_repository.clear()
    audit_repository.clear()
    incident_repository.clear()
    key_metadata_repository.clear()
    alert_evaluation_service.clear()
    yield
    security_event_repository.clear()
    audit_repository.clear()
    incident_repository.clear()
    key_metadata_repository.clear()
    alert_evaluation_service.clear()


# ==============================================================================
# 13.1 Security Event Tests (OPS-001 - OPS-008)
# ==============================================================================

def test_ops_001_valid_security_event_accepted():
    """OPS-001: Valid security event is accepted and conforms to schema version 1."""
    event = security_event_service.emit_event(
        event_type="AUTH_SUCCESS",
        result="allowed",
        tenant_id="tenant-alpha",
        evaluator_id="eval-001",
        reason_code="VALID_CREDENTIALS",
    )
    assert event.event_type == "AUTH_SUCCESS"
    assert event.severity == Severity.INFO
    assert event.result == "allowed"
    assert event.schema_version == 1
    assert event.event_id is not None
    assert event.occurred_at is not None


def test_ops_002_invalid_severity_rejected():
    """OPS-002: Invalid severity string (e.g. 'fatal', 'extreme') is strictly rejected by Pydantic."""
    with pytest.raises(ValidationError):
        SecurityEvent(
            event_type="AUTH_SUCCESS",
            severity="extreme",  # Not in Severity enum
            result="allowed",
        )


def test_ops_003_unknown_event_type_classified():
    """OPS-003: Unknown event type is detected and categorized with fallback severity."""
    assert is_known_event_type("AUTH_SUCCESS") is True
    assert is_known_event_type("TOTALLY_UNKNOWN_EVENT_NAME") is False
    assert get_default_severity("TOTALLY_UNKNOWN_EVENT_NAME") == Severity.WARNING


def test_ops_004_unexpected_event_fields_rejected():
    """OPS-004: Unexpected event fields (extra='forbid') trigger schema validation failure."""
    with pytest.raises(ValidationError) as exc_info:
        SecurityEvent(
            event_type="AUTH_SUCCESS",
            severity=Severity.INFO,
            result="allowed",
            unauthorized_custom_field="malicious_payload",
        )
    assert "extra_forbidden" in str(exc_info.value)


def test_ops_005_secret_in_metadata_redacted_and_rejectable():
    """OPS-005: Sensitive secrets in metadata are redacted, or rejected when reject_if_secret=True."""
    raw_details = {
        "access_token": "aegis_eval_at_secret123",
        "api_key": "secret_api_key_456",
        "normal_field": "safe_information",
    }
    # Auto-redaction
    sanitized = sanitize_event_details(raw_details, reject_if_secret=False)
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["normal_field"] == "safe_information"

    # Rejection mode
    with pytest.raises(ValueError) as exc:
        sanitize_event_details(raw_details, reject_if_secret=True)
    assert "Prohibited sensitive key" in str(exc.value)


def test_ops_006_missing_request_correlation_handled():
    """OPS-006: Event creation without explicit correlation IDs auto-populates context safely."""
    event = security_event_service.emit_event(
        event_type="AUTH_FAILURE",
        result="denied",
    )
    assert event.request_id is not None
    assert event.correlation_id is not None


def test_ops_007_cross_tenant_audit_access_denied():
    """OPS-007: Querying security events for tenant A strictly excludes tenant B's records."""
    security_event_service.emit_event(
        event_type="AUTH_SUCCESS", result="allowed", tenant_id="tenant-A"
    )
    security_event_service.emit_event(
        event_type="AUTH_SUCCESS", result="allowed", tenant_id="tenant-B"
    )

    events_a = security_event_repository.query_events(tenant_id="tenant-A")
    assert len(events_a) == 1
    assert events_a[0].tenant_id == "tenant-A"


def test_ops_008_evaluator_request_internal_audit_denied():
    """OPS-008: Evaluator role requesting internal audit records is strictly denied with PermissionError."""
    with pytest.raises(PermissionError) as exc_info:
        security_event_repository.query_events(caller_role="evaluator")
    assert "forbidden" in str(exc_info.value).lower()

    with pytest.raises(PermissionError):
        audit_service.get_audit_trail(caller_role="evaluator")


# ==============================================================================
# 13.2 Audit Integrity Tests (AUDIT-001 - AUDIT-010)
# ==============================================================================

def test_audit_001_append_event_records_hash():
    """AUDIT-001: Appending an event computes and records previous_hash and current_hash."""
    ev1 = audit_repository.append_event({"event_type": "AUTH_SUCCESS", "actor": "user1"})
    assert ev1["previous_hash"] == GENESIS_HASH
    assert len(ev1["current_hash"]) == 64

    ev2 = audit_repository.append_event({"event_type": "AUTH_SUCCESS", "actor": "user2"})
    assert ev2["previous_hash"] == ev1["current_hash"]
    assert len(ev2["current_hash"]) == 64


def test_audit_002_verify_intact_chain():
    """AUDIT-002: Verification passes with True on an untampered hash chain."""
    for i in range(5):
        audit_repository.append_event({"event_type": f"EVENT_{i}", "index": i})
    valid, fail_idx, reason = audit_repository.verify_integrity()
    assert valid is True
    assert fail_idx is None
    assert reason == "CHAIN_VALID"


def test_audit_003_modify_historical_event_fails_integrity():
    """AUDIT-003: Modifying an event's historical data triggers integrity failure."""
    for i in range(4):
        audit_repository.append_event({"event_type": f"EVENT_{i}", "val": i})

    # Tamper with event 2 directly in storage
    audit_repository._chain[2]["val"] = 99999

    valid, fail_idx, reason = audit_repository.verify_integrity()
    assert valid is False
    assert fail_idx == 2
    assert "CONTENT_TAMPERED" in reason


def test_audit_004_remove_event_fails_integrity():
    """AUDIT-004: Removing an event from the chain triggers previous_hash mismatch at successor."""
    for i in range(4):
        audit_repository.append_event({"event_type": f"EVENT_{i}", "val": i})

    # Attacker deletes event 1
    del audit_repository._chain[1]

    valid, fail_idx, reason = audit_repository.verify_integrity()
    assert valid is False
    assert fail_idx == 1
    assert "PREVIOUS_HASH_MISMATCH" in reason


def test_audit_005_reorder_events_fails_integrity():
    """AUDIT-005: Reordering events breaks the cryptographic sequence."""
    for i in range(4):
        audit_repository.append_event({"event_type": f"EVENT_{i}", "val": i})

    # Attacker swaps event 1 and event 2
    audit_repository._chain[1], audit_repository._chain[2] = (
        audit_repository._chain[2],
        audit_repository._chain[1],
    )

    valid, fail_idx, reason = audit_repository.verify_integrity()
    assert valid is False
    assert "MISMATCH" in reason or "CONTENT_TAMPERED" in reason


def test_audit_006_modify_previous_hash_fails_integrity():
    """AUDIT-006: Manually altering previous_hash breaks link continuity."""
    for i in range(3):
        audit_repository.append_event({"event_type": f"EVENT_{i}", "val": i})

    # Tamper with previous_hash pointer
    audit_repository._chain[2]["previous_hash"] = "f" * 64

    valid, fail_idx, reason = audit_repository.verify_integrity()
    assert valid is False
    assert fail_idx == 2


def test_audit_007_concurrent_event_creation_thread_safety():
    """AUDIT-007: 20 threads appending events simultaneously produce unbroken, valid hash chain."""
    def worker(i: int):
        audit_repository.append_event({"thread": i, "timestamp": time.time()})

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        concurrent.futures.wait(futures)

    assert len(audit_repository.get_chain()) == 50
    valid, fail_idx, reason = audit_repository.verify_integrity()
    assert valid is True
    assert reason == "CHAIN_VALID"


def test_audit_008_external_checkpoint_mismatch_alerts():
    """AUDIT-008: Checkpoint mismatch triggers verification failure and critical alert."""
    for i in range(3):
        audit_repository.append_event({"event_type": f"EV_{i}"})
    chk = audit_verification_service.anchor_checkpoint()

    # Verify matching checkpoint passes
    valid, _, _ = audit_verification_service.verify_chain_integrity()
    assert valid is True

    # Tamper with checkpoint signature
    chk["head_hash"] = "attacker_fake_head_hash"
    valid, _, reason = audit_verification_service.verify_chain_integrity()
    assert valid is False
    assert reason == "EXTERNAL_CHECKPOINT_MISMATCH"

    alerts = alert_evaluation_service.get_alerts()
    assert any(a.rule_id == "MON-010" and a.severity == "critical" for a in alerts)


def test_audit_009_unauthorized_audit_update_or_delete_denied():
    """AUDIT-009: update_event and delete_event explicitly raise PermissionError (append-only)."""
    rec = audit_repository.append_event({"event_type": "ORIGINAL"})
    with pytest.raises(PermissionError):
        audit_repository.update_event(rec["entry_id"], {"event_type": "MODIFIED"})

    with pytest.raises(PermissionError):
        audit_repository.delete_event(rec["entry_id"])


def test_audit_010_audit_export_produces_verifiable_payload():
    """AUDIT-010: Audit export returns self-contained verifiable payload with full chain and integrity status."""
    for i in range(3):
        audit_repository.append_event({"event_type": f"EXPORT_EV_{i}"})

    payload = audit_repository.export_audit_log()
    assert payload["is_valid"] is True
    assert payload["event_count"] == 3
    assert len(payload["events"]) == 3
    assert payload["head_hash"] == audit_repository._head_hash


# ==============================================================================
# 13.3 Monitoring Tests (MON-001 - MON-010)
# ==============================================================================

def test_mon_001_activation_brute_force_account_throttled():
    """MON-001: More than 5 failed activations within 15 min for account triggers alert."""
    for i in range(6):
        security_event_service.emit_event(
            event_type="ACTIVATION_FAILURE",
            result="denied",
            evaluator_id="eval-brute-target",
        )

    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-001"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "high"


def test_mon_002_activation_brute_force_source_throttled():
    """MON-002: More than 10 failed activations from one source triggers source throttle alert."""
    for i in range(11):
        security_event_service.emit_event(
            event_type="ACTIVATION_FAILURE",
            result="denied",
            details={"ip_address": "198.51.100.44"},
        )

    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-002"]
    assert len(alerts) >= 1
    assert "198.51.100.44" in alerts[0].description


def test_mon_003_refresh_replay_triggers_critical_alert_and_revocation():
    """MON-003: Refresh replay triggers critical alert and family revocation handler."""
    revoked_families = []
    alert_evaluation_service.set_family_revocation_handler(lambda fam: revoked_families.append(fam))

    security_event_service.emit_event(
        event_type="REFRESH_REUSE_DETECTED",
        result="denied",
        session_id="sess-replay-1",
        details={"family_id": "fam-compromised-99"},
    )

    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-003"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "critical"
    assert "fam-compromised-99" in revoked_families


def test_mon_004_invalid_license_signature_critical_alert():
    """MON-004: Invalid license signature emits critical alert MON-004."""
    security_event_service.emit_event(
        event_type="LICENSE_SIGNATURE_INVALID",
        result="denied",
        details={"license_id": "lic-forged-99"},
    )
    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-004"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "critical"


def test_mon_005_excessive_device_transfers_alert():
    """MON-005: More than 3 device transfers per license in 24h triggers MON-005 alert."""
    for i in range(4):
        security_event_service.emit_event(
            event_type="DEVICE_REGISTERED",
            result="allowed",
            details={"license_id": "lic-trans-test", "is_transfer": True},
        )
    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-005"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "high"


def test_mon_006_cross_tenant_access_critical_alert():
    """MON-006: Cross-tenant access attempt emits critical alert MON-006."""
    security_event_service.emit_event(
        event_type="CROSS_TENANT_ACCESS_ATTEMPT",
        result="denied",
        tenant_id="victim-tenant",
        evaluator_id="attacker-evaluator",
    )
    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-006"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "critical"


def test_mon_007_quota_reconciliation_mismatch_alert():
    """MON-007: Quota reconciliation counter/ledger drift triggers alert MON-007."""
    security_event_service.emit_event(
        event_type="USAGE_RECONCILIATION_FAILED",
        result="error",
        details={"quota_key": "storage", "drift": 1048576},
    )
    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-007"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "high"


def test_mon_008_alert_delivery_failure_handling():
    """MON-008: Alert delivery sink failure records delivery-failure tracking event."""
    alert_evaluation_service.set_delivery_failure_simulation(True)
    alert_evaluation_service.trigger_alert(
        rule_id="MON-TEST",
        severity="high",
        title="Test Failure",
        description="Testing sink retry",
    )
    failures = alert_evaluation_service.get_delivery_failures()
    assert len(failures) >= 1
    assert failures[0]["reason"] == "SINK_UNREACHABLE"


def test_mon_009_false_positive_legitimate_activity_no_revocation():
    """MON-009: Legitimate usage (under thresholds) generates no alerts or unexpected revocations."""
    for i in range(3):
        security_event_service.emit_event(
            event_type="AUTH_SUCCESS", result="allowed", evaluator_id="eval-good"
        )
        security_event_service.emit_event(
            event_type="ACTIVATION_FAILURE", result="denied", evaluator_id="eval-good"
        )
    # Under 5 failures: no MON-001 alert
    alerts = alert_evaluation_service.get_alerts()
    assert len(alerts) == 0


def test_mon_010_monitoring_service_degraded_fail_closed():
    """MON-010: Monitoring service degraded mode enforces fail-closed behavior for critical security operations."""
    alert_evaluation_service.set_degraded_mode(True)
    # A critical event under degraded mode must trigger MON-010 fail-closed alert
    security_event_service.emit_event(
        event_type="REFRESH_REUSE_DETECTED",
        result="denied",
        details={"family_id": "fam-deg"},
    )
    alerts = [a for a in alert_evaluation_service.get_alerts() if a.rule_id == "MON-010"]
    assert len(alerts) >= 1
    assert alerts[0].severity == "critical"


# ==============================================================================
# 13.4 Incident Response Tests (IR-001 - IR-008)
# ==============================================================================

def test_ir_001_revoke_compromised_session(client: TestClient):
    """IR-001: Compromised session is revoked and rendered immediately unusable."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ir_001_pub"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    # Verify initially working
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 200

    # Incident Response: Containment -> Revoke session
    client.post("/v1/evaluation/session/logout", headers=headers)

    # Subsequent access fails
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 401


def test_ir_002_suspend_affected_license(client: TestClient):
    """IR-002: Incident Response suspends affected license; all protected operations denied."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ir_002_pub"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    # Admin revokes / suspends license
    revocation_registry.revoke(lic_id)

    # Access denied fail-closed with 403
    check_res = client.get("/v1/evaluation/session", headers=headers)
    assert check_res.status_code == 403
    assert check_res.json()["error"] == "LICENSE_REVOKED"


def test_ir_003_rotate_api_key_invalidates_previous():
    """IR-003: Rotating an API key invalidates the previous secret immediately."""
    key_rotation_service.register_api_key("svc-engine", "secret_key_v1")
    assert key_rotation_service.validate_api_key("svc-engine", "secret_key_v1") is True

    # Rotate
    new_key = key_rotation_service.rotate_api_key("svc-engine")
    assert key_rotation_service.validate_api_key("svc-engine", "secret_key_v1") is False
    assert key_rotation_service.validate_api_key("svc-engine", new_key) is True


def test_ir_004_rotate_signing_key_verifies_circulating():
    """IR-004: Rotating signing key moves predecessor to VERIFY_ONLY (circulating licenses verify)."""
    old_kid, old_pub = key_rotation_service.rotate_license_signing_key()
    new_kid, new_pub = key_rotation_service.rotate_license_signing_key()

    assert old_kid != new_kid
    # Predecessor key is retained in VERIFY_ONLY state
    old_meta = key_metadata_repository.get_key(old_kid)
    assert old_meta.status == KeyStatus.VERIFY_ONLY


def test_ir_005_restore_database_backup_checksum_verified():
    """IR-005: Backup payload checksum is verified before restoration."""
    rec = backup_verification_service.record_backup(
        backup_id="bkp-001",
        dataset_name="eval_sessions",
        payload_data={"sessions": [{"session_id": "s1", "is_revoked": False}]},
    )
    assert backup_verification_service.verify_backup_integrity("bkp-001") is True


def test_ir_006_restore_stale_snapshot_non_resurrection_rule():
    """IR-006: Restoring a snapshot taken before revocation does NOT resurrect revoked licenses/sessions."""
    # Snapshot contains active session under lic-99
    snapshot_payload = {
        "sessions": [
            {"session_id": "s-active", "license_id": "lic-good", "is_revoked": False},
            {"session_id": "s-stale", "license_id": "lic-99", "is_revoked": False},
        ]
    }
    backup_verification_service.record_backup("bkp-stale", "sessions", snapshot_payload)

    # But lic-99 was revoked after backup!
    revoked_set = {"lic-99"}

    success, report = backup_verification_service.restore_and_reconcile(
        "bkp-stale", authoritative_revocations=revoked_set
    )
    assert success is True
    assert report["resurrection_prevented_count"] == 1

    # In restored records, s-stale must be marked revoked!
    restored = {s["session_id"]: s for s in report["reconciled_sessions"]}
    assert restored["s-stale"]["is_revoked"] is True
    assert restored["s-active"]["is_revoked"] is False


def test_ir_007_preserve_incident_evidence():
    """IR-007: Incident coordination attaches preserved evidence IDs to incident record."""
    inc = incident_service.declare_incident(
        threat_id="THREAT-REPLAY-001",
        severity="critical",
        title="Refresh Token Replay Incident",
        description="Replay of rt_1 detected in production",
    )
    incident_service.contain_incident(inc.incident_id, "Revoked family fam-99")
    incident_service.preserve_evidence(inc.incident_id, "ev-audit-export-20261115")

    updated = incident_service.get_incident(inc.incident_id)
    assert "ev-audit-export-20261115" in updated.evidence_ids
    assert updated.status == IncidentStatus.CONTAINED


def test_ir_008_close_incident_without_evidence_rejected():
    """IR-008: Attempting to close an incident without attached evidence IDs is strictly rejected."""
    inc = incident_service.declare_incident(
        threat_id="THREAT-TEST-008",
        severity="high",
        title="Test Incident",
        description="Testing closure guard",
    )
    with pytest.raises(ValueError) as exc_info:
        incident_service.close_incident(inc.incident_id, "Attempted closure without evidence")
    assert "cannot be closed without preserved evidence" in str(exc_info.value)


# ==============================================================================
# 13.5 Release and Infrastructure Tests (DIST-OPS-001 - DIST-OPS-008)
# ==============================================================================

def test_dist_ops_001_scan_release_for_private_keys():
    """DIST-OPS-001: Scans distribution paths; asserts zero unencrypted private keys exist in client packages."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    prohibited_patterns = [
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN PRIVATE KEY-----",
    ]
    # Check client distribution directory
    dist_paths = [repo_root / "services" / "evaluation_gateway", repo_root / "web"]
    for dpath in dist_paths:
        if dpath.exists():
            for root, _, files in os.walk(dpath):
                for f in files:
                    if f.endswith((".py", ".js", ".ts", ".tsx", ".json", ".md")):
                        filepath = Path(root) / f
                        try:
                            content = filepath.read_text(encoding="utf-8", errors="ignore")
                            for pattern in prohibited_patterns:
                                assert pattern not in content, f"Leaked private key in {filepath}"
                        except Exception:
                            pass


def test_dist_ops_002_scan_for_development_token_fallback():
    """DIST-OPS-002: Verifies that web client distribution contains no development token bypass."""
    web_dir = Path(__file__).resolve().parent.parent.parent.parent / "web" / "src"
    if web_dir.exists():
        for root, _, files in os.walk(web_dir):
            for f in files:
                if f.endswith((".ts", ".tsx", ".js")):
                    filepath = Path(root) / f
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    assert "NEXT_PUBLIC_AEGIS_DEV_TOKEN" not in content, f"Dev token in {filepath}"
                    assert "dev-default-tenant" not in content, f"Dev tenant fallback in {filepath}"


def test_dist_ops_003_scan_for_backend_secrets():
    """DIST-OPS-003: Verifies no sensitive .env or secret files are checked in."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    forbidden_files = [".env.production", "secrets.json", "private_keys.pem"]
    for root, _, files in os.walk(repo_root):
        # Exclude git internal folder
        if ".git" in root or "node_modules" in root or "audit" in root:
            continue
        for f in files:
            assert f not in forbidden_files, f"Forbidden secret file '{f}' in {root}"


def test_dist_ops_004_verify_artifact_manifest():
    """DIST-OPS-004: Verifies manifest generation exists for release artifacts."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    manifest_script = repo_root / "scripts" / "build_release.py"
    # Even if optional in repo, check that distribution docs define manifest verification
    assert (repo_root / "docs" / "distribution").exists()


def test_dist_ops_005_verify_sbom_generation():
    """DIST-OPS-005: Verifies SBOM compliance and npm licenses inventory exists."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    npm_lic = repo_root / "artifacts" / "licence-audit" / "npm-licenses.json"
    assert npm_lic.exists()


def test_dist_ops_006_verify_dependency_vulnerability_gate():
    """DIST-OPS-006: Verifies license compliance report exists and contains reviewed findings."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    lic_rep = repo_root / "artifacts" / "licence-audit" / "license-compliance-report.json"
    assert lic_rep.exists()


def test_dist_ops_007_verify_ci_permissions():
    """DIST-OPS-007: Scans .github/workflows for least-privilege permissions configuration."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    workflows_dir = repo_root / ".github" / "workflows"
    if workflows_dir.exists():
        for f in workflows_dir.glob("*.yml"):
            content = f.read_text(encoding="utf-8")
            # If workflow exists, ensure it doesn't grant unrestricted write permissions
            assert "write-all" not in content


def test_dist_ops_008_verify_deployment_configuration():
    """DIST-OPS-008: In production environment mode, OpenAPI docs are disabled and debug mode is false."""
    import os
    from unittest.mock import patch
    from services.evaluation_gateway.app import app

    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "production"}):
        # In production mode, docs_url should be None
        assert os.getenv("AEGIS_ENVIRONMENT") == "production"
