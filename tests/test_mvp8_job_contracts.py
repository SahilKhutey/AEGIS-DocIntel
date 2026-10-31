"""
tests/test_mvp8_job_contracts.py
================================
Unit tests for background job contracts, status invariants, and input fingerprinting.
"""

from __future__ import annotations

import pytest

from src.operations.job_contracts import (
    JobEvent,
    JobRecord,
    JobRequest,
    JobStatus,
    JobType,
    compute_input_fingerprint,
)


def test_job_status_invariants():
    assert JobStatus.SUCCEEDED.is_terminal is True
    assert JobStatus.FAILED.is_terminal is True
    assert JobStatus.CANCELLED.is_terminal is True
    assert JobStatus.QUEUED.is_terminal is False
    assert JobStatus.RUNNING.is_terminal is False
    assert JobStatus.RETRY_WAIT.is_terminal is False

    assert JobStatus.QUEUED.can_be_claimed is True
    assert JobStatus.RETRY_WAIT.can_be_claimed is True
    assert JobStatus.RUNNING.can_be_claimed is True
    assert JobStatus.SUCCEEDED.can_be_claimed is False
    assert JobStatus.FAILED.can_be_claimed is False
    assert JobStatus.CANCELLED.can_be_claimed is False


def test_input_fingerprint_deterministic():
    fp1 = compute_input_fingerprint(JobType.EXTRACT_FACTS, "doc-1", {"schema": "contracts"})
    fp2 = compute_input_fingerprint(JobType.EXTRACT_FACTS, "doc-1", {"schema": "contracts"})
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex length

    # Changing resource id alters fingerprint
    fp_diff_res = compute_input_fingerprint(JobType.EXTRACT_FACTS, "doc-2", {"schema": "contracts"})
    assert fp1 != fp_diff_res

    # Changing payload alters fingerprint
    fp_diff_payload = compute_input_fingerprint(JobType.EXTRACT_FACTS, "doc-1", {"schema": "financial"})
    assert fp1 != fp_diff_payload


def test_job_request_validation():
    # Valid request
    req = JobRequest(
        tenant_id="tenant-1",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-1",
        idempotency_key="idem-1",
        input_fingerprint="fp-1",
        requested_by="user-1",
    )
    assert req.tenant_id == "tenant-1"
    assert req.payload == {}

    # Empty tenant_id rejected
    with pytest.raises(ValueError, match="tenant_id"):
        JobRequest(
            tenant_id="",
            job_type=JobType.INGEST_DOCUMENT,
            resource_id="doc-1",
            idempotency_key="idem-1",
            input_fingerprint="fp-1",
            requested_by="user-1",
        )

    # Empty resource_id rejected
    with pytest.raises(ValueError, match="resource_id"):
        JobRequest(
            tenant_id="tenant-1",
            job_type=JobType.INGEST_DOCUMENT,
            resource_id="",
            idempotency_key="idem-1",
            input_fingerprint="fp-1",
            requested_by="user-1",
        )


def test_job_record_and_event_serialization():
    record = JobRecord(
        job_id="job-100",
        tenant_id="tenant-1",
        job_type=JobType.COMPARE_DOCUMENTS,
        resource_id="comp-1",
        status=JobStatus.QUEUED,
        attempt=0,
        max_attempts=4,
        version=1,
        idempotency_key="idem-100",
        input_fingerprint="fp-100",
        requested_by="user-1",
        payload={"doc_ids": ["d1", "d2"]},
        created_at="2026-10-31T12:00:00Z",
        updated_at="2026-10-31T12:00:00Z",
    )
    d = record.to_dict()
    assert d["job_id"] == "job-100"
    assert d["status"] == "queued"
    assert d["payload"]["doc_ids"] == ["d1", "d2"]

    event = JobEvent(
        event_id="evt-100",
        job_id="job-100",
        sequence=1,
        tenant_id="tenant-1",
        from_status="",
        to_status="queued",
        attempt=0,
        message="Job enqueued",
        timestamp="2026-10-31T12:00:00Z",
    )
    ed = event.to_dict()
    assert ed["event_id"] == "evt-100"
    assert ed["to_status"] == "queued"
