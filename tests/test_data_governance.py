"""
AEGIS-DocIntel — Data Governance & Lifecycle Policy Tests
=========================================================
Verifies:
- RetentionPolicy bounds and validation
- Automated expiry calculation
- Legal hold locking, preventing purge/deletion
- Tenant matching verification
- Cascading purge execution and audit trail recording
"""
import pytest
import time
from unittest.mock import AsyncMock

from src.core.governance import (
    ClassificationLevel,
    DocumentGovernanceRecord,
    RetentionPolicy,
    RetentionEngine,
    LegalHoldActiveError,
    RetentionPolicyViolationError,
)


def test_retention_policy_validation():
    # Valid policy
    policy = RetentionPolicy(
        policy_id="pol-standard-90",
        tenant_id="tenant-alpha",
        name="90 Day Standard Retention",
        max_age_days=90,
    )
    assert policy.max_age_days == 90
    assert policy.delete_source is True

    # Empty policy_id
    with pytest.raises(ValueError, match="non-empty policy_id"):
        RetentionPolicy(policy_id="", tenant_id="tenant-alpha", name="Invalid", max_age_days=30)

    # Empty tenant_id
    with pytest.raises(ValueError, match="non-empty tenant_id"):
        RetentionPolicy(policy_id="p1", tenant_id="", name="Invalid", max_age_days=30)

    # Negative max_age_days
    with pytest.raises(ValueError, match="non-negative"):
        RetentionPolicy(policy_id="p1", tenant_id="t1", name="Invalid", max_age_days=-5)


def test_document_governance_record_defaults():
    rec = DocumentGovernanceRecord(doc_id="doc-123", tenant_id="tenant-alpha")
    assert rec.classification == ClassificationLevel.INTERNAL
    assert rec.legal_hold is False
    assert rec.expires_at is None
    assert rec.purged_at is None


def test_expiry_calculation_and_policy_binding():
    base_time = 1700000000.0
    policy = RetentionPolicy(
        policy_id="pol-30d",
        tenant_id="tenant-alpha",
        name="30 Days",
        max_age_days=30,
    )
    rec = DocumentGovernanceRecord(
        doc_id="doc-1",
        tenant_id="tenant-alpha",
        created_at=base_time,
    )

    RetentionEngine.apply_policy(rec, policy)
    expected_expiry = base_time + (30 * 86400.0)
    assert rec.expires_at == expected_expiry
    assert rec.retention_policy_id == "pol-30d"

    # Before expiry
    assert not RetentionEngine.is_expired(rec, now=base_time + 100)
    can_purge, reason = RetentionEngine.can_purge(rec, now=base_time + 100)
    assert can_purge is False
    assert "has not yet expired" in reason

    # After expiry
    assert RetentionEngine.is_expired(rec, now=expected_expiry + 1)
    can_purge, reason = RetentionEngine.can_purge(rec, now=expected_expiry + 1)
    assert can_purge is True


def test_tenant_mismatch_policy_binding():
    policy = RetentionPolicy(
        policy_id="pol-1",
        tenant_id="tenant-alpha",
        name="Policy Alpha",
        max_age_days=30,
    )
    rec = DocumentGovernanceRecord(doc_id="doc-2", tenant_id="tenant-bravo")

    with pytest.raises(ValueError, match="Tenant mismatch"):
        RetentionEngine.apply_policy(rec, policy)


def test_legal_hold_blocks_purge():
    base_time = 1700000000.0
    rec = DocumentGovernanceRecord(
        doc_id="doc-litigation",
        tenant_id="tenant-alpha",
        created_at=base_time,
        expires_at=base_time + 10,
    )

    RetentionEngine.set_legal_hold(
        rec,
        principal_id="counsel-jane",
        reason="Pending litigation matter Case-492",
    )
    assert rec.legal_hold is True
    assert rec.legal_hold_set_by == "counsel-jane"
    assert "Case-492" in rec.legal_hold_reason

    # Attempting purge after expiry must fail due to legal hold
    can_purge, reason = RetentionEngine.can_purge(rec, now=base_time + 20)
    assert can_purge is False
    assert "active legal hold" in reason

    # Release legal hold
    RetentionEngine.release_legal_hold(rec, principal_id="counsel-jane")
    assert rec.legal_hold is False
    assert rec.legal_hold_reason is None

    can_purge, _ = RetentionEngine.can_purge(rec, now=base_time + 20)
    assert can_purge is True


@pytest.mark.asyncio
async def test_execute_purge_flow_and_audit():
    base_time = 1700000000.0
    rec = DocumentGovernanceRecord(
        doc_id="doc-expiring",
        tenant_id="tenant-alpha",
        created_at=base_time,
        expires_at=base_time + 100,
    )

    mock_doc_service = AsyncMock()
    mock_doc_service.delete.return_value = True

    # Purge before expiry should raise error
    with pytest.raises(RetentionPolicyViolationError):
        await RetentionEngine.execute_purge(rec, mock_doc_service, now=base_time + 10)

    # Purge after expiry succeeds
    inventory = await RetentionEngine.execute_purge(rec, mock_doc_service, now=base_time + 200)
    assert inventory.doc_id == "doc-expiring"
    assert inventory.tenant_id == "tenant-alpha"
    assert inventory.source_bytes_deleted is True
    assert inventory.audit_event_id.startswith("audit_purge_")
    assert rec.purged_at == base_time + 200
    assert rec.purge_audit_id == inventory.audit_event_id

    # Secondary purge attempt must be blocked
    with pytest.raises(RetentionPolicyViolationError, match="already been purged"):
        await RetentionEngine.execute_purge(rec, mock_doc_service, now=base_time + 300)


@pytest.mark.asyncio
async def test_execute_purge_with_legal_hold_raises_error():
    base_time = 1700000000.0
    rec = DocumentGovernanceRecord(
        doc_id="doc-held",
        tenant_id="tenant-alpha",
        created_at=base_time,
        expires_at=base_time + 100,
        legal_hold=True,
        legal_hold_reason="SEC Investigation",
    )
    mock_doc_service = AsyncMock()

    with pytest.raises(LegalHoldActiveError, match="SEC Investigation"):
        await RetentionEngine.execute_purge(rec, mock_doc_service, now=base_time + 200)
