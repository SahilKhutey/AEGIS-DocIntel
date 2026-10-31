"""
src/operations/job_repository.py
================================
SQLite-backed, tenant-isolated transactional repository for background jobs,
leases, state transitions, and audit events.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.operations.job_contracts import (
    JobEvent,
    JobRecord,
    JobRequest,
    JobStatus,
    JobType,
    StandardErrorCode,
)
from src.operations.retry_policy import RetryDecision


class JobNotFoundError(KeyError):
    """Raised when a job is not found for the specified tenant."""
    pass


class StaleLeaseError(RuntimeError):
    """Raised when a worker attempts to update a job it no longer owns."""
    pass


class IdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused with a different input fingerprint."""
    pass


class JobRepository:
    """
    Data access layer managing durable background jobs, lease acquisition,
    heartbeats, retry schedules, and append-only operational events.
    """

    def __init__(self, db_path: str = "data/operations.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if not hasattr(self, "_mem_conn") or self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._mem_conn.row_factory = sqlite3.Row
            return self._mem_conn
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS operation_jobs (
                        job_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        job_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        attempt INTEGER NOT NULL DEFAULT 0,
                        max_attempts INTEGER NOT NULL DEFAULT 4,
                        version INTEGER NOT NULL DEFAULT 1,
                        idempotency_key TEXT NOT NULL,
                        input_fingerprint TEXT NOT NULL,
                        requested_by TEXT NOT NULL,
                        lease_owner TEXT,
                        lease_expires_at TEXT,
                        next_attempt_at TEXT,
                        result_reference TEXT,
                        error_code TEXT,
                        payload TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE (tenant_id, requested_by, idempotency_key)
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_jobs_claim
                    ON operation_jobs (status, next_attempt_at, lease_expires_at)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_jobs_tenant
                    ON operation_jobs (tenant_id, created_at DESC)
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS operation_job_events (
                        event_id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        tenant_id TEXT NOT NULL,
                        from_status TEXT NOT NULL,
                        to_status TEXT NOT NULL,
                        attempt INTEGER NOT NULL,
                        worker_id TEXT,
                        error_code TEXT,
                        message TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (job_id) REFERENCES operation_jobs(job_id) ON DELETE CASCADE,
                        UNIQUE (job_id, sequence)
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_job_events_job
                    ON operation_job_events (job_id, sequence ASC)
                """)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> JobRecord:
        payload = {}
        if row["payload"]:
            try:
                payload = json.loads(row["payload"])
            except Exception:
                payload = {}

        return JobRecord(
            job_id=row["job_id"],
            tenant_id=row["tenant_id"],
            job_type=JobType(row["job_type"]),
            resource_id=row["resource_id"],
            status=JobStatus(row["status"]),
            attempt=row["attempt"],
            max_attempts=row["max_attempts"],
            version=row["version"],
            idempotency_key=row["idempotency_key"],
            input_fingerprint=row["input_fingerprint"],
            requested_by=row["requested_by"],
            lease_owner=row["lease_owner"],
            lease_expires_at=row["lease_expires_at"],
            next_attempt_at=row["next_attempt_at"],
            result_reference=row["result_reference"],
            error_code=row["error_code"],
            payload=payload,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_event(self, row: sqlite3.Row) -> JobEvent:
        return JobEvent(
            event_id=row["event_id"],
            job_id=row["job_id"],
            sequence=row["sequence"],
            tenant_id=row["tenant_id"],
            from_status=row["from_status"],
            to_status=row["to_status"],
            attempt=row["attempt"],
            worker_id=row["worker_id"],
            error_code=row["error_code"],
            message=row["message"],
            timestamp=row["timestamp"],
        )

    def enqueue(self, request: JobRequest, max_attempts: int = 4) -> JobRecord:
        """
        Durable, idempotent enqueueing of a job.
        If idempotency key already exists for (tenant_id, requested_by):
        - Matching fingerprint: returns existing JobRecord.
        - Differing fingerprint: raises IdempotencyConflictError.
        """
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                # 1. Idempotency Check
                existing = conn.execute(
                    """
                    SELECT * FROM operation_jobs
                    WHERE tenant_id = ? AND requested_by = ? AND idempotency_key = ?
                    """,
                    (request.tenant_id, request.requested_by, request.idempotency_key),
                ).fetchone()

                if existing:
                    if existing["input_fingerprint"] != request.input_fingerprint:
                        raise IdempotencyConflictError(
                            f"Idempotency key '{request.idempotency_key}' reused with different input fingerprint."
                        )
                    return self._row_to_record(existing)

                # 2. Insert New Job Record
                job_id = f"job-{uuid.uuid4().hex}"
                payload_json = json.dumps(request.payload, default=str)

                conn.execute(
                    """
                    INSERT INTO operation_jobs (
                        job_id, tenant_id, job_type, resource_id, status,
                        attempt, max_attempts, version, idempotency_key,
                        input_fingerprint, requested_by, payload, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        request.tenant_id,
                        str(request.job_type),
                        request.resource_id,
                        str(JobStatus.QUEUED),
                        0,
                        max_attempts,
                        1,
                        request.idempotency_key,
                        request.input_fingerprint,
                        request.requested_by,
                        payload_json,
                        now,
                        now,
                    ),
                )

                # 3. Insert Initial Event
                event_id = f"evt-{uuid.uuid4().hex}"
                conn.execute(
                    """
                    INSERT INTO operation_job_events (
                        event_id, job_id, sequence, tenant_id, from_status,
                        to_status, attempt, worker_id, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        job_id,
                        1,
                        request.tenant_id,
                        "",
                        str(JobStatus.QUEUED),
                        0,
                        None,
                        "Job enqueued",
                        now,
                    ),
                )

                row = conn.execute("SELECT * FROM operation_jobs WHERE job_id = ?", (job_id,)).fetchone()
                return self._row_to_record(row)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def claim_next(
        self,
        *,
        worker_id: str,
        lease_seconds: int = 120,
        job_types: Optional[Sequence[JobType]] = None,
    ) -> Optional[JobRecord]:
        """
        Atomically claim one eligible queued, retrying, or expired-lease running job.
        Increments attempt count and sets worker lease in a single transaction.
        """
        conn = self._get_connection()
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        lease_expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat()

        try:
            with conn:
                # Build eligible query
                query = """
                    SELECT * FROM operation_jobs
                    WHERE (
                        (status = 'queued' AND (next_attempt_at IS NULL OR next_attempt_at <= ?))
                        OR (status = 'retry_wait' AND next_attempt_at <= ?)
                        OR (status = 'running' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?)
                    )
                """
                params: List[Any] = [now, now, now]

                if job_types:
                    types_placeholders = ",".join(["?"] * len(job_types))
                    query += f" AND job_type IN ({types_placeholders})"
                    params.extend([str(jt) for jt in job_types])

                # Prioritize expired leases and retries, then FIFO creation
                query += """
                    ORDER BY
                        CASE status
                            WHEN 'running' THEN 1
                            WHEN 'retry_wait' THEN 2
                            ELSE 3
                        END ASC,
                        created_at ASC
                    LIMIT 1
                """

                candidate = conn.execute(query, params).fetchone()
                if not candidate:
                    return None

                job_id = candidate["job_id"]
                curr_version = candidate["version"]
                old_status = candidate["status"]
                new_attempt = candidate["attempt"] + 1

                # Optimistically update to running with lease
                cursor = conn.execute(
                    """
                    UPDATE operation_jobs
                    SET status = ?, lease_owner = ?, lease_expires_at = ?,
                        attempt = ?, version = version + 1, updated_at = ?
                    WHERE job_id = ? AND version = ?
                    """,
                    (
                        str(JobStatus.RUNNING),
                        worker_id,
                        lease_expires,
                        new_attempt,
                        now,
                        job_id,
                        curr_version,
                    ),
                )

                if cursor.rowcount == 0:
                    # Concurrently claimed by another worker
                    return None

                # Record claim event
                seq_row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM operation_job_events WHERE job_id = ?",
                    (job_id,),
                ).fetchone()
                next_seq = seq_row[0]

                conn.execute(
                    """
                    INSERT INTO operation_job_events (
                        event_id, job_id, sequence, tenant_id, from_status,
                        to_status, attempt, worker_id, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"evt-{uuid.uuid4().hex}",
                        job_id,
                        next_seq,
                        candidate["tenant_id"],
                        old_status,
                        str(JobStatus.RUNNING),
                        new_attempt,
                        worker_id,
                        f"Claimed by worker {worker_id}" + (" (lease recovery)" if old_status == "running" else ""),
                        now,
                    ),
                )

                updated = conn.execute("SELECT * FROM operation_jobs WHERE job_id = ?", (job_id,)).fetchone()
                return self._row_to_record(updated)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def renew_lease(self, *, job_id: str, worker_id: str, lease_seconds: int = 120) -> bool:
        """Extend heartbeat lease for an in-flight job if the worker still holds it."""
        conn = self._get_connection()
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        lease_expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat()

        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE operation_jobs
                    SET lease_expires_at = ?, updated_at = ?
                    WHERE job_id = ? AND lease_owner = ? AND status = 'running'
                    """,
                    (lease_expires, now, job_id, worker_id),
                )
                return cursor.rowcount > 0
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def mark_succeeded(
        self,
        *,
        job_id: str,
        worker_id: str,
        result_reference: Optional[Any] = None,
    ) -> bool:
        """Mark job as succeeded and clear lease. Returns False if worker lost lease."""
        if result_reference is not None and not isinstance(result_reference, str):
            try:
                result_reference = json.dumps(result_reference)
            except Exception:
                result_reference = str(result_reference)
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE operation_jobs
                    SET status = ?, result_reference = ?, lease_owner = NULL,
                        lease_expires_at = NULL, version = version + 1, updated_at = ?
                    WHERE job_id = ? AND lease_owner = ? AND status = 'running'
                    """,
                    (str(JobStatus.SUCCEEDED), result_reference, now, job_id, worker_id),
                )
                if cursor.rowcount == 0:
                    return False

                row = conn.execute("SELECT tenant_id, attempt FROM operation_jobs WHERE job_id = ?", (job_id,)).fetchone()
                seq_row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM operation_job_events WHERE job_id = ?",
                    (job_id,),
                ).fetchone()

                conn.execute(
                    """
                    INSERT INTO operation_job_events (
                        event_id, job_id, sequence, tenant_id, from_status,
                        to_status, attempt, worker_id, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"evt-{uuid.uuid4().hex}",
                        job_id,
                        seq_row[0],
                        row["tenant_id"],
                        str(JobStatus.RUNNING),
                        str(JobStatus.SUCCEEDED),
                        row["attempt"],
                        worker_id,
                        "Job completed successfully",
                        now,
                    ),
                )
                return True
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def mark_failed(
        self,
        *,
        job_id: str,
        worker_id: str,
        error_code: str,
        retry_decision: RetryDecision,
    ) -> bool:
        """Transition job to retry_wait or failed state. Returns False if worker lost lease."""
        conn = self._get_connection()
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()

        try:
            with conn:
                if retry_decision.should_retry:
                    next_attempt_dt = now_dt + timedelta(seconds=retry_decision.delay_seconds)
                    next_attempt = next_attempt_dt.isoformat()
                    target_status = JobStatus.RETRY_WAIT
                else:
                    next_attempt = None
                    target_status = JobStatus.FAILED

                cursor = conn.execute(
                    """
                    UPDATE operation_jobs
                    SET status = ?, next_attempt_at = ?, error_code = ?,
                        lease_owner = NULL, lease_expires_at = NULL,
                        version = version + 1, updated_at = ?
                    WHERE job_id = ? AND lease_owner = ? AND status = 'running'
                    """,
                    (str(target_status), next_attempt, error_code, now, job_id, worker_id),
                )

                if cursor.rowcount == 0:
                    return False

                row = conn.execute("SELECT tenant_id, attempt FROM operation_jobs WHERE job_id = ?", (job_id,)).fetchone()
                seq_row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM operation_job_events WHERE job_id = ?",
                    (job_id,),
                ).fetchone()

                msg = (
                    f"Retry scheduled in {retry_decision.delay_seconds:.1f}s ({retry_decision.reason})"
                    if retry_decision.should_retry
                    else f"Permanent failure: {retry_decision.reason}"
                )

                conn.execute(
                    """
                    INSERT INTO operation_job_events (
                        event_id, job_id, sequence, tenant_id, from_status,
                        to_status, attempt, worker_id, error_code, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"evt-{uuid.uuid4().hex}",
                        job_id,
                        seq_row[0],
                        row["tenant_id"],
                        str(JobStatus.RUNNING),
                        str(target_status),
                        row["attempt"],
                        worker_id,
                        error_code,
                        msg,
                        now,
                    ),
                )
                return True
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def cancel_job(
        self,
        *,
        tenant_id: str,
        job_id: str,
        requested_by: str,
        reason: str = "User requested cancellation",
    ) -> Optional[JobRecord]:
        """Request cancellation of an active or pending job within tenant scope."""
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                row = conn.execute(
                    "SELECT * FROM operation_jobs WHERE tenant_id = ? AND job_id = ?",
                    (tenant_id, job_id),
                ).fetchone()
                if not row:
                    return None

                old_status = JobStatus(row["status"])
                if old_status.is_terminal:
                    return self._row_to_record(row)

                conn.execute(
                    """
                    UPDATE operation_jobs
                    SET status = ?, lease_owner = NULL, lease_expires_at = NULL,
                        version = version + 1, updated_at = ?
                    WHERE tenant_id = ? AND job_id = ?
                    """,
                    (str(JobStatus.CANCELLED), now, tenant_id, job_id),
                )

                seq_row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM operation_job_events WHERE job_id = ?",
                    (job_id,),
                ).fetchone()

                conn.execute(
                    """
                    INSERT INTO operation_job_events (
                        event_id, job_id, sequence, tenant_id, from_status,
                        to_status, attempt, worker_id, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"evt-{uuid.uuid4().hex}",
                        job_id,
                        seq_row[0],
                        tenant_id,
                        str(old_status),
                        str(JobStatus.CANCELLED),
                        row["attempt"],
                        requested_by,
                        reason,
                        now,
                    ),
                )

                updated = conn.execute("SELECT * FROM operation_jobs WHERE job_id = ?", (job_id,)).fetchone()
                return self._row_to_record(updated)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def manual_retry(
        self,
        *,
        tenant_id: str,
        job_id: str,
        requested_by: str,
    ) -> Optional[JobRecord]:
        """Manually reschedule a failed or cancelled job for re-execution."""
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                row = conn.execute(
                    "SELECT * FROM operation_jobs WHERE tenant_id = ? AND job_id = ?",
                    (tenant_id, job_id),
                ).fetchone()
                if not row:
                    return None

                old_status = JobStatus(row["status"])
                if old_status not in (JobStatus.FAILED, JobStatus.CANCELLED):
                    # Only terminal failed or cancelled jobs may be manually retried
                    return self._row_to_record(row)

                conn.execute(
                    """
                    UPDATE operation_jobs
                    SET status = ?, next_attempt_at = NULL, error_code = NULL,
                        lease_owner = NULL, lease_expires_at = NULL,
                        version = version + 1, updated_at = ?
                    WHERE tenant_id = ? AND job_id = ?
                    """,
                    (str(JobStatus.QUEUED), now, tenant_id, job_id),
                )

                seq_row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM operation_job_events WHERE job_id = ?",
                    (job_id,),
                ).fetchone()

                conn.execute(
                    """
                    INSERT INTO operation_job_events (
                        event_id, job_id, sequence, tenant_id, from_status,
                        to_status, attempt, worker_id, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"evt-{uuid.uuid4().hex}",
                        job_id,
                        seq_row[0],
                        tenant_id,
                        str(old_status),
                        str(JobStatus.QUEUED),
                        row["attempt"],
                        requested_by,
                        f"Manual retry initiated by {requested_by}",
                        now,
                    ),
                )

                updated = conn.execute("SELECT * FROM operation_jobs WHERE job_id = ?", (job_id,)).fetchone()
                return self._row_to_record(updated)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_job(self, tenant_id: str, job_id: str) -> Optional[JobRecord]:
        """Retrieve job record within strict tenant boundary."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM operation_jobs WHERE tenant_id = ? AND job_id = ?",
                (tenant_id, job_id),
            ).fetchone()
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def list_jobs(
        self,
        tenant_id: str,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[JobRecord], Optional[str]]:
        """List tenant jobs with optional status/type filter and cursor-based pagination."""
        conn = self._get_connection()
        try:
            query = "SELECT * FROM operation_jobs WHERE tenant_id = ?"
            params: List[Any] = [tenant_id]

            if status:
                query += " AND status = ?"
                params.append(str(status))
            if job_type:
                query += " AND job_type = ?"
                params.append(str(job_type))
            if cursor:
                query += " AND created_at < ?"
                params.append(cursor)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit + 1)

            rows = conn.execute(query, params).fetchall()
            records = [self._row_to_record(r) for r in rows[:limit]]

            next_cursor = None
            if len(rows) > limit:
                next_cursor = records[-1].created_at

            return records, next_cursor
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_events(self, tenant_id: str, job_id: str) -> List[JobEvent]:
        """Fetch ordered operational audit history for a job within tenant boundary."""
        conn = self._get_connection()
        try:
            # Enforce tenant ownership check first
            job = self.get_job(tenant_id, job_id)
            if not job:
                return []

            rows = conn.execute(
                """
                SELECT * FROM operation_job_events
                WHERE job_id = ?
                ORDER BY sequence ASC
                """,
                (job_id,),
            ).fetchall()
            return [self._row_to_event(r) for r in rows]
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_queue_stats(self, tenant_id: Optional[str] = None) -> Dict[str, int]:
        """Get operational count metrics by status."""
        conn = self._get_connection()
        try:
            query = "SELECT status, COUNT(*) as cnt FROM operation_jobs"
            params: List[Any] = []
            if tenant_id:
                query += " WHERE tenant_id = ?"
                params.append(tenant_id)
            query += " GROUP BY status"

            rows = conn.execute(query, params).fetchall()
            stats = {s.value: 0 for s in JobStatus}
            for r in rows:
                if r["status"] in stats:
                    stats[r["status"]] = r["cnt"]
            return stats
        finally:
            if self.db_path != ":memory:":
                conn.close()
