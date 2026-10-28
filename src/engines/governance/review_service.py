"""
src/engines/governance/review_service.py
========================================
Core Human-in-the-Loop review coordinator enforcing governance rules,
evidence validation, versioned decisions, and audit trail consistency.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.engines.governance.contracts import (
    AuditEvent,
    CandidateType,
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
    ReviewDecision,
    ReviewItem,
    ReviewRevision,
    ReviewStatus,
)
from src.engines.governance.evidence_validator import (
    EvidenceValidationError,
    validate_evidence_quote,
)
from src.engines.governance.feedback import (
    FeedbackCategory,
    ReviewFeedback,
    compute_governance_metrics,
)
from src.engines.governance.policy import (
    ReviewPolicyError,
    authorize_review_action,
)
from src.engines.intelligence.contracts import ConflictReport, ExtractedFact
from src.repositories.review_repository import (
    IdempotencyConflictError,
    ReviewNotFoundError,
    ReviewRepository,
    StaleReviewVersionError,
)

log = logging.getLogger("aegis.governance.review")


class ReviewService:
    """
    Coordinates review queues, reviewer assignments, decisions, evidence validation,
    and append-only audit histories within tenant boundaries.
    """

    def __init__(
        self,
        repository: Optional[ReviewRepository] = None,
        orchestrator: Optional[Any] = None,
    ) -> None:
        self.repository = repository or ReviewRepository()
        self.orchestrator = orchestrator

    def create_review_from_fact(
        self,
        tenant_id: str,
        fact: ExtractedFact,
        assigned_to: Optional[str] = None,
    ) -> ReviewItem:
        """Create a pending review item from an extracted candidate fact."""
        return self.repository.create_review_item(
            tenant_id=tenant_id,
            candidate_id=fact.fact_id,
            candidate_type="fact",
            document_id=fact.document_id,
            candidate_data=fact.to_dict(),
            assigned_to=assigned_to,
        )

    def create_review_from_conflict(
        self,
        tenant_id: str,
        conflict: ConflictReport,
        assigned_to: Optional[str] = None,
    ) -> ReviewItem:
        """Create a pending review item from a detected cross-document conflict."""
        conflict_id = f"conf-{conflict.subject}-{conflict.attribute}"
        doc_id = conflict.conflicting_document_ids[0] if conflict.conflicting_document_ids else "multi-doc"
        return self.repository.create_review_item(
            tenant_id=tenant_id,
            candidate_id=conflict_id,
            candidate_type="conflict",
            document_id=doc_id,
            candidate_data=conflict.to_dict(),
            assigned_to=assigned_to,
        )

    def claim(
        self,
        actor: ReviewActor,
        review_id: str,
        expected_version: int,
    ) -> ReviewItem:
        """
        Claim a pending or needs_evidence review item, transitioning it to in_review.
        """
        item = self.repository.get_review(actor.tenant_id, review_id)
        if not item:
            raise ReviewNotFoundError(f"Review item '{review_id}' not found for tenant '{actor.tenant_id}'")

        authorize_review_action(
            actor=actor,
            action=ReviewAction.CLAIM,
            status=item.status,
            is_assigned_reviewer=False,
        )

        decision = ReviewDecision(
            decision_id=f"dec-{uuid.uuid4().hex}",
            review_id=review_id,
            tenant_id=actor.tenant_id,
            actor_id=actor.user_id,
            action=ReviewAction.CLAIM,
            from_status=item.status,
            to_status=ReviewStatus.IN_REVIEW,
            version_reviewed=expected_version,
            rationale=f"Claimed by reviewer {actor.user_id}",
        )

        updated_item, _, _ = self.repository.save_transition(
            tenant_id=actor.tenant_id,
            review_id=review_id,
            expected_version=expected_version,
            new_status=ReviewStatus.IN_REVIEW,
            new_assigned_to=actor.user_id,
            decision=decision,
            audit_event_rationale=f"Item claimed by reviewer {actor.user_id}",
        )
        return updated_item

    def decide(
        self,
        actor: ReviewActor,
        review_id: str,
        submission: DecisionSubmission,
        request_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        authoritative_text: Optional[str] = None,
    ) -> Tuple[ReviewItem, ReviewDecision, AuditEvent]:
        """
        Execute a reviewer decision (approve, correct, reject, request_evidence).
        Validates evidence grounding against authoritative text and applies atomic transition.
        """
        item = self.repository.get_review(actor.tenant_id, review_id)
        if not item:
            raise ReviewNotFoundError(f"Review item '{review_id}' not found for tenant '{actor.tenant_id}'")

        # Idempotency fast-path: return cached response if key was already executed
        if idempotency_key:
            cached = self.repository.get_idempotent_decision(
                tenant_id=actor.tenant_id,
                review_id=review_id,
                idempotency_key=idempotency_key,
            )
            if cached:
                return cached

        is_assigned = (item.assigned_to == actor.user_id)
        authorize_review_action(
            actor=actor,
            action=submission.action,
            status=item.status,
            is_assigned_reviewer=is_assigned,
        )

        # Retrieve authoritative text if not supplied directly
        auth_text = authoritative_text or self._resolve_authoritative_text(actor.tenant_id, item)

        revision: Optional[ReviewRevision] = None
        new_status: ReviewStatus

        if submission.action == ReviewAction.APPROVE:
            if submission.evidence_quote and auth_text:
                validate_evidence_quote(quote=submission.evidence_quote, authoritative_text=auth_text)
            new_status = ReviewStatus.APPROVED
            new_assigned_to = item.assigned_to

        elif submission.action == ReviewAction.CORRECT:
            if submission.corrected_value is None:
                raise ValueError("Corrected value is required for action 'correct'")
            if submission.evidence_quote and auth_text:
                validate_evidence_quote(quote=submission.evidence_quote, authoritative_text=auth_text)

            rev_id = f"rev-{uuid.uuid4().hex}"
            revision = ReviewRevision(
                revision_id=rev_id,
                review_id=review_id,
                tenant_id=actor.tenant_id,
                actor_id=actor.user_id,
                version=item.version + 1,
                corrected_value=submission.corrected_value,
                corrected_type=submission.corrected_type or "string",
                unit=submission.unit,
                evidence_quote=submission.evidence_quote,
                rationale=submission.rationale,
            )
            new_status = ReviewStatus.CORRECTED
            new_assigned_to = item.assigned_to

        elif submission.action == ReviewAction.REJECT:
            if not submission.rationale or len(submission.rationale.strip()) < 3:
                raise ValueError("A clear rationale (min 3 characters) is required to reject a candidate.")
            new_status = ReviewStatus.REJECTED
            new_assigned_to = item.assigned_to

        elif submission.action == ReviewAction.REQUEST_EVIDENCE:
            if not submission.rationale or len(submission.rationale.strip()) < 3:
                raise ValueError("A detailed explanation is required when requesting additional evidence.")
            new_status = ReviewStatus.NEEDS_EVIDENCE
            new_assigned_to = item.assigned_to

        else:
            raise ReviewPolicyError(f"Action '{submission.action}' is not supported by decide()")

        decision_id = f"dec-{uuid.uuid4().hex}"
        decision = ReviewDecision(
            decision_id=decision_id,
            review_id=review_id,
            tenant_id=actor.tenant_id,
            actor_id=actor.user_id,
            action=submission.action,
            from_status=item.status,
            to_status=new_status,
            version_reviewed=submission.expected_version,
            rationale=submission.rationale,
            evidence_quote=submission.evidence_quote,
            idempotency_key=idempotency_key,
        )

        return self.repository.save_transition(
            tenant_id=actor.tenant_id,
            review_id=review_id,
            expected_version=submission.expected_version,
            new_status=new_status,
            new_assigned_to=new_assigned_to,
            decision=decision,
            revision=revision,
            audit_event_rationale=submission.rationale,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    def reopen(
        self,
        actor: ReviewActor,
        review_id: str,
        expected_version: int,
        rationale: str,
        request_id: Optional[str] = None,
    ) -> Tuple[ReviewItem, ReviewDecision, AuditEvent]:
        """
        Reopen an approved, corrected, or rejected item back into review.
        Requires review administrator or admin role.
        """
        item = self.repository.get_review(actor.tenant_id, review_id)
        if not item:
            raise ReviewNotFoundError(f"Review item '{review_id}' not found for tenant '{actor.tenant_id}'")

        authorize_review_action(
            actor=actor,
            action=ReviewAction.REOPEN,
            status=item.status,
            is_assigned_reviewer=False,
        )

        if not rationale or len(rationale.strip()) < 5:
            raise ValueError("A substantive administrative rationale (min 5 chars) is required to reopen an item.")

        decision = ReviewDecision(
            decision_id=f"dec-{uuid.uuid4().hex}",
            review_id=review_id,
            tenant_id=actor.tenant_id,
            actor_id=actor.user_id,
            action=ReviewAction.REOPEN,
            from_status=item.status,
            to_status=ReviewStatus.IN_REVIEW,
            version_reviewed=expected_version,
            rationale=rationale,
        )

        return self.repository.save_transition(
            tenant_id=actor.tenant_id,
            review_id=review_id,
            expected_version=expected_version,
            new_status=ReviewStatus.IN_REVIEW,
            new_assigned_to=actor.user_id,
            decision=decision,
            audit_event_rationale=f"Administrative reopen: {rationale}",
            request_id=request_id,
        )

    def get_review(self, actor: ReviewActor, review_id: str) -> Optional[ReviewItem]:
        """Fetch review item guaranteeing tenant isolation."""
        return self.repository.get_review(actor.tenant_id, review_id)

    def list_queue(
        self,
        actor: ReviewActor,
        status: Optional[ReviewStatus] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[ReviewItem], Optional[str]]:
        """List review queue items scoped to authenticated tenant."""
        return self.repository.list_reviews(
            tenant_id=actor.tenant_id,
            status=status,
            assigned_to=assigned_to,
            limit=limit,
            cursor=cursor,
        )

    def get_history(self, actor: ReviewActor, review_id: str) -> List[AuditEvent]:
        """Fetch ordered audit trail events scoped to tenant."""
        return self.repository.get_audit_history(actor.tenant_id, review_id)

    def submit_feedback(
        self,
        actor: ReviewActor,
        review_id: str,
        category: FeedbackCategory,
        notes: str = "",
        corrected_reference: Optional[str] = None,
    ) -> str:
        """Submit structured feedback on an extraction or review item."""
        item = self.repository.get_review(actor.tenant_id, review_id)
        if not item:
            raise ReviewNotFoundError(f"Review item '{review_id}' not found for tenant '{actor.tenant_id}'")

        fb = ReviewFeedback(
            feedback_id=f"fb-{uuid.uuid4().hex}",
            tenant_id=actor.tenant_id,
            review_id=review_id,
            candidate_id=item.candidate_id,
            category=category,
            reviewer_id=actor.user_id,
            notes=notes,
            corrected_value_reference=corrected_reference,
        )
        return self.repository.record_feedback(actor.tenant_id, fb)

    def get_approved_facts_for_report(
        self,
        actor: ReviewActor,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch approved and corrected facts only, excluding pending and rejected facts."""
        return self.repository.get_approved_facts(
            tenant_id=actor.tenant_id,
            document_id=document_id,
        )

    def get_metrics(self, actor: ReviewActor) -> Dict[str, Any]:
        """Compute review governance metrics for the tenant."""
        items, _ = self.repository.list_reviews(tenant_id=actor.tenant_id, limit=1000)
        feedback = self.repository.list_feedback(tenant_id=actor.tenant_id)
        return compute_governance_metrics(items, feedback)

    def _resolve_authoritative_text(self, tenant_id: str, item: ReviewItem) -> Optional[str]:
        """Attempt to extract source document text from candidate or orchestrator."""
        # 1. From candidate evidence quote
        cand = item.candidate_data
        ev_list = cand.get("evidence", [])
        if ev_list and isinstance(ev_list, list):
            first_ev = ev_list[0]
            if isinstance(first_ev, dict) and first_ev.get("quoted_text"):
                return first_ev["quoted_text"]

        # 2. From orchestrator if available
        if self.orchestrator and hasattr(self.orchestrator, "get_document_elements"):
            try:
                elements = self.orchestrator.get_document_elements(item.document_id, tenant_id=tenant_id)
                return "\n".join(getattr(el, "content", "") for el in elements)
            except Exception:
                pass

        return None
