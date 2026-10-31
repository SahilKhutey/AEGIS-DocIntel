"""
tests/test_mvp8_job_recovery.py
===============================
Tests for worker crash recovery, stale worker lease rejection, and heartbeat renewal.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import pytest

from src.operations.handlers import HandlerRegistry, JobContext
from src.operations.job_contracts import JobStatus, JobType
from src.operations.job_repository import JobRepository
from src.operations.job_service import JobService
from src.operations.retry_policy import RetryPolicy
from src.operations.worker import JobWorker


@pytest.fixture
def temp_repo(tmp_path):
    db_file = tmp_path / "test_ops_recovery.db"
    return JobRepository(db_path=str(db_file))


@pytest.mark.asyncio
async def test_worker_crash_recovery_after_lease_expiry(temp_repo):
    """
    If worker A crashes while executing a job, its lease eventually expires.
    Worker B must be able to claim the job and finish it.
    """
    registry = HandlerRegistry()

    async def normal_handler(ctx: JobContext, record):
        return {"processed": True}

    registry.register(JobType.INDEX_DOCUMENT, normal_handler)

    service = JobService(repository=temp_repo)
    job = service.submit_job(
        tenant_id="tenant-crash",
        requested_by="admin",
        job_type=JobType.INDEX_DOCUMENT,
        resource_id="doc-999",
        idempotency_key="idem-crash-1",
    )

    # Worker A claims the job with a short 2-second lease
    claimed_a = temp_repo.claim_next(worker_id="worker-a", lease_seconds=2)
    assert claimed_a is not None
    assert claimed_a.job_id == job.job_id
    assert claimed_a.status == JobStatus.RUNNING
    assert claimed_a.lease_owner == "worker-a"

    # Immediately, Worker B tries to claim, but should find nothing because Worker A's lease is active
    claimed_b_early = temp_repo.claim_next(worker_id="worker-b", lease_seconds=60)
    assert claimed_b_early is None

    # Simulate Worker A crashing and time elapsing beyond lease_expires_at
    past_expiry = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    conn = temp_repo._get_connection()
    with conn:
        conn.execute(
            "UPDATE operation_jobs SET lease_expires_at = ? WHERE job_id = ?",
            (past_expiry, job.job_id),
        )
    conn.close()

    # Now Worker B should detect expired lease, claim the job, and increment the attempt
    claimed_b = temp_repo.claim_next(worker_id="worker-b", lease_seconds=60)
    assert claimed_b is not None
    assert claimed_b.job_id == job.job_id
    assert claimed_b.status == JobStatus.RUNNING
    assert claimed_b.lease_owner == "worker-b"
    assert claimed_b.attempt == 2

    # Worker B completes the job
    success = temp_repo.mark_succeeded(
        job_id=claimed_b.job_id,
        worker_id="worker-b",
        result_reference="recovered-ref",
    )
    assert success is True

    final_job = temp_repo.get_job(tenant_id="tenant-crash", job_id=job.job_id)
    assert final_job is not None
    assert final_job.status == JobStatus.SUCCEEDED
    assert final_job.result_reference == "recovered-ref"


@pytest.mark.asyncio
async def test_stale_worker_rejection(temp_repo):
    """
    If Worker A awakens after its lease expired and Worker B already claimed the job,
    Worker A's attempts to complete or fail the job must return False (lease lost).
    """
    service = JobService(repository=temp_repo)
    job = service.submit_job(
        tenant_id="tenant-stale",
        requested_by="admin",
        job_type=JobType.EXTRACT_FACTS,
        resource_id="doc-stale-1",
    )

    # Worker A claims job
    claimed_a = temp_repo.claim_next(worker_id="worker-a", lease_seconds=2)
    assert claimed_a is not None

    # Fast forward expiry
    past_expiry = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    conn = temp_repo._get_connection()
    with conn:
        conn.execute(
            "UPDATE operation_jobs SET lease_expires_at = ? WHERE job_id = ?",
            (past_expiry, job.job_id),
        )
    conn.close()

    # Worker B claims job
    claimed_b = temp_repo.claim_next(worker_id="worker-b", lease_seconds=60)
    assert claimed_b is not None

    # Worker A now wakes up and attempts to mark succeeded -> must return False
    marked = temp_repo.mark_succeeded(
        job_id=claimed_a.job_id,
        worker_id="worker-a",
        result_reference="stale-ref",
    )
    assert marked is False

    # Worker A attempts to renew lease -> fails
    renewed = temp_repo.renew_lease(
        job_id=claimed_a.job_id,
        worker_id="worker-a",
        lease_seconds=30,
    )
    assert renewed is False


@pytest.mark.asyncio
async def test_lease_renewal_prevents_stale_reclaim(temp_repo):
    """
    A living worker renewing its lease prevents other workers from claiming the job.
    """
    service = JobService(repository=temp_repo)
    job = service.submit_job(
        tenant_id="tenant-renew",
        requested_by="admin",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-renew-1",
    )

    claimed = temp_repo.claim_next(worker_id="worker-live", lease_seconds=5)
    assert claimed is not None

    # Successfully renew lease
    renewed = temp_repo.renew_lease(
        job_id=claimed.job_id,
        worker_id="worker-live",
        lease_seconds=300,
    )
    assert renewed is True

    # Another worker cannot claim it
    claimed_other = temp_repo.claim_next(worker_id="worker-other", lease_seconds=30)
    assert claimed_other is None
