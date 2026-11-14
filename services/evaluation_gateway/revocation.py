"""
AEGIS-DocIntel Evaluation Gateway — License Revocation Registry
Tracks revoked license IDs, suspended evaluation tokens, and rogue hardware fingerprints.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Set

REVOCATION_STORE_PATH = Path(__file__).resolve().parent / "revocation_list.json"

class RevocationRegistry:
    def __init__(self, storage_path: Path = REVOCATION_STORE_PATH):
        self.storage_path = storage_path
        self._revoked_license_ids: Set[str] = set()
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._revoked_license_ids = set(data.get("revoked_license_ids", []))
            except Exception:
                self._revoked_license_ids = set()
        else:
            self._revoked_license_ids = set()

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "revoked_license_ids": sorted(list(self._revoked_license_ids))
        }
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def is_revoked(self, license_id: str) -> bool:
        return license_id in self._revoked_license_ids

    def revoke(self, license_id: str) -> None:
        self._revoked_license_ids.add(license_id)
        self._save()

    def unrevoke(self, license_id: str) -> None:
        self._revoked_license_ids.discard(license_id)
        self._save()

    def get_revoked_set(self) -> Set[str]:
        return set(self._revoked_license_ids)

    def clear(self) -> None:
        self._revoked_license_ids.clear()
        self._save()

# Global default instance
registry = RevocationRegistry()
