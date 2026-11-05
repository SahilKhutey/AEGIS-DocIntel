"""
aegis.corpus.registry.licence_registry
======================================
Registry and permission checking engine for corpus licences.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import yaml

from aegis.corpus.models import LicenceRecord, PermissionValue, ReviewStatus


class LicenceRegistry:
    """Manages legal licences and fine-grained permission queries."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        self.licences: Dict[str, LicenceRecord] = {}
        if config_path:
            self.load(config_path)

    def load(self, config_path: Path | str) -> None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Licence config not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        lic_list = raw.get("licences", [])
        self.licences.clear()
        for item in lic_list:
            record = LicenceRecord(**item)
            self.licences[record.licence_id] = record

    def get(self, licence_id: str) -> Optional[LicenceRecord]:
        return self.licences.get(licence_id)

    def has_permission(self, licence_id: str, activity: str) -> bool:
        """
        Checks whether the licence grants explicit permission for an activity.
        Returns True only if permission is explicitly 'YES'.
        """
        lic = self.get(licence_id)
        if not lic:
            return False

        if lic.legal_review_status in (ReviewStatus.PENDING, ReviewStatus.REJECTED):
            return False

        val = getattr(lic.permissions, activity, PermissionValue.UNKNOWN)
        return val == PermissionValue.YES

    def requires_attribution(self, licence_id: str) -> bool:
        lic = self.get(licence_id)
        return lic.attribution_required if lic else True

    def get_attribution_text(self, licence_id: str) -> str:
        lic = self.get(licence_id)
        return lic.attribution_text or "" if lic else ""

    def list_all(self) -> List[LicenceRecord]:
        return list(self.licences.values())
