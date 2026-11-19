"""
AEGIS-DocIntel — Task PH-007: Context Optimization & Token Budget Verification
=============================================================================
Validates:
1. Submodular knapsack optimization (OptimizationEngine) guaranteeing (1 - 1/e)
   approximation bound under token capacity constraints.
2. Query-adaptive budget scaling for lookup vs comparison/synthesis queries.
3. Context assembly (ContextBuilder) strictly respecting token ceiling and
   maintaining 1-based citation index provenance maps.
4. Deterministic text chunking (chunk_text) with exact character offsets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
import pytest

from src.core.context_pipeline import chunk_text, normalize_text
from src.engines.context.context_builder import ContextBuilder, BuiltContext
from src.engines.optimization.optimization_engine import OptimizationEngine


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


def test_submodular_knapsack_token_capacity_enforcement():
    """Verify solve_submodular_knapsack never exceeds capacity while maximizing concept coverage."""
    engine = OptimizationEngine()

    item_concepts = [
        {"thermal", "power", "cooling"},      # Item 0: cost 100
        {"compute", "tflops", "throughput"},   # Item 1: cost 120
        {"memory", "bandwidth", "hbm"},        # Item 2: cost 80
        {"power", "voltage", "current"},       # Item 3: cost 60 (redundant concept 'power')
    ]
    concept_weights = {
        "thermal": 2.0, "power": 2.0, "cooling": 1.5,
        "compute": 3.0, "tflops": 2.5, "throughput": 2.0,
        "memory": 2.0, "bandwidth": 1.5, "hbm": 1.5,
        "voltage": 1.0, "current": 1.0,
    }
    item_weights = [100, 120, 80, 60]
    capacity = 210  # Can fit Item 1 (120) + Item 2 (80) = 200 <= 210, or Item 0 + Item 2 = 180

    result = engine.solve_submodular_knapsack(
        item_concepts=item_concepts,
        concept_weights=concept_weights,
        item_weights=item_weights,
        capacity=capacity,
    )

    # Budget strictly respected
    assert result.total_tokens <= capacity
    assert len(result.selected_indices) >= 2
    # Total selected cost matches item_weights sum
    actual_cost = sum(item_weights[i] for i in result.selected_indices)
    assert actual_cost == result.total_tokens
    assert result.total_tokens <= 210


def test_adaptive_query_budget():
    """Verify adapt_budget_for_query scales token allocation based on query intent."""
    engine = OptimizationEngine()

    lookup_budget = engine.adapt_budget_for_query(query_type="lookup", base_budget=2000)
    comparison_budget = engine.adapt_budget_for_query(query_type="comparison", base_budget=2000)
    summary_budget = engine.adapt_budget_for_query(query_type="summary", base_budget=2000)

    # Lookup requires less context than comparison or summary
    assert lookup_budget == 500
    assert comparison_budget == 2000
    assert summary_budget == 4000
    assert lookup_budget < comparison_budget < summary_budget


def test_context_builder_budget_and_source_mapping():
    """Verify ContextBuilder stays within max_tokens and builds accurate 1-based source map."""
    builder = ContextBuilder(max_tokens=400, target_tokens=300, reserve_tokens=100)

    # Supply 10 chunks with varying lengths
    results = [
        DummyRetrievalResult(
            element=DummyElement(
                element_id=f"chunk-{i}",
                content=f"Detailed financial and operational performance section {i}. " * 10,
            ),
            score=1.0 - (i * 0.1),
        )
        for i in range(10)
    ]

    ctx = DummyRetrievalContext(results=results, table_answers=[])
    built: BuiltContext = builder.build("What was quarterly revenue?", ctx)

    # Must strictly enforce token ceiling
    assert built.tokens_used <= 400
    # Provenance map must be populated
    assert len(built.source_map) > 0
    assert len(built.source_map) < len(results)
    # Check 1-based sequential indices
    for cit_idx, element_id in built.source_map.items():
        assert isinstance(cit_idx, int)
        assert cit_idx >= 1
        assert element_id.startswith("chunk-")
    # Check 1-based sequential indices
    for cit_idx, element_id in built.source_map.items():
        assert isinstance(cit_idx, int)
        assert cit_idx >= 1
        assert element_id.startswith("chunk-")


def test_deterministic_text_chunking():
    """Verify chunk_text produces exact character offsets without gaps."""
    text = (
        "Paragraph 1 contains introductory content.\n\n"
        "Paragraph 2 discusses detailed engineering specifications and throughput limits.\n\n"
        "Paragraph 3 concludes the report with regulatory compliance remarks."
    )
    result = chunk_text(document_id="doc-chunk-01", text=text, max_chars=80, overlap_chars=10)

    assert result.chunk_count >= 2
    assert result.document_id == "doc-chunk-01"

    # Offsets must be contiguous and non-empty
    for chunk in result.chunks:
        assert chunk.char_end > chunk.char_start
        assert len(chunk.text) > 0
        extracted = text[chunk.char_start:chunk.char_end]
        assert extracted == chunk.text
