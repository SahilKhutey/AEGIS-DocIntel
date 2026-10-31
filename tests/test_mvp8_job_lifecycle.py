"""
tests/test_mvp8_job_lifecycle.py
================================
Integration tests for job lifecycle, state transitions, idempotency deduplication, and worker execution.
"""

from __future__ import annotations

import asyncio
import pytest

from src.operations.handlers import HandlerRegistry, JobContext
from src.operations.job_contracts import (
    JobRequest,
    JobStatus,
    JobType,
    compute_input_fingerprint,
)
from src.operations.job_repository import (
    IdempotencyConflictError,
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
def temp_repo(tmp_path):
    db_file = tmp_path / "test_ops_lifecycle.db"
    return JobRepository(db_path=str(db_file))


def test_idempotent_enqueue_and_conflict(temp_repo):
    service = JobService(repository=temp_repo)

    # 1. Enqueue job
    job1 = service.submit_job(
        tenant_id="tenant-alpha",
        requested_by="user-1",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-123",
        idempotency_key="idem-key-1",
        payload={"filename": "contract.pdf"},
    )
    assert job1.status == JobStatus.QUEUED
    assert job1.attempt == 0

    # 2. Replay with identical input fingerprint returns exact same job
    job1_replay = service.submit_job(
        tenant_id="tenant-alpha",
        requested_by="user-1",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-123",
        idempotency_key="idem-key-1",
        payload={"filename": "contract.pdf"},
    )
    assert job1_replay.job_id == job1.job_id
    assert job1_replay.version == job1.version

    # 3. Reuse idempotency key with conflicting fingerprint raises IdempotencyConflictError
    with pytest.raises(IdempotencyConflictError, match="different input fingerprint"):
        service.submit_job(
            tenant_id="tenant-alpha",
            requested_by="user-1",
            job_type=JobType.INGEST_DOCUMENT,
            resource_id="doc-DIFFERENT",
            idempotency_key="idem-key-1",
            payload={"filename": "different.pdf"},
        )


@pytest.mark.asyncio
async def test_worker_successful_execution_and_events(temp_repo):
    registry = HandlerRegistry()
    executed_jobs = []

    async def mock_handler(ctx: JobContext, record):
        executed_jobs.append((ctx.job_id, record.resource_id))
        return f"result-for-{record.resource_id}"

    registry.register(JobType.EXTRACT_FACTS, mock_handler)

    service = JobService(repository=temp_repo)
    job = service.submit_job(
        tenant_id="tenant-alpha",
        requested_by="user-1",
        job_type=JobType.EXTRACT_FACTS,
        resource_id="doc-456",
        idempotency_key="idem-exec-1",
    )

    worker = JobWorker(
        repository=temp_repo,
        registry=registry,
        worker_id="worker-test-1",
        lease_seconds=30,
    )

    # Run single job pass
    processed = await worker.run_once()
    assert processed is not None
    assert processed.job_id == job.job_id
    assert processed.status == JobStatus.SUCCEEDED
    assert processed.result_reference == "result-for-doc-456"
    assert processed.attempt == 1
    assert len(executed_jobs) == 1

    # Check audit events
    events = service.get_job_events(tenant_id="tenant-alpha", job_id=job.job_id)
    assert len(events) == 3  # queued -> running -> succeeded
    assert events[0].to_status == "queued"
    assert events[1].to_status == "running"
    assert events[1].worker_id == "worker-test-1"
    assert events[2].to_status == "succeeded"


@pytest.mark.asyncio
async def test_transient_error_and_exponential_retry(temp_repo):
    registry = HandlerRegistry()
    attempts_made = 0

    async def mock_failing_handler(ctx: JobContext, record):
        nonlocal attempts_made
        attempts_made += 1
        raise TransientJobError(error_code="DEPENDENCY_TIMEOUT", message="Temporary service outage")

    registry.register(JobType.INDEX_DOCUMENT, mock_failing_handler)

    service = JobService(repository=temp_repo)
    job = service.submit_job(
        tenant_id="tenant-alpha",
        requested_by="user-1",
        job_type=JobType.INDEX_DOCUMENT,
        resource_id="doc-789",
        idempotency_key="idem-retry-1",
        max_attempts=3,
    )

    worker = JobWorker(
        repository=temp_repo,
        registry=registry,
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=1.0),
        worker_id="worker-test-2",
        lease_seconds=30,
    )

    # First attempt: transient failure -> retry_wait
    res1 = await worker.run_once()
    assert res1.status == JobStatus.RETRY_WAIT
    assert res1.attempt == 1
    assert res1.next_attempt_at is not None

    # Fast forward: manually set next_attempt_at to past so it can be claimed again
    conn = temp_repo._get_connection()
    with conn:
        conn.execute(
            "UPDATE operation_jobs SET next_attempt_at = '2020-01-01T00:00:00Z' WHERE job_id = ?",
            (job.job_id,),
        )
    conn.close()

    # Second attempt: fails -> retry_wait
    res2 = await worker.run_once()
    assert res2.status == JobStatus.RETRY_WAIT
    assert res2.attempt == 2

    conn = temp_repo._get_connection()
    with conn:
        conn.execute(
            "UPDATE operation_jobs SET next_attempt_at = '2020-01-01T00:00:00Z' WHERE job_id = ?",
            (job.job_id,),
        )
    conn.close()

    # Third attempt: reaches max_attempts (3) -> terminal FAILED
    res3 = await worker.run_once()
    assert res3.status == JobStatus.FAILED
    assert res3.attempt == 3
    assert res3.error_code == "DEPENDENCY_TIMEOUT"


@pytest.mark.asyncio
async def test_permanent_error_fails_immediately(temp_repo):
    registry = HandlerRegistry()

    async def mock_perm_handler(ctx: JobContext, record):
        raise PermanentJobError(error_code="DOCUMENT_INVALID", message="Corrupted PDF bytes")

    registry.register(JobType.INGEST_DOCUMENT, mock_perm_handler)

    service = JobService(repository=temp_repo)
    job = service.submit_job(
        tenant_id="tenant-alpha",
        requested_by="user-1",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-bad",
        idempotency_key="idem-perm-1",
    )

    worker = JobWorker(
        repository=temp_repo,
        registry=registry,
        worker_id="worker-test-3",
    )

    res = await worker.run_once()
    assert res.status == JobStatus.FAILED
    assert res.attempt == 1
    assert res.error_code == "DOCUMENT_INVALID"

    # Manual retry allows rescheduling
    retried = service.retry_job(tenant_id="tenant-alpha", job_id=job.job_id, requested_by="user-1")
    assert retried.status == JobStatus.QUEUED
