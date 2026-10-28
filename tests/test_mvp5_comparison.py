"""
tests/test_mvp5_comparison.py
=============================
Unit tests for deterministic cross-document fact comparison and tenant isolation enforcement.
"""

import pytest
from src.engines.intelligence.comparison import (
    CrossTenantComparisonError,
    DocumentComparator,
)
from src.engines.intelligence.contracts import ExtractedFact


def test_cross_tenant_comparison_prohibited():
    comparator = DocumentComparator()
    fact_a = ExtractedFact(
        fact_id="fa",
        tenant_id="tenant-alpha",
        document_id="doc-a",
        subject="sla",
        attribute="notice_period",
        value=30,
        raw_value="30 days",
    )
    fact_b = ExtractedFact(
        fact_id="fb",
        tenant_id="tenant-beta",
        document_id="doc-b",
        subject="sla",
        attribute="notice_period",
        value=30,
        raw_value="30 days",
    )

    with pytest.raises(CrossTenantComparisonError):
        comparator.compare_facts(
            tenant_id="tenant-alpha",
            left_doc_id="doc-a",
            left_facts=[fact_a],
            right_doc_id="doc-b",
            right_facts=[fact_b],
        )


def test_comparison_equal_and_discrepancy():
    comparator = DocumentComparator()
    f1 = ExtractedFact(
        fact_id="f1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="liability_cap",
        value=1000000.0,
        raw_value="$1,000,000",
        value_type="decimal",
        unit="USD",
    )
    f2 = ExtractedFact(
        fact_id="f2",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="contract",
        attribute="liability_cap",
        value=2500000.0,
        raw_value="$2,500,000",
        value_type="decimal",
        unit="USD",
    )
    f3_match = ExtractedFact(
        fact_id="f3",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="contract",
        attribute="governing_law",
        value="Delaware",
        raw_value="Delaware",
        value_type="string",
    )
    f1_match = ExtractedFact(
        fact_id="f4",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="governing_law",
        value="Delaware",
        raw_value="Delaware",
        value_type="string",
    )

    res = comparator.compare_facts(
        tenant_id="tenant-1",
        left_doc_id="doc-1",
        left_facts=[f1, f1_match],
        right_doc_id="doc-2",
        right_facts=[f2, f3_match],
    )

    assert res.summary["potential_conflict"] == 1
    assert res.summary["equal"] == 1
    comp_map = {c.attribute: c.status for c in res.comparisons}
    assert comp_map["liability_cap"] == "potential_conflict"
    assert comp_map["governing_law"] == "equal"


def test_comparison_unit_and_period_compatibility():
    comparator = DocumentComparator()

    # Unit mismatch -> not_comparable
    f_usd = ExtractedFact(
        fact_id="f1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="invoice",
        attribute="total",
        value=5000.0,
        raw_value="5000 USD",
        value_type="decimal",
        unit="USD",
    )
    f_eur = ExtractedFact(
        fact_id="f2",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="invoice",
        attribute="total",
        value=5000.0,
        raw_value="5000 EUR",
        value_type="decimal",
        unit="EUR",
    )

    res = comparator.compare_facts(
        tenant_id="tenant-1",
        left_doc_id="doc-1",
        left_facts=[f_usd],
        right_doc_id="doc-2",
        right_facts=[f_eur],
    )
    assert res.comparisons[0].status == "not_comparable"

    # Period mismatch with different values -> different (not conflict)
    f_2025 = ExtractedFact(
        fact_id="f3",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="report",
        attribute="revenue",
        value=100.0,
        raw_value="100",
        value_type="decimal",
        unit="USD",
        period="FY2025",
    )
    f_2026 = ExtractedFact(
        fact_id="f4",
        tenant_id="tenant-1",
        document_id="doc-2",
        subject="report",
        attribute="revenue",
        value=120.0,
        raw_value="120",
        value_type="decimal",
        unit="USD",
        period="FY2026",
    )

    res_period = comparator.compare_facts(
        tenant_id="tenant-1",
        left_doc_id="doc-1",
        left_facts=[f_2025],
        right_doc_id="doc-2",
        right_facts=[f_2026],
    )
    assert res_period.comparisons[0].status == "different"
