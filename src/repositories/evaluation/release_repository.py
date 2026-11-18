"""
AEGIS-DocIntel Release & Download Repository
PROT-FINAL-08: Release Manifests, Time-Limited Grants, and Audit Logs
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.schemas.evaluation.release import ReleaseManifest


class ReleaseRepository:
    """Thread-safe repository for release manifests and download audit."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._manifests: Dict[str, ReleaseManifest] = {}
        self._download_grants: Dict[str, dict] = {}  # token -> grant_info
        self._download_audit: List[dict] = []

    def register_manifest(self, manifest: ReleaseManifest) -> None:
        with self._lock:
            self._manifests[manifest.version] = manifest

    def get_manifest(self, version: str = "0.1.0") -> Optional[ReleaseManifest]:
        with self._lock:
            return self._manifests.get(version)

    def list_manifests(self) -> List[ReleaseManifest]:
        with self._lock:
            return list(self._manifests.values())

    def create_download_grant(
        self,
        token: str,
        evaluator_id: str,
        artifact_filename: str,
        expires_at_iso: str,
    ) -> dict:
        with self._lock:
            grant = {
                "token": token,
                "evaluator_id": evaluator_id,
                "artifact_filename": artifact_filename,
                "expires_at": expires_at_iso,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "consumed": False,
            }
            self._download_grants[token] = grant
            return grant

    def verify_and_consume_grant(self, token: str) -> Optional[dict]:
        with self._lock:
            grant = self._download_grants.get(token)
            if not grant:
                return None

            expires_at = datetime.fromisoformat(grant["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                return None

            grant["consumed"] = True
            return grant

    def record_download_event(
        self,
        evaluator_id: str,
        artifact_filename: str,
        ip_address: str,
        success: bool,
        reason: Optional[str] = None,
    ) -> None:
        with self._lock:
            self._download_audit.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "evaluator_id": evaluator_id,
                "artifact_filename": artifact_filename,
                "ip_address": ip_address,
                "success": success,
                "reason": reason,
            })

    def get_download_audit_logs(
        self, evaluator_id: Optional[str] = None
    ) -> List[dict]:
        with self._lock:
            if evaluator_id is None:
                return list(self._download_audit)
            return [l for l in self._download_audit if l["evaluator_id"] == evaluator_id]
