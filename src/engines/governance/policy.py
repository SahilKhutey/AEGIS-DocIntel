"""
src/engines/governance/policy.py
================================
Role-based authorization and state transition policies for review actions.
"""

from __future__ import annotations

from src.engines.governance.contracts import (
    ReviewAction,
    ReviewActor,
    ReviewStatus,
)


class ReviewPolicyError(PermissionError):
    """Raised when a review action violates a governance or authorization rule."""
    pass


def authorize_review_action(
    actor: ReviewActor,
    action: ReviewAction,
    status: ReviewStatus,
    *,
    is_assigned_reviewer: bool,
) -> None:
    """
    Authorize a review action against current item status, caller identity, and roles.
    Enforces strict separation of duties and valid state machine transitions.
    """
    if not actor.tenant_id or not actor.tenant_id.strip():
        raise ReviewPolicyError("Authenticated actor tenant_id is required.")
    if not actor.user_id or not actor.user_id.strip():
        raise ReviewPolicyError("Authenticated actor user_id is required.")

    roles = actor.roles
    is_admin = bool(roles.intersection({"admin", "tenant_admin", "review_admin"}))
    is_reviewer = bool(roles.intersection({"reviewer", "review_admin", "admin", "tenant_admin"}))

    if action == ReviewAction.CLAIM:
        if not is_reviewer:
            raise ReviewPolicyError("Reviewer or administrator role required to claim item.")
        if status not in {ReviewStatus.PENDING, ReviewStatus.NEEDS_EVIDENCE}:
            raise ReviewPolicyError(f"Item cannot be claimed in state '{status}'.")
        return

    if action == ReviewAction.REOPEN:
        if not is_admin:
            raise ReviewPolicyError("Review administrator or admin role required to reopen completed review.")
        if status not in {
            ReviewStatus.APPROVED,
            ReviewStatus.CORRECTED,
            ReviewStatus.REJECTED,
        }:
            raise ReviewPolicyError(f"Cannot reopen item in non-terminal state '{status}'.")
        return

    # Actions: APPROVE, CORRECT, REJECT, REQUEST_EVIDENCE
    if action in {
        ReviewAction.APPROVE,
        ReviewAction.CORRECT,
        ReviewAction.REJECT,
        ReviewAction.REQUEST_EVIDENCE,
    }:
        if not is_reviewer:
            raise ReviewPolicyError("Reviewer role required to submit review decisions.")
        if status != ReviewStatus.IN_REVIEW:
            raise ReviewPolicyError(
                f"Action '{action}' requires item to be in 'in_review' status (current: '{status}')."
            )
        if not is_assigned_reviewer and not is_admin:
            raise ReviewPolicyError(
                "Only the assigned reviewer or an authorized administrator can decide this item."
            )
        return

    raise ReviewPolicyError(f"Unrecognized or unsupported review action: '{action}'.")
