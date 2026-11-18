"""
AEGIS-DocIntel Compliance Evidence Service
PROT-FINAL-07: Workstream 07.08

Validates and indexes empirical compliance evidence records (COMP-015):
- Ensures all evidence references point to genuine artifacts on disk
- Prevents broken, stale, or fabricated evidence
- Validates schema conformance against evidence.schema.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from src.repositories.compliance.evidence_repository import evidence_repository

logger = logging.getLogger("aegis.compliance.evidence_service")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "compliance" / "schemas"


class EvidenceService:
    def __init__(self):
        self.evidence_repo = evidence_repository
        self.schema_path = SCHEMAS_DIR / "evidence.schema.json"

    def audit_all_evidence(self) -> Dict[str, Any]:
        """
        COMP-015: Asserts that all registered evidence records have valid artifact paths
        on disk, non-empty content, and pass structural validation.
        """
        all_records = self.evidence_repo.list_evidence()
        if not all_records:
            return {"compliant": False, "error": "No evidence registered", "invalid_records": []}

        invalid_records = []
        valid_records = []

        for ev in all_records:
            ev_id = ev.get("evidence_id")
            val_res = self.evidence_repo.validate_evidence_artifact(ev_id)
            if not val_res["valid"]:
                invalid_records.append({"evidence_id": ev_id, "error": val_res.get("error")})
            else:
                valid_records.append(val_res)

        compliant = len(invalid_records) == 0 and len(valid_records) > 0
        return {
            "compliant": compliant,
            "total_evidence_records": len(all_records),
            "valid_records_count": len(valid_records),
            "invalid_records": invalid_records,
            "evidence": valid_records,
        }


evidence_service = EvidenceService()
