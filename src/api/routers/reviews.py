"""
src/api/routers/reviews.py
==========================
FastAPI Router for Human-in-the-Loop review, governance, decisions, audit trails, and feedback.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, get_current_tenant
from src.engines.governance.contracts import (
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
    ReviewStatus,
)
from src.engines.governance.evidence_validator import EvidenceValidationError
from src.engines.governance.feedback import FeedbackCategory
from src.engines.governance.policy import ReviewPolicyError
from src.engines.governance.review_service import ReviewService
from src.repositories.review_repository import (
    IdempotencyConflictError,
    ReviewNotFoundError,
    StaleReviewVersionError,
)

router = APIRouter(prefix="/reviews", tags=["Governance"])
log = structlog.get_logger("aegis.api.reviews")

_default_service: Optional[ReviewService] = None


def get_review_service(request: Request) -> ReviewService:
    global _default_service
    container = getattr(request.app.state, "container", None)
    if container is not None and hasattr(container, "review_service") and container.review_service is not None:
        return container.review_service
    svc = getattr(request.app.state, "review_service", None)
    if svc is not None:
        return svc
    if _default_service is None:
        _default_service = ReviewService()
    return _default_service


def _build_actor(tenant: TenantContext) -> ReviewActor:
    return ReviewActor(
        tenant_id=tenant.tenant_id,
        user_id=tenant.user_id,
        roles=tenant.roles,
    )


# ─────────────────────────────────────────────────────────────────
# Request & Response Schemas
# ─────────────────────────────────────────────────────────────────

class ReviewItemResponse(BaseModel):
    review_id: str
    tenant_id: str
    candidate_id: str
    candidate_type: str
    document_id: str
    status: str
    version: int
    assigned_to: Optional[str] = None
    candidate_data: Dict[str, Any]
    current_revision_id: Optional[str] = None
    created_at: str
    updated_at: str


class ReviewQueueResponse(BaseModel):
    items: List[ReviewItemResponse]
    next_cursor: Optional[str] = None


class ClaimRequest(BaseModel):
    expected_version: int = Field(ge=1, description="Expected version of review item for optimistic locking")


class DecisionRequest(BaseModel):
    action: Literal["approve", "correct", "reject", "request_evidence"]
    expected_version: int = Field(ge=1, description="Expected version for concurrency verification")
    rationale: str = Field(min_length=3, max_length=2000, description="Reviewer rationale")
    corrected_value: Optional[Any] = Field(default=None, description="Corrected value if action is 'correct'")
    corrected_type: Optional[str] = Field(default=None, description="Type descriptor (decimal, string, etc.)")
    unit: Optional[str] = Field(default=None, description="Optional unit descriptor")
    evidence_quote: Optional[str] = Field(default=None, max_length=5000, description="Authoritative evidence quote")


class DecisionRecordResponse(BaseModel):
    decision_id: str
    review_id: str
    tenant_id: str
    actor_id: str
    action: str
    from_status: str
    to_status: str
    version_reviewed: int
    rationale: str
    evidence_quote: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: str


class AuditEventResponse(BaseModel):
    event_id: str
    review_id: str
    sequence: int
    tenant_id: str
    actor_id: str
    action: str
    previous_status: str
    new_status: str
    previous_version: int
    new_version: int
    rationale: str
    revision_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str


class DecisionResponse(BaseModel):
    item: ReviewItemResponse
    decision: DecisionRecordResponse
    audit_event: AuditEventResponse


class ReopenRequest(BaseModel):
    expected_version: int = Field(ge=1)
    rationale: str = Field(min_length=5, max_length=2000, description="Administrative reopening justification")


class FeedbackRequest(BaseModel):
    category: str = Field(description="Feedback category (e.g., wrong_value, bad_evidence)")
    notes: Optional[str] = Field(default="", max_length=2000)
    corrected_reference: Optional[str] = Field(default=None)


class GovernanceMetricsResponse(BaseModel):
    total_items: int
    decided_count: int
    approval_rate: float
    correction_rate: float
    rejection_rate: float
    evidence_failure_rate: float
    feedback_categories: Dict[str, int]


# ─────────────────────────────────────────────────────────────────
# Route Handlers
# ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=ReviewQueueResponse,
    summary="List tenant review queue items",
)
@router.get(
    "/",
    response_model=ReviewQueueResponse,
    include_in_schema=False,
)
async def list_reviews(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned reviewer ID"),
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> ReviewQueueResponse:
    """Retrieve review items for the authenticated tenant with cursor pagination."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    parsed_status = ReviewStatus(status_filter) if status_filter else None

    items, next_cursor = svc.list_queue(
        actor=actor,
        status=parsed_status,
        assigned_to=assigned_to,
        limit=limit,
        cursor=cursor,
    )
    return ReviewQueueResponse(
        items=[ReviewItemResponse(**i.to_dict()) for i in items],
        next_cursor=next_cursor,
    )


@router.get(
    "/approved-facts",
    response_model=List[Dict[str, Any]],
    summary="Retrieve approved facts for report generation",
)
async def get_approved_facts(
    request: Request,
    document_id: Optional[str] = Query(None, description="Optional document filter"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[Dict[str, Any]]:
    """Fetch approved and corrected facts only. Pending and rejected facts are excluded."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    return svc.get_approved_facts_for_report(actor=actor, document_id=document_id)


@router.get(
    "/metrics",
    response_model=GovernanceMetricsResponse,
    summary="Get review governance and quality metrics",
)
async def get_metrics(
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> GovernanceMetricsResponse:
    """Compute review quality metrics across tenant items."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    metrics_data = svc.get_metrics(actor)
    return GovernanceMetricsResponse(**metrics_data)


@router.get(
    "/{review_id}",
    response_model=ReviewItemResponse,
    summary="Fetch review item details and evidence links",
)
async def get_review_detail(
    review_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ReviewItemResponse:
    """Fetch a single review item within tenant boundary."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    item = svc.get_review(actor=actor, review_id=review_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item '{review_id}' not found.",
        )
    return ReviewItemResponse(**item.to_dict())


@router.post(
    "/{review_id}/claim",
    response_model=ReviewItemResponse,
    summary="Claim a review item",
)
async def claim_review(
    review_id: str,
    body: ClaimRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ReviewItemResponse:
    """Claim a review item, transitioning it from pending or needs_evidence to in_review."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    try:
        updated = svc.claim(
            actor=actor,
            review_id=review_id,
            expected_version=body.expected_version,
        )
        return ReviewItemResponse(**updated.to_dict())
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReviewPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except StaleReviewVersionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/{review_id}/decisions",
    response_model=DecisionResponse,
    summary="Submit a reviewer decision (approve, correct, reject, request_evidence)",
)
async def submit_decision(
    review_id: str,
    body: DecisionRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> DecisionResponse:
    """
    Submit a reviewer decision with evidence validation, optimistic locking,
    and single-transaction audit event logging.
    """
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    request_id = getattr(request.state, "request_id", None)

    submission = DecisionSubmission(
        action=ReviewAction(body.action),
        expected_version=body.expected_version,
        rationale=body.rationale,
        corrected_value=body.corrected_value,
        corrected_type=body.corrected_type,
        unit=body.unit,
        evidence_quote=body.evidence_quote,
    )

    try:
        item, dec, audit = svc.decide(
            actor=actor,
            review_id=review_id,
            submission=submission,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
        return DecisionResponse(
            item=ReviewItemResponse(**item.to_dict()),
            decision=DecisionRecordResponse(**dec.to_dict()),
            audit_event=AuditEventResponse(**audit.to_dict()),
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReviewPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except StaleReviewVersionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except EvidenceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{review_id}/history",
    response_model=List[AuditEventResponse],
    summary="Read audit history of state transitions",
)
async def get_history(
    review_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[AuditEventResponse]:
    """Retrieve ordered, append-only history of every successful state transition."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    events = svc.get_history(actor=actor, review_id=review_id)
    return [AuditEventResponse(**e.to_dict()) for e in events]


@router.post(
    "/{review_id}/feedback",
    summary="Record structured evaluation feedback",
)
async def submit_feedback(
    review_id: str,
    body: FeedbackRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> Dict[str, str]:
    """Record structured feedback categorizing extraction quality or reviewer corrections."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    try:
        cat = FeedbackCategory(body.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feedback category '{body.category}'.",
        )

    try:
        fb_id = svc.submit_feedback(
            actor=actor,
            review_id=review_id,
            category=cat,
            notes=body.notes or "",
            corrected_reference=body.corrected_reference,
        )
        return {"feedback_id": fb_id, "status": "recorded"}
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{review_id}/reopen",
    response_model=DecisionResponse,
    summary="Reopen a completed review under administrative authority",
)
async def reopen_review(
    review_id: str,
    body: ReopenRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> DecisionResponse:
    """Reopen an approved, corrected, or rejected item back into active review."""
    svc = get_review_service(request)
    actor = _build_actor(tenant)
    request_id = getattr(request.state, "request_id", None)
    try:
        item, dec, audit = svc.reopen(
            actor=actor,
            review_id=review_id,
            expected_version=body.expected_version,
            rationale=body.rationale,
            request_id=request_id,
        )
        return DecisionResponse(
            item=ReviewItemResponse(**item.to_dict()),
            decision=DecisionRecordResponse(**dec.to_dict()),
            audit_event=AuditEventResponse(**audit.to_dict()),
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ReviewPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except StaleReviewVersionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
