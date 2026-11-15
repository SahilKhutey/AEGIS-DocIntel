"""
AEGIS-DocIntel Evaluation Licenses Router (PROT-FINAL-02 / REM-02)
Exposes license verification, public keys, and status inspection.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.services.evaluation.license_service import license_service

router = APIRouter(prefix="/v1/evaluation/license", tags=["Evaluation Licensing"])


class LicenseValidationRequest(BaseModel):
    license: Dict[str, Any]
    user_id: Optional[str] = None
    device_id: Optional[str] = None


@router.post("/validate")
async def validate_license(req: LicenseValidationRequest):
    ok, err, parsed = license_service.verify_license(
        req.license,
        expected_user_id=req.user_id,
        expected_device_id=req.device_id,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if err == "LICENSE_REVOKED" else status.HTTP_400_BAD_REQUEST,
            detail={"error": err or "INVALID_LICENSE", "message": "License validation failed."},
        )
    return {"status": "valid", "license": parsed}


@router.get("/public-keys")
async def get_public_keys():
    return {"keys": license_service.get_public_keys()}
