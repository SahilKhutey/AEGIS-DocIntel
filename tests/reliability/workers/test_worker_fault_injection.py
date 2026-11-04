"""
tests.reliability.workers.test_worker_fault_injection
=====================================================
Tests for WP-07.05 Background Worker Reliability & Fault Injection (WORK-001 through WORK-016).
"""

import pytest
from aegis.reliability.workers import WorkerFaultInjector, WorkerReliabilityBenchmarkRunner, JobState


@pytest.fixture
def injector():
    return WorkerFaultInjector()


def test_work_001_crash_recovery_lease_expiration(injector):
    injector.submit_job("j1", "ocr", "t1", {"doc_id": "d1"})
    # Claim and simulate crash
    claimed = injector.claim_job("w-crashed", lease_seconds=1.0)
    assert claimed is not None
    injector.execute_job("w-crashed", "j1", "t1", simulate_crash=True)

    # Recovery worker claims expired lease
    rec_claim = injector.claim_job("w-rec", lease_seconds=60.0)
    assert rec_claim is not None
    assert rec_claim.job_id == "j1"
    ok, _ = injector.execute_job("w-rec", "j1", "t1")
    assert ok
    assert injector.jobs["j1"].status == JobState.COMPLETED


def test_work_002_partial_write_atomicity(injector):
    injector.submit_job("j2", "ocr", "t1", {"doc_id": "d2"})
    injector.claim_job("w-1")
    ok, _ = injector.execute_job("w-1", "j2", "t1", simulate_partial_write=True)
    assert not ok
    assert injector.jobs["j2"].result is None


def test_work_003_idempotency_duplicate_delivery(injector):
    j_a = injector.submit_job("j3", "ocr", "t1", {"doc_id": "d3"}, idempotency_key="idemp-3")
    injector.claim_job("w-1")
    injector.execute_job("w-1", "j3", "t1")

    # Duplicate delivery
    j_b = injector.submit_job("j3-dup", "ocr", "t1", {"doc_id": "d3"}, idempotency_key="idemp-3")
    assert j_b.job_id == j_a.job_id
    injector.execute_job("w-1", "j3-dup", "t1")

    # Side effects executed exactly once
    assert injector.executed_side_effects["j3"] == 1


def test_work_004_concurrent_claim_one_winner(injector):
    injector.submit_job("j4", "ocr", "t1", {"doc_id": "d4"})
    w1 = injector.claim_job("w-1")
    w2 = injector.claim_job("w-2")
    assert w1 is not None
    assert w2 is None


def test_work_005_retry_budget_exhaustion_dead_letter(injector):
    injector.submit_job("j5", "ocr", "t1", {"doc_id": "d5"}, max_retries=2)
    injector.storage_connected = False
    injector.execute_job("w-1", "j5", "t1")
    assert injector.jobs["j5"].status == JobState.RETRY_PENDING
    injector.execute_job("w-1", "j5", "t1")
    assert injector.jobs["j5"].status == JobState.FAILED
    assert injector.jobs["j5"].error_code == "DEAD_LETTER_EXHAUSTED"


def test_work_006_permanent_payload_error_no_retry(injector):
    injector.submit_job("j6", "ocr", "t1", {"doc_id": "d6", "valid": False})
    ok, _ = injector.execute_job("w-1", "j6", "t1", is_permanent_error=True)
    assert not ok
    assert injector.jobs["j6"].status == JobState.FAILED
    assert injector.jobs["j6"].retry_count == 0


def test_work_007_tenant_mismatch_security_rejection(injector):
    injector.submit_job("j7", "ocr", "tenant_beta", {"doc_id": "d7"})
    ok, _ = injector.execute_job("w-alpha", "j7", "tenant_alpha")
    assert not ok
    assert injector.jobs["j7"].error_code == "SECURITY_VIOLATION"


def test_work_008_benchmark_runner_full_suite():
    runner = WorkerReliabilityBenchmarkRunner()
    report = runner.run_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 16
    assert report["metrics"]["silent_job_losses"] == 0
    assert report["metrics"]["duplicate_execution_rate"] == 0.0
