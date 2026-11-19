"""
AEGIS-DocIntel — Canonical Document Lifecycle State Machine
============================================================
Enforces Section 3.2 of the PROT-FINAL-10 Product Development Sprint.
Defines canonical document states, legal transitions, audit ledger logging,
and validation rules to ensure monotonic, observable, and recoverable document processing.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("amdi.lifecycle")


class DocumentLifecycleState(StrEnum):
    """Canonical document lifecycle states (PROT-FINAL-10 Section 3.2)."""
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED"
    EXTRACTING = "EXTRACTING"
    PARSING = "PARSING"
    NORMALIZING = "NORMALIZING"
    INDEXING = "INDEXING"
    READY = "READY"
    REJECTED = "REJECTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    PARSING_FAILED = "PARSING_FAILED"
    INDEXING_FAILED = "INDEXING_FAILED"
    ARCHIVED = "ARCHIVED"
    DELETION_PENDING = "DELETION_PENDING"
    DELETED = "DELETED"

    @property
    def is_terminal(self) -> bool:
        """Indicates whether this is a terminal state that accepts no further forward processing."""
        return self in (
            DocumentLifecycleState.REJECTED,
            DocumentLifecycleState.DELETED,
        )

    @property
    def is_error_state(self) -> bool:
        """Indicates whether this is an error or failure state requiring retry or inspection."""
        return self in (
            DocumentLifecycleState.REJECTED,
            DocumentLifecycleState.EXTRACTION_FAILED,
            DocumentLifecycleState.PARSING_FAILED,
            DocumentLifecycleState.INDEXING_FAILED,
        )

    @property
    def is_queryable(self) -> bool:
        """Indicates whether the document can be queried by the intelligence engine."""
        return self == DocumentLifecycleState.READY


class InvalidLifecycleTransitionError(ValueError):
    """Raised when an illegal document lifecycle transition is attempted."""
    def __init__(self, from_state: Optional[DocumentLifecycleState], to_state: DocumentLifecycleState, reason: str = ""):
        msg = f"Invalid document lifecycle transition from '{from_state}' to '{to_state}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.from_state = from_state
        self.to_state = to_state


# Canonical State Transition Graph
VALID_TRANSITIONS: Dict[Optional[DocumentLifecycleState], Set[DocumentLifecycleState]] = {
    None: {DocumentLifecycleState.UPLOADED},
    DocumentLifecycleState.UPLOADED: {
        DocumentLifecycleState.VALIDATING,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.VALIDATING: {
        DocumentLifecycleState.ACCEPTED,
        DocumentLifecycleState.REJECTED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.ACCEPTED: {
        DocumentLifecycleState.QUEUED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.QUEUED: {
        DocumentLifecycleState.EXTRACTING,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.EXTRACTING: {
        DocumentLifecycleState.PARSING,
        DocumentLifecycleState.EXTRACTION_FAILED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.PARSING: {
        DocumentLifecycleState.NORMALIZING,
        DocumentLifecycleState.PARSING_FAILED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.NORMALIZING: {
        DocumentLifecycleState.INDEXING,
        DocumentLifecycleState.INDEXING_FAILED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.INDEXING: {
        DocumentLifecycleState.READY,
        DocumentLifecycleState.INDEXING_FAILED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.READY: {
        DocumentLifecycleState.ARCHIVED,
        DocumentLifecycleState.DELETION_PENDING,
        DocumentLifecycleState.QUEUED,  # Re-indexing
    },
    DocumentLifecycleState.ARCHIVED: {
        DocumentLifecycleState.READY,   # Restore
        DocumentLifecycleState.DELETION_PENDING,
    },
    # Recoverable Failure States -> QUEUED for retry
    DocumentLifecycleState.EXTRACTION_FAILED: {
        DocumentLifecycleState.QUEUED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.PARSING_FAILED: {
        DocumentLifecycleState.QUEUED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    DocumentLifecycleState.INDEXING_FAILED: {
        DocumentLifecycleState.QUEUED,
        DocumentLifecycleState.DELETION_PENDING,
    },
    # Deletion Pipeline
    DocumentLifecycleState.DELETION_PENDING: {
        DocumentLifecycleState.DELETED,
    },
    # Terminal States
    DocumentLifecycleState.REJECTED: set(),
    DocumentLifecycleState.DELETED: set(),
}


@dataclass(frozen=True, slots=True)
class LifecycleTransitionRecord:
    """Immutable transition audit record enforcing PROT-FINAL-10 Section 3.2."""
    document_id: str
    tenant_id: str
    previous_state: Optional[DocumentLifecycleState]
    new_state: DocumentLifecycleState
    job_id: Optional[str]
    stage: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    attempt_number: int = 1
    sanitized_error_code: Optional[str] = None
    diagnostic_ref: Optional[str] = None
    pipeline_version: str = "1.1.0"
    artifact_checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to sanitized operational audit dictionary (never includes sensitive content)."""
        return {
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "previous_state": str(self.previous_state) if self.previous_state else None,
            "new_state": str(self.new_state),
            "job_id": self.job_id,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "attempt_number": self.attempt_number,
            "sanitized_error_code": self.sanitized_error_code,
            "diagnostic_ref": self.diagnostic_ref,
            "pipeline_version": self.pipeline_version,
            "artifact_checksum": self.artifact_checksum,
        }


class DocumentLifecycleManager:
    """State machine manager for document lifecycle transitions."""

    def __init__(self, document_id: str, tenant_id: str, initial_state: Optional[DocumentLifecycleState] = None):
        self.document_id = document_id
        self.tenant_id = tenant_id
        self.current_state: Optional[DocumentLifecycleState] = initial_state
        self.history: List[LifecycleTransitionRecord] = []

    def can_transition_to(self, new_state: DocumentLifecycleState) -> bool:
        """Check if transition from current_state to new_state is permissible."""
        valid_targets = VALID_TRANSITIONS.get(self.current_state, set())
        return new_state in valid_targets

    def transition_to(
        self,
        new_state: DocumentLifecycleState,
        stage: str,
        job_id: Optional[str] = None,
        duration_ms: float = 0.0,
        attempt_number: int = 1,
        sanitized_error_code: Optional[str] = None,
        diagnostic_ref: Optional[str] = None,
        pipeline_version: str = "1.1.0",
        artifact_checksum: Optional[str] = None,
    ) -> LifecycleTransitionRecord:
        """Validate and apply state transition, recording immutable transition record."""
        if not self.can_transition_to(new_state):
            raise InvalidLifecycleTransitionError(
                from_state=self.current_state,
                to_state=new_state,
                reason=f"Transition from {self.current_state} to {new_state} is prohibited by canonical lifecycle",
            )

        record = LifecycleTransitionRecord(
            document_id=self.document_id,
            tenant_id=self.tenant_id,
            previous_state=self.current_state,
            new_state=new_state,
            job_id=job_id,
            stage=stage,
            duration_ms=duration_ms,
            attempt_number=attempt_number,
            sanitized_error_code=sanitized_error_code,
            diagnostic_ref=diagnostic_ref,
            pipeline_version=pipeline_version,
            artifact_checksum=artifact_checksum,
        )
        self.current_state = new_state
        self.history.append(record)
        return record
