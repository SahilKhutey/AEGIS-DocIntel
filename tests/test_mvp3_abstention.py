"""tests/test_mvp3_abstention.py
===============================
MVP 3 tests for safe abstention on insufficient or conflicting evidence.
"""

from __future__ import annotations

import json
from src.engines.generation.contracts import (
    Evidence,
    GenerationPolicy,
    GenerationRequest,
)
from src.engines.generation.generator import AnswerGenerator
from src.engines.generation.service import GenerationService


class FakeTextModel:
    def __init__(self, response: str) -> None:
        self.response = response
        self.call_count = 0

    def generate(self, **kwargs) -> str:
        self.call_count += 1
        return self.response


def test_abstention_on_empty_retrieved_evidence():
    """When no evidence items are retrieved, the service abstains immediately without invoking the model."""
    fake_model = FakeTextModel('{"status": "answered", "answer": "hallucinated", "claims": []}')
    generator = AnswerGenerator(fake_model)
    service = GenerationService(generator)

    req = GenerationRequest(
        question="What is the undisclosed forward guidance?",
        tenant_id="tenant-a",
        evidence=(),  # Zero evidence items
        policy=GenerationPolicy(min_evidence_items=1),
    )

    result = service.answer(req)
    assert result.status == "insufficient_evidence"
    assert "not contain sufficient evidence" in result.answer
    assert len(result.claims) == 0
    assert len(result.citations) == 0
    # Model was never called
    assert fake_model.call_count == 0


def test_model_initiated_insufficient_evidence_status():
    """Model explicitly determines evidence is irrelevant or insufficient."""
    payload = {
        "status": "insufficient_evidence",
        "answer": "The provided passage describes corporate governance but does not state annual revenue.",
        "claims": [],
        "warnings": ["Query topic not covered in source text."],
    }
    fake_model = FakeTextModel(json.dumps(payload))
    generator = AnswerGenerator(fake_model)
    service = GenerationService(generator)

    ev = Evidence(
        chunk_id="chunk-gov",
        document_id="doc-gov",
        tenant_id="tenant-a",
        text="The board of directors meets quarterly.",
        score=0.45,
    )

    req = GenerationRequest(
        question="What was annual revenue?",
        tenant_id="tenant-a",
        evidence=(ev,),
    )

    result = service.answer(req)
    assert result.status == "insufficient_evidence"
    assert "does not state annual revenue" in result.answer
    assert "Query topic not covered" in result.warnings[0]
    assert len(result.citations) == 0


def test_model_detected_conflicting_evidence_status():
    """Model detects conflicting evidence between two retrieved sources and flags it."""
    payload = {
        "status": "conflicting_evidence",
        "answer": "Source 1 states the merger price was $20M, whereas Source 2 states it was $25M.",
        "claims": [],
        "warnings": ["Conflicting purchase price figures detected across sources."],
    }
    fake_model = FakeTextModel(json.dumps(payload))
    generator = AnswerGenerator(fake_model)
    service = GenerationService(generator)

    ev1 = Evidence(
        chunk_id="chk-v1",
        document_id="doc-1",
        tenant_id="tenant-a",
        text="Acquisition closed at $20M.",
        score=0.91,
    )
    ev2 = Evidence(
        chunk_id="chk-v2",
        document_id="doc-2",
        tenant_id="tenant-a",
        text="Acquisition closed at $25M.",
        score=0.90,
    )

    req = GenerationRequest(
        question="What was the acquisition price?",
        tenant_id="tenant-a",
        evidence=(ev1, ev2),
    )

    result = service.answer(req)
    assert result.status == "conflicting_evidence"
    assert "$20M" in result.answer and "$25M" in result.answer
    assert "Conflicting purchase price" in result.warnings[0]
    assert len(result.citations) == 0
