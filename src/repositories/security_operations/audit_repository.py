"""
AEGIS-DocIntel Append-Only Hash-Chained Audit Ledger Repository (PROT-04 WP-04.08)
Thread-safe, append-only repository maintaining cryptographic chain continuity.
"""

from __future__ import annotations

import copy
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.security.audit_integrity import (
    GENESIS_HASH,
    calculate_event_hash,
    create_checkpoint,
    verify_chain,
    verify_checkpoint,
)


class AuditRepository:
    """
    Authoritative append-only audit repository.
    Enforces cryptographic linkage:
        H_i = SHA-256(H_{i-1} || Canonical(E_i))
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._chain: List[Dict[str, Any]] = []
        self._head_hash: str = GENESIS_HASH
        self._external_checkpoints: List[Dict[str, Any]] = []

    def append_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atomically computes the next link in the hash chain and appends the event.
        Guarantees thread-safe serialized writes.
        """
        with self._lock:
            entry_id = str(uuid4())
            record = copy.deepcopy(event_data)
            record["entry_id"] = entry_id
            record["previous_hash"] = self._head_hash
            record["recorded_at"] = datetime.now(timezone.utc).isoformat()

            # Calculate current hash over canonical representation
            curr_hash = calculate_event_hash(self._head_hash, record)
            record["current_hash"] = curr_hash

            self._chain.append(record)
            self._head_hash = curr_hash

            return record

    def update_event(self, entry_id: str, new_data: Dict[str, Any]) -> None:
        """Explicitly rejected to satisfy AUDIT-009 (immutable append-only invariant)."""
        raise PermissionError("Audit ledger is strictly append-only; modification of historical events is forbidden.")

    def delete_event(self, entry_id: str) -> None:
        """Explicitly rejected to satisfy AUDIT-009 (immutable append-only invariant)."""
        raise PermissionError("Audit ledger is strictly append-only; deletion of events is forbidden.")

    def verify_integrity(self) -> Tuple[bool, Optional[int], Optional[str]]:
        """Verifies full cryptographic chain integrity from genesis to head."""
        with self._lock:
            return verify_chain(self._chain)

    def create_checkpoint(self) -> Dict[str, Any]:
        """Generates an externally verifiable signed checkpoint of the current audit head."""
        with self._lock:
            chk = create_checkpoint(self._head_hash, len(self._chain))
            self._external_checkpoints.append(chk)
            return chk

    def verify_latest_checkpoint(self) -> bool:
        """Verifies the latest anchored checkpoint against the live chain head."""
        with self._lock:
            if not self._external_checkpoints:
                return True
            latest = self._external_checkpoints[-1]
            return verify_checkpoint(latest, self._head_hash, len(self._chain))

    def export_audit_log(self) -> Dict[str, Any]:
        """Produces a verifiable, self-contained export of the entire audit chain."""
        with self._lock:
            valid, fail_idx, reason = verify_chain(self._chain)
            return {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "head_hash": self._head_hash,
                "event_count": len(self._chain),
                "is_valid": valid,
                "integrity_status": reason,
                "events": copy.deepcopy(self._chain),
            }

    def get_chain(self) -> List[Dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._chain)

    def clear(self) -> None:
        with self._lock:
            self._chain.clear()
            self._head_hash = GENESIS_HASH
            self._external_checkpoints.clear()


audit_repository = AuditRepository()
