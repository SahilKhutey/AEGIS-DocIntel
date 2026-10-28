"""
src/api/routers/health.py
=========================
AEGIS-DocIntel — Liveness and Readiness API Router.
Exposes standard non-disclosing probes for container orchestration.
"""

from __future__ import annotations

from typing import Dict
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.services.health_service import HealthService

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    dependencies: Dict[str, str]


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Liveness probe",
)
async def liveness() -> HealthResponse:
    """Verifies process is active and responsive without calling external dependencies."""
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
)
async def readiness(request: Request):
    """Verifies internal services and database storage can accept traffic."""
    container = getattr(request.app.state, "container", None)
    health_svc = HealthService(container=container)

    is_ready, dependencies = await health_svc.check_readiness()
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    resp_body = {
        "status": "ok" if is_ready else "degraded",
        "dependencies": dependencies,
    }
    return JSONResponse(status_code=status_code, content=resp_body)
