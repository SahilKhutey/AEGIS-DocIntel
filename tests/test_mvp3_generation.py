"""tests/test_mvp3_generation.py
===============================
MVP 3 tests for end-to-end answer generation service and provider adapter.
"""

from __future__ import annotations

import json
import pytest

from src.engines.generation.contracts import (
    Evidence,
    GenerationPolicy,
    GenerationRequest,
)
from src.engines.generation.generator import AnswerGenerator, ModelGenerationError
from src.engines.generation.service import GenerationService


class FakeTextModel:
    def __init__(self, response: str, fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        if self.fail:
            raise RuntimeError("Provider connection timeout")
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        return self.response


def make_evidence() -> tuple[Evidence, ...]:
    return (
        Evidence(
            chunk_id="chunk-1",
            document_id="doc-1",
            tenant_id="tenant-alpha",
            text="Net income for the fiscal period was $50M.",
            score=0.96,
            page_number=4,
            section_path=("Financial Statements", "Income"),
        ),
    )


def test_generation_service_end_to_end_success():
    payload = {
        "status": "answered",
        "answer": "Net income for the fiscal period was $50M.",
        "claims": [
            {
                "text": "Net income was $50M.",
                "evidence_ids": ["chunk-1"],
            }
        ],
        "warnings": [],
    }
    fake_model = FakeTextModel(json.dumps(payload))
    generator = AnswerGenerator(fake_model, max_output_tokens=1000)
    service = GenerationService(generator)

    req = GenerationRequest(
        question="What was net income?",
        tenant_id="tenant-alpha",
        evidence=make_evidence(),
    )

    result = service.answer(req)
    assert result.status == "answered"
    assert "Net income for the fiscal period was $50M." in result.answer
    assert len(result.claims) == 1
    assert result.claims[0].evidence_ids == ("chunk-1",)
    assert len(result.citations) == 1
    assert result.citations[0].evidence_id == "chunk-1"
    assert result.citations[0].document_id == "doc-1"
    assert result.citations[0].page_number == 4


def test_generation_service_provider_error_handling():
    fake_model = FakeTextModel("", fail=True)
    generator = AnswerGenerator(fake_model)
    service = GenerationService(generator)

    req = GenerationRequest(
        question="What was net income?",
        tenant_id="tenant-alpha",
        evidence=make_evidence(),
    )

    with pytest.raises(ModelGenerationError, match="Underlying model generation failed"):
        service.answer(req)


def test_generation_service_empty_output_handling():
    fake_model = FakeTextModel("   ")
    generator = AnswerGenerator(fake_model)
    service = GenerationService(generator)

    req = GenerationRequest(
        question="What was net income?",
        tenant_id="tenant-alpha",
        evidence=make_evidence(),
    )

    with pytest.raises(ModelGenerationError, match="Model returned empty response"):
        service.answer(req)


def test_generation_service_answer_exceeding_length_limit():
    payload = {
        "status": "answered",
        "answer": "A" * 501,
        "claims": [{"text": "Fact", "evidence_ids": ["chunk-1"]}],
        "warnings": [],
    }
    fake_model = FakeTextModel(json.dumps(payload))
    generator = AnswerGenerator(fake_model)
    service = GenerationService(generator)

    req = GenerationRequest(
        question="What was net income?",
        tenant_id="tenant-alpha",
        evidence=make_evidence(),
        policy=GenerationPolicy(max_answer_chars=500),
    )

    with pytest.raises(Exception, match="exceeds maximum length"):
        service.answer(req)
