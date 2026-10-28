"""
tests/test_mvp6_feedback.py
===========================
Unit tests for reviewer feedback capture, categorization, metrics, and tenant isolation.
"""

from src.engines.governance.contracts import (
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
)
from src.engines.governance.feedback import (
    FeedbackCategory,
    ReviewFeedback,
    compute_governance_metrics,
)
from src.engines.governance.review_service import ReviewService
from src.engines.intelligence.contracts import ExtractedFact
from src.repositories.review_repository import ReviewRepository


def test_feedback_recording_and_metrics(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "feedback_test.db"))
    svc = ReviewService(repository=repo)

    reviewer = ReviewActor(
        tenant_id="tenant-fb",
        user_id="reviewer-1",
        roles=frozenset({"reviewer"}),
    )

    fact = ExtractedFact(
        fact_id="fact-fb-1",
        tenant_id="tenant-fb",
        document_id="doc-1",
        subject="agreement",
        attribute="revenue",
        value=500.0,
        raw_value="$500",
    )
    item = svc.create_review_from_fact("tenant-fb", fact)

    # Claim and decide as corrected
    svc.claim(reviewer, item.review_id, expected_version=1)
    sub = DecisionSubmission(
        action=ReviewAction.CORRECT,
        expected_version=2,
        rationale="Corrected missing magnitude",
        corrected_value=500000.0,
        corrected_type="decimal",
    )
    svc.decide(reviewer, item.review_id, sub)

    # Submit feedback
    fb_id = svc.submit_feedback(
        actor=reviewer,
        review_id=item.review_id,
        category=FeedbackCategory.WRONG_VALUE,
        notes="Model extracted 500 instead of 500,000",
        corrected_reference="500000.0",
    )
    assert fb_id.startswith("fb-")

    # Retrieve feedback from repo
    feedback_records = repo.list_feedback("tenant-fb", item.review_id)
    assert len(feedback_records) == 1
    assert feedback_records[0].category == FeedbackCategory.WRONG_VALUE
    assert feedback_records[0].notes == "Model extracted 500 instead of 500,000"

    # Compute metrics
    metrics = svc.get_metrics(reviewer)
    assert metrics["total_items"] == 1
    assert metrics["decided_count"] == 1
    assert metrics["correction_rate"] == 1.0
    assert metrics["approval_rate"] == 0.0
    assert metrics["feedback_categories"]["wrong_value"] == 1


def test_feedback_tenant_isolation(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "feedback_iso.db"))

    fb_a = ReviewFeedback(
        feedback_id="fb-a",
        tenant_id="tenant-alpha",
        review_id="rev-a",
        candidate_id="cand-a",
        category=FeedbackCategory.BAD_EVIDENCE,
        reviewer_id="user-a",
        notes="Tenant Alpha notes",
    )
    fb_b = ReviewFeedback(
        feedback_id="fb-b",
        tenant_id="tenant-beta",
        review_id="rev-b",
        candidate_id="cand-b",
        category=FeedbackCategory.WRONG_ENTITY,
        reviewer_id="user-b",
        notes="Tenant Beta notes",
    )

    repo.record_feedback("tenant-alpha", fb_a)
    repo.record_feedback("tenant-beta", fb_b)

    # Alpha sees only fb_a
    records_a = repo.list_feedback("tenant-alpha")
    assert len(records_a) == 1
    assert records_a[0].feedback_id == "fb-a"

    # Beta sees only fb_b
    records_b = repo.list_feedback("tenant-beta")
    assert len(records_b) == 1
    assert records_b[0].feedback_id == "fb-b"
