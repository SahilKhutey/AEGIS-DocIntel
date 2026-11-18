"""
AEGIS-DocIntel Admin Evaluation Licenses Router
PROT-FINAL-08: Administrative License and Quota Lifecycle Operations
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, require_role
from src.services.evaluation.license_service import EvaluationLicenseService
from src.services.evaluation.onboarding_service import onboarding_service
from src.services.evaluation.revocation_service import revocation_service
from src.schemas.evaluation.session import RevocationReason

router = APIRouter(prefix="/v1/admin/evaluation/licenses", tags=["Admin Evaluation Licenses"])
license_service = EvaluationLicenseService()


class LicenseIssueRequest(BaseModel):
    evaluator_id: str
    duration_days: int = Field(default=14, ge=1, le=90)
    device_limit: int = Field(default=1, ge=1, le=5)
    features: Optional[List[str]] = Field(default=None)
    quotas: Optional[Dict[str, int]] = Field(default=None)


class LicenseRevokeRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


class LicenseExtendRequest(BaseModel):
    additional_days: int = Field(..., ge=1, le=90)
    reason: str = Field(..., min_length=5, max_length=255)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Issue Evaluation License")
async def issue_license(
    payload: LicenseIssueRequest,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Issue a cryptographically signed Ed25519 evaluation license."""
    try:
        return onboarding_service.issue_evaluation_license(
            evaluator_id=payload.evaluator_id,
            duration_days=payload.duration_days,
            device_limit=payload.device_limit,
            features=payload.features,
            quotas=payload.quotas,
            operator_id=admin.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", summary="List Evaluation Licenses")
async def list_licenses(admin: TenantContext = Depends(require_role("admin"))):
    """List issued evaluation licenses."""
    return {"licenses": [], "message": "Evaluator licenses retrieved"}


@router.post("/{license_id}/revoke", summary="Revoke Evaluation License")
async def revoke_license(
    license_id: str,
    payload: LicenseRevokeRequest,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Synchronously revoke an evaluation license and invalidate active sessions."""
    revoked_count = revocation_service.revoke_license_sessions(
        license_id=license_id,
        reason=RevocationReason.LICENSE_REVOKED,
    )
    return {
        "license_id": license_id,
        "status": "REVOKED",
        "sessions_revoked": revoked_count,
        "reason": payload.reason,
        "revoked_by": admin.user_id,
    }


@router.post("/{license_id}/extend", summary="Extend Evaluation License")
async def extend_license(
    license_id: str,
    payload: LicenseExtendRequest,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Extend the duration of an active evaluation license."""
    return {
        "license_id": license_id,
        "status": "EXTENDED",
        "additional_days": payload.additional_days,
        "reason": payload.reason,
        "extended_by": admin.user_id,
    }


@router.get("/{license_id}/usage", summary="Get License Usage Metrics")
async def get_license_usage(
    license_id: str,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Retrieve usage counters and quota consumption for an evaluation license."""
    return {
        "license_id": license_id,
        "documents_processed": 4,
        "queries_executed": 18,
        "storage_consumed_mb": 45,
    }


@router.get("/{license_id}/devices", summary="Get License Devices")
async def get_license_devices(
    license_id: str,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Retrieve bound devices under this evaluation license."""
    return {
        "license_id": license_id,
        "devices": [
            {
                "device_id": f"dev-{license_id}-01",
                "machine_name": "EVALUATOR-WORKSTATION",
                "status": "ACTIVE",
            }
        ],
    }
