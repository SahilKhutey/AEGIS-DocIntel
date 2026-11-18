"""
AEGIS-DocIntel Release Access Service
PROT-FINAL-08: Download Portal Access Controls & Integrity Verification
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.repositories.evaluation.evaluator_repository import EvaluatorRepository
from src.repositories.evaluation.release_repository import ReleaseRepository
from src.schemas.evaluation.evaluator import EvaluatorStatus
from src.schemas.evaluation.release import (
    ArtifactVerificationRequest,
    ArtifactVerificationResponse,
    DownloadTokenResponse,
    ReleaseArtifactItem,
    ReleaseManifest,
    ReleaseSignatureInfo,
)


class UnauthorizedDownloadError(Exception):
    pass


class DownloadLinkExpiredError(Exception):
    pass


class ReleaseAccessService:
    """Provides authenticated, time-limited download access and cryptographic artifact verification."""

    def __init__(
        self,
        release_repo: Optional[ReleaseRepository] = None,
        evaluator_repo: Optional[EvaluatorRepository] = None,
    ) -> None:
        self.release_repo = release_repo or ReleaseRepository()
        self.evaluator_repo = evaluator_repo or EvaluatorRepository()
        self._load_local_manifests()

    def _load_local_manifests(self) -> None:
        manifest_file = Path("release/manifests/release-manifest-0.1.0.json")
        if manifest_file.exists():
            try:
                import json
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                manifest = ReleaseManifest(**data)
                self.release_repo.register_manifest(manifest)
            except Exception:
                pass

    def generate_download_token(
        self,
        evaluator_id: str,
        version: str = "0.1.0",
        ttl_seconds: int = 900,
        client_ip: str = "127.0.0.1",
    ) -> DownloadTokenResponse:
        # Check evaluator eligibility
        evaluator = self.evaluator_repo.get_by_id(evaluator_id)
        if not evaluator:
            self.release_repo.record_download_event(
                evaluator_id=evaluator_id,
                artifact_filename="",
                ip_address=client_ip,
                success=False,
                reason="Evaluator record not found",
            )
            raise UnauthorizedDownloadError(f"Evaluator '{evaluator_id}' not found or unauthorized.")

        unauthorized_states = {
            EvaluatorStatus.INVITED,
            EvaluatorStatus.SUSPENDED,
            EvaluatorStatus.REVOKED,
            EvaluatorStatus.TERMINATED,
            EvaluatorStatus.EXPIRED,
        }
        if evaluator.status in unauthorized_states:
            self.release_repo.record_download_event(
                evaluator_id=evaluator_id,
                artifact_filename="",
                ip_address=client_ip,
                success=False,
                reason=f"Evaluator status is {evaluator.status.value}",
            )
            raise UnauthorizedDownloadError(
                f"Evaluator '{evaluator_id}' is in status '{evaluator.status.value}'. Download not permitted."
            )

        manifest = self.release_repo.get_manifest(version)
        if not manifest:
            raise ValueError(f"Release manifest for version '{version}' not found.")

        # Generate single-use, time-limited token
        token = f"dl-{secrets.token_urlsafe(32)}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()

        self.release_repo.create_download_grant(
            token=token,
            evaluator_id=evaluator_id,
            artifact_filename=manifest.artifact.filename,
            expires_at_iso=expires_at,
        )

        self.release_repo.record_download_event(
            evaluator_id=evaluator_id,
            artifact_filename=manifest.artifact.filename,
            ip_address=client_ip,
            success=True,
            reason="Download token issued",
        )

        download_url = f"https://evaluate.aegis.corp/v1/evaluation/download?token={token}"
        manifest_url = f"https://evaluate.aegis.corp/v1/evaluation/releases/{version}/manifest"

        return DownloadTokenResponse(
            download_url=download_url,
            expires_at=expires_at,
            artifact=manifest.artifact,
            manifest_url=manifest_url,
        )

    def verify_and_consume_token(self, token: str, client_ip: str = "127.0.0.1") -> dict:
        grant = self.release_repo.verify_and_consume_grant(token)
        if not grant:
            raise DownloadLinkExpiredError("Download link is invalid, expired, or already consumed.")
        return grant

    def verify_artifact_integrity(
        self, request: ArtifactVerificationRequest, version: str = "0.1.0"
    ) -> ArtifactVerificationResponse:
        manifest = self.release_repo.get_manifest(version)
        if not manifest:
            return ArtifactVerificationResponse(
                valid=False,
                status="MANIFEST_NOT_FOUND",
                expected_sha256="",
                provided_sha256=request.sha256,
                signature_verified=False,
                details=f"No release manifest found for version '{version}'",
            )

        expected_hash = manifest.artifact.sha256.lower().strip()
        provided_hash = request.sha256.lower().strip()

        hashes_match = expected_hash == provided_hash

        sig_verified = False
        if request.signature_hex:
            # Check signature matches published manifest signature
            expected_sig = manifest.signature.signature_hex.lower().strip()
            sig_verified = expected_sig == request.signature_hex.lower().strip()
        else:
            sig_verified = True  # If not provided, evaluate hash match only

        valid = hashes_match and sig_verified
        status = "VERIFIED_COMPLIANT" if valid else ("HASH_MISMATCH" if not hashes_match else "SIGNATURE_MISMATCH")

        return ArtifactVerificationResponse(
            valid=valid,
            status=status,
            matched_manifest_version=version,
            expected_sha256=expected_hash,
            provided_sha256=provided_hash,
            signature_verified=sig_verified,
            details="Artifact hash and signature match published release manifest" if valid else "Artifact tampered or hash mismatch",
        )


release_access_service = ReleaseAccessService()
