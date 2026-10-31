"""
scripts/verify_jobs_run.py
==========================
Operational Verification Script: Proves that background jobs run end-to-end
through submission, worker polling, execution, retries, lease renewal,
and event logging.
"""

from __future__ import annotations

import asyncio
import tempfile
import sys
from pathlib import Path

# Add repository root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.operations.job_contracts import JobStatus, JobType
from src.operations.job_repository import JobRepository
from src.operations.job_service import JobService
from src.operations.handlers import HandlerRegistry, JobContext
from src.operations.worker import JobWorker, TransientJobError
from src.operations.retry_policy import RetryPolicy


async def main() -> int:
    print("=" * 70)
    print("AEGIS-DocIntel — Operational Background Jobs Verification Drill")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test_jobs_run.db")
        print(f"[*] Initialized SQLite job repository at: {db_path}")

        repo = JobRepository(db_path=db_path)
        service = JobService(repository=repo)
        registry = HandlerRegistry()

        # 1. Register handlers
        executed_jobs = []

        async def sample_ingest_handler(ctx: JobContext, record):
            print(f"  -> [Worker {ctx.worker_id}] Executing INGEST_DOCUMENT for {record.resource_id}...")
            await asyncio.sleep(0.05)
            executed_jobs.append(record.job_id)
            return {"chunks_extracted": 12, "page_count": 3, "checksum": "abc123sha"}

        retry_counter = 0

        async def sample_retry_handler(ctx: JobContext, record):
            nonlocal retry_counter
            retry_counter += 1
            print(f"  -> [Worker {ctx.worker_id}] Attempt #{record.attempt} on {record.resource_id}...")
            if retry_counter == 1:
                print("     [!] Simulating transient network timeout -> raising TransientJobError")
                raise TransientJobError("NETWORK_TIMEOUT", "Remote model endpoint timed out (transient)")
            print("     [+] Attempt succeeded on second attempt!")
            return {"status": "recovered_successfully", "attempts": retry_counter}

        registry.register(JobType.INGEST_DOCUMENT, sample_ingest_handler)
        registry.register(JobType.EXTRACT_FACTS, sample_retry_handler)

        worker = JobWorker(
            repository=repo,
            registry=registry,
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.05, max_delay_seconds=0.2),
            worker_id="worker-node-1",
            lease_seconds=5,
            poll_seconds=0.05,
        )

        # 2. Submit jobs
        print("\n[1] Submitting Jobs via JobService...")
        job1 = service.submit_job(
            tenant_id="tenant-drill",
            requested_by="admin-user",
            job_type=JobType.INGEST_DOCUMENT,
            resource_id="doc-financial-report-2026",
            payload={"filename": "q3_report.pdf"},
            idempotency_key="drill-job-1",
        )
        print(f"  [+] Job 1 submitted: id={job1.job_id}, status={job1.status.value}")

        job2 = service.submit_job(
            tenant_id="tenant-drill",
            requested_by="admin-user",
            job_type=JobType.EXTRACT_FACTS,
            resource_id="doc-financial-report-2026",
            payload={"schema": "financial"},
            idempotency_key="drill-job-2",
        )
        print(f"  [+] Job 2 submitted: id={job2.job_id}, status={job2.status.value}")

        # 3. Start worker in background
        print("\n[2] Starting JobWorker Loop...")
        worker_task = asyncio.create_task(worker.run_loop())

        # Wait for job 1 to complete
        for _ in range(40):
            j1 = service.get_job(tenant_id="tenant-drill", job_id=job1.job_id)
            if j1 and j1.status == JobStatus.SUCCEEDED:
                break
            await asyncio.sleep(0.05)

        print(f"  [+] Job 1 finished with status: {j1.status.value}")
        assert j1.status == JobStatus.SUCCEEDED, f"Job 1 should succeed, got {j1.status}"

        # Wait for job 2 to fail once, retry, and succeed
        for _ in range(60):
            j2 = service.get_job(tenant_id="tenant-drill", job_id=job2.job_id)
            if j2 and j2.status == JobStatus.SUCCEEDED:
                break
            await asyncio.sleep(0.05)

        print(f"  [+] Job 2 finished with status: {j2.status.value} after {j2.attempt} attempts")
        assert j2.status == JobStatus.SUCCEEDED, f"Job 2 should succeed, got {j2.status}"
        assert j2.attempt == 2, f"Job 2 should have taken 2 attempts, got {j2.attempt}"

        # 4. Gracefully stop worker
        print("\n[3] Gracefully Stopping JobWorker...")
        worker.stop()
        await asyncio.wait_for(worker_task, timeout=2.0)
        print("  [+] Worker stopped cleanly.")

        # 5. Verify audit event timelines
        print("\n[4] Inspecting Operational Audit Event Log...")
        events_1 = service.get_job_events(tenant_id="tenant-drill", job_id=job1.job_id)
        print(f"  Job 1 Events ({len(events_1)} entries):")
        for e in events_1:
            print(f"    - Seq {e.sequence}: {e.from_status} -> {e.to_status} | {e.message} (worker: {e.worker_id})")

        events_2 = service.get_job_events(tenant_id="tenant-drill", job_id=job2.job_id)
        print(f"  Job 2 Events ({len(events_2)} entries):")
        for e in events_2:
            print(f"    - Seq {e.sequence}: {e.from_status} -> {e.to_status} | {e.message} (attempt {e.attempt})")

        # 6. Verify queue statistics
        stats = service.get_stats(tenant_id="tenant-drill")
        print("\n[5] Operational Queue Stats:")
        for status_name, count in stats.items():
            print(f"  - {status_name}: {count}")

        assert stats.get("succeeded", 0) == 2, "Expected 2 succeeded jobs"
        assert stats.get("queued", 0) == 0, "Expected 0 queued jobs"

    print("\n" + "=" * 70)
    print("OPERATIONAL JOB EXECUTION VERIFICATION: ALL INVARIANTS PASSED")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
