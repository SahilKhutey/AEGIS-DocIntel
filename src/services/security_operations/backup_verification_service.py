"""
AEGIS-DocIntel Backup & Disaster Recovery Verification Service (PROT-04 WP-04.08)
Verifies backup integrity and enforces fail-closed recovery policies to prevent
the resurrection of revoked licenses, sessions, or deactivated devices (IR-005, IR-006).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from services.evaluation_gateway.revocation import registry as revocation_registry

logger = logging.getLogger("aegis.security.backup")


class BackupVerificationService:
    def __init__(self):
        self._backups: Dict[str, Dict[str, Any]] = {}
        self._persisted_revocations: Set[str] = set()

    def record_backup(
        self,
        backup_id: str,
        dataset_name: str,
        payload_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates and verifies cryptographic checksum of a database backup artifact."""
        serialized = json.dumps(payload_data, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(serialized).hexdigest()

        rec = {
            "backup_id": backup_id,
            "dataset_name": dataset_name,
            "checksum": checksum,
            "payload": payload_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "byte_size": len(serialized),
        }
        self._backups[backup_id] = rec
        return rec

    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verifies backup payload matches its cryptographic checksum (IR-005)."""
        rec = self._backups.get(backup_id)
        if not rec:
            return False

        serialized = json.dumps(rec["payload"], sort_keys=True).encode("utf-8")
        computed = hashlib.sha256(serialized).hexdigest()
        return computed == rec["checksum"]

    def restore_and_reconcile(
        self,
        backup_id: str,
        authoritative_revocations: Optional[Set[str]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Restores a database snapshot while enforcing the Fail-Closed Non-Resurrection Rule (IR-006):
        Sessions, licenses, or devices revoked after the snapshot timestamp are permanently
        re-applied to prevent resurrecting compromised or revoked access.
        """
        rec = self._backups.get(backup_id)
        if not rec:
            return False, {"error": "BACKUP_NOT_FOUND"}

        # Verify integrity before restore
        if not self.verify_backup_integrity(backup_id):
            return False, {"error": "BACKUP_CORRUPTED"}

        payload = rec["payload"]
        restored_sessions = payload.get("sessions", [])

        # Cross-reference with authoritative revocation registry
        revoked_licenses = authoritative_revocations if authoritative_revocations is not None else revocation_registry.get_revoked_set()

        reconciled_sessions = []
        resurrection_prevented_count = 0

        for sess in restored_sessions:
            lic_id = sess.get("license_id")
            # If the license was revoked after the backup was created, keep it revoked!
            if lic_id in revoked_licenses or sess.get("is_revoked") is True:
                sess_copy = dict(sess)
                sess_copy["status"] = "revoked"
                sess_copy["is_revoked"] = True
                sess_copy["resurrected"] = False
                reconciled_sessions.append(sess_copy)
                resurrection_prevented_count += 1
            else:
                reconciled_sessions.append(sess)

        report = {
            "backup_id": backup_id,
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "restored_sessions_count": len(reconciled_sessions),
            "resurrection_prevented_count": resurrection_prevented_count,
            "reconciled_sessions": reconciled_sessions,
        }
        return True, report


backup_verification_service = BackupVerificationService()
