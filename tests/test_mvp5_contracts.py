"""
tests/test_mvp5_contracts.py
============================
Unit tests for MVP 5 data contracts, immutability, and serialization round-trips.
"""

import pytest
from src.engines.intelligence.contracts import (
    EvidenceSpan,
    ExtractedFact,
    FieldDefinition,
    ExtractionSchema,
    ExtractionResult,
    PairComparison,
    DocumentComparisonResult,
    ConflictReport,
)


def test_evidence_span_immutability_and_roundtrip():
    span = EvidenceSpan(
        document_id="doc-100",
        tenant_id="tenant-1",
        chunk_id="chk-1",
        page_number=2,
        start_offset=10,
        end_offset=35,
        quoted_text="liability shall not exceed $1M",
    )
    with pytest.raises(AttributeError):
        span.page_number = 3  # type: ignore

    d = span.to_dict()
    assert d["document_id"] == "doc-100"
    assert d["start_offset"] == 10
    assert d["end_offset"] == 35

    restored = EvidenceSpan.from_dict(d)
    assert restored == span


def test_extracted_fact_immutability_and_roundtrip():
    span = EvidenceSpan(
        document_id="doc-100",
        tenant_id="tenant-1",
        chunk_id="chk-1",
        page_number=1,
        start_offset=0,
        end_offset=25,
        quoted_text="revenue was $10.5 million",
    )
    fact = ExtractedFact(
        fact_id="fact-001",
        tenant_id="tenant-1",
        document_id="doc-100",
        subject="financial_report",
        attribute="revenue",
        value=10500000.0,
        raw_value="$10.5 million",
        value_type="decimal",
        unit="USD",
        period="FY2026",
        evidence=(span,),
        confidence=0.98,
        metadata={"source": "10-K"},
    )
    with pytest.raises(AttributeError):
        fact.value = 20000000.0  # type: ignore

    d = fact.to_dict()
    assert d["value"] == 10500000.0
    assert d["unit"] == "USD"
    assert len(d["evidence"]) == 1

    restored = ExtractedFact.from_dict(d)
    assert restored.fact_id == fact.fact_id
    assert restored.value == fact.value
    assert restored.evidence == fact.evidence


def test_field_and_schema_roundtrip():
    field_def = FieldDefinition(
        name="Net Income",
        attribute="net_income",
        value_type="decimal",
        unit="USD",
        description="Net profits after taxes",
        required=True,
        patterns=(r"(?i)net\s+income\s*[:=\-]?\s*([$€£¥]?[\d.,]+)",),
        aliases=("net_profit",),
    )
    schema = ExtractionSchema(
        schema_name="custom_finance",
        schema_version=2,
        target_subject="corp_filing",
        fields=(field_def,),
        description="Custom financial statement schema",
    )

    d = schema.to_dict()
    assert d["schema_name"] == "custom_finance"
    assert d["schema_version"] == 2
    assert len(d["fields"]) == 1

    restored = ExtractionSchema.from_dict(d)
    assert restored.schema_name == schema.schema_name
    assert restored.fields[0].attribute == "net_income"
    assert restored.fields[0].required is True


def test_extraction_result_roundtrip():
    span = EvidenceSpan(
        document_id="doc-1",
        tenant_id="tenant-1",
        chunk_id="chk-1",
        quoted_text="term: 12 months",
    )
    fact = ExtractedFact(
        fact_id="f1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="agreement",
        attribute="term",
        value=12,
        raw_value="12 months",
        value_type="quantity",
        unit="months",
        evidence=(span,),
    )
    res = ExtractionResult(
        status="completed",
        document_id="doc-1",
        tenant_id="tenant-1",
        facts=(fact,),
        errors=(),
        schema_name="contract_terms",
        schema_version=1,
    )

    d = res.to_dict()
    assert d["status"] == "completed"
    assert len(d["facts"]) == 1

    restored = ExtractionResult.from_dict(d)
    assert restored.status == "completed"
    assert restored.facts[0].fact_id == "f1"


def test_comparison_and_conflict_contracts():
    fact1 = ExtractedFact(
        fact_id="f1",
        tenant_id="t1",
        document_id="doc-a",
        subject="sla",
        attribute="notice_period",
        value=30,
        raw_value="30 days",
        value_type="quantity",
        unit="days",
    )
    fact2 = ExtractedFact(
        fact_id="f2",
        tenant_id="t1",
        document_id="doc-b",
        subject="sla",
        attribute="notice_period",
        value=60,
        raw_value="60 days",
        value_type="quantity",
        unit="days",
    )
    comp = PairComparison(
        subject="sla",
        attribute="notice_period",
        status="potential_conflict",
        left_doc_id="doc-a",
        left_fact=fact1,
        right_doc_id="doc-b",
        right_fact=fact2,
        difference_summary="Notice period discrepancy (30 vs 60 days)",
    )
    result = DocumentComparisonResult(
        tenant_id="t1",
        left_doc_id="doc-a",
        right_doc_id="doc-b",
        comparisons=(comp,),
        summary={"potential_conflict": 1},
    )
    d_res = result.to_dict()
    assert d_res["tenant_id"] == "t1"
    assert len(d_res["comparisons"]) == 1

    conflict = ConflictReport(
        tenant_id="t1",
        subject="sla",
        attribute="notice_period",
        conflict_type="obligation_conflict",
        description="Conflicting termination notice period",
        participating_facts=(fact1, fact2),
        conflicting_document_ids=("doc-a", "doc-b"),
    )
    d_conf = conflict.to_dict()
    assert d_conf["conflict_type"] == "obligation_conflict"
    assert len(d_conf["conflicting_document_ids"]) == 2
