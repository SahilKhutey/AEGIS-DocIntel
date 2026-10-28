"""
tests/test_mvp6_review_repository.py
====================================
Unit and integration tests for ReviewRepository, transactional transitions,
optimistic concurrency, and idempotency.
"""

import pytest
from src.engines.governance.contracts import (
    ReviewAction,
    ReviewDecision,
    ReviewRevision,
    ReviewStatus,
)
from src.repositories.review_repository import (
    ReviewNotFoundError,
    ReviewRepository,
    StaleReviewVersionError,
)


def test_repository_item_creation_and_idempotent_get(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "reviews.db"))

    item = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="fact-100",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "revenue", "value": 50000.0},
        assigned_to="reviewer-a",
    )

    assert item.review_id.startswith("rev-")
    assert item.status == ReviewStatus.PENDING
    assert item.version == 1
    assert item.assigned_to == "reviewer-a"

    # Creating again returns same existing item
    item2 = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="fact-100",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "revenue", "value": 50000.0},
    )
    assert item2.review_id == item.review_id


def test_repository_optimistic_concurrency_and_rollback(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "reviews_concurrency.db"))

    item = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="fact-200",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "term", "value": 30},
    )

    dec = ReviewDecision(
        decision_id="dec-1",
        review_id=item.review_id,
        tenant_id="tenant-1",
        actor_id="reviewer-1",
        action=ReviewAction.APPROVE,
        from_status=ReviewStatus.PENDING,
        to_status=ReviewStatus.APPROVED,
        version_reviewed=1,
        rationale="Approved",
    )

    # 1. Successful transition version 1 -> 2
    updated_item, _, audit = repo.save_transition(
        tenant_id="tenant-1",
        review_id=item.review_id,
        expected_version=1,
        new_status=ReviewStatus.APPROVED,
        new_assigned_to="reviewer-1",
        decision=dec,
    )
    assert updated_item.version == 2
    assert updated_item.status == ReviewStatus.APPROVED
    assert audit.sequence == 2

    # 2. Conflicting transition attempting to use expected_version=1 again must fail
    dec_stale = ReviewDecision(
        decision_id="dec-stale",
        review_id=item.review_id,
        tenant_id="tenant-1",
        actor_id="reviewer-2",
        action=ReviewAction.REJECT,
        from_status=ReviewStatus.PENDING,
        to_status=ReviewStatus.REJECTED,
        version_reviewed=1,
        rationale="Rejected",
    )

    with pytest.raises(StaleReviewVersionError):
        repo.save_transition(
            tenant_id="tenant-1",
            review_id=item.review_id,
            expected_version=1,
            new_status=ReviewStatus.REJECTED,
            new_assigned_to="reviewer-2",
            decision=dec_stale,
        )

    # Verify no partial rollback occurred: item remains version 2, approved
    persisted = repo.get_review("tenant-1", item.review_id)
    assert persisted.version == 2
    assert persisted.status == ReviewStatus.APPROVED


def test_repository_idempotency_key_replay(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "reviews_idem.db"))

    item = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="fact-300",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "liability_cap", "value": 1000000.0},
    )

    dec = ReviewDecision(
        decision_id="dec-orig",
        review_id=item.review_id,
        tenant_id="tenant-1",
        actor_id="reviewer-1",
        action=ReviewAction.APPROVE,
        from_status=ReviewStatus.PENDING,
        to_status=ReviewStatus.APPROVED,
        version_reviewed=1,
        rationale="Approved via idempotent call",
        idempotency_key="key-abc-123",
    )

    # First call
    up_item, res_dec, audit = repo.save_transition(
        tenant_id="tenant-1",
        review_id=item.review_id,
        expected_version=1,
        new_status=ReviewStatus.APPROVED,
        new_assigned_to="reviewer-1",
        decision=dec,
        idempotency_key="key-abc-123",
    )
    assert up_item.version == 2
    assert res_dec.decision_id == "dec-orig"

    # Replay with same idempotency key returns cached decision without re-advancing version
    replay_item, replay_dec, replay_audit = repo.save_transition(
        tenant_id="tenant-1",
        review_id=item.review_id,
        expected_version=1,
        new_status=ReviewStatus.APPROVED,
        new_assigned_to="reviewer-1",
        decision=dec,
        idempotency_key="key-abc-123",
    )
    assert replay_item.version == 2
    assert replay_dec.decision_id == "dec-orig"


def test_repository_approved_facts_filtering(tmp_path):
    repo = ReviewRepository(db_path=str(tmp_path / "reviews_approved.db"))

    # Item 1: approved fact
    item1 = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="f1",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "effective_date", "value": "2026-01-01"},
    )
    dec1 = ReviewDecision(
        decision_id="d1",
        review_id=item1.review_id,
        tenant_id="tenant-1",
        actor_id="r1",
        action=ReviewAction.APPROVE,
        from_status=ReviewStatus.PENDING,
        to_status=ReviewStatus.APPROVED,
        version_reviewed=1,
        rationale="Good",
    )
    repo.save_transition(
        tenant_id="tenant-1",
        review_id=item1.review_id,
        expected_version=1,
        new_status=ReviewStatus.APPROVED,
        new_assigned_to="r1",
        decision=dec1,
    )

    # Item 2: corrected fact
    item2 = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="f2",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "liability_cap", "value": 1000.0, "unit": "USD"},
    )
    rev2 = ReviewRevision(
        revision_id="rev-2",
        review_id=item2.review_id,
        tenant_id="tenant-1",
        actor_id="r1",
        version=2,
        corrected_value=2500000.0,
        corrected_type="decimal",
        unit="USD",
        rationale="Corrected scale",
    )
    dec2 = ReviewDecision(
        decision_id="d2",
        review_id=item2.review_id,
        tenant_id="tenant-1",
        actor_id="r1",
        action=ReviewAction.CORRECT,
        from_status=ReviewStatus.PENDING,
        to_status=ReviewStatus.CORRECTED,
        version_reviewed=1,
        rationale="Corrected scale",
    )
    repo.save_transition(
        tenant_id="tenant-1",
        review_id=item2.review_id,
        expected_version=1,
        new_status=ReviewStatus.CORRECTED,
        new_assigned_to="r1",
        decision=dec2,
        revision=rev2,
    )

    # Item 3: rejected fact
    item3 = repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="f3",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "false_fact", "value": "untrue"},
    )
    dec3 = ReviewDecision(
        decision_id="d3",
        review_id=item3.review_id,
        tenant_id="tenant-1",
        actor_id="r1",
        action=ReviewAction.REJECT,
        from_status=ReviewStatus.PENDING,
        to_status=ReviewStatus.REJECTED,
        version_reviewed=1,
        rationale="Hallucination",
    )
    repo.save_transition(
        tenant_id="tenant-1",
        review_id=item3.review_id,
        expected_version=1,
        new_status=ReviewStatus.REJECTED,
        new_assigned_to="r1",
        decision=dec3,
    )

    # Item 4: pending fact
    repo.create_review_item(
        tenant_id="tenant-1",
        candidate_id="f4",
        candidate_type="fact",
        document_id="doc-1",
        candidate_data={"attribute": "pending_fact", "value": 123},
    )

    approved = repo.get_approved_facts("tenant-1", "doc-1")
    assert len(approved) == 2

    attrs = {f["attribute"]: f for f in approved}
    assert "effective_date" in attrs
    assert attrs["effective_date"]["value"] == "2026-01-01"
    assert attrs["effective_date"]["is_corrected"] is False

    assert "liability_cap" in attrs
    assert attrs["liability_cap"]["value"] == 2500000.0
    assert attrs["liability_cap"]["is_corrected"] is True

    # Confirm rejected and pending facts are excluded
    assert "false_fact" not in attrs
    assert "pending_fact" not in attrs
