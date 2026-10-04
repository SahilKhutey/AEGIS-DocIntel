"""
Tests for AEGIS PII Compliance & Redaction Engine and Pipeline Integration.
"""
from __future__ import annotations

import pytest

from src.compliance.redaction_engine import (
    detect_pii,
    apply_redaction_policy,
    redact_elements,
    RedactionPolicy,
)
from src.core.geometric_element import GeometricElement, ElementType
from src.models.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator


def test_pii_detection_ssn_credit_card_phone_person():
    elem = {
        "id": "e1",
        "text": "Contact John Doe at 555-123-4567 or SSN 123-45-6789. Card 4111-2222-3333-4444.",
        "doc_id": "d1",
    }
    entities = detect_pii(elem)
    entity_types = {e.entity_type for e in entities}
    assert "US_SSN" in entity_types
    assert "CREDIT_CARD" in entity_types
    assert "PHONE_NUMBER" in entity_types
    assert "PERSON" in entity_types


def test_apply_redaction_policy():
    elem = {
        "id": "e1",
        "text": "SSN: 987-65-4321",
        "doc_id": "d1",
    }
    entities = detect_pii(elem)
    assert len(entities) > 0

    policies = [RedactionPolicy("US_SSN", "redact", replacement="[SSN_REDACTED]")]
    redacted_elem, report = apply_redaction_policy(elem, entities, policies)
    assert "[SSN_REDACTED]" in redacted_elem["text"]
    assert "987-65-4321" not in redacted_elem["text"]
    assert report.redactions_applied == 1


def test_redact_geometric_elements():
    elements = [
        GeometricElement(
            element_id="g1",
            doc_id="d1",
            type=ElementType.PARAGRAPH,
            content="Call Jane Smith at 123-456-7890 for credit card 1234-5678-9012-3456.",
        )
    ]
    redacted, report = redact_elements(elements)
    assert len(redacted) == 1
    assert "123-456-7890" not in redacted[0].content
    assert "1234-5678-9012-3456" not in redacted[0].content
    assert report.redactions_applied >= 2


@pytest.mark.asyncio
async def test_orchestrator_ingest_with_pii_redaction():
    orchestrator = AMDIOrchestrator()
    try:
        doc = DocumentObject(
            filename="pii_sample.txt",
            raw_bytes=b"Confidential report for John Smith, SSN 111-22-3333.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-compliance",
        )
        # Enable PII redaction
        doc.enable_redaction = True

        stats = await orchestrator.ingest(doc)
        assert stats["pii_entities_found"] > 0
        assert stats["redactions_applied"] > 0

        # Verify ingested elements stored in orchestrator carry redacted text
        elements = orchestrator.get_document_elements(stats["doc_id"], tenant_id="tenant-compliance")
        assert len(elements) > 0
        assert "111-22-3333" not in elements[0].content
    finally:
        await orchestrator.close()
