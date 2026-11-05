"""
tests.security.tenant_isolation.test_tenant_isolation_suite
===========================================================
Tests for WP-07.02 Tenant Isolation Security Gate (TENANT-001 through TENANT-012).
"""

import pytest
from aegis.security.tenant import TenantIsolationStore, TenantIsolationBenchmarkRunner


@pytest.fixture
def store():
    s = TenantIsolationStore()
    s.populate_synthetic_fixtures()
    return s


def test_tenant_001_document_cross_tenant_access_denied(store):
    doc, code, _ = store.get_document("tenant_alpha", "doc-b1")
    assert doc is None
    assert code == 404


def test_tenant_002_file_download_cross_tenant_denied(store):
    data, code, _ = store.download_file("tenant_alpha", "doc-b1")
    assert data is None
    assert code == 404


def test_tenant_003_search_marker_isolation(store):
    hits = store.search_documents("tenant_alpha", "TENANT_BETA_SECRET_MARKER_8426")
    assert len(hits) == 0


def test_tenant_004_vector_pre_filter_isolation(store):
    hits = store.vector_search("tenant_alpha", [0.8, -0.1, 0.5])
    assert all(v["tenant_id"] == "tenant_alpha" for v in hits)


def test_tenant_005_report_cross_tenant_denied(store):
    rep, code, _ = store.get_report("tenant_alpha", "rep-b1")
    assert rep is None
    assert code == 404


def test_tenant_006_cross_tenant_deletion_denied_and_preserved(store):
    del_ok, code, _ = store.delete_document("tenant_alpha", "doc-b1")
    assert not del_ok
    assert code == 404
    # Ensure doc still in beta
    b_doc, _, _ = store.get_document("tenant_beta", "doc-b1")
    assert b_doc is not None


def test_tenant_007_cross_tenant_job_status_denied(store):
    job, code, _ = store.get_job("tenant_alpha", "job-b1")
    assert job is None
    assert code == 404


def test_tenant_008_audit_events_strictly_scoped(store):
    events = store.get_audit_events("tenant_alpha")
    assert all(e["tenant_id"] == "tenant_alpha" for e in events)


def test_tenant_009_cache_cross_tenant_isolation(store):
    cached = store.get_cache_response("tenant_alpha", "query:earnings")
    assert cached is None


def test_tenant_010_citation_resolution_cross_tenant_fails(store):
    ok, _ = store.resolve_citation("tenant_alpha", "doc-b1")
    assert not ok


def test_tenant_011_worker_job_tenant_mismatch_rejected(store):
    ok, reason = store.execute_worker_job("tenant_alpha", "job-b1")
    assert not ok
    assert "security violation" in reason.lower()


def test_tenant_012_benchmark_runner_full_suite():
    runner = TenantIsolationBenchmarkRunner()
    report = runner.run_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 12
    assert report["metrics"]["cross_tenant_disclosures"] == 0
