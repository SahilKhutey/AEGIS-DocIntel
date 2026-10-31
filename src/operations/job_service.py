"""
src/operations/job_service.py
=============================
High-level service orchestrating durable job submissions, lifecycle queries,
cancellations, retries, and operational status.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.operations.job_contracts import (
    JobEvent,
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


class JobService:
    """
    Coordinates tenant-isolated background job submissions, status tracking,
    cancellations, manual retries, and audit history.
    """

    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def submit_job(
        self,
        *,
        tenant_id: str,
        requested_by: str,
        job_type: JobType,
        resource_id: str,
        idempotency_key: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        max_attempts: int = 4,
    ) -> JobRecord:
        """
        Durable, idempotent submission of a background job.
        Computes input fingerprint and guarantees atomic deduplication.
        """
        effective_key = idempotency_key or f"idem-{uuid.uuid4().hex}"
        payload = payload or {}
        fingerprint = compute_input_fingerprint(job_type, resource_id, payload)

        request = JobRequest(
            tenant_id=tenant_id,
            job_type=job_type,
            resource_id=resource_id,
            idempotency_key=effective_key,
            input_fingerprint=fingerprint,
            requested_by=requested_by,
            payload=payload,
        )

        return self.repository.enqueue(request, max_attempts=max_attempts)

    def get_job(self, *, tenant_id: str, job_id: str) -> Optional[JobRecord]:
        """Fetch job record strictly within caller's tenant boundary."""
        return self.repository.get_job(tenant_id=tenant_id, job_id=job_id)

    def list_jobs(
        self,
        *,
        tenant_id: str,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[JobRecord], Optional[str]]:
        """List jobs for the authenticated tenant with optional filters."""
        return self.repository.list_jobs(
            tenant_id=tenant_id,
            status=status,
            job_type=job_type,
            limit=limit,
            cursor=cursor,
        )

    def cancel_job(
        self,
        *,
        tenant_id: str,
        job_id: str,
        requested_by: str,
        reason: str = "User requested cancellation",
    ) -> JobRecord:
        """Request cancellation of an active or pending job."""
        record = self.repository.cancel_job(
            tenant_id=tenant_id,
            job_id=job_id,
            requested_by=requested_by,
            reason=reason,
        )
        if not record:
            raise JobNotFoundError(f"Job '{job_id}' not found for tenant '{tenant_id}'.")
        return record

    def retry_job(
        self,
        *,
        tenant_id: str,
        job_id: str,
        requested_by: str,
    ) -> JobRecord:
        """Manually reschedule a terminal failed or cancelled job."""
        record = self.repository.manual_retry(
            tenant_id=tenant_id,
            job_id=job_id,
            requested_by=requested_by,
        )
        if not record:
            raise JobNotFoundError(f"Job '{job_id}' not found for tenant '{tenant_id}'.")
        return record

    def get_job_events(self, *, tenant_id: str, job_id: str) -> List[JobEvent]:
        """Get complete event audit log for a job within tenant boundary."""
        return self.repository.get_events(tenant_id=tenant_id, job_id=job_id)

    def get_stats(self, *, tenant_id: Optional[str] = None) -> Dict[str, int]:
        """Get count statistics by status."""
        return self.repository.get_queue_stats(tenant_id=tenant_id)
