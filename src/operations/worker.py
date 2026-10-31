"""
src/operations/worker.py
========================
Resilient background worker with atomic claiming, lease renewal heartbeats,
timeout enforcement, error classification, and graceful shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from collections.abc import Callable
from typing import Optional

from src.operations.handlers import HandlerRegistry, JobContext
from src.operations.job_contracts import JobRecord, StandardErrorCode
from src.operations.job_repository import JobRepository
from src.operations.retry_policy import RetryPolicy

logger = logging.getLogger("aegis.operations.worker")


class PermanentJobError(Exception):
    """Permanent error that should not be retried (e.g. invalid file, schema error)."""
    def __init__(self, error_code: str = StandardErrorCode.PERMANENT_ERROR, message: str = ""):
        super().__init__(message or error_code)
        self.error_code = error_code


class TransientJobError(Exception):
    """Transient error that should be retried with exponential backoff (e.g. timeout)."""
    def __init__(self, error_code: str = StandardErrorCode.DEPENDENCY_TIMEOUT, message: str = ""):
        super().__init__(message or error_code)
        self.error_code = error_code


class JobWorker:
    """
    Background worker process executing registered jobs with bounded retries,
    lease renewal heartbeats, and atomic status transitions.
    """

    def __init__(
        self,
        *,
        repository: JobRepository,
        registry: HandlerRegistry,
        retry_policy: Optional[RetryPolicy] = None,
        worker_id: str,
        lease_seconds: int = 120,
        poll_seconds: float = 1.0,
        operation_timeout_seconds: float = 300.0,
        is_shutting_down: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.retry_policy = retry_policy or RetryPolicy()
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self.poll_seconds = poll_seconds
        self.operation_timeout_seconds = operation_timeout_seconds
        self._external_shutdown = is_shutting_down
        self._stopped = False
        self._active_jobs = 0

    def is_shutting_down(self) -> bool:
        if self._stopped:
            return True
        if self._external_shutdown and self._external_shutdown():
            return True
        return False

    def stop(self) -> None:
        """Signal worker to stop claiming new jobs and drain in-flight work."""
        logger.info(f"Worker {self.worker_id} stopping...")
        self._stopped = True

    async def _heartbeat_loop(self, job_id: str, stop_event: asyncio.Event) -> None:
        """Periodically renew lease while job execution is underway."""
        interval = max(5.0, self.lease_seconds / 3.0)
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                break
            except asyncio.TimeoutError:
                renewed = self.repository.renew_lease(
                    job_id=job_id,
                    worker_id=self.worker_id,
                    lease_seconds=self.lease_seconds,
                )
                if not renewed:
                    logger.warning(
                        f"Worker {self.worker_id} lost lease for job {job_id} during execution heartbeat."
                    )
                    break

    async def process_job(self, job: JobRecord) -> bool:
        """Execute a claimed job with lease renewal heartbeat and timeout."""
        handler = self.registry.get(job.job_type)
        ctx = JobContext(
            tenant_id=job.tenant_id,
            job_id=job.job_id,
            attempt=job.attempt,
            worker_id=self.worker_id,
        )

        stop_heartbeat = asyncio.Event()
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(job.job_id, stop_heartbeat))

        try:
            logger.info(
                f"Worker {self.worker_id} starting job {job.job_id} "
                f"({job.job_type}) for tenant {job.tenant_id} [Attempt {job.attempt}]"
            )

            result_ref = await asyncio.wait_for(
                handler(ctx, job),
                timeout=self.operation_timeout_seconds,
            )

            committed = self.repository.mark_succeeded(
                job_id=job.job_id,
                worker_id=self.worker_id,
                result_reference=result_ref,
            )
            if not committed:
                logger.error(f"Worker {self.worker_id} failed to commit success: lease lost for {job.job_id}")
                return False

            logger.info(f"Worker {self.worker_id} completed job {job.job_id} successfully.")
            return True

        except PermanentJobError as exc:
            logger.warning(f"Permanent job error on {job.job_id}: {exc}")
            decision = self.retry_policy.decide(attempt=job.attempt, retryable=False)
            self.repository.mark_failed(
                job_id=job.job_id,
                worker_id=self.worker_id,
                error_code=exc.error_code,
                retry_decision=decision,
            )
            return False

        except TransientJobError as exc:
            logger.warning(f"Transient job error on {job.job_id}: {exc}")
            decision = self.retry_policy.decide(attempt=job.attempt, retryable=True)
            self.repository.mark_failed(
                job_id=job.job_id,
                worker_id=self.worker_id,
                error_code=exc.error_code,
                retry_decision=decision,
            )
            return False

        except asyncio.TimeoutError:
            logger.warning(f"Job {job.job_id} timed out after {self.operation_timeout_seconds}s")
            decision = self.retry_policy.decide(attempt=job.attempt, retryable=True)
            self.repository.mark_failed(
                job_id=job.job_id,
                worker_id=self.worker_id,
                error_code=StandardErrorCode.DEPENDENCY_TIMEOUT,
                retry_decision=decision,
            )
            return False

        except (ValueError, TypeError, KeyError) as exc:
            # Permanent validation error
            logger.error(f"Non-retryable data error in job {job.job_id}: {exc}")
            decision = self.retry_policy.decide(attempt=job.attempt, retryable=False)
            self.repository.mark_failed(
                job_id=job.job_id,
                worker_id=self.worker_id,
                error_code=StandardErrorCode.DOCUMENT_INVALID,
                retry_decision=decision,
            )
            return False

        except (ConnectionError, IOError, sqlite3.OperationalError) as exc:
            # Transient infrastructure error
            logger.error(f"Transient infrastructure error in job {job.job_id}: {exc}")
            decision = self.retry_policy.decide(attempt=job.attempt, retryable=True)
            self.repository.mark_failed(
                job_id=job.job_id,
                worker_id=self.worker_id,
                error_code=StandardErrorCode.DEPENDENCY_TIMEOUT,
                retry_decision=decision,
            )
            return False

        except Exception as exc:
            # Unhandled unexpected error: classify based on retry policy
            logger.exception(f"Unhandled exception in job {job.job_id}: {exc}")
            decision = self.retry_policy.decide(attempt=job.attempt, retryable=True)
            self.repository.mark_failed(
                job_id=job.job_id,
                worker_id=self.worker_id,
                error_code=StandardErrorCode.PROCESSING_FAILED,
                retry_decision=decision,
            )
            return False

        finally:
            stop_heartbeat.set()
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def run_once(self) -> Optional[JobRecord]:
        """Claim and execute one eligible job. Returns claimed JobRecord or None."""
        if self.is_shutting_down():
            return None

        job = self.repository.claim_next(
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
        )
        if not job:
            return None

        self._active_jobs += 1
        try:
            await self.process_job(job)
            # Re-fetch latest state
            return self.repository.get_job(job.tenant_id, job.job_id)
        finally:
            self._active_jobs -= 1

    async def run_loop(self) -> None:
        """Continuous execution loop until shutdown is signaled."""
        logger.info(f"Worker {self.worker_id} entering execution loop.")
        while not self.is_shutting_down():
            job = await self.run_once()
            if job is None and not self.is_shutting_down():
                await asyncio.sleep(self.poll_seconds)
        logger.info(f"Worker {self.worker_id} exited loop.")
