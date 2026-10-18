"""
AEGIS-DocIntel — Tamper-Evident Audit Logging
==============================================
Append-only, cryptographically-chained structured audit logging for security,
compliance (SOC 2, GDPR, HIPAA), and multi-tenant access monitoring.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import structlog

log = structlog.get_logger("aegis.audit")

_AUDIT_LOCK = threading.Lock()
_GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditLogger:
    """Tamper-evident audit logger with cryptographic hash chaining."""

    def __init__(self, log_path: Optional[str | Path] = None):
        if log_path is None:
            env_path = os.environ.get("AEGIS_AUDIT_LOG_PATH")
            if env_path:
                self.log_path = Path(env_path)
            else:
                self.log_path = Path("data") / "audit.log"
        else:
            self.log_path = Path(log_path)

        self._last_hash = self._read_last_hash()

    def _read_last_hash(self) -> str:
        """Read the hash of the last entry in the log file, or return genesis hash."""
        if not self.log_path.exists():
            return _GENESIS_HASH

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                if not lines:
                    return _GENESIS_HASH
                last_entry = json.loads(lines[-1])
                return last_entry.get("entry_hash", _GENESIS_HASH)
        except Exception as e:
            log.warning("Could not read last audit hash, resetting to genesis", error=str(e))
            return _GENESIS_HASH

    def log(
        self,
        action: str,
        tenant_id: str,
        user_id: str = "system",
        status: str = "SUCCESS",
        resource_id: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record an immutable audit event."""
        event_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        record = {
            "event_id": event_id,
            "timestamp": now_iso,
            "action": action,
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "status": status,
            "resource_id": str(resource_id) if resource_id is not None else None,
            "client_ip": client_ip,
            "detail": detail or {},
        }

        with _AUDIT_LOCK:
            prev_hash = self._last_hash
            canonical_repr = json.dumps(record, sort_keys=True)
            entry_hash = hashlib.sha256(f"{prev_hash}:{canonical_repr}".encode("utf-8")).hexdigest()

            record["prev_hash"] = prev_hash
            record["entry_hash"] = entry_hash

            # Ensure directory exists
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
                self._last_hash = entry_hash
            except Exception as exc:
                log.error("Failed to write audit log to disk", error=str(exc))

        log.info(
            "Audit event",
            action=action,
            tenant_id=tenant_id,
            status=status,
            user_id=user_id,
            resource_id=resource_id,
        )
        return record

    def verify_integrity(self) -> Tuple[bool, int, Optional[str]]:
        """
        Verify the cryptographic hash chain of the audit log.
        Returns (is_valid, record_count, error_reason).
        """
        if not self.log_path.exists():
            return True, 0, None

        expected_prev = _GENESIS_HASH
        count = 0

        with open(self.log_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception as e:
                    return False, count, f"Malformed JSON at line {idx}: {e}"

                recorded_prev = entry.get("prev_hash")
                recorded_hash = entry.get("entry_hash")

                if recorded_prev != expected_prev:
                    return (
                        False,
                        count,
                        f"Broken chain at line {idx}: expected prev {expected_prev}, got {recorded_prev}",
                    )

                clean_record = {k: v for k, v in entry.items() if k not in ("prev_hash", "entry_hash")}
                canonical_repr = json.dumps(clean_record, sort_keys=True)
                computed_hash = hashlib.sha256(f"{recorded_prev}:{canonical_repr}".encode("utf-8")).hexdigest()

                if computed_hash != recorded_hash:
                    return (
                        False,
                        count,
                        f"Hash mismatch at line {idx}: computed {computed_hash}, recorded {recorded_hash}",
                    )

                expected_prev = recorded_hash
                count += 1

        return True, count, None


# Global singleton audit logger
audit_logger = AuditLogger()
