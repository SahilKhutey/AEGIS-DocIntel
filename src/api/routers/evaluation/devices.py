"""
AEGIS-DocIntel Evaluation Devices Router (PROT-FINAL-02 / REM-02)
Exposes device presence heartbeat, deactivation, and emergency recovery endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.services.evaluation.device_service import device_service
from services.evaluation_gateway.activation import activation_service as gateway_activation_service

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluation Devices"])


class DeviceRecoveryRequest(BaseModel):
    recovery_code: str = Field(..., description="Emergency recovery code issued during device binding")
    license_id: Optional[str] = Field(default=None)
    device_id: Optional[str] = Field(default=None)


@router.post("/device/recover")
@router.post("/devices/{device_id}/recover")
async def recover_device(req: DeviceRecoveryRequest, request: Request, device_id: Optional[str] = None):
    target_device = device_id or req.device_id
    if not target_device:
        raise HTTPException(status_code=400, detail="device_id must be provided")

    lic_id = req.license_id
    if not lic_id:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            sess = gateway_activation_service.validate_session(auth_hdr[7:].strip())
            if sess:
                lic_id = sess.license_id

    if not lic_id:
        raise HTTPException(status_code=400, detail="license_id must be provided")

    try:
        return device_service.recover_device(lic_id, target_device, req.recovery_code)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
