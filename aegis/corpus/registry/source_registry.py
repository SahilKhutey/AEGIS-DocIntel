"""
aegis.corpus.registry.source_registry
=====================================
Registry and validator for corpus dataset sources, portals, and repositories.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

from aegis.corpus.models import ProvenanceStatus, SourceRecord
from .licence_registry import LicenceRegistry


class SourceRegistry:
    """Manages document sources and enforces provenance and licence binding."""

    def __init__(
        self,
        config_path: Path | str | None = None,
        licence_registry: Optional[LicenceRegistry] = None,
    ) -> None:
        self.sources: Dict[str, SourceRecord] = {}
        self.licence_registry = licence_registry
        if config_path:
            self.load(config_path)

    def load(self, config_path: Path | str) -> None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Sources config not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        src_list = raw.get("sources", [])
        self.sources.clear()
        for item in src_list:
            record = SourceRecord(**item)
            self.sources[record.source_id] = record

    def get(self, source_id: str) -> Optional[SourceRecord]:
        return self.sources.get(source_id)

    def validate_integrity(self) -> Tuple[bool, List[str]]:
        """
        Validates cross-register integrity:
        - Every source must reference an existing licence in licence_registry.
        - Provenance status must not be REJECTED.
        - Source URLs must be well-formed.
        """
        errors: List[str] = []

        for s_id, s_rec in self.sources.items():
            if self.licence_registry:
                lic = self.licence_registry.get(s_rec.licence_id)
                if not lic:
                    errors.append(f"Source '{s_id}' references unknown licence '{s_rec.licence_id}'")

            if s_rec.provenance_status == ProvenanceStatus.REJECTED:
                errors.append(f"Source '{s_id}' is marked REJECTED in provenance register")

            if not s_rec.source_url.startswith(("http://", "https://", "file://")):
                errors.append(f"Source '{s_id}' has invalid URL protocol: {s_rec.source_url}")

        return len(errors) == 0, errors

    def list_all(self) -> List[SourceRecord]:
        return list(self.sources.values())
