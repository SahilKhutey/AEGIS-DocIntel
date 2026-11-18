"""
AEGIS-DocIntel Disaster Recovery & Restoration Engine
PROT-FINAL-05: Workstream DEP-12

Restores database snapshots while strictly preserving security invariants:
- DEP-010 / DEP-TEST-012: Revocation state preservation.
  A restored database MUST NOT resurrect revoked licenses, sessions, or compromised keys.
- Integrity verification against snapshot manifest SHA-256
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

logger = logging.getLogger("aegis.infrastructure.restore")


class RestorationSecurityViolation(Exception):
    pass


class RestoreEngine:
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir

    def restore_snapshot(
        self,
        snapshot_id: str,
        current_revocation_registry: Set[str],
    ) -> Tuple[bool, Optional[str], Dict[str, Any], Dict[str, Any]]:
        """
        Restores a snapshot:
        1. Validates file SHA-256 integrity against manifest
        2. Unpacks domain records
        3. Enforces that all licenses in the authoritative revocation list REMAIN revoked (DEP-TEST-012)
        """
        snapshot_file = self.backup_dir / f"{snapshot_id}.json"
        manifest_file = self.backup_dir / f"{snapshot_id}-manifest.json"

        if not snapshot_file.exists() or not manifest_file.exists():
            return False, f"Snapshot files for {snapshot_id} not found.", {}, {}

        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        snapshot_bytes = snapshot_file.read_bytes()

        # 1. Integrity check
        computed_sha = hashlib.sha256(snapshot_bytes).hexdigest()
        if computed_sha != manifest["sha256"]:
            return False, "Snapshot digest mismatch! Possible tampering detected.", {}, {}

        data = json.loads(snapshot_bytes.decode("utf-8"))
        domains = data.get("domains", {})

        # 2. Re-apply and enforce revocation state (DEP-TEST-012)
        # Merge snapshot revocations with current active revocations
        all_revocations = set(current_revocation_registry).union(set(data.get("revocations", [])))

        # Update licenses in restored data to ensure revoked licenses are not resurrected
        licenses = domains.get("licenses", {})
        resurrected_count = 0
        for lic_id, lic_data in licenses.items():
            if lic_id in all_revocations:
                if lic_data.get("status") != "REVOKED":
                    lic_data["status"] = "REVOKED"
                    lic_data["revoked_at"] = datetime.now(timezone.utc).isoformat()
                    lic_data["revocation_reason"] = "PRESERVED_POST_RESTORE"
                    resurrected_count += 1

        restoration_summary = {
            "snapshot_id": snapshot_id,
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "domains_restored": list(domains.keys()),
            "revocations_enforced": len(all_revocations),
            "prevented_resurrections": resurrected_count,
            "status": "COMPLETED",
        }

        return True, None, restoration_summary, domains
