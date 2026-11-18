"""
AEGIS-DocIntel Release Artifact & Verification Schemas
PROT-FINAL-08: Download Portal & Release Integrity
"""

from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field


class ReleaseArtifactItem(BaseModel):
    filename: str
    sha256: str
    size_bytes: int


class ReleaseSignatureInfo(BaseModel):
    algorithm: str = "Ed25519"
    key_id: str
    signature_hex: str


class ReleaseManifest(BaseModel):
    product: str = "AEGIS-DocIntel"
    release_channel: str = "controlled-evaluation"
    version: str = "0.1.0"
    source_commit: str
    build_timestamp: str
    platform: str = "windows-x64"
    artifact: ReleaseArtifactItem
    sbom: ReleaseArtifactItem
    signature: ReleaseSignatureInfo
    minimum_gateway_version: str = "0.1.0"
    minimum_client_version: str = "0.1.0"


class DownloadTokenRequest(BaseModel):
    evaluator_id: str
    artifact_filename: str
    ttl_seconds: int = Field(default=900, ge=60, le=3600)


class DownloadTokenResponse(BaseModel):
    download_url: str
    expires_at: str
    artifact: ReleaseArtifactItem
    manifest_url: str


class ArtifactVerificationRequest(BaseModel):
    artifact_filename: str
    sha256: str
    signature_hex: Optional[str] = None


class ArtifactVerificationResponse(BaseModel):
    valid: bool
    status: str
    matched_manifest_version: Optional[str] = None
    expected_sha256: str
    provided_sha256: str
    signature_verified: bool
    details: str
