"""
Consolidated Security Audit: Operational Integrity, DR & Regression Verification (SEC-018, SEC-019)
"""

from uuid import uuid4
import pytest

from src.repositories.security_operations.audit_repository import audit_repository
from src.services.security_operations.audit_verification_service import audit_verification_service
from src.services.security_operations.backup_verification_service import backup_verification_service
from src.services.security_operations.security_event_service import security_event_service
from services.evaluation_gateway.revocation import registry as revocation_registry


def test_regr_001_audit_hash_chain_tamper_evident():
    """SEC-018.1: Audit ledger hash chain detects any modification to historical events."""
    # Emit events
    security_event_service.emit_event(
        event_type="AUTH_SUCCESS",
        result="allowed",
        evaluator_id="eval-regr-1",
        details={"step": "first"},
    )
    security_event_service.emit_event(
        event_type="TOKEN_ROTATED",
        result="allowed",
        evaluator_id="eval-regr-1",
        details={"step": "second"},
    )

    # Valid chain
    is_valid, _, _ = audit_verification_service.verify_chain_integrity()
    assert is_valid is True

    # Tamper with an event in the chain
    with audit_repository._lock:
        if audit_repository._chain:
            audit_repository._chain[0]["details"]["step"] = "corrupted_tamper"

    # Verification must fail
    is_valid_after, fail_idx, _ = audit_verification_service.verify_chain_integrity()
    assert is_valid_after is False
    assert fail_idx == 0


def test_regr_002_backup_restoration_preserves_revocations():
    """SEC-019.1: Restoring backup from earlier snapshot never resurrects revoked licenses."""
    backup_data = {
        "sessions": [
            {"session_id": "sess-prior-1", "license_id": "lic-revoked-001", "is_revoked": False},
            {"session_id": "sess-prior-2", "license_id": "lic-active-002", "is_revoked": False},
        ]
    }
    backup_verification_service.record_backup("bk-regr-002", "db", backup_data)

    # Authoritative revocation registry contains lic-revoked-001
    authoritative = {"lic-revoked-001"}
    ok, report = backup_verification_service.restore_and_reconcile("bk-regr-002", authoritative)
    assert ok is True
    assert report["resurrection_prevented_count"] == 1

    # In reconciled sessions, lic-revoked-001 remains strictly revoked
    for s in report["reconciled_sessions"]:
        if s["license_id"] == "lic-revoked-001":
            assert s["status"] == "revoked"
            assert s["is_revoked"] is True
            assert s["resurrected"] is False


def test_regr_003_audit_ledger_strictly_append_only():
    """SEC-018.2: Audit repository raises PermissionError on attempts to update or delete events."""
    with pytest.raises(PermissionError):
        audit_repository.update_event("entry-1", {"danger": "update"})

    with pytest.raises(PermissionError):
        audit_repository.delete_event("entry-1")


def test_regr_004_fail_closed_on_authority_failure():
    """SEC-016.6: Core security authority defaults to fail-closed denial."""
    from src.security.private_engine_guard import private_engine_guard

    # Verifying malformed token fails closed
    ok, err, ctx = private_engine_guard.verify_engine_request("invalid.token", "documents.query")
    assert ok is False
    assert ctx is None
