"""
AEGIS-DocIntel Evaluation Usage & Quotas Router (PROT-FINAL-02 / REM-04)
Exposes evaluator usage summaries, limits, and historical balances.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from services.evaluation_gateway.quotas import quota_manager as gateway_quota_manager
from services.evaluation_gateway.activation import activation_service as gateway_activation_service

router = APIRouter(prefix="/v1/evaluation/usage", tags=["Evaluation Usage"])


@router.get("")
async def get_my_usage(request: Request):
    auth_hdr = request.headers.get("Authorization", "")
    if not auth_hdr.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    sess = gateway_activation_service.validate_session(auth_hdr[7:].strip())
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")

    summary = gateway_quota_manager.get_quota_status(sess.license_id)
    return summary
