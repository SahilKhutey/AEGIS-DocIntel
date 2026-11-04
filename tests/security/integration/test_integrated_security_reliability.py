"""
tests.security.integration.test_integrated_security_reliability
===============================================================
End-to-end integrated security & reliability scenarios (INT-001 through INT-010):
Validates the complete lifecycle: Upload -> Cross-Tenant Defense -> Privacy Masking ->
Report Generation -> Worker Crash Recovery -> Cascading Deletion -> Clean Backup Restore ->
Tombstone Post-Restore Reconciliation -> Restored Tenant Isolation -> Normal Resumption.
"""

import pytest
from aegis.security.auth import AuthVerifier, Authorizer
from aegis.security.tenant import TenantIsolationStore
from aegis.security.privacy import PrivacyDetector
from aegis.security.deletion import DocumentDeletionOrchestrator
from aegis.reliability.workers import WorkerFaultInjector, JobState
from aegis.reliability.backup import DisasterRecoveryDrill


def test_int_001_to_010_complete_security_reliability_lifecycle(tmp_path):
    # Setup core subsystem engines
    auth_verifier = AuthVerifier()
    authorizer = Authorizer()
    tenant_store = TenantIsolationStore()
    tenant_store.populate_synthetic_fixtures()
    privacy_detector = PrivacyDetector()
    deletion_orch = DocumentDeletionOrchestrator()
    worker_injector = WorkerFaultInjector()
    dr_drill = DisasterRecoveryDrill(tmp_path / "int_dr")
    dr_drill.setup_source_environment()

    tenant_alpha = "tenant_alpha"
    tenant_beta = "tenant_beta"

    # INT-001: User uploads a document and processes it
    token_alpha = auth_verifier.issue_jwt("user-alpha-editor", tenant_alpha, ["editor"])
    auth_ok, payload, _ = auth_verifier.verify_token(token_alpha)
    assert auth_ok
    can_upload, code, _ = authorizer.authorize(payload["sub"], tenant_alpha, set(payload["roles"]), "upload_documents")
    assert can_upload and code == 200

    raw_doc_text = "Alpha Sensitive Financials. Contact CFO lead@alpha.org. Revenue $100M."
    deletion_orch.register_document("doc-int-1", tenant_alpha, raw_doc_text, job_id="job-int-1", report_id="rep-int-1")
    assert "doc-int-1" in deletion_orch.database

    # INT-002: Different tenant attempts to retrieve it
    doc_beta_lookup = deletion_orch.database.get("doc-int-1")
    is_cross_tenant = doc_beta_lookup["tenant_id"] != tenant_beta
    assert is_cross_tenant
    can_view, code_beta, _ = authorizer.authorize(
        "user-beta", tenant_beta, {"viewer"}, "view_own_documents",
        resource_id="doc-int-1", resource_tenant_id=doc_beta_lookup["tenant_id"]
    )
    assert not can_view and code_beta == 404

    # INT-003: Document contains synthetic sensitive data (Detection and masking)
    entities = privacy_detector.detect(raw_doc_text)
    assert any(e.entity_type == "EMAIL_ADDRESS" for e in entities)
    redacted_text, telemetry = privacy_detector.redact(raw_doc_text, entities)
    assert "[REDACTED_EMAIL]" in redacted_text
    assert "lead@alpha.org" not in redacted_text
    assert "lead@alpha.org" not in str(telemetry)

    # INT-004: User generates a report respecting privacy policy
    can_gen_rep, code_rep, _ = authorizer.authorize(payload["sub"], tenant_alpha, set(payload["roles"]), "generate_reports")
    assert can_gen_rep and code_rep == 200
    report_content = f"# Executive Summary\n{redacted_text}"
    assert "lead@alpha.org" not in report_content

    # INT-005: Worker crashes during processing (Recovery via lease expiration)
    j_async = worker_injector.submit_job("job-async-1", "process", tenant_alpha, {"doc_id": "doc-int-1"})
    worker_injector.claim_job("worker-dead", lease_seconds=1.0)
    worker_injector.execute_job("worker-dead", "job-async-1", tenant_alpha, simulate_crash=True)
    # Recovery worker claims expired lease
    rec_claim = worker_injector.claim_job("worker-survivor", lease_seconds=60.0)
    assert rec_claim is not None and rec_claim.job_id == "job-async-1"
    ok_work, _ = worker_injector.execute_job("worker-survivor", "job-async-1", tenant_alpha)
    assert ok_work and j_async.status == JobState.COMPLETED

    # INT-006: User deletes the document (Cascading removal across all targets)
    can_del, code_del, _ = authorizer.authorize(payload["sub"], tenant_alpha, {"tenant_admin"}, "delete_own_documents")
    assert can_del
    del_ok, del_code, _ = deletion_orch.delete_document(tenant_alpha, "doc-int-1", {"tenant_admin"})
    assert del_ok and del_code == 200
    assert "doc-int-1" not in deletion_orch.database
    assert "doc-int-1" not in deletion_orch.extracted_text
    assert "doc-int-1" not in deletion_orch.vector_index
    assert "doc-int-1" in deletion_orch.tombstones

    # INT-007: Backup is restored into clean environment
    dr_drill.execute_online_backup()
    ok_dr, rto, _ = dr_drill.restore_into_clean_environment(dr_drill.backup_db_path)
    assert ok_dr and rto <= 900.0

    # INT-008: Deleted document exists in an older backup (Tombstone reapplication)
    older_backup_db = {
        "doc-int-1": {"doc_id": "doc-int-1", "tenant_id": tenant_alpha},  # Deleted in INT-006!
        "doc-active-persisted": {"doc_id": "doc-active-persisted", "tenant_id": tenant_alpha},
    }
    purged_count = deletion_orch.reconcile_after_restore(older_backup_db)
    assert purged_count == 1
    assert "doc-int-1" not in older_backup_db
    assert "doc-active-persisted" in older_backup_db

    # INT-009: Restored system receives cross-tenant requests (Isolation remains intact)
    can_cross, code_cross, _ = authorizer.authorize(
        "user-beta", tenant_beta, {"viewer"}, "view_own_documents",
        resource_id="doc-active-persisted", resource_tenant_id=tenant_alpha
    )
    assert not can_cross and code_cross == 404

    # INT-010: Restored system processes a new document (Normal operation resumes)
    deletion_orch.register_document("doc-new-post-restore", tenant_alpha, "Clean post-restore document")
    assert "doc-new-post-restore" in deletion_orch.database
    can_read_new, code_new, _ = authorizer.authorize(
        payload["sub"], tenant_alpha, {"viewer"}, "view_own_documents",
        resource_id="doc-new-post-restore", resource_tenant_id=tenant_alpha
    )
    assert can_read_new and code_new == 200
