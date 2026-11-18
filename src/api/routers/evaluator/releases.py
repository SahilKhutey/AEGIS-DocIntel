"""
AEGIS-DocIntel Evaluator Releases Router
PROT-FINAL-08: Release Metadata, Authenticated Downloads, and Verification
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from src.api.auth import TenantContext, get_current_tenant
from src.schemas.evaluation.release import (
    ArtifactVerificationRequest,
    ArtifactVerificationResponse,
    DownloadTokenRequest,
    DownloadTokenResponse,
    ReleaseManifest,
)
from src.services.evaluation.release_access_service import (
    DownloadLinkExpiredError,
    UnauthorizedDownloadError,
    release_access_service,
)

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluator Releases"])


@router.get("/releases", summary="List Available Evaluation Releases")
async def list_evaluation_releases(tenant: TenantContext = Depends(get_current_tenant)):
    """List published evaluation releases and platform manifests."""
    manifests = release_access_service.release_repo.list_manifests()
    return {
        "releases": [m.model_dump() for m in manifests],
        "current_recommended_version": "0.1.0",
    }


@router.get("/releases/{version}/manifest", response_model=ReleaseManifest, summary="Get Release Manifest")
async def get_release_manifest(version: str):
    """Public/evaluator endpoint to retrieve release manifest and signature."""
    manifest = release_access_service.release_repo.get_manifest(version)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Release manifest for version '{version}' not found.",
        )
    return manifest


@router.post("/releases/download-token", response_model=DownloadTokenResponse, summary="Request Signed Download Link")
async def request_download_token(
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Generate time-limited signed download token for authorized evaluators."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        return release_access_service.generate_download_token(
            evaluator_id=tenant.tenant_id,
            version="0.1.0",
            ttl_seconds=900,
            client_ip=client_ip,
        )
    except UnauthorizedDownloadError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/download", summary="Download Release Artifact")
async def download_release_artifact(
    request: Request,
    token: str = Query(..., description="Single-use time-limited download token"),
):
    """Serve release package zip if token is valid and unexpired."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        grant = release_access_service.verify_and_consume_token(token, client_ip=client_ip)
        return {
            "status": "DOWNLOAD_GRANTED",
            "artifact": grant["artifact_filename"],
            "evaluator_id": grant["evaluator_id"],
            "message": "Authorized evaluation artifact stream initialized.",
        }
    except DownloadLinkExpiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/releases/verify", response_model=ArtifactVerificationResponse, summary="Verify Downloaded Artifact")
async def verify_artifact(payload: ArtifactVerificationRequest):
    """Verify downloaded package integrity against published manifest."""
    return release_access_service.verify_artifact_integrity(payload)
