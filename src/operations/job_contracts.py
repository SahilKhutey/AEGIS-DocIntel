"""
src/operations/job_contracts.py
===============================
Data contracts for durable background jobs, operational states, retry rules, and event logs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, Optional


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRY_WAIT = "retry_wait"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def can_be_claimed(self) -> bool:
        return self in (JobStatus.QUEUED, JobStatus.RETRY_WAIT, JobStatus.RUNNING)


class JobType(StrEnum):
    INGEST_DOCUMENT = "ingest_document"
    INDEX_DOCUMENT = "index_document"
    EXTRACT_FACTS = "extract_facts"
    COMPARE_DOCUMENTS = "compare_documents"
    GENERATE_REPORT = "generate_report"


class StandardErrorCode(StrEnum):
    DOCUMENT_INVALID = "DOCUMENT_INVALID"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    DEPENDENCY_TIMEOUT = "DEPENDENCY_TIMEOUT"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    ATTEMPTS_EXHAUSTED = "ATTEMPTS_EXHAUSTED"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    PERMANENT_ERROR = "PERMANENT_ERROR"


def compute_input_fingerprint(job_type: str | JobType, resource_id: str, payload: Optional[Dict[str, Any]] = None) -> str:
    """Compute deterministic SHA-256 fingerprint of job inputs."""
    serialized = json.dumps(
        {
            "job_type": str(job_type),
            "resource_id": str(resource_id),
            "payload": payload or {},
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class JobRequest:
    tenant_id: str
    job_type: JobType
    resource_id: str
    idempotency_key: str
    input_fingerprint: str
    requested_by: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.tenant_id:
            raise ValueError("tenant_id must not be empty")
        if not self.resource_id:
            raise ValueError("resource_id must not be empty")
        if not self.idempotency_key:
            raise ValueError("idempotency_key must not be empty")
        if not self.requested_by:
            raise ValueError("requested_by must not be empty")


@dataclass(frozen=True, slots=True)
class JobRecord:
    job_id: str
    tenant_id: str
    job_type: JobType
    resource_id: str
    status: JobStatus
    attempt: int
    max_attempts: int
    version: int
    idempotency_key: str
    input_fingerprint: str
    requested_by: str
    lease_owner: Optional[str] = None
    lease_expires_at: Optional[str] = None
    next_attempt_at: Optional[str] = None
    result_reference: Optional[str] = None
    error_code: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "job_type": str(self.job_type),
            "resource_id": self.resource_id,
            "status": str(self.status),
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "version": self.version,
            "idempotency_key": self.idempotency_key,
            "input_fingerprint": self.input_fingerprint,
            "requested_by": self.requested_by,
            "lease_owner": self.lease_owner,
            "lease_expires_at": self.lease_expires_at,
            "next_attempt_at": self.next_attempt_at,
            "result_reference": self.result_reference,
            "error_code": self.error_code,
            "payload": self.payload,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True, slots=True)
class JobEvent:
    event_id: str
    job_id: str
    sequence: int
    tenant_id: str
    from_status: str
    to_status: str
    attempt: int
    worker_id: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "job_id": self.job_id,
            "sequence": self.sequence,
            "tenant_id": self.tenant_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "attempt": self.attempt,
            "worker_id": self.worker_id,
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp,
        }
