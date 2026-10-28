"""
tests/test_mvp6_review_contracts.py
===================================
Unit tests for MVP 6 governance contracts, immutability, and serialization round-trips.
"""

import pytest
from src.engines.governance.contracts import (
    AuditEvent,
    DecisionSubmission,
    ReviewAction,
    ReviewActor,
    ReviewDecision,
    ReviewItem,
    ReviewRevision,
    ReviewStatus,
)


def test_review_actor_contract():
    actor = ReviewActor(
        tenant_id="tenant-alpha",
        user_id="user-123",
        roles=frozenset({"reviewer"}),
    )
    assert actor.tenant_id == "tenant-alpha"
    assert actor.user_id == "user-123"
    assert actor.has_role("reviewer") is True
    assert actor.has_role("admin") is False

    with pytest.raises(AttributeError):
        actor.user_id = "user-456"  # type: ignore


def test_review_item_roundtrip():
    item = ReviewItem(
        review_id="rev-001",
        tenant_id="tenant-alpha",
        candidate_id="fact-100",
        candidate_type="fact",
        document_id="doc-1",
        status=ReviewStatus.PENDING,
        version=1,
        candidate_data={"attribute": "revenue", "value": 1000000.0},
        assigned_to="reviewer-bob",
        current_revision_id=None,
        created_at="2026-10-28T10:00:00Z",
        updated_at="2026-10-28T10:00:00Z",
    )

    d = item.to_dict()
    assert d["review_id"] == "rev-001"
    assert d["status"] == "pending"
    assert d["candidate_data"]["attribute"] == "revenue"

    restored = ReviewItem.from_dict(d)
    assert restored == item


def test_review_decision_and_revision_roundtrip():
    rev = ReviewRevision(
        revision_id="rev-rev-1",
        review_id="rev-001",
        tenant_id="tenant-alpha",
        actor_id="user-123",
        version=2,
        corrected_value=1250000.0,
        corrected_type="decimal",
        unit="USD",
        evidence_quote="total revenue was $1.25 million",
        rationale="Corrected missing decimal",
        created_at="2026-10-28T10:05:00Z",
    )
    d_rev = rev.to_dict()
    assert d_rev["corrected_value"] == 1250000.0
    assert ReviewRevision.from_dict(d_rev) == rev

    dec = ReviewDecision(
        decision_id="dec-1",
        review_id="rev-001",
        tenant_id="tenant-alpha",
        actor_id="user-123",
        action=ReviewAction.CORRECT,
        from_status=ReviewStatus.IN_REVIEW,
        to_status=ReviewStatus.CORRECTED,
        version_reviewed=1,
        rationale="Corrected missing decimal",
        evidence_quote="total revenue was $1.25 million",
        idempotency_key="idem-key-1",
        created_at="2026-10-28T10:05:00Z",
    )
    d_dec = dec.to_dict()
    assert d_dec["action"] == "correct"
    assert ReviewDecision.from_dict(d_dec) == dec


def test_audit_event_roundtrip():
    event = AuditEvent(
        event_id="evt-1",
        review_id="rev-001",
        sequence=1,
        tenant_id="tenant-alpha",
        actor_id="user-123",
        action=ReviewAction.APPROVE,
        previous_status=ReviewStatus.IN_REVIEW,
        new_status=ReviewStatus.APPROVED,
        previous_version=1,
        new_version=2,
        rationale="Approved as accurate",
        revision_id=None,
        request_id="req-abc",
        timestamp="2026-10-28T10:10:00Z",
    )
    d_evt = event.to_dict()
    assert d_evt["sequence"] == 1
    assert AuditEvent.from_dict(d_evt) == event
