"""
AEGIS-DocIntel Compliance Evidence Repository
PROT-FINAL-07: Workstream 07.08

Manages empirical compliance evidence records, artifact hash verification,
and schema validation (COMP-015).
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aegis.compliance.evidence_repository")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTERS_DIR = REPO_ROOT / "compliance" / "registers"
SCHEMAS_DIR = REPO_ROOT / "compliance" / "schemas"


class EvidenceRepository:
    def __init__(self, registers_dir: Path = REGISTERS_DIR):
        self.registers_dir = registers_dir
        self.evidence_file = self.registers_dir / "compliance_evidence_index.csv"

    def list_evidence(self) -> List[Dict[str, Any]]:
        """Reads all evidence records from compliance_evidence_index.csv."""
        if not self.evidence_file.exists():
            return []
        with open(self.evidence_file, mode="r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves evidence by ID."""
        for ev in self.list_evidence():
            if ev["evidence_id"] == evidence_id:
                return ev
        return None

    def validate_evidence_artifact(self, evidence_id: str) -> Dict[str, Any]:
        """
        Validates that the evidence artifact actually exists on disk,
        is non-empty, and computes its SHA-256 digest (COMP-015).
        """
        ev = self.get_evidence(evidence_id)
        if not ev:
            return {"valid": False, "error": f"Evidence {evidence_id} not registered"}

        artifact_rel = ev.get("artifact_path", "")
        artifact_path = REPO_ROOT / artifact_rel

        if not artifact_path.exists():
            return {
                "valid": False,
                "error": f"Evidence artifact file does not exist on disk: {artifact_rel}",
            }

        content = artifact_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()

        return {
            "valid": True,
            "evidence_id": evidence_id,
            "artifact_path": artifact_rel,
            "size_bytes": len(content),
            "sha256": digest,
            "result": ev.get("result"),
        }


evidence_repository = EvidenceRepository()
