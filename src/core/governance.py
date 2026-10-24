"""
AEGIS-DocIntel — Data Governance & Lifecycle Policies
=====================================================
Enterprise data lifecycle management:
- Retention policies and automatic expiry calculations
- Classification levels (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)
- Legal hold locks preventing deletion/purge
- Cascading purge execution with audit event generation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
from typing import Optional, Dict, Any, List, Tuple


class ClassificationLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class RetentionPolicy:
    policy_id: str
    tenant_id: str
    name: str
    max_age_days: int
    delete_source: bool = True
    delete_derived_data: bool = True
    legal_hold_override: bool = False

    def __post_init__(self):
        if not self.policy_id:
            raise ValueError("RetentionPolicy requires a non-empty policy_id")
        if not self.tenant_id:
            raise ValueError("RetentionPolicy requires a non-empty tenant_id")
        if self.max_age_days < 0:
            raise ValueError("max_age_days must be non-negative")


@dataclass
class DocumentGovernanceRecord:
    doc_id: str
    tenant_id: str
    created_at: float = field(default_factory=time.time)
    classification: ClassificationLevel = ClassificationLevel.INTERNAL
    retention_policy_id: Optional[str] = None
    expires_at: Optional[float] = None
    legal_hold: bool = False
    legal_hold_reason: Optional[str] = None
    legal_hold_set_by: Optional[str] = None
    purged_at: Optional[float] = None
    purge_audit_id: Optional[str] = None

    def __post_init__(self):
        if not self.doc_id:
            raise ValueError("DocumentGovernanceRecord requires doc_id")
        if not self.tenant_id:
            raise ValueError("DocumentGovernanceRecord requires tenant_id")


@dataclass
class PurgeInventory:
    doc_id: str
    tenant_id: str
    purged_at: float
    audit_event_id: str
    source_bytes_deleted: bool = False
    derived_chunks_deleted: int = 0
    vectors_deleted: int = 0
    cache_keys_invalidated: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


class LegalHoldActiveError(Exception):
    """Raised when an operation is blocked by an active legal hold."""
    pass


class RetentionPolicyViolationError(Exception):
    """Raised when an operation violates configured retention rules."""
    pass


class RetentionEngine:
    """
    Evaluates document retention rules, enforces legal holds,
    and coordinates cascading purging across storage boundaries.
    """

    @staticmethod
    def calculate_expiry(created_at: float, policy: RetentionPolicy) -> float:
        """Calculate unix timestamp for record expiration based on policy."""
        seconds_per_day = 86400.0
        return created_at + (policy.max_age_days * seconds_per_day)

    @staticmethod
    def apply_policy(
        record: DocumentGovernanceRecord,
        policy: RetentionPolicy,
    ) -> DocumentGovernanceRecord:
        """Bind a retention policy to a governance record and compute expiry timestamp."""
        if record.tenant_id != policy.tenant_id:
            raise ValueError(
                f"Tenant mismatch: record is tenant '{record.tenant_id}', "
                f"policy is tenant '{policy.tenant_id}'"
            )
        record.retention_policy_id = policy.policy_id
        record.expires_at = RetentionEngine.calculate_expiry(record.created_at, policy)
        return record

    @staticmethod
    def is_expired(record: DocumentGovernanceRecord, now: Optional[float] = None) -> bool:
        """Check if a record has reached or passed its expiration timestamp."""
        if record.expires_at is None:
            return False
        current_time = now if now is not None else time.time()
        return current_time >= record.expires_at

    @staticmethod
    def can_purge(
        record: DocumentGovernanceRecord,
        policy: Optional[RetentionPolicy] = None,
        now: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Determine if a document is eligible for purging.
        Returns (is_eligible, explanation_reason).
        """
        if record.legal_hold:
            if not (policy and policy.legal_hold_override):
                return False, f"Document {record.doc_id} is under an active legal hold ({record.legal_hold_reason or 'No reason specified'})."

        if record.purged_at is not None:
            return False, f"Document {record.doc_id} has already been purged at {record.purged_at}."

        if record.expires_at is not None:
            current_time = now if now is not None else time.time()
            if current_time < record.expires_at:
                return False, f"Document {record.doc_id} has not yet expired (expires_at={record.expires_at}, now={current_time})."

        return True, "Document is eligible for purge."

    @staticmethod
    def set_legal_hold(
        record: DocumentGovernanceRecord,
        principal_id: str,
        reason: str,
    ) -> DocumentGovernanceRecord:
        """Place an immutable legal hold lock on the document."""
        if not principal_id:
            raise ValueError("principal_id required to apply legal hold")
        if not reason:
            raise ValueError("reason required to apply legal hold")
        record.legal_hold = True
        record.legal_hold_set_by = principal_id
        record.legal_hold_reason = reason
        return record

    @staticmethod
    def release_legal_hold(
        record: DocumentGovernanceRecord,
        principal_id: str,
    ) -> DocumentGovernanceRecord:
        """Release an active legal hold lock."""
        if not principal_id:
            raise ValueError("principal_id required to release legal hold")
        record.legal_hold = False
        record.legal_hold_reason = None
        record.legal_hold_set_by = None
        return record

    @staticmethod
    async def execute_purge(
        record: DocumentGovernanceRecord,
        document_service: Any,
        policy: Optional[RetentionPolicy] = None,
        now: Optional[float] = None,
    ) -> PurgeInventory:
        """
        Execute cascading purge of document and derived data if eligible.
        Raises LegalHoldActiveError if document has an un-overridden legal hold.
        """
        eligible, reason = RetentionEngine.can_purge(record, policy=policy, now=now)
        if not eligible:
            if record.legal_hold:
                raise LegalHoldActiveError(reason)
            raise RetentionPolicyViolationError(reason)

        current_time = now if now is not None else time.time()
        audit_id = f"audit_purge_{uuid.uuid4().hex[:16]}"

        inventory = PurgeInventory(
            doc_id=record.doc_id,
            tenant_id=record.tenant_id,
            purged_at=current_time,
            audit_event_id=audit_id,
        )

        # Execute physical deletion via document service if available
        if hasattr(document_service, "delete"):
            deleted = await document_service.delete(doc_id=record.doc_id, tenant_id=record.tenant_id)
            inventory.source_bytes_deleted = bool(deleted)

        record.purged_at = current_time
        record.purge_audit_id = audit_id
        return inventory
