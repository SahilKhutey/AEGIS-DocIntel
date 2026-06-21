"""
AEGIS-MDIE — Context Builder
==============================
Token-budget-aware mathematical context assembly.

Optimization:
    max Σ_i R(q, e_i) · w(e_i)
    s.t. Σ_i tokens(e_i) ≤ B

This is a greedy 0/1 knapsack by R/tokens ratio.
Includes: unique elements + recurrence representatives + table reprs + equations.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from MDIE.engines.geometry.element import ElementType, GeometricElement
from MDIE.engines.hybrid_retriever.hybrid_retriever import RetrievalContext, RetrievalResult
from MDIE.engines.matrix.matrix_engine import MatrixEngine

log = logging.getLogger("mdie.context")

SYSTEM_PROMPT = """You are AEGIS-MDIE, an advanced mathematical document intelligence assistant.

You reason over documents represented as mathematical objects:
  - Geometric elements with spatial coordinates
  - Tables as matrices with exact algebraic values
  - Structural graphs capturing document hierarchy
  - Frequency-weighted importance scores

Rules:
1. Answer ONLY from the provided mathematical context. Never hallucinate.
2. For table questions: use the pre-computed algebraic values provided — DO NOT re-derive.
3. Cite all claims with [Source-N] referencing the source number in the context.
4. For numerical answers: state exact values from the matrix representation.
5. Respect element importance weights — higher-weight elements are more reliable.
6. If no context matches: state "Not found in the provided document."
7. End with **Confidence: HIGH / MEDIUM / LOW** based on evidence quality.

Mathematical context format:
  [Source-N | type | page P | weight W]: content
  [TABLE-N | page P]: matrix representation with pre-computed statistics
"""


@dataclass
class BuiltContext:
    """Assembled LLM-ready context."""
    messages:       list[dict]
    context_text:   str
    source_map:     dict[int, str]     # source_num → element_id
    token_budget:   int
    tokens_used:    int
    elements_used:  int
    tables_used:    int
    table_answers:  list[str]


class ContextBuilder:
    """
    Builds token-budget-aware LLM context from retrieval results.

    Strategy (greedy knapsack by score/token ratio):
        1. Sort elements by R(q,e) · w(e) / tokens(e)
        2. Include greedily until budget exhausted
        3. Atomic blocks (tables, equations) get priority inclusion
        4. Direct table algebraic answers prepended (no token cost)
        5. Hierarchical coordinates guide source labeling
    """

    def __init__(
        self,
        matrix_engine: Optional[MatrixEngine] = None,
        max_tokens: int = 8000,
        reserve_output: int = 2000,
    ):
        self.matrix     = matrix_engine or MatrixEngine()
        self.max_tokens = max_tokens
        self.reserve    = reserve_output

    @property
    def context_budget(self) -> int:
        return self.max_tokens - self.reserve - 400   # 400 for system/query overhead

    # ──────────────────────────────────────────────────────────────
    # Main build
    # ──────────────────────────────────────────────────────────────

    def build(
        self,
        query: str,
        retrieval: RetrievalContext,
        history: Optional[list[dict]] = None,
    ) -> BuiltContext:
        """
        Assemble full LLM message list from retrieval context.
        """
        budget = self.context_budget
        results = retrieval.results

        # Greedy knapsack selection
        selected, tokens_used = self._knapsack(results, budget)

        # Build context text
        ctx_parts:  list[str] = []
        source_map: dict[int, str] = {}

        # Prepend direct table algebraic answers (free — no token cost)
        if retrieval.table_answers:
            ctx_parts.append("=== Direct Algebraic Results ===")
            for ans in retrieval.table_answers:
                ctx_parts.append(ans)
            ctx_parts.append("")

        tables_used = 0
        for i, result in enumerate(selected):
            src_num = i + 1
            e       = result.element
            source_map[src_num] = e.element_id

            label = (
                f"[Source-{src_num} | {e.type.value} | "
                f"page {e.page} | weight {e.importance_weight:.2f}"
                f"{' | section: ' + e.section if e.section else ''}]"
            )

            if e.type == ElementType.TABLE:
                table = self.matrix.get(e.element_id)
                content = table.to_llm_repr() if table else e.content
                tables_used += 1
            elif e.type == ElementType.EQUATION:
                content = f"Equation: {e.content}"
            elif e.type == ElementType.HEADING:
                content = f"[HEADING] {e.content}"
            else:
                content = e.content

            ctx_parts.append(f"{label}\n{content}")

        # Geometric summary note
        if selected:
            page_range = sorted({r.element.page for r in selected})
            ctx_parts.append(
                f"\n[Document context spans pages: {page_range[0]}–{page_range[-1]}]"
            )

        context_text = "\n\n".join(ctx_parts)

        # Weight description (transparency)
        w = retrieval.weights_used
        weight_note = (
            f"[Retrieval weights: Semantic={w.get('alpha',0):.2f} "
            f"Geometric={w.get('beta',0):.2f} "
            f"Frequency={w.get('gamma',0):.2f} "
            f"Matrix={w.get('delta',0):.2f}]"
        )

        # Assemble messages
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-6:])   # last 3 turns

        user_content = (
            f"Question: {query}\n\n"
            f"Mathematical Document Context:\n"
            f"{'='*60}\n"
            f"{context_text}\n"
            f"{'='*60}\n"
            f"{weight_note}\n\n"
            f"Answer based strictly on the context above."
        )
        messages.append({"role": "user", "content": user_content})

        log.info(
            "Context built: %d elements | %d tables | %d tokens (budget: %d)",
            len(selected), tables_used, tokens_used, budget,
        )

        return BuiltContext(
            messages      = messages,
            context_text  = context_text,
            source_map    = source_map,
            token_budget  = budget,
            tokens_used   = tokens_used,
            elements_used = len(selected),
            tables_used   = tables_used,
            table_answers = retrieval.table_answers,
        )

    # ──────────────────────────────────────────────────────────────
    # Greedy knapsack (0/1 by R·w / tokens)
    # ──────────────────────────────────────────────────────────────

    def _knapsack(
        self,
        results: list[RetrievalResult],
        budget: int,
    ) -> tuple[list[RetrievalResult], int]:
        """
        Greedy selection:
            value = R(q,e) · importance_weight(e)
            cost  = tokens(e)
            ratio = value / cost
        Atomic blocks (TABLE, EQUATION) get 1.5× ratio bonus.
        """
        def priority(r: RetrievalResult) -> float:
            cost = max(1, r.element.token_count)
            val  = r.score * r.element.importance_weight
            bonus = 1.5 if r.element.type in (ElementType.TABLE, ElementType.EQUATION) else 1.0
            return val * bonus / cost

        sorted_results = sorted(results, key=priority, reverse=True)
        selected: list[RetrievalResult] = []
        tokens_used = 0

        for r in sorted_results:
            cost = r.element.token_count
            if tokens_used + cost <= budget:
                selected.append(r)
                tokens_used += cost

        # Re-sort selected by page + reading order (for coherent context)
        selected.sort(key=lambda r: (r.element.page,
                                     r.element.bbox.y0 if r.element.bbox else 0))
        return selected, tokens_used

    # ──────────────────────────────────────────────────────────────
    # Token accounting
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def count_tokens(text: str) -> int:
        return max(1, int(len(text.split()) * 1.33))

    def utilization(self, built: BuiltContext) -> float:
        return built.tokens_used / max(1, built.token_budget)
