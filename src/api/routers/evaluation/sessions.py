"""
AEGIS-DocIntel Evaluation Sessions Router (PROT-FINAL-02 / REM-05)
Exposes session status, refresh rotation, single logout, and logout-all endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from services.evaluation_gateway.activation import activation_service as gateway_activation_service
from src.services.evaluation.refresh_rotation_service import refresh_rotation_service
from src.services.evaluation.session_revocation_service import session_revocation_service

router = APIRouter(prefix="/v1/evaluation/session", tags=["Evaluation Sessions"])


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_session(req: RefreshRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        new_at, new_rt, sess = refresh_rotation_service.rotate_refresh_token(
            raw_refresh_token=req.refresh_token,
            client_ip=client_ip,
        )
        return {
            "access_token": new_at,
            "refresh_token": new_rt,
            "token_type": "bearer",
            "session_id": sess.session_id,
            "expires_in": 900,
        }
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "REFRESH_REPLAY_DETECTED", "message": str(e)},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_REFRESH_TOKEN", "message": str(e)},
        )


@router.post("/logout")
async def logout(request: Request):
    auth_hdr = request.headers.get("Authorization", "")
    if auth_hdr.startswith("Bearer "):
        raw_token = auth_hdr[7:].strip()
        session_revocation_service.revoke_by_access_token(raw_token)
    return {"status": "logged_out", "message": "Session successfully terminated."}


@router.post("/logout-all")
async def logout_all(request: Request):
    auth_hdr = request.headers.get("Authorization", "")
    if not auth_hdr.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    raw_token = auth_hdr[7:].strip()
    sess = gateway_activation_service.validate_session(raw_token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")
    count = session_revocation_service.revoke_all_evaluator_sessions(sess.evaluator_id)
    return {"status": "all_sessions_revoked", "revoked_count": count}
