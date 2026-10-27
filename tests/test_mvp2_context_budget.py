"""tests/test_mvp2_context_budget.py
===================================
MVP 2 tests for context assembly token budgeting and source provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.engines.context.context_builder import ContextBuilder, BuiltContext


@dataclass
class DummyElement:
    element_id: str
    content: str
    page_number: int = 1
    element_type: str = "PARAGRAPH"


@dataclass
class DummyRetrievalResult:
    element: DummyElement
    score: float = 0.9


@dataclass
class DummyRetrievalContext:
    results: List[DummyRetrievalResult]
    table_answers: List[str]


def test_context_budget_strict_enforcement():
    """Total tokens must respect the configured budget limit."""
    builder = ContextBuilder(max_tokens=400, target_tokens=300, reserve_tokens=100)
    # Context budget is 400 - 100 = 300 tokens

    # Create several paragraph results
    elements = [
        DummyRetrievalResult(
            element=DummyElement(
                element_id=f"chunk-{i}",
                content=f"Detailed financial and operational performance section {i}. " * 10,
            ),
            score=1.0 - (i * 0.1),
        )
        for i in range(10)
    ]

    ctx = DummyRetrievalContext(results=elements, table_answers=[])
    built: BuiltContext = builder.build("What was quarterly revenue?", ctx)

    # Hard budget is max_tokens
    assert built.tokens_used <= 400
    # The source map should only include the elements that fit
    assert len(built.source_map) < len(elements)
    # Source map citation numbers should be 1-based sequential integers
    for cit_idx, eid in built.source_map.items():
        assert isinstance(cit_idx, int)
        assert cit_idx >= 1
        assert eid.startswith("chunk-")


def test_oversized_passage_skipped_safely():
    """An oversized passage that exceeds the budget is skipped without crashing."""
    builder = ContextBuilder(max_tokens=250, target_tokens=200, reserve_tokens=50)

    # Passage 1 is huge and exceeds budget
    huge_elem = DummyRetrievalResult(
        element=DummyElement(
            element_id="huge-chunk",
            content="Extremely long text content repeating. " * 300,
        ),
        score=0.99,
    )
    # Passage 2 is small
    small_elem = DummyRetrievalResult(
        element=DummyElement(
            element_id="small-chunk",
            content="Short compact fact.",
        ),
        score=0.50,
    )

    ctx = DummyRetrievalContext(results=[huge_elem, small_elem], table_answers=[])
    built = builder.build("Question?", ctx)

    # Huge element was skipped because it exceeded the budget
    assert "huge-chunk" not in built.source_map.values()
    # Built messages exist and are properly structured
    assert len(built.messages) >= 2  # system + user


def test_source_mapping_preserves_provenance():
    """Source map accurately links 1-based citation IDs to source element IDs."""
    builder = ContextBuilder(max_tokens=1000, target_tokens=800, reserve_tokens=200)

    results = [
        DummyRetrievalResult(
            element=DummyElement(element_id="doc1::sec1::chk1", content="Fact one."),
            score=0.95,
        ),
        DummyRetrievalResult(
            element=DummyElement(element_id="doc1::sec2::chk2", content="Fact two."),
            score=0.85,
        ),
    ]

    ctx = DummyRetrievalContext(results=results, table_answers=[])
    built = builder.build("Verify facts", ctx)

    assert built.source_map == {1: "doc1::sec1::chk1", 2: "doc1::sec2::chk2"}
    assert built.element_count == 2
    # Check that citation indicators appear in user message content
    user_msg = next(m["content"] for m in built.messages if m["role"] == "user")
    assert "[1] PARAGRAPH (p.1):" in user_msg
    assert "[2] PARAGRAPH (p.1):" in user_msg
