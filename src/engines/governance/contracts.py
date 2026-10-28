"""
src/engines/governance/contracts.py
===================================
Data contracts for Human-in-the-Loop review, governance, decisions, and audit events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, FrozenSet, Literal, Optional, Tuple


class ReviewStatus(StrEnum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    NEEDS_EVIDENCE = "needs_evidence"


class ReviewAction(StrEnum):
    CREATE = "create"
    CLAIM = "claim"
    APPROVE = "approve"
    CORRECT = "correct"
    REJECT = "reject"
    REQUEST_EVIDENCE = "request_evidence"
    REOPEN = "reopen"


CandidateType = Literal["fact", "conflict"]


@dataclass(frozen=True, slots=True)
class ReviewActor:
    """Authenticated user performing a review action within a tenant boundary."""

    tenant_id: str
    user_id: str
    roles: FrozenSet[str]

    def has_role(self, *role_names: str) -> bool:
        target = set(role_names)
        if "admin" in target:
            target.add("tenant_admin")
            target.add("review_admin")
        return bool(self.roles.intersection(target))


@dataclass(frozen=True, slots=True)
class ReviewRevision:
    """Immutable record of an approved human correction to a candidate fact."""

    revision_id: str
    review_id: str
    tenant_id: str
    actor_id: str
    version: int
    corrected_value: Any
    corrected_type: str
    unit: Optional[str] = None
    evidence_quote: Optional[str] = None
    rationale: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "review_id": self.review_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "version": self.version,
            "corrected_value": self.corrected_value,
            "corrected_type": self.corrected_type,
            "unit": self.unit,
            "evidence_quote": self.evidence_quote,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReviewRevision:
        return cls(
            revision_id=data["revision_id"],
            review_id=data["review_id"],
            tenant_id=data["tenant_id"],
            actor_id=data["actor_id"],
            version=data["version"],
            corrected_value=data["corrected_value"],
            corrected_type=data["corrected_type"],
            unit=data.get("unit"),
            evidence_quote=data.get("evidence_quote"),
            rationale=data.get("rationale", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    """Immutable record of a decision submitted by a reviewer."""

    decision_id: str
    review_id: str
    tenant_id: str
    actor_id: str
    action: ReviewAction
    from_status: ReviewStatus
    to_status: ReviewStatus
    version_reviewed: int
    rationale: str
    evidence_quote: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "review_id": self.review_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "action": str(self.action),
            "from_status": str(self.from_status),
            "to_status": str(self.to_status),
            "version_reviewed": self.version_reviewed,
            "rationale": self.rationale,
            "evidence_quote": self.evidence_quote,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReviewDecision:
        return cls(
            decision_id=data["decision_id"],
            review_id=data["review_id"],
            tenant_id=data["tenant_id"],
            actor_id=data["actor_id"],
            action=ReviewAction(data["action"]),
            from_status=ReviewStatus(data["from_status"]),
            to_status=ReviewStatus(data["to_status"]),
            version_reviewed=data["version_reviewed"],
            rationale=data["rationale"],
            evidence_quote=data.get("evidence_quote"),
            idempotency_key=data.get("idempotency_key"),
            created_at=data.get("created_at", ""),
        )


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Ordered, append-only history of a successful review state transition."""

    event_id: str
    review_id: str
    sequence: int
    tenant_id: str
    actor_id: str
    action: ReviewAction
    previous_status: ReviewStatus
    new_status: ReviewStatus
    previous_version: int
    new_version: int
    rationale: str
    revision_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "review_id": self.review_id,
            "sequence": self.sequence,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "action": str(self.action),
            "previous_status": str(self.previous_status),
            "new_status": str(self.new_status),
            "previous_version": self.previous_version,
            "new_version": self.new_version,
            "rationale": self.rationale,
            "revision_id": self.revision_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEvent:
        return cls(
            event_id=data["event_id"],
            review_id=data["review_id"],
            sequence=data["sequence"],
            tenant_id=data["tenant_id"],
            actor_id=data["actor_id"],
            action=ReviewAction(data["action"]),
            previous_status=ReviewStatus(data["previous_status"]),
            new_status=ReviewStatus(data["new_status"]),
            previous_version=data["previous_version"],
            new_version=data["new_version"],
            rationale=data["rationale"],
            revision_id=data.get("revision_id"),
            request_id=data.get("request_id"),
            timestamp=data.get("timestamp", ""),
        )


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """Current state and history pointers of a reviewable candidate."""

    review_id: str
    tenant_id: str
    candidate_id: str
    candidate_type: CandidateType
    document_id: str
    status: ReviewStatus
    version: int
    candidate_data: Dict[str, Any]
    assigned_to: Optional[str] = None
    current_revision_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "tenant_id": self.tenant_id,
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "document_id": self.document_id,
            "status": str(self.status),
            "version": self.version,
            "assigned_to": self.assigned_to,
            "candidate_data": dict(self.candidate_data),
            "current_revision_id": self.current_revision_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReviewItem:
        return cls(
            review_id=data["review_id"],
            tenant_id=data["tenant_id"],
            candidate_id=data["candidate_id"],
            candidate_type=data.get("candidate_type", "fact"),
            document_id=data["document_id"],
            status=ReviewStatus(data["status"]),
            version=data["version"],
            assigned_to=data.get("assigned_to"),
            candidate_data=dict(data.get("candidate_data", {})),
            current_revision_id=data.get("current_revision_id"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass(frozen=True, slots=True)
class DecisionSubmission:
    """Incoming user payload to execute a review decision."""

    action: ReviewAction
    expected_version: int
    rationale: str
    corrected_value: Optional[Any] = None
    corrected_type: Optional[str] = None
    unit: Optional[str] = None
    evidence_quote: Optional[str] = None
