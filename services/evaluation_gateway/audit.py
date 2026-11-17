"""
AEGIS-DocIntel Evaluation Gateway — Security Audit & Operational Telemetry
Complies with PROT-04 WP-04.08 specifications.
Ensures zero exposure of raw credentials, activation codes, private keys, or document text.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

AUDIT_LOG_FILE = Path(__file__).resolve().parent / "audit_events.jsonl"
logger = logging.getLogger("aegis.security.audit")

REDACTED_PATTERNS = [
    (re.compile(r"AEGIS-EVAL-[A-Z0-9]{4}-[A-Z0-9]{4}", re.IGNORECASE), "AEGIS-EVAL-****-****"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_.]+", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"eyJ[A-Za-z0-9\-_.]+\.[A-Za-z0-9\-_.]+\.[A-Za-z0-9\-_.]+"), "[REDACTED_JWT]"),
    (re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC )?PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


def redact_sensitive_data(text: str) -> str:
    """Masks secret patterns, tokens, and private keys from strings."""
    redacted = text
    for pattern, replacement in REDACTED_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class SecurityAuditService:
    def __init__(self, log_path: Path = AUDIT_LOG_FILE):
        self.log_path = log_path
        self._events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record_event(
        self,
        event_type: str,
        status: str,
        actor_id: str = "anonymous",
        license_id: Optional[str] = None,
        device_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Records an immutable structured security audit event.
        Guarantees that sensitive credentials and document content are redacted.
        """
        now = datetime.now(timezone.utc).isoformat()
        clean_details = {}
        if details:
            for k, v in details.items():
                if k in ("token", "access_token", "refresh_token", "private_key", "password", "secret"):
                    clean_details[k] = "[REDACTED]"
                elif k in ("activation_code",):
                    val_str = str(v)
                    clean_details[k] = val_str[:11] + "****" if len(val_str) > 11 else "[REDACTED]"
                elif k in ("document_content", "text", "query"):
                    clean_details[k] = "[CONTENT_REDACTED]"
                else:
                    if isinstance(v, str):
                        clean_details[k] = redact_sensitive_data(v)
                    else:
                        clean_details[k] = v

        event = {
            "timestamp": now,
            "event_type": event_type,
            "status": status,
            "actor_id": actor_id,
            "license_id": license_id or "unassigned",
            "device_id": device_id or "unassigned",
            "resource": resource or "gateway",
            "details": clean_details,
        }

        with self._lock:
            self._events.append(event)
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception as e:
                logger.error("Failed to append security audit event to disk: %s", e)

        return event

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns recent in-memory security events."""
        with self._lock:
            return list(self._events[-limit:])

    def clear(self) -> None:
        """Clears events (for testing)."""
        with self._lock:
            self._events.clear()
            if self.log_path.exists():
                try:
                    self.log_path.unlink()
                except Exception:
                    pass


# Global audit instance
audit_service = SecurityAuditService()
