"""
AEGIS-DocIntel Evaluation Entitlements Router (PROT-FINAL-02 / REM-03)
Exposes server-authoritative feature entitlement inspection.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from src.services.evaluation.entitlement_service import entitlement_service
from services.evaluation_gateway.activation import activation_service as gateway_activation_service

router = APIRouter(prefix="/v1/evaluation/entitlements", tags=["Evaluation Entitlements"])


class CheckFeatureRequest(BaseModel):
    feature: str


@router.get("")
async def get_my_entitlements(request: Request):
    auth_hdr = request.headers.get("Authorization", "")
    if not auth_hdr.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    sess = gateway_activation_service.validate_session(auth_hdr[7:].strip())
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")

    policy = entitlement_service.get_effective_policy(sess.license_id)
    return {
        "license_id": sess.license_id,
        "features": sorted(list(policy.features)),
        "permissions": sorted(list(policy.permissions)),
    }


@router.post("/check")
async def check_feature_entitlement(req: CheckFeatureRequest, request: Request):
    auth_hdr = request.headers.get("Authorization", "")
    if not auth_hdr.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    sess = gateway_activation_service.validate_session(auth_hdr[7:].strip())
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")

    is_allowed = entitlement_service.is_feature_enabled(sess.license_id, req.feature)
    return {
        "feature": req.feature,
        "is_entitled": is_allowed,
    }
