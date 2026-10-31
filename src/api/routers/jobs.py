"""
src/api/routers/jobs.py
=======================
AEGIS-DocIntel — Background Jobs API Router.
Endpoints for durable background job submission, status tracking, cancellation,
manual retry, and operational event history.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, get_current_tenant
from src.operations.job_contracts import JobStatus, JobType
from src.operations.job_repository import (
    IdempotencyConflictError,
    JobNotFoundError,
    JobRepository,
)
from src.operations.job_service import JobService

router = APIRouter(tags=["Jobs"])


def get_job_service(request: Request) -> JobService:
    """Dependency provider resolving JobService from container or app state."""
    svc = getattr(request.app.state, "job_service", None)
    if svc is not None:
        return svc

    container = getattr(request.app.state, "container", None)
    if container is not None and getattr(container, "job_service", None) is not None:
        return container.job_service

    # Fallback instantiation
    repo = getattr(container, "job_repository", None) or JobRepository()
    service = JobService(repository=repo)
    request.app.state.job_service = service
    return service


# ─────────────────────────────────────────────────────────────────
# Request / Response Schemas
# ─────────────────────────────────────────────────────────────────

class SubmitJobRequest(BaseModel):
    job_type: str = Field(..., description="Operation type (ingest_document, index_document, extract_facts, compare_documents, generate_report)")
    resource_id: str = Field(..., min_length=1, max_length=500, description="Target document or resource ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Safe input parameters")


class JobResponse(BaseModel):
    job_id: str
    tenant_id: str
    job_type: str
    resource_id: str
    status: str
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
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    status_url: Optional[str] = None


class JobListResponse(BaseModel):
    items: List[JobResponse]
    next_cursor: Optional[str] = None


class JobEventResponse(BaseModel):
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
    timestamp: str


class CancelJobRequest(BaseModel):
    reason: str = Field(default="User requested cancellation", max_length=500)


# ─────────────────────────────────────────────────────────────────
# Route Handlers
# ─────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a background processing job",
)
@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,
)
async def submit_job(
    body: SubmitJobRequest,
    request: Request,
    response: Response,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> JobResponse:
    """
    Durably enqueue a background operation for execution by worker pool.
    Guarantees idempotent deduplication via Idempotency-Key and payload fingerprint.
    """
    if not tenant.can_write_document():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Submitting background operations requires editor or admin permissions.",
        )

    try:
        jt = JobType(body.job_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported job_type: '{body.job_type}'. Allowed types: {[t.value for t in JobType]}",
        )

    svc = get_job_service(request)
    try:
        record = svc.submit_job(
            tenant_id=tenant.tenant_id,
            requested_by=tenant.principal_id,
            job_type=jt,
            resource_id=body.resource_id,
            idempotency_key=idempotency_key,
            payload=body.payload,
        )
        data = record.to_dict()
        status_url = f"/v1/jobs/{record.job_id}"
        data["status_url"] = status_url
        response.headers["Location"] = status_url
        return JobResponse(**data)
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "",
    response_model=JobListResponse,
    summary="List background jobs for authenticated tenant",
)
@router.get(
    "/",
    response_model=JobListResponse,
    include_in_schema=False,
)
async def list_jobs(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    job_type_filter: Optional[str] = Query(None, alias="job_type", description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="Cursor timestamp for pagination"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> JobListResponse:
    """List jobs visible to caller within strict tenant isolation boundary."""
    svc = get_job_service(request)

    st_enum = None
    if status_filter:
        try:
            st_enum = JobStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status filter: {status_filter}",
            )

    jt_enum = None
    if job_type_filter:
        try:
            jt_enum = JobType(job_type_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid job_type filter: {job_type_filter}",
            )

    records, next_cursor = svc.list_jobs(
        tenant_id=tenant.tenant_id,
        status=st_enum,
        job_type=jt_enum,
        limit=limit,
        cursor=cursor,
    )
    items = []
    for r in records:
        d = r.to_dict()
        d["status_url"] = f"/v1/jobs/{r.job_id}"
        items.append(JobResponse(**d))

    return JobListResponse(items=items, next_cursor=next_cursor)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get background job status and progress metadata",
)
async def get_job(
    job_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> JobResponse:
    """Fetch status and result metadata for a specific job within tenant boundary."""
    svc = get_job_service(request)
    record = svc.get_job(tenant_id=tenant.tenant_id, job_id=job_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    data = record.to_dict()
    data["status_url"] = f"/v1/jobs/{record.job_id}"
    return JobResponse(**data)


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
    summary="Cancel an active or pending background job",
)
async def cancel_job(
    job_id: str,
    request: Request,
    body: Optional[CancelJobRequest] = None,
    tenant: TenantContext = Depends(get_current_tenant),
) -> JobResponse:
    """Request safe cancellation of an active or pending job."""
    if not tenant.can_write_document():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cancelling jobs requires editor or admin permissions.",
        )

    svc = get_job_service(request)
    reason = body.reason if body else "User requested cancellation"
    try:
        record = svc.cancel_job(
            tenant_id=tenant.tenant_id,
            job_id=job_id,
            requested_by=tenant.principal_id,
            reason=reason,
        )
        data = record.to_dict()
        status_url = f"/v1/jobs/{record.job_id}"
        data["status_url"] = status_url
        return JobResponse(**data)
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )


@router.post(
    "/{job_id}/retry",
    response_model=JobResponse,
    summary="Manually reschedule a failed or cancelled background job",
)
async def retry_job(
    job_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> JobResponse:
    """Manually reschedule a failed or cancelled job for execution."""
    if not tenant.can_write_document():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Retrying jobs requires editor or admin permissions.",
        )

    svc = get_job_service(request)
    try:
        record = svc.retry_job(
            tenant_id=tenant.tenant_id,
            job_id=job_id,
            requested_by=tenant.principal_id,
        )
        data = record.to_dict()
        status_url = f"/v1/jobs/{record.job_id}"
        data["status_url"] = status_url
        return JobResponse(**data)
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )


@router.get(
    "/{job_id}/events",
    response_model=List[JobEventResponse],
    summary="Read operational audit events and attempt history for a job",
)
async def get_job_events(
    job_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[JobEventResponse]:
    """Fetch ordered transition history and worker execution attempts."""
    svc = get_job_service(request)
    # Check if job exists in tenant first
    job = svc.get_job(tenant_id=tenant.tenant_id, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    events = svc.get_job_events(tenant_id=tenant.tenant_id, job_id=job_id)
    return [JobEventResponse(**e.to_dict()) for e in events]
