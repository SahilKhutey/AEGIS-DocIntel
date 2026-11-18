"""
AEGIS-DocIntel Privacy Requests Router
PROT-FINAL-07: Workstream 07.07
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.services.compliance.privacy_request_service import (
    PrivacyAccessDenied,
    privacy_request_service,
)

router = APIRouter(prefix="/v1/compliance/privacy-requests", tags=["Compliance Privacy"])


class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(..., description="access, erasure, rectification, or export")
    requester_id: str = Field(..., description="Identifier of the requesting evaluator/principal")


class ErasureExecuteRequest(BaseModel):
    document_ids: Optional[List[str]] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_privacy_request(
    body: PrivacyRequestCreate,
    tenant_id: str = "tenant-eval-default",
) -> Dict[str, Any]:
    """Submits a new data subject privacy request."""
    return privacy_request_service.submit_request(
        tenant_id=tenant_id,
        requester_id=body.requester_id,
        request_type=body.request_type,
    )


@router.get("/{request_id}")
def get_privacy_request_status(
    request_id: str,
    tenant_id: str = "tenant-eval-default",
) -> Dict[str, Any]:
    """Retrieves privacy request status under authenticated tenant boundary (COMP-008)."""
    try:
        return privacy_request_service.get_request_status(
            tenant_id=tenant_id,
            request_id=request_id,
        )
    except PrivacyAccessDenied as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{request_id}/execute")
def execute_privacy_erasure(
    request_id: str,
    body: ErasureExecuteRequest,
    tenant_id: str = "tenant-eval-default",
) -> Dict[str, Any]:
    """Executes cascading erasure for an approved privacy request (COMP-009, COMP-010)."""
    try:
        return privacy_request_service.execute_erasure(
            tenant_id=tenant_id,
            request_id=request_id,
            target_document_ids=body.document_ids,
        )
    except PrivacyAccessDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
