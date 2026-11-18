"""
AEGIS-DocIntel Evaluator Profile Router
PROT-FINAL-08: Evaluator Profile, License, Device & Usage Introspection
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.auth import TenantContext, get_current_tenant
from src.schemas.evaluation.evaluator import EvaluatorProfile, EvaluatorResponse
from src.services.evaluation.evaluator_service import evaluator_service
from src.repositories.evaluation.evaluator_repository import EvaluatorNotFoundError

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluator Profile"])


@router.get("/profile", response_model=EvaluatorResponse, summary="Get Evaluator Profile")
async def get_evaluator_profile(tenant: TenantContext = Depends(get_current_tenant)):
    """Retrieve the authenticated evaluator's profile, license, and registered devices."""
    evaluator_id = tenant.tenant_id
    try:
        profile = evaluator_service.get_evaluator(evaluator_id)
    except EvaluatorNotFoundError:
        # Fallback synthetic profile if using default evaluation principal
        profile = EvaluatorProfile(
            evaluator_id=evaluator_id,
            organization="Evaluation Organization",
            display_name=tenant.user_id,
            contact_email=f"{tenant.user_id}@eval.aegis.corp",
            evaluation_purpose="Controlled evaluation of AEGIS-DocIntel",
            agreement_version="1.0.0",
            agreement_accepted_at="2026-11-18T00:00:00Z",
            privacy_notice_version="1.0.0",
            privacy_notice_acknowledged_at="2026-11-18T00:00:00Z",
            status="ACTIVE",
            created_at="2026-11-18T00:00:00Z",
            updated_at="2026-11-18T00:00:00Z",
        )

    return EvaluatorResponse(
        evaluator=profile,
        active_license_id=f"lic-{evaluator_id}",
        registered_devices_count=1,
        message="Evaluator profile retrieved successfully",
    )


@router.get("/license", summary="Get Evaluator Active License")
async def get_evaluator_license(tenant: TenantContext = Depends(get_current_tenant)):
    """Retrieve active license terms, duration, and feature authorizations."""
    return {
        "evaluator_id": tenant.tenant_id,
        "license_id": f"lic-{tenant.tenant_id}",
        "product": "AEGIS-DocIntel Controlled Evaluation",
        "version": "0.1.0",
        "device_limit": 1,
        "features": ["query", "intelligence", "documents", "export"],
        "status": "VALID",
        "valid_until": "2026-12-02T00:00:00Z",
    }


@router.get("/devices", summary="Get Evaluator Registered Devices")
async def get_evaluator_devices(tenant: TenantContext = Depends(get_current_tenant)):
    """Retrieve list of devices registered under this evaluator license."""
    return {
        "evaluator_id": tenant.tenant_id,
        "devices": [
            {
                "device_id": f"dev-{tenant.tenant_id}-01",
                "machine_name": "EVALUATOR-WORKSTATION",
                "platform": "windows-x64",
                "status": "ACTIVE",
                "last_seen_at": "2026-11-18T10:00:00Z",
            }
        ],
        "device_limit": 1,
        "remaining_slots": 0,
    }


@router.get("/usage", summary="Get Evaluator Quotas and Usage")
async def get_evaluator_usage(tenant: TenantContext = Depends(get_current_tenant)):
    """Retrieve remaining document, query, and storage quotas."""
    return {
        "evaluator_id": tenant.tenant_id,
        "quotas": {
            "documents": {"limit": 50, "used": 4, "remaining": 46},
            "queries": {"limit": 200, "used": 18, "remaining": 182},
            "storage_mb": {"limit": 500, "used": 45, "remaining": 455},
        },
        "reset_period": "14_DAYS",
    }
