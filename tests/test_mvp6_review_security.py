"""
tests/test_mvp6_review_security.py
==================================
Security tests verifying tenant isolation, cross-tenant denial, and role restrictions.
"""

import pytest
from src.engines.governance.contracts import (
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
    ReviewStatus,
)
from src.engines.governance.policy import ReviewPolicyError
from src.engines.governance.review_service import ReviewService
from src.engines.intelligence.contracts import ExtractedFact
from src.repositories.review_repository import (
    ReviewNotFoundError,
    ReviewRepository,
)


def test_tenant_isolation_denies_cross_tenant_access(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "security_test.db"))
    svc = ReviewService(repository=repo)

    fact_a = ExtractedFact(
        fact_id="fact-a",
        tenant_id="tenant-alpha",
        document_id="doc-confidential",
        subject="agreement",
        attribute="pricing",
        value=100.0,
        raw_value="$100",
    )
    item_a = svc.create_review_from_fact("tenant-alpha", fact_a)

    actor_b = ReviewActor(
        tenant_id="tenant-beta",
        user_id="reviewer-mallory",
        roles=frozenset({"reviewer", "review_admin"}),
    )

    # 1. Tenant-B cannot get Tenant-A review item
    assert svc.get_review(actor_b, item_a.review_id) is None

    # 2. Tenant-B queue list cannot see Tenant-A review item
    items_b, _ = svc.list_queue(actor_b)
    assert len(items_b) == 0

    # 3. Tenant-B cannot claim Tenant-A review item
    with pytest.raises(ReviewNotFoundError):
        svc.claim(actor_b, item_a.review_id, expected_version=1)

    # 4. Tenant-B cannot decide Tenant-A review item
    sub = DecisionSubmission(
        action=ReviewAction.APPROVE,
        expected_version=1,
        rationale="Malicious cross-tenant approval",
    )
    with pytest.raises(ReviewNotFoundError):
        svc.decide(actor_b, item_a.review_id, sub)

    # 5. Tenant-B cannot read Tenant-A audit history
    history = svc.get_history(actor_b, item_a.review_id)
    assert len(history) == 0


def test_viewer_role_cannot_decide_or_claim(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "roles_test.db"))
    svc = ReviewService(repository=repo)

    fact = ExtractedFact(
        fact_id="fact-viewer",
        tenant_id="tenant-alpha",
        document_id="doc-1",
        subject="agreement",
        attribute="term",
        value=12,
        raw_value="12 months",
    )
    item = svc.create_review_from_fact("tenant-alpha", fact)

    viewer = ReviewActor(
        tenant_id="tenant-alpha",
        user_id="viewer-dan",
        roles=frozenset({"viewer"}),
    )

    # Viewer cannot claim
    with pytest.raises(ReviewPolicyError, match="Reviewer or administrator role required"):
        svc.claim(viewer, item.review_id, expected_version=1)

    # Viewer cannot decide
    sub = DecisionSubmission(
        action=ReviewAction.APPROVE,
        expected_version=1,
        rationale="Viewer trying to approve",
    )
    with pytest.raises(ReviewPolicyError):
        svc.decide(viewer, item.review_id, sub)
