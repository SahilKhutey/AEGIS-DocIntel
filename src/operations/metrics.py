"""
src/operations/metrics.py
=========================
Prometheus metrics instrumentation for background jobs, queues, workers, and leases.
Strict invariant: Labels are low-cardinality only (job_type, status, error_code).
Never use document_id, tenant_id, or raw error messages as labels.
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:
    class _MockMetric:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    Counter = Gauge = Histogram = _MockMetric  # type: ignore

JOBS_SUBMITTED = Counter(
    "aegis_jobs_submitted_total",
    "Total background jobs submitted",
    ["job_type"],
)

JOBS_COMPLETED = Counter(
    "aegis_jobs_completed_total",
    "Total background jobs successfully completed",
    ["job_type"],
)

JOBS_FAILED = Counter(
    "aegis_jobs_failed_total",
    "Total background jobs failed",
    ["job_type", "error_code"],
)

JOBS_RETRIED = Counter(
    "aegis_jobs_retried_total",
    "Total background job retry attempts scheduled",
    ["job_type", "reason"],
)

QUEUE_DEPTH = Gauge(
    "aegis_jobs_queue_depth",
    "Current count of background jobs by status",
    ["job_type", "status"],
)

QUEUE_WAIT_SECONDS = Histogram(
    "aegis_jobs_queue_wait_seconds",
    "Time elapsed between job enqueue and worker claim",
    ["job_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

EXECUTION_SECONDS = Histogram(
    "aegis_jobs_execution_seconds",
    "Time elapsed during job execution by worker",
    ["job_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

EXPIRED_LEASES = Counter(
    "aegis_jobs_expired_leases_total",
    "Total worker leases that expired before completion",
    ["job_type"],
)

HANDLER_ERRORS = Counter(
    "aegis_job_handler_errors_total",
    "Total exceptions raised in job handlers",
    ["job_type", "error_code"],
)
