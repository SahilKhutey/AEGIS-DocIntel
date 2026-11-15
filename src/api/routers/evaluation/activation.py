"""
AEGIS-DocIntel Evaluation Activation Router (PROT-FINAL-02 / REM-02)
Exposes device challenge-response registration and license activation endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.services.evaluation.activation_service import activation_service

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluation Activation"])


class ChallengeRequest(BaseModel):
    client_id: Optional[str] = Field(default=None)
    machine_name: str
    platform: str
    hardware_fingerprint: str
    activation_code: str
    installation_id: str
    device_public_key: str


class ActivationRequest(BaseModel):
    client_id: Optional[str] = None
    machine_name: str = "Evaluation Host"
    platform: str = "windows"
    hardware_fingerprint: str = "hw-fingerprint"
    activation_code: str
    device_public_key: str
    device_label: Optional[str] = "Evaluation Device"
    client_version: Optional[str] = "1.1.0"


class VerifyChallengeRequest(BaseModel):
    challenge_id: str
    signature: str
    installation_id: str
    client_version: Optional[str] = "1.1.0"


@router.post("/challenge")
async def request_challenge(req: ChallengeRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    client_id = req.client_id or f"client-{uuid.uuid4().hex[:8]}"
    try:
        return activation_service.generate_challenge(
            client_id=client_id,
            machine_name=req.machine_name,
            platform=req.platform,
            client_ip=client_ip,
            hardware_fingerprint=req.hardware_fingerprint,
            activation_code=req.activation_code,
            installation_id=req.installation_id,
            device_public_key=req.device_public_key,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "CODE_UNAVAILABLE", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "INVALID_PARAMETERS", "message": str(e)})


@router.post("/activate")
async def activate_instance(req: ActivationRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    client_id = req.client_id or f"client-{uuid.uuid4().hex[:8]}"
    try:
        return activation_service.activate_instance(
            client_id=client_id,
            machine_name=req.machine_name,
            platform=req.platform,
            client_ip=client_ip,
            hardware_fingerprint=req.hardware_fingerprint,
            activation_code=req.activation_code,
            device_public_key=req.device_public_key,
            device_label=req.device_label or "Evaluation Device",
            client_version=req.client_version or "1.1.0",
        )
    except PermissionError as e:
        msg = str(e)
        if "Device limit exceeded" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "DEVICE_LIMIT_EXCEEDED", "message": msg})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "LICENSE_UNAVAILABLE", "message": msg})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "INVALID_ACTIVATION_CODE", "message": str(e)})


@router.post("/challenge/verify")
async def verify_challenge(req: VerifyChallengeRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        return activation_service.verify_challenge_and_activate(
            challenge_id=req.challenge_id,
            signature=req.signature,
            installation_id=req.installation_id,
            client_version=req.client_version or "1.1.0",
            client_ip=client_ip,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "CHALLENGE_FAILED", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "INVALID_CHALLENGE", "message": str(e)})
