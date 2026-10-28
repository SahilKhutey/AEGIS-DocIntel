"""
tests/test_mvp5_conflicts.py
============================
Unit tests for multi-document conflict detection and evidence preservation.
"""

import pytest
from src.engines.intelligence.conflict_detection import ConflictDetector
from src.engines.intelligence.contracts import EvidenceSpan, ExtractedFact


def test_conflict_detector_tenant_isolation():
    detector = ConflictDetector()
    f1 = ExtractedFact(
        fact_id="f1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="effective_date",
        value="2026-01-01",
        raw_value="2026-01-01",
    )
    f2 = ExtractedFact(
        fact_id="f2",
        tenant_id="tenant-2",
        document_id="doc-2",
        subject="contract",
        attribute="effective_date",
        value="2026-02-01",
        raw_value="2026-02-01",
    )

    with pytest.raises(PermissionError):
        detector.detect_conflicts(tenant_id="tenant-1", facts=[f1, f2])


def test_conflict_detector_types_and_evidence_preservation():
    detector = ConflictDetector()

    span1 = EvidenceSpan(
        document_id="doc-1",
        tenant_id="tenant-1",
        chunk_id="c1",
        quoted_text="liability shall not exceed $1,000,000",
    )
    span2 = EvidenceSpan(
        document_id="doc-2",
        tenant_id="tenant-1",
        chunk_id="c2",
        quoted_text="liability shall not exceed $2,500,000",
    )

    # Quantity discrepancy
    f1 = ExtractedFact(
        fact_id="f1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="agreement",
        attribute="liability_cap",
        value=1000000.0,
        raw_value="$1,000,000",
        value_type="decimal",
        unit="USD",
        evidence=(span1,),
    )
    f2 = ExtractedFact(
        fact_id="f2",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="agreement",
        attribute="liability_cap",
        value=2500000.0,
        raw_value="$2,500,000",
        value_type="decimal",
        unit="USD",
        evidence=(span2,),
    )

    # Date mismatch
    f3 = ExtractedFact(
        fact_id="f3",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="agreement",
        attribute="effective_date",
        value="2026-01-01",
        raw_value="January 1, 2026",
        value_type="date",
    )
    f4 = ExtractedFact(
        fact_id="f4",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="agreement",
        attribute="effective_date",
        value="2026-02-01",
        raw_value="February 1, 2026",
        value_type="date",
    )

    # Obligation conflict (booleans)
    f5 = ExtractedFact(
        fact_id="f5",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="agreement",
        attribute="indemnification",
        value=True,
        raw_value="required",
        value_type="boolean",
    )
    f6 = ExtractedFact(
        fact_id="f6",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="agreement",
        attribute="indemnification",
        value=False,
        raw_value="waived",
        value_type="boolean",
    )

    conflicts = detector.detect_conflicts(
        tenant_id="tenant-1",
        facts=[f1, f2, f3, f4, f5, f6],
    )

    assert len(conflicts) == 3
    conflict_types = {c.attribute: c.conflict_type for c in conflicts}
    assert conflict_types["liability_cap"] == "quantity_discrepancy"
    assert conflict_types["effective_date"] == "date_mismatch"
    assert conflict_types["indemnification"] == "obligation_conflict"

    # Verify both sources are preserved without silently choosing one
    cap_conflict = next(c for c in conflicts if c.attribute == "liability_cap")
    assert len(cap_conflict.participating_facts) == 2
    assert "doc-1" in cap_conflict.conflicting_document_ids
    assert "doc-2" in cap_conflict.conflicting_document_ids
    assert cap_conflict.participating_facts[0].evidence[0].quoted_text == "liability shall not exceed $1,000,000"
    assert cap_conflict.participating_facts[1].evidence[0].quoted_text == "liability shall not exceed $2,500,000"
