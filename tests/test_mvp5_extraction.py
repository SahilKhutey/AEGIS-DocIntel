"""
tests/test_mvp5_extraction.py
=============================
Unit tests for schema-guided fact extraction, quote verification, and envelope boundaries.
"""

import json
from src.engines.intelligence.contracts import ExtractionSchema, FieldDefinition
from src.engines.intelligence.fact_extractor import (
    FactExtractor,
    build_untrusted_document_envelope,
    verify_quote_in_source,
)


def test_verify_quote_in_source():
    text = "The aggregate liability shall not exceed $5,000,000 USD under any circumstances."

    # Exact match with offsets
    ok, s, e = verify_quote_in_source("aggregate liability shall not exceed $5,000,000 USD", text, 4, 60)
    assert ok is True
    assert s == 4
    assert e == 60

    # Match without offsets (calculates offsets)
    ok, s, e = verify_quote_in_source("liability shall not exceed", text)
    assert ok is True
    assert s == 14
    assert e == 40
    assert text[s:e] == "liability shall not exceed"

    # Case-insensitive match
    ok, s, e = verify_quote_in_source("AGGREGATE LIABILITY", text)
    assert ok is True
    assert s == 4

    # Non-existent quote
    ok, s, e = verify_quote_in_source("unlimited indemnification", text)
    assert ok is False
    assert s is None
    assert e is None


def test_build_untrusted_document_envelope():
    content = "Sensitive untrusted text with <b>injection</b> attempts."
    envelope_str = build_untrusted_document_envelope("doc-secure-1", content)
    envelope = json.loads(envelope_str)

    assert envelope["__security_boundary__"] == "UNTRUSTED_DOCUMENT_SOURCE"
    assert envelope["document_id"] == "doc-secure-1"
    assert envelope["payload"] == content
    assert "content_hash" in envelope


def test_fact_extractor_financial_metrics():
    extractor = FactExtractor()
    passages = [
        {
            "chunk_id": "c1",
            "text": "In FY2026, total revenue was $14.2 billion and operating expenses reached $5.8 billion.",
            "page_number": 1,
        },
        {
            "chunk_id": "c2",
            "text": "Net income of $3.4 billion was recorded, while EBITDA was $4.9 billion for the quarter.",
            "page_number": 2,
        },
    ]

    res = extractor.extract_document_facts(
        tenant_id="tenant-1",
        document_id="doc-fin-1",
        passages=passages,
        schema_name="financial_metrics",
    )

    assert res.status == "completed"
    assert len(res.facts) >= 4
    attrs = {f.attribute: f for f in res.facts}

    assert "revenue" in attrs
    assert attrs["revenue"].value == 14200000000.0
    assert attrs["revenue"].unit == "USD"
    assert attrs["revenue"].period == "FY2026"
    assert len(attrs["revenue"].evidence) == 1
    assert attrs["revenue"].evidence[0].page_number == 1

    assert "net_income" in attrs
    assert attrs["net_income"].value == 3400000000.0


def test_fact_extractor_custom_schema():
    extractor = FactExtractor()
    custom_field = FieldDefinition(
        name="Security SLA",
        attribute="security_sla",
        value_type="decimal",
        unit="percent",
        patterns=(r"(?i)uptime\s+sla\s*(?:of|is|was)?\s*[:=\-]?\s*([\d.,]+\s*%)",),
    )
    schema = ExtractionSchema(
        schema_name="sla_schema",
        schema_version=1,
        target_subject="cloud_agreement",
        fields=(custom_field,),
    )
    extractor.register_schema(schema)

    passages = [
        {"chunk_id": "chk-1", "text": "Provider guarantees uptime SLA of 99.95% per month.", "page_number": 1}
    ]

    res = extractor.extract_document_facts(
        tenant_id="tenant-1",
        document_id="doc-sla-1",
        passages=passages,
        schema_name="sla_schema",
    )

    assert res.status == "completed"
    assert len(res.facts) == 1
    f = res.facts[0]
    assert f.attribute == "security_sla"
    assert f.value == 99.95
    assert f.unit == "percent"
