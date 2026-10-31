"""
src/operations/__init__.py
==========================
AEGIS-DocIntel — Background Operations & Reliability Infrastructure.
"""

from src.operations.handlers import (
    HandlerRegistry,
    JobContext,
    JobHandler,
    build_default_handler_registry,
)
from src.operations.job_contracts import (
    JobEvent,
    JobRecord,
    JobRequest,
    JobStatus,
    JobType,
    StandardErrorCode,
    compute_input_fingerprint,
)
from src.operations.job_repository import (
    IdempotencyConflictError,
    JobNotFoundError,
    JobRepository,
    StaleLeaseError,
)
from src.operations.job_service import JobService
from src.operations.retry_policy import RetryDecision, RetryPolicy
from src.operations.worker import JobWorker, PermanentJobError, TransientJobError

__all__ = [
    "HandlerRegistry",
    "IdempotencyConflictError",
    "JobContext",
    "JobEvent",
    "JobHandler",
    "JobNotFoundError",
    "JobRecord",
    "JobRepository",
    "JobRequest",
    "JobService",
    "JobStatus",
    "JobType",
    "JobWorker",
    "PermanentJobError",
    "RetryDecision",
    "RetryPolicy",
    "StaleLeaseError",
    "StandardErrorCode",
    "TransientJobError",
    "build_default_handler_registry",
    "compute_input_fingerprint",
]
