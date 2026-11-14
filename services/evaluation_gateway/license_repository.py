"""
AEGIS-DocIntel Evaluation Gateway — License Repository
Implements PROT-04 WP-04.04 specifications:
- Authoritative server-side persistence for evaluation licenses
- License status lifecycle: DRAFT, ISSUED, ACTIVE, SUSPENDED, REVOKED, EXPIRED
- Idempotent issuance tracking to prevent duplicate licenses
- Authoritative cross-check store for verification pipeline
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LicenseRecord:
    id: str                         # License UUID (jti)
    evaluator_id: str               # Evaluator identity (sub)
    tenant_id: str                  # Assigned tenant ID
    status: str                     # ISSUED, ACTIVE, SUSPENDED, REVOKED, EXPIRED
    license_type: str               # e.g. "protected_demo_evaluation"
    policy_version: str             # e.g. "evaluation-1.0"
    key_id: str                     # kid used to sign
    signed_token_hash: str          # SHA-256 hash of issued token
    signed_jws: str                 # Compact JWS token
    issued_at: float                # Epoch seconds
    not_before: float               # Epoch seconds
    expires_at: float               # Epoch seconds
    revoked_at: Optional[float] = None
    revocation_reason_code: Optional[str] = None
    created_by: str = "admin"
    idempotency_key: Optional[str] = None
    device_limit: int = 1
    features: List[str] = field(default_factory=list)
    quotas: Dict[str, int] = field(default_factory=dict)


class LicenseRepository:
    def __init__(self):
        # license_id -> LicenseRecord
        self._licenses: Dict[str, LicenseRecord] = {}
        # idempotency_key -> license_id
        self._idempotency_index: Dict[str, str] = {}
        # evaluator_id -> list of license_ids
        self._evaluator_index: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def save_license(self, record: LicenseRecord) -> None:
        """Saves or updates an authoritative license record."""
        with self._lock:
            self._licenses[record.id] = record
            if record.idempotency_key:
                self._idempotency_index[record.idempotency_key] = record.id
            if record.evaluator_id not in self._evaluator_index:
                self._evaluator_index[record.evaluator_id] = []
            if record.id not in self._evaluator_index[record.evaluator_id]:
                self._evaluator_index[record.evaluator_id].append(record.id)

    def get_license(self, license_id: str) -> Optional[LicenseRecord]:
        """Retrieves authoritative license record by ID."""
        with self._lock:
            return self._licenses.get(license_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[LicenseRecord]:
        """Retrieves existing license by idempotency key to prevent duplicates."""
        with self._lock:
            lic_id = self._idempotency_index.get(idempotency_key)
            if lic_id:
                return self._licenses.get(lic_id)
            return None

    def suspend_license(self, license_id: str) -> bool:
        """Temporarily suspends an active license."""
        with self._lock:
            lic = self._licenses.get(license_id)
            if not lic:
                return False
            lic.status = "SUSPENDED"
            return True

    def revoke_license(self, license_id: str, reason_code: str = "administrative_revocation") -> bool:
        """Permanently revokes an evaluation license."""
        with self._lock:
            lic = self._licenses.get(license_id)
            if not lic:
                return False
            lic.status = "REVOKED"
            lic.revoked_at = time.time()
            lic.revocation_reason_code = reason_code
            return True

    def renew_license(self, license_id: str, additional_days: int) -> Optional[LicenseRecord]:
        """Extends license expiry timestamp by specified days."""
        with self._lock:
            lic = self._licenses.get(license_id)
            if not lic:
                return None
            lic.expires_at += (additional_days * 86400.0)
            if lic.status in ("EXPIRED", "SUSPENDED"):
                lic.status = "ACTIVE"
            return lic

    def list_licenses(self, evaluator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists authoritative license records, optionally filtered by evaluator."""
        with self._lock:
            records = self._licenses.values()
            if evaluator_id:
                records = [r for r in records if r.evaluator_id == evaluator_id]
            return [
                {
                    "id": r.id,
                    "evaluator_id": r.evaluator_id,
                    "tenant_id": r.tenant_id,
                    "status": r.status,
                    "license_type": r.license_type,
                    "policy_version": r.policy_version,
                    "key_id": r.key_id,
                    "issued_at": r.issued_at,
                    "expires_at": r.expires_at,
                    "device_limit": r.device_limit,
                    "features": r.features,
                    "quotas": r.quotas,
                }
                for r in records
            ]

    def reset(self) -> None:
        """Clears all records for test isolation."""
        with self._lock:
            self._licenses.clear()
            self._idempotency_index.clear()
            self._evaluator_index.clear()


# Global license repository instance
license_repository = LicenseRepository()
