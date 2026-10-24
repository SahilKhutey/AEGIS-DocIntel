"""
AEGIS-DocIntel — Enterprise API Contracts & Asynchronous Jobs Tests
===================================================================
Verifies:
- Durable Job state machine transitions and progress tracking
- Multi-tenant boundary enforcement on async jobs (IDOR protection)
- Job serialization and pipeline version fingerprinting
- Document upload and deletion RBAC permission checks
"""
import pytest
from src.core.jobs import JobManager, JobStatus, JobType
from src.core.security_context import (
    TenantContext,
    ROLE_VIEWER,
    ROLE_EDITOR,
    ROLE_TENANT_ADMIN,
)


def test_job_lifecycle_and_transitions():
    manager = JobManager()

    job = manager.create_job(
        tenant_id="tenant-acme",
        job_type=JobType.INGEST,
        metadata={"filename": "contract.pdf"},
    )
    assert job.status == JobStatus.QUEUED
    assert job.progress == 0.0
    assert job.tenant_id == "tenant-acme"
    assert "aegis" in job.pipeline_version

    # Progress update transitions to RUNNING
    manager.update_progress(job.job_id, "tenant-acme", progress=45.5)
    updated = manager.get_job(job.job_id, "tenant-acme")
    assert updated.status == JobStatus.RUNNING
    assert updated.progress == 45.5

    # Complete job transitions to SUCCEEDED
    manager.complete_job(job.job_id, "tenant-acme", result={"chunks": 12})
    finished = manager.get_job(job.job_id, "tenant-acme")
    assert finished.status == JobStatus.SUCCEEDED
    assert finished.progress == 100.0
    assert finished.result == {"chunks": 12}
    assert finished.completed_at is not None

    # Cannot update progress after completion
    res = manager.update_progress(job.job_id, "tenant-acme", progress=50.0)
    assert res is None


def test_job_isolation_across_tenants():
    manager = JobManager()

    job_alpha = manager.create_job(
        tenant_id="tenant-alpha",
        job_type=JobType.REINDEX,
    )

    # Tenant Bravo attempting to read Alpha's job gets None
    assert manager.get_job(job_alpha.job_id, "tenant-bravo") is None

    # Tenant Bravo attempting to cancel Alpha's job gets None
    assert manager.cancel_job(job_alpha.job_id, "tenant-bravo") is None
    assert manager.get_job(job_alpha.job_id, "tenant-alpha").status == JobStatus.QUEUED

    # List jobs isolates results
    manager.create_job(tenant_id="tenant-bravo", job_type=JobType.PURGE)
    alpha_jobs = manager.list_jobs(tenant_id="tenant-alpha")
    bravo_jobs = manager.list_jobs(tenant_id="tenant-bravo")

    assert len(alpha_jobs) == 1
    assert alpha_jobs[0].job_id == job_alpha.job_id
    assert len(bravo_jobs) == 1
    assert bravo_jobs[0].tenant_id == "tenant-bravo"


def test_job_failure_and_cancellation():
    manager = JobManager()

    job_fail = manager.create_job("tenant-x", JobType.EXPORT)
    manager.fail_job(job_fail.job_id, "tenant-x", error="S3 bucket access denied")
    assert job_fail.status == JobStatus.FAILED
    assert job_fail.error == "S3 bucket access denied"

    job_cancel = manager.create_job("tenant-x", JobType.PURGE)
    manager.cancel_job(job_cancel.job_id, "tenant-x")
    assert job_cancel.status == JobStatus.CANCELLED


def test_document_rbac_permission_rules():
    viewer = TenantContext(
        tenant_id="t1",
        principal_id="u1",
        roles=frozenset([ROLE_VIEWER]),
    )
    editor = TenantContext(
        tenant_id="t1",
        principal_id="u2",
        roles=frozenset([ROLE_EDITOR]),
    )
    admin = TenantContext(
        tenant_id="t1",
        principal_id="u3",
        roles=frozenset([ROLE_TENANT_ADMIN]),
    )

    # Viewer
    assert viewer.can_read_document() is True
    assert viewer.can_write_document() is False
    assert viewer.can_delete_document() is False

    # Editor
    assert editor.can_read_document() is True
    assert editor.can_write_document() is True
    assert editor.can_delete_document() is False

    # Admin
    assert admin.can_read_document() is True
    assert admin.can_write_document() is True
    assert admin.can_delete_document() is True
