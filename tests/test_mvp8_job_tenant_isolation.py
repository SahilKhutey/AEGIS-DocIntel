"""
tests/test_mvp8_job_tenant_isolation.py
======================================
Tests verifying strict tenant isolation across all background job repository and service operations.
"""

from __future__ import annotations

import pytest

from src.operations.job_contracts import JobStatus, JobType
from src.operations.job_repository import JobRepository
from src.operations.job_service import JobService


@pytest.fixture
def temp_repo(tmp_path):
    db_file = tmp_path / "test_ops_tenant_isolation.db"
    return JobRepository(db_path=str(db_file))


def test_cross_tenant_isolation_in_repository(temp_repo):
    service = JobService(repository=temp_repo)

    job_a = service.submit_job(
        tenant_id="tenant-acme",
        requested_by="alice",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-acme-1",
    )

    job_b = service.submit_job(
        tenant_id="tenant-globex",
        requested_by="bob",
        job_type=JobType.INGEST_DOCUMENT,
        resource_id="doc-globex-1",
    )

    # 1. get_job cross-tenant check
    assert temp_repo.get_job(tenant_id="tenant-globex", job_id=job_a.job_id) is None
    assert temp_repo.get_job(tenant_id="tenant-acme", job_id=job_b.job_id) is None

    # 2. list_jobs cross-tenant check
    acme_jobs, _ = temp_repo.list_jobs(tenant_id="tenant-acme")
    assert len(acme_jobs) == 1
    assert acme_jobs[0].job_id == job_a.job_id

    globex_jobs, _ = temp_repo.list_jobs(tenant_id="tenant-globex")
    assert len(globex_jobs) == 1
    assert globex_jobs[0].job_id == job_b.job_id

    # 3. cancel_job cross-tenant check
    assert temp_repo.cancel_job(tenant_id="tenant-globex", job_id=job_a.job_id, requested_by="bob") is None

    # 4. get_events cross-tenant check
    assert temp_repo.get_events(tenant_id="tenant-globex", job_id=job_a.job_id) == []

    # 5. manual_retry cross-tenant check
    assert temp_repo.manual_retry(tenant_id="tenant-globex", job_id=job_a.job_id, requested_by="bob") is None
