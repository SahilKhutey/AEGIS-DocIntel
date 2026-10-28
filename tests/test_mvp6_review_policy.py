"""
tests/test_mvp6_review_policy.py
================================
Unit tests for review policy authorization, separation of duties, and state transitions.
"""

import pytest
from src.engines.governance.contracts import (
    ReviewAction,
    ReviewActor,
    ReviewStatus,
)
from src.engines.governance.policy import (
    ReviewPolicyError,
    authorize_review_action,
)


def test_assigned_reviewer_can_approve_open_item():
    actor = ReviewActor(
        tenant_id="tenant-a",
        user_id="reviewer-1",
        roles=frozenset({"reviewer"}),
    )
    # Allowed when item is in_review and actor is assigned reviewer
    authorize_review_action(
        actor,
        ReviewAction.APPROVE,
        ReviewStatus.IN_REVIEW,
        is_assigned_reviewer=True,
    )


def test_unassigned_reviewer_cannot_approve():
    actor = ReviewActor(
        tenant_id="tenant-a",
        user_id="reviewer-2",
        roles=frozenset({"reviewer"}),
    )
    with pytest.raises(ReviewPolicyError, match="Only the assigned reviewer"):
        authorize_review_action(
            actor,
            ReviewAction.APPROVE,
            ReviewStatus.IN_REVIEW,
            is_assigned_reviewer=False,
        )


def test_admin_can_approve_unassigned_item():
    actor = ReviewActor(
        tenant_id="tenant-a",
        user_id="admin-1",
        roles=frozenset({"review_admin"}),
    )
    # Admin is authorized even if not directly assigned reviewer
    authorize_review_action(
        actor,
        ReviewAction.APPROVE,
        ReviewStatus.IN_REVIEW,
        is_assigned_reviewer=False,
    )


def test_claim_action_rules():
    actor = ReviewActor(
        tenant_id="tenant-a",
        user_id="reviewer-1",
        roles=frozenset({"reviewer"}),
    )
    # Can claim pending
    authorize_review_action(actor, ReviewAction.CLAIM, ReviewStatus.PENDING, is_assigned_reviewer=False)
    # Can claim needs_evidence
    authorize_review_action(actor, ReviewAction.CLAIM, ReviewStatus.NEEDS_EVIDENCE, is_assigned_reviewer=False)

    # Cannot claim already in_review or approved item
    with pytest.raises(ReviewPolicyError, match="cannot be claimed"):
        authorize_review_action(actor, ReviewAction.CLAIM, ReviewStatus.IN_REVIEW, is_assigned_reviewer=False)
    with pytest.raises(ReviewPolicyError, match="cannot be claimed"):
        authorize_review_action(actor, ReviewAction.CLAIM, ReviewStatus.APPROVED, is_assigned_reviewer=False)


def test_reopen_requires_admin_and_terminal_status():
    reviewer = ReviewActor(
        tenant_id="tenant-a",
        user_id="reviewer-1",
        roles=frozenset({"reviewer"}),
    )
    admin = ReviewActor(
        tenant_id="tenant-a",
        user_id="admin-1",
        roles=frozenset({"review_admin"}),
    )

    # Reviewer cannot reopen
    with pytest.raises(ReviewPolicyError, match="Review administrator"):
        authorize_review_action(reviewer, ReviewAction.REOPEN, ReviewStatus.APPROVED, is_assigned_reviewer=True)

    # Admin cannot reopen pending or in_review item (must be terminal)
    with pytest.raises(ReviewPolicyError, match="non-terminal state"):
        authorize_review_action(admin, ReviewAction.REOPEN, ReviewStatus.IN_REVIEW, is_assigned_reviewer=False)

    # Admin CAN reopen approved, corrected, or rejected
    authorize_review_action(admin, ReviewAction.REOPEN, ReviewStatus.APPROVED, is_assigned_reviewer=False)
    authorize_review_action(admin, ReviewAction.REOPEN, ReviewStatus.CORRECTED, is_assigned_reviewer=False)
    authorize_review_action(admin, ReviewAction.REOPEN, ReviewStatus.REJECTED, is_assigned_reviewer=False)


def test_missing_tenant_or_user_fails():
    actor_no_tenant = ReviewActor(tenant_id="", user_id="u1", roles=frozenset({"reviewer"}))
    with pytest.raises(ReviewPolicyError, match="tenant_id is required"):
        authorize_review_action(actor_no_tenant, ReviewAction.APPROVE, ReviewStatus.IN_REVIEW, is_assigned_reviewer=True)

    actor_no_user = ReviewActor(tenant_id="t1", user_id="", roles=frozenset({"reviewer"}))
    with pytest.raises(ReviewPolicyError, match="user_id is required"):
        authorize_review_action(actor_no_user, ReviewAction.APPROVE, ReviewStatus.IN_REVIEW, is_assigned_reviewer=True)
