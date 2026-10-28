"""
tests/test_mvp6_review_service.py
=================================
Unit and workflow integration tests for ReviewService governance operations.
"""

import pytest
from src.engines.governance.contracts import (
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
    ReviewStatus,
)
from src.engines.governance.evidence_validator import EvidenceValidationError
from src.engines.governance.policy import ReviewPolicyError
from src.engines.governance.review_service import ReviewService
from src.engines.intelligence.contracts import EvidenceSpan, ExtractedFact
from src.repositories.review_repository import ReviewRepository

AUTH_DOC_TEXT = "Master Services Agreement. The total aggregate liability shall not exceed $2,500,000 USD."


def test_review_service_full_workflow(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "service_test.db"))
    svc = ReviewService(repository=repo)

    reviewer = ReviewActor(
        tenant_id="tenant-1",
        user_id="reviewer-alice",
        roles=frozenset({"reviewer"}),
    )
    admin = ReviewActor(
        tenant_id="tenant-1",
        user_id="admin-carol",
        roles=frozenset({"review_admin"}),
    )

    span = EvidenceSpan(
        document_id="doc-1",
        tenant_id="tenant-1",
        chunk_id="c1",
        quoted_text="liability shall not exceed $2,500,000 USD",
    )
    fact = ExtractedFact(
        fact_id="fact-1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="liability_cap",
        value=2500000.0,
        raw_value="$2,500,000",
        value_type="decimal",
        unit="USD",
        evidence=(span,),
    )

    # 1. Ingest fact -> create review item
    item = svc.create_review_from_fact("tenant-1", fact)
    assert item.status == ReviewStatus.PENDING
    assert item.version == 1

    # 2. Reviewer claims item
    claimed = svc.claim(reviewer, item.review_id, expected_version=1)
    assert claimed.status == ReviewStatus.IN_REVIEW
    assert claimed.assigned_to == "reviewer-alice"
    assert claimed.version == 2

    # 3. Reviewer submits correction with valid quote
    submission = DecisionSubmission(
        action=ReviewAction.CORRECT,
        expected_version=2,
        rationale="Specified in millions format",
        corrected_value=2500000.0,
        corrected_type="decimal",
        unit="USD",
        evidence_quote="liability shall not exceed $2,500,000 USD",
    )
    updated, decision, audit = svc.decide(
        actor=reviewer,
        review_id=item.review_id,
        submission=submission,
        authoritative_text=AUTH_DOC_TEXT,
    )
    assert updated.status == ReviewStatus.CORRECTED
    assert updated.version == 3
    assert decision.action == ReviewAction.CORRECT
    assert audit.sequence == 3

    # 4. Attempt to approve already-corrected item directly fails (must be in_review)
    approve_sub = DecisionSubmission(
        action=ReviewAction.APPROVE,
        expected_version=3,
        rationale="Try to approve directly",
    )
    with pytest.raises(ReviewPolicyError, match="requires item to be in 'in_review' status"):
        svc.decide(reviewer, item.review_id, approve_sub)

    # 5. Admin reopens item
    reopened, reopen_dec, reopen_audit = svc.reopen(
        actor=admin,
        review_id=item.review_id,
        expected_version=3,
        rationale="Reopening for secondary executive verification",
    )
    assert reopened.status == ReviewStatus.IN_REVIEW
    assert reopened.version == 4

    # 6. Admin approves item
    approve_final = DecisionSubmission(
        action=ReviewAction.APPROVE,
        expected_version=4,
        rationale="Approved after executive review",
        evidence_quote="liability shall not exceed $2,500,000 USD",
    )
    approved_item, _, _ = svc.decide(
        actor=admin,
        review_id=item.review_id,
        submission=approve_final,
        authoritative_text=AUTH_DOC_TEXT,
    )
    assert approved_item.status == ReviewStatus.APPROVED
    assert approved_item.version == 5

    # 7. Check audit history
    history = svc.get_history(reviewer, item.review_id)
    assert len(history) == 5  # create (1), claim (2), correct (3), reopen (4), approve (5)
    actions = [h.action for h in history]
    assert actions == ["create", "claim", "correct", "reopen", "approve"]


def test_review_service_evidence_validation_failure(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "service_ev_fail.db"))
    svc = ReviewService(repository=repo)

    reviewer = ReviewActor(
        tenant_id="tenant-1",
        user_id="reviewer-alice",
        roles=frozenset({"reviewer"}),
    )

    fact = ExtractedFact(
        fact_id="fact-2",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="notice_period",
        value=30,
        raw_value="30 days",
    )
    item = svc.create_review_from_fact("tenant-1", fact)
    svc.claim(reviewer, item.review_id, expected_version=1)

    # Submitting an ungrounded quote fails with EvidenceValidationError
    submission = DecisionSubmission(
        action=ReviewAction.APPROVE,
        expected_version=2,
        rationale="Approval with fictitious quote",
        evidence_quote="90 days notice shall be strictly required",
    )

    with pytest.raises(EvidenceValidationError, match="not present in the authoritative text"):
        svc.decide(
            actor=reviewer,
            review_id=item.review_id,
            submission=submission,
            authoritative_text=AUTH_DOC_TEXT,
        )

    # Status remains in_review at version 2
    cur = svc.get_review(reviewer, item.review_id)
    assert cur.status == ReviewStatus.IN_REVIEW
    assert cur.version == 2
