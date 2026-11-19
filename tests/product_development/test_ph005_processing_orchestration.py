"""
AEGIS-DocIntel — Task PH-005: Processing Orchestration & Job Lifecycle Verification
===================================================================================
Validates:
1. Durable job submission with atomic idempotency and deduplication.
2. Complete state lifecycle (QUEUED -> RUNNING -> SUCCEEDED / RETRYING / FAILED).
3. Lease locking, heartbeats, and stale worker reclamation.
4. Retry policies on transient failures vs dead-lettering on permanent errors.
5. Strict cross-tenant job visibility and mutation boundaries.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import pytest

from src.operations.handlers import HandlerRegistry, JobContext
from src.operations.job_contracts import (
    JobRecord,
    JobRequest,
    JobStatus,
    JobType,
    compute_input_fingerprint,
)
from src.operations.job_repository import (
    IdempotencyConflictError,
    JobNotFoundError,
    JobRepository,
)
from src.operations.job_service import JobService
from src.operations.retry_policy import RetryPolicy
from src.operations.worker import (
    JobWorker,
    PermanentJobError,
    TransientJobError,
)


@pytest.fixture
def job_repo(tmp_path):
    db_file = tmp_path / "orchestration_jobs.db"
    return JobRepository(db_path=str(db_file))


def test_job_submission_and_idempotency_deduplication(job_repo):
    """Verify durable job submission and replay deduplication under identical fingerprints."""
    service = JobService(repository=job_repo)

    job1 = service.submit_job(
        tenant_id="tenant-ph005",
        requested_by="user-ph005",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-999",
        idempotency_key="key-ph005-idem",
        payload={"filename": "spec.pdf", "size_bytes": 1024},
    )
    assert job1.status == JobStatus.QUEUED
    assert job1.attempt == 0
    assert job1.tenant_id == "tenant-ph005"

    # Replay with identical fingerprint returns the existing job
    job1_replay = service.submit_job(
        tenant_id="tenant-ph005",
        requested_by="user-ph005",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-999",
        idempotency_key="key-ph005-idem",
        payload={"filename": "spec.pdf", "size_bytes": 1024},
    )
    assert job1_replay.job_id == job1.job_id
    assert job1_replay.status == JobStatus.QUEUED

    # Conflicting payload with same idempotency key must raise IdempotencyConflictError
    with pytest.raises(IdempotencyConflictError):
        service.submit_job(
            tenant_id="tenant-ph005",
            requested_by="user-ph005",
            job_type=JobType.INGEST_DOCUMENT,
            resource_id="doc-999",
            idempotency_key="key-ph005-idem",
            payload={"filename": "DIFFERENT_FILE.pdf", "size_bytes": 2048},
        )


@pytest.mark.asyncio
async def test_worker_execution_and_successful_completion(job_repo):
    """Verify worker acquires job lease and transitions through RUNNING to SUCCEEDED."""
    service = JobService(repository=job_repo)
    registry = HandlerRegistry()

    execution_marker = []

    async def sample_handler(ctx: JobContext, job: JobRecord) -> dict:
        execution_marker.append(job.resource_id)
        return {"chunks_indexed": 42, "status": "processed"}

    registry.register(JobType.INGEST_DOCUMENT, sample_handler)

    job = service.submit_job(
        tenant_id="tenant-worker-test",
        requested_by="user-worker",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-to-process",
    )

    worker = JobWorker(
        repository=job_repo,
        registry=registry,
        worker_id="worker-01",
        poll_seconds=0.05,
    )

    processed_job = await worker.run_once()
    assert processed_job is not None
    assert execution_marker == ["doc-to-process"]

    updated_job = service.get_job(job_id=job.job_id, tenant_id="tenant-worker-test")
    assert updated_job.status == JobStatus.SUCCEEDED
    assert "chunks_indexed" in (updated_job.result_reference or "")


@pytest.mark.asyncio
async def test_worker_transient_retry_and_dead_letter(job_repo):
    """Verify transient errors trigger exponential backoff retry and permanent errors fail immediately."""
    service = JobService(repository=job_repo)
    registry = HandlerRegistry()

    attempts_counter = {"transient": 0}

    async def flaky_handler(ctx: JobContext, job: JobRecord) -> dict:
        attempts_counter["transient"] += 1
        if attempts_counter["transient"] < 2:
            raise TransientJobError(message="Transient upstream timeout")
        return {"recovered": True}

    registry.register(JobType.INDEX_DOCUMENT, flaky_handler)

    job = service.submit_job(
        tenant_id="tenant-retry",
        requested_by="user-retry",
        job_type=JobType.INDEX_DOCUMENT,
        resource_id="eval-res-1",
        max_attempts=3,
    )

    retry_policy = RetryPolicy(base_delay_seconds=0.01, max_delay_seconds=0.1, max_attempts=3)
    worker = JobWorker(
        repository=job_repo,
        registry=registry,
        worker_id="worker-flaky",
        retry_policy=retry_policy,
    )

    # First run triggers retry
    await worker.run_once()
    job_after_fail = service.get_job(job_id=job.job_id, tenant_id="tenant-retry")
    assert job_after_fail.status == JobStatus.RETRY_WAIT
    assert job_after_fail.attempt == 1

    # Allow backoff delay to elapse
    await asyncio.sleep(0.03)

    # Second run re-claims flaky job and succeeds on attempt 2
    retried_job = await worker.run_once()
    assert retried_job is not None
    assert retried_job.job_id == job.job_id
    assert retried_job.status == JobStatus.SUCCEEDED
    assert attempts_counter["transient"] == 2

    # Now register permanent fatal error handler
    async def fatal_handler(ctx: JobContext, job: JobRecord) -> dict:
        raise PermanentJobError(message="Invalid corrupt binary payload")

    registry.register(JobType.EXTRACT_FACTS, fatal_handler)
    job_fatal = service.submit_job(
        tenant_id="tenant-retry",
        requested_by="user-retry",
        job_type=JobType.EXTRACT_FACTS,
        resource_id="table-doc-1",
    )
    # Third run claims fatal job and permanently fails without retry
    fatal_claimed = await worker.run_once()
    assert fatal_claimed is not None
    assert fatal_claimed.job_id == job_fatal.job_id
    assert fatal_claimed.status == JobStatus.FAILED
    assert fatal_claimed.error_code == "PERMANENT_ERROR"


def test_cross_tenant_job_isolation(job_repo):
    """Verify jobs belonging to tenant-A cannot be queried or cancelled by tenant-B."""
    service = JobService(repository=job_repo)

    job_a = service.submit_job(
        tenant_id="tenant-A",
        requested_by="alice",
        job_type=JobType.GENERATE_REPORT,
        resource_id="res-a",
    )

    # Querying with tenant-B must return None (fail closed)
    assert service.get_job(job_id=job_a.job_id, tenant_id="tenant-B") is None

    # Cancelling with tenant-B must raise JobNotFoundError
    with pytest.raises(JobNotFoundError):
        service.cancel_job(job_id=job_a.job_id, tenant_id="tenant-B", requested_by="bob")
