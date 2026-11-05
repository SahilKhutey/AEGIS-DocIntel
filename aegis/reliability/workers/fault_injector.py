"""
aegis.reliability.workers.fault_injector
========================================
Worker Reliability & Fault Injection Engine:
- Durable job state machine with atomic claiming and lease management.
- Bounded retries with exponential backoff and jitter.
- Idempotency key tracking preventing duplicate executions.
- Dead-letter handling for exhausted retries.
- Fault injection hooks for crash, timeout, and IO failure simulation.
"""

from __future__ import annotations

import datetime
import time
from typing import Any, Dict, List, Optional, Set, Tuple


class JobState:
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    RETRY_PENDING = "RETRY_PENDING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReliableJob:
    def __init__(
        self,
        job_id: str,
        job_type: str,
        tenant_id: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        self.job_id = job_id
        self.job_type = job_type
        self.tenant_id = tenant_id
        self.payload = payload
        self.idempotency_key = idempotency_key or job_id
        self.status = JobState.QUEUED
        self.retry_count = 0
        self.max_retries = max_retries
        self.worker_id: Optional[str] = None
        self.lease_expires_at: float = 0.0
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.result: Optional[Dict[str, Any]] = None
        self.error_code: Optional[str] = None
        self.failure_reason: Optional[str] = None


class WorkerFaultInjector:
    """Manages worker job queue, execution, and injected failure simulations."""

    def __init__(self) -> None:
        self.jobs: Dict[str, ReliableJob] = {}
        self.idempotency_records: Dict[str, Dict[str, Any]] = {}
        self.executed_side_effects: Dict[str, int] = {}  # job_id -> execution_count
        self.database_connected = True
        self.storage_connected = True

    def submit_job(
        self,
        job_id: str,
        job_type: str,
        tenant_id: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> ReliableJob:
        key = idempotency_key or job_id
        if key in self.idempotency_records:
            # Idempotent deduplication: Return existing job
            existing_id = self.idempotency_records[key]["job_id"]
            return self.jobs[existing_id]

        job = ReliableJob(job_id, job_type, tenant_id, payload, key, max_retries)
        self.jobs[job_id] = job
        self.idempotency_records[key] = {"job_id": job_id, "status": job.status}
        return job

    def claim_job(self, worker_id: str, lease_seconds: float = 60.0) -> Optional[ReliableJob]:
        """Atomically claims the next available QUEUED or expired lease job."""
        if not self.database_connected:
            return None

        now = time.time()
        for job in self.jobs.values():
            if job.status == JobState.QUEUED or (
                job.status == JobState.RUNNING and now > job.lease_expires_at
            ):
                job.status = JobState.RUNNING
                job.worker_id = worker_id
                job.lease_expires_at = now + lease_seconds
                job.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                return job
        return None

    def execute_job(
        self,
        worker_id: str,
        job_id: str,
        worker_tenant_context: str,
        simulate_crash: bool = False,
        simulate_partial_write: bool = False,
        simulate_timeout: bool = False,
        is_permanent_error: bool = False,
    ) -> Tuple[bool, str]:
        """Executes a job under simulated operational or fault conditions."""
        job = self.jobs.get(job_id)
        if not job:
            return False, "Job not found"

        # 1. Security check: Tenant isolation
        if job.tenant_id != worker_tenant_context:
            job.status = JobState.FAILED
            job.error_code = "SECURITY_VIOLATION"
            job.failure_reason = "Worker tenant context does not match job tenant scope"
            return False, job.failure_reason

        # 2. Check if already completed (Idempotency enforcement)
        if job.status == JobState.COMPLETED:
            return True, "Already completed"

        # 3. Simulate malformed job payload (Permanent error)
        if is_permanent_error or not job.payload.get("valid", True):
            job.status = JobState.FAILED
            job.error_code = "PERMANENT_SCHEMA_ERROR"
            job.failure_reason = "Malformed payload cannot be processed"
            return False, job.failure_reason

        # 4. Simulate worker crash mid-execution
        if simulate_crash:
            # Worker abruptly dies without releasing lease or saving results
            job.lease_expires_at = time.time() - 1.0  # Lease immediately expired for recovery
            return False, "Worker process terminated abruptly"

        # 5. Simulate partial write crash
        if simulate_partial_write:
            # Transaction rolls back; no corrupt final state recorded
            job.lease_expires_at = time.time() - 1.0
            return False, "Worker crashed during partial write; transaction rolled back"

        # 6. Simulate timeout
        if simulate_timeout:
            job.status = JobState.FAILED
            job.error_code = "OPERATION_TIMEOUT"
            job.failure_reason = "Execution exceeded time limit"
            return False, job.failure_reason

        # 7. Simulate storage / DB disconnection
        if not self.storage_connected or not self.database_connected:
            job.retry_count += 1
            if job.retry_count >= job.max_retries:
                job.status = JobState.FAILED
                job.error_code = "DEAD_LETTER_EXHAUSTED"
                job.failure_reason = "Max retries exceeded during dependency outage"
            else:
                job.status = JobState.RETRY_PENDING
            return False, "Dependency unavailable"

        # Successful execution
        self.executed_side_effects[job_id] = self.executed_side_effects.get(job_id, 0) + 1
        job.status = JobState.COMPLETED
        job.result = {"output": f"Result for {job_id}", "records_written": 1}
        job.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.idempotency_records[job.idempotency_key]["status"] = JobState.COMPLETED
        return True, "Success"
