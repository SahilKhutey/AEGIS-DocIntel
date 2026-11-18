"""
AEGIS-DocIntel Client Release Policy & Version Revocation Service
PROT-FINAL-04: Workstream REL-10

Enforces server-side client release version gates, minimum version compliance,
and instantaneous client release blocking upon security incidents (REL-010).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from packaging.version import InvalidVersion, Version

from fastapi import HTTPException, Request, status

POLICY_STORAGE_PATH = Path(__file__).resolve().parent / "release_policy.json"


class ReleasePolicyManager:
    """
    Authoritative server-side policy manager tracking supported and revoked client versions.
    """

    def __init__(self, storage_path: Path = POLICY_STORAGE_PATH):
        self.storage_path = storage_path
        self._minimum_supported_version: str = "1.0.0"
        self._blocked_versions: Set[str] = set()
        self._release_channel: str = "evaluation"
        self._policy_revision: int = 1
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._minimum_supported_version = data.get("minimum_supported_version", "1.0.0")
                self._blocked_versions = set(data.get("blocked_versions", []))
                self._release_channel = data.get("release_channel", "evaluation")
                self._policy_revision = data.get("policy_revision", 1)
            except Exception:
                pass

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "minimum_supported_version": self._minimum_supported_version,
            "blocked_versions": sorted(list(self._blocked_versions)),
            "release_channel": self._release_channel,
            "policy_revision": self._policy_revision,
        }
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_policy(self) -> Dict[str, Any]:
        return {
            "minimum_supported_version": self._minimum_supported_version,
            "blocked_versions": sorted(list(self._blocked_versions)),
            "release_channel": self._release_channel,
            "policy_revision": self._policy_revision,
        }

    def block_version(self, version: str, reason: str = "Compromised or superseded release") -> None:
        self._blocked_versions.add(version)
        self._policy_revision += 1
        self._save()

    def unblock_version(self, version: str) -> None:
        self._blocked_versions.discard(version)
        self._policy_revision += 1
        self._save()

    def set_minimum_version(self, version: str) -> None:
        # Validate semver
        Version(version)
        self._minimum_supported_version = version
        self._policy_revision += 1
        self._save()

    def reset(self) -> None:
        self._minimum_supported_version = "1.0.0"
        self._blocked_versions = set()
        self._policy_revision = 1
        self._save()

    def validate_client_version(self, version_str: Optional[str]) -> bool:
        """
        Validates the client version against the server release policy.
        If version is explicitly blocked or below minimum supported version,
        raises HTTPException(403).
        """
        if not version_str:
            # Default or unversioned client treated as baseline 1.1.0 unless strict
            return True

        clean_ver = version_str.strip().lstrip("v")

        # 1. Check explicit blocklist
        if clean_ver in self._blocked_versions or version_str in self._blocked_versions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "CLIENT_VERSION_BLOCKED",
                    "version": version_str,
                    "message": f"Client release version {version_str} has been revoked due to a security incident. Please update to the latest release.",
                },
            )

        # 2. Check semver minimum
        try:
            parsed_client = Version(clean_ver)
            parsed_min = Version(self._minimum_supported_version)
            if parsed_client < parsed_min:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "CLIENT_VERSION_UNSUPPORTED",
                        "version": version_str,
                        "minimum_required": self._minimum_supported_version,
                        "message": f"Client release {version_str} is below the minimum supported version {self._minimum_supported_version}. Please upgrade.",
                    },
                )
        except InvalidVersion:
            # If invalid version string provided, reject with 400
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_CLIENT_VERSION",
                    "version": version_str,
                    "message": "Malformed semantic version string.",
                },
            )

        return True


release_policy = ReleasePolicyManager()
