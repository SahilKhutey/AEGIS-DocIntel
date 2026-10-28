"""
tests/test_mvp6_review_audit.py
===============================
Audit trail verification tests for sequence ordering, completeness, and append-only invariants.
"""

from src.engines.governance.contracts import (
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
)
from src.engines.governance.review_service import ReviewService
from src.engines.intelligence.contracts import ExtractedFact
from src.repositories.review_repository import ReviewRepository


def test_audit_trail_sequence_and_completeness(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "audit_test.db"))
    svc = ReviewService(repository=repo)

    reviewer = ReviewActor(
        tenant_id="tenant-audit",
        user_id="reviewer-1",
        roles=frozenset({"reviewer"}),
    )

    fact = ExtractedFact(
        fact_id="f-audit-1",
        tenant_id="tenant-audit",
        document_id="doc-audit-1",
        subject="agreement",
        attribute="notice_period",
        value=30,
        raw_value="30 days",
    )

    # 1. Creation event
    item = svc.create_review_from_fact("tenant-audit", fact)
    history = svc.get_history(reviewer, item.review_id)
    assert len(history) == 1
    assert history[0].sequence == 1
    assert history[0].action == "create"
    assert history[0].previous_version == 1
    assert history[0].new_version == 1

    # 2. Claim event
    svc.claim(reviewer, item.review_id, expected_version=1)
    history = svc.get_history(reviewer, item.review_id)
    assert len(history) == 2
    assert history[1].sequence == 2
    assert history[1].action == "claim"
    assert history[1].actor_id == "reviewer-1"
    assert history[1].previous_status == "pending"
    assert history[1].new_status == "in_review"
    assert history[1].previous_version == 1
    assert history[1].new_version == 2

    # 3. Decision event
    sub = DecisionSubmission(
        action=ReviewAction.APPROVE,
        expected_version=2,
        rationale="Evidence fully grounded and verified",
    )
    svc.decide(
        actor=reviewer,
        review_id=item.review_id,
        submission=sub,
        request_id="req-audit-test-999",
    )

    history = svc.get_history(reviewer, item.review_id)
    assert len(history) == 3
    assert history[2].sequence == 3
    assert history[2].action == "approve"
    assert history[2].actor_id == "reviewer-1"
    assert history[2].previous_status == "in_review"
    assert history[2].new_status == "approved"
    assert history[2].previous_version == 2
    assert history[2].new_version == 3
    assert history[2].rationale == "Evidence fully grounded and verified"
    assert history[2].request_id == "req-audit-test-999"
    assert bool(history[2].timestamp) is True
