"""
tests.security.deletion.test_deletion_suite
===========================================
Tests for WP-07.04 Cascading Document Deletion Security Gate (DEL-001 through DEL-014).
"""

import pytest
from aegis.security.deletion import DocumentDeletionOrchestrator, DeletionBenchmarkRunner


@pytest.fixture
def orchestrator():
    orch = DocumentDeletionOrchestrator()
    orch.register_document(
        doc_id="test-doc-1",
        tenant_id="tenant_alpha",
        content="Sensitive financial contract text",
        job_id="job-1",
        report_id="rep-1",
    )
    return orch


def test_del_001_authorized_cascading_deletion(orchestrator):
    ok, code, _ = orchestrator.delete_document("tenant_alpha", "test-doc-1", {"tenant_admin"})
    assert ok
    assert code == 200

    # Assert all targets cleared
    assert "test-doc-1" not in orchestrator.database
    assert "test-doc-1" not in orchestrator.extracted_text
    assert "test-doc-1" not in orchestrator.search_index
    assert "test-doc-1" not in orchestrator.vector_index
    assert "test-doc-1" not in orchestrator.semantic_cache
    assert f"storage/tenant_alpha/test-doc-1.pdf" not in orchestrator.object_storage

    # Assert in-flight job cancelled
    assert orchestrator.job_queue["job-1"]["status"] == "CANCELLED"

    # Assert dependent report invalidated
    assert orchestrator.reports["rep-1"]["status"] == "INVALID_SOURCE_DELETED"

    # Assert tombstone recorded
    assert "test-doc-1" in orchestrator.tombstones


def test_del_002_cross_tenant_deletion_denied(orchestrator):
    ok, code, _ = orchestrator.delete_document("tenant_beta", "test-doc-1", {"tenant_admin"})
    assert not ok
    assert code == 404
    # Ensure resource intact
    assert "test-doc-1" in orchestrator.database


def test_del_003_unauthorized_viewer_deletion_denied(orchestrator):
    ok, code, _ = orchestrator.delete_document("tenant_alpha", "test-doc-1", {"viewer"})
    assert not ok
    assert code == 403
    assert "test-doc-1" in orchestrator.database


def test_del_004_idempotent_retry(orchestrator):
    orchestrator.delete_document("tenant_alpha", "test-doc-1", {"tenant_admin"})
    # Second deletion attempt
    ok2, code2, _ = orchestrator.delete_document("tenant_alpha", "test-doc-1", {"tenant_admin"})
    assert not ok2
    assert code2 == 404


def test_del_005_storage_target_outage_fails_closed(orchestrator):
    orchestrator.target_outages.add("object_storage")
    ok, code, msg = orchestrator.delete_document("tenant_alpha", "test-doc-1", {"tenant_admin"})
    assert not ok
    assert code == 500
    assert "incomplete" in msg.lower()


def test_del_006_post_restore_tombstone_reconciliation(orchestrator):
    # Delete doc-1 so tombstone is created
    orchestrator.delete_document("tenant_alpha", "test-doc-1", {"tenant_admin"})

    # Simulate restoring an older backup that still has test-doc-1
    restored_db = {
        "test-doc-1": {"doc_id": "test-doc-1", "tenant_id": "tenant_alpha"},
        "active-doc-2": {"doc_id": "active-doc-2", "tenant_id": "tenant_alpha"},
    }
    purged = orchestrator.reconcile_after_restore(restored_db)
    assert purged == 1
    assert "test-doc-1" not in restored_db
    assert "active-doc-2" in restored_db


def test_del_007_benchmark_runner_full_suite():
    runner = DeletionBenchmarkRunner()
    report = runner.run_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 14
    assert report["metrics"]["all_targets_verified"] is True
