"""
AEGIS-DocIntel — Asynchronous Job Contracts & State Machine
===========================================================
Defines durable job lifecycle states, progress tracking, and tenant isolation:
- JobStatus enum (QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED)
- Job dataclass with progress %, pipeline version fingerprint, and metadata
- JobManager interface ensuring tenant-isolated job lookups and state transitions
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import structlog

log = structlog.get_logger("aegis.jobs")

PIPELINE_VERSION = "aegis-v1.4.0"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    INGEST = "ingest"
    REINDEX = "reindex"
    BATCH_INGEST = "batch_ingest"
    PURGE = "purge"
    EXPORT = "export"


@dataclass
class Job:
    job_id: str
    tenant_id: str
    job_type: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0  # 0.0 to 100.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    pipeline_version: str = PIPELINE_VERSION
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "job_type": self.job_type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "progress": round(self.progress, 2),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "pipeline_version": self.pipeline_version,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class JobManager:
    """
    Manages tenant-scoped async jobs and atomic lifecycle transitions.
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}

    def create_job(
        self,
        tenant_id: str,
        job_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """Create a new job in QUEUED state for the specified tenant."""
        if not tenant_id:
            raise ValueError("tenant_id is required to create a job")

        job_id = f"job_{uuid.uuid4().hex[:16]}"
        now = time.time()
        job = Job(
            job_id=job_id,
            tenant_id=tenant_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            progress=0.0,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._jobs[job_id] = job
        log.info("Created async job", job_id=job_id, tenant_id=tenant_id, job_type=job_type)
        return job

    def get_job(self, job_id: str, tenant_id: str) -> Optional[Job]:
        """Retrieve job by id, strictly verifying tenant ownership."""
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return None
        return job

    def list_jobs(
        self,
        tenant_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> List[Job]:
        """List jobs belonging to the tenant, with optional status filter."""
        results = [
            j for j in self._jobs.values()
            if j.tenant_id == tenant_id
            and (status is None or j.status == status)
        ]
        results.sort(key=lambda j: j.created_at, reverse=True)
        return results[:limit]

    def update_progress(
        self,
        job_id: str,
        tenant_id: str,
        progress: float,
        status: Optional[JobStatus] = None,
    ) -> Optional[Job]:
        """Update job progress percentage (clamped 0-100) and optional status."""
        job = self.get_job(job_id, tenant_id)
        if not job or job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
            return None

        job.progress = max(0.0, min(100.0, float(progress)))
        if status:
            job.status = status
        elif job.status == JobStatus.QUEUED and progress > 0.0:
            job.status = JobStatus.RUNNING
        job.updated_at = time.time()
        return job

    def complete_job(
        self,
        job_id: str,
        tenant_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> Optional[Job]:
        """Transition job to SUCCEEDED state."""
        job = self.get_job(job_id, tenant_id)
        if not job:
            return None

        now = time.time()
        job.status = JobStatus.SUCCEEDED
        job.progress = 100.0
        job.result = result or {}
        job.updated_at = now
        job.completed_at = now
        log.info("Job succeeded", job_id=job_id, tenant_id=tenant_id)
        return job

    def fail_job(
        self,
        job_id: str,
        tenant_id: str,
        error: str,
    ) -> Optional[Job]:
        """Transition job to FAILED state."""
        job = self.get_job(job_id, tenant_id)
        if not job:
            return None

        now = time.time()
        job.status = JobStatus.FAILED
        job.error = error
        job.updated_at = now
        job.completed_at = now
        log.warning("Job failed", job_id=job_id, tenant_id=tenant_id, error=error)
        return job

    def cancel_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> Optional[Job]:
        """Transition job to CANCELLED state if not already completed."""
        job = self.get_job(job_id, tenant_id)
        if not job or job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED):
            return None

        now = time.time()
        job.status = JobStatus.CANCELLED
        job.updated_at = now
        job.completed_at = now
        log.info("Job cancelled", job_id=job_id, tenant_id=tenant_id)
        return job
