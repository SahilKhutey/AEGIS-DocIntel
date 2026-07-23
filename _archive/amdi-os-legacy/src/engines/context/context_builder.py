"""
context_builder.py
==================
AEGIS-AMDI-OS — LLM Context Builder

Transforms a :class:`~src.engines.retrieval.amdi_retriever.RetrievalContext`
into a structured list of OpenAI-style chat messages ready for LLM inference.

Strategy
--------
1. A **system prompt** establishes the AMDI assistant persona and instructs
   the model to cite sources as ``[1]``, ``[2]``, …
2. Tables are **always prioritised first** — they are inserted verbatim as
   Markdown tables before any paragraph content.
3. Remaining token budget is filled with semantic paragraph elements sorted
   in descending score order (greedy knapsack).
4. The user message appends the assembled context block, followed by the
   question.

Token counting uses *tiktoken* when available (fast, accurate) and falls
back to a word-count heuristic otherwise.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional tiktoken import
# ---------------------------------------------------------------------------
try:
    import tiktoken  # type: ignore

    _TIKTOKEN_AVAILABLE = True
    _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
    logger.info("tiktoken loaded — using cl100k_base for token counting.")
except Exception:  # pylint: disable=broad-except
    tiktoken = None  # type: ignore
    _TIKTOKEN_AVAILABLE = False
    _TIKTOKEN_ENC = None
    logger.warning(
        "tiktoken not available — token counts are estimated via word-count heuristic. "
        "Install with: pip install tiktoken"
    )

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are AMDI (Adaptive Multi-modal Document Intelligence), an expert \
document analysis assistant. You answer questions strictly based on the \
provided document context.

Citation format:
- Every factual claim MUST be followed by its source citation in square \
brackets, e.g. [1], [2].
- If multiple sources support a claim, cite them all: [1][3].
- Never fabricate information not present in the context.
- If the context does not contain sufficient information to answer, \
state: "The provided documents do not contain enough information to \
answer this question."

Response format:
- Write in clear, professional prose.
- For numerical data or comparisons, prefer structured lists or tables.
- Conclude with a brief summary if the answer is multi-part.\
"""

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class BuiltContext:
    """
    The output of :meth:`ContextBuilder.build`.

    Attributes
    ----------
    messages:
        List of ``{"role": str, "content": str}`` dicts suitable for
        passing directly to an OpenAI-compatible chat API.
    tokens_used:
        Estimated total tokens consumed by all messages combined.
    source_map:
        Mapping of citation number (int) → element identifier (str).
        E.g. ``{1: "doc1::chunk::7", 2: "doc1::table::2"}``.
    table_count:
        Number of table elements included in the context.
    element_count:
        Total number of document elements included (tables + paragraphs).
    """

    messages: List[Dict[str, str]] = field(default_factory=list)
    tokens_used: int = 0
    source_map: Dict[int, str] = field(default_factory=dict)
    table_count: int = 0
    element_count: int = 0


# ---------------------------------------------------------------------------
# ContextBuilder
# ---------------------------------------------------------------------------


class ContextBuilder:
    """
    Assembles an LLM-ready chat context from retrieval results.

    Parameters
    ----------
    max_tokens:
        Hard upper bound on total tokens across all messages.
    target_tokens:
        Soft target for the context block inside the user message.  The
        builder fills the knapsack up to ``max_tokens - reserve_tokens``.
    reserve_tokens:
        Tokens reserved for the model's *output*.  The builder stops
        adding content once the consumed budget approaches
        ``max_tokens - reserve_tokens``.

    Examples
    --------
    >>> builder = ContextBuilder(max_tokens=4096, target_tokens=1500, reserve_tokens=1000)
    >>> built = builder.build(question, retrieval_ctx, history)
    >>> response = await llm.chat(built.messages)
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        target_tokens: int = 1500,
        reserve_tokens: int = 1000,
    ) -> None:
        self._max_tokens = max_tokens
        self._target_tokens = target_tokens
        self._reserve_tokens = reserve_tokens
        # Effective token budget for document context
        self._context_budget = max_tokens - reserve_tokens
        logger.info(
            "ContextBuilder initialised — max_tokens=%d target=%d reserve=%d budget=%d",
            max_tokens,
            target_tokens,
            reserve_tokens,
            self._context_budget,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        question: str,
        retrieval_ctx: Any,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> BuiltContext:
        """
        Build an LLM-ready message list from retrieval results.

        Parameters
        ----------
        question:
            The user's original question.
        retrieval_ctx:
            A :class:`~src.engines.retrieval.amdi_retriever.RetrievalContext`
            (or any object with ``results: list[RetrievalResult]`` and
            ``table_answers: list[str]`` attributes).
        history:
            Optional prior conversation turns as a list of
            ``{"role": "user"|"assistant", "content": str}`` dicts.
            Injected between the system prompt and the current user turn.

        Returns
        -------
        BuiltContext
            Fully assembled context ready for LLM inference.
        """
        messages: List[Dict[str, str]] = []
        source_map: Dict[int, str] = {}
        source_counter = 0
        tokens_used = 0
        table_count = 0

        # ---- 1. System prompt ----------------------------------------
        sys_tokens = self._count_tokens(_SYSTEM_PROMPT)
        messages.append({"role": "system", "content": _SYSTEM_PROMPT})
        tokens_used += sys_tokens

        # ---- 2. Optional conversation history ------------------------
        if history:
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                turn_tokens = self._count_tokens(content)
                if tokens_used + turn_tokens < self._context_budget:
                    messages.append({"role": role, "content": content})
                    tokens_used += turn_tokens

        # ---- 3. Separate results into tables and paragraphs ----------
        results = getattr(retrieval_ctx, "results", []) or []
        table_answers = getattr(retrieval_ctx, "table_answers", []) or []

        table_results = [
            r for r in results
            if _is_table_element(r)
        ]
        para_results = [
            r for r in results
            if not _is_table_element(r)
        ]

        # Sort paragraphs by fused score descending
        para_results.sort(key=lambda r: getattr(r, "score", 0.0), reverse=True)

        # ---- 4. Build context block ----------------------------------
        context_parts: List[str] = []

        # 4a. Direct table answers from matrix engine
        if table_answers:
            context_parts.append("**Direct Table Answers:**")
            for ta in table_answers:
                context_parts.append(f"- {ta}")
            context_parts.append("")

        # 4b. Tables (always included first, up to budget)
        for result in table_results:
            source_counter += 1
            elem = getattr(result, "element", result)
            eid = getattr(elem, "element_id", str(source_counter))
            formatted = self._format_element(elem, source_counter)
            block_tokens = self._count_tokens(formatted)

            if tokens_used + block_tokens > self._context_budget:
                logger.debug(
                    "Budget exceeded adding table [%d]; skipping.", source_counter
                )
                source_counter -= 1
                break

            context_parts.append(formatted)
            source_map[source_counter] = eid
            tokens_used += block_tokens
            table_count += 1

        # 4c. Semantic paragraphs — greedy knapsack by score
        for result in para_results:
            source_counter += 1
            elem = getattr(result, "element", result)
            eid = getattr(elem, "element_id", str(source_counter))
            formatted = self._format_element(elem, source_counter)
            block_tokens = self._count_tokens(formatted)

            if tokens_used + block_tokens > self._context_budget:
                logger.debug(
                    "Budget exhausted at element [%d] (%.1f tokens used / %d budget).",
                    source_counter,
                    tokens_used,
                    self._context_budget,
                )
                source_counter -= 1
                break

            context_parts.append(formatted)
            source_map[source_counter] = eid
            tokens_used += block_tokens

        element_count = table_count + (source_counter - table_count)

        # ---- 5. Assemble user message --------------------------------
        context_block = "\n".join(context_parts).strip()
        if context_block:
            user_content = (
                f"**Document Context:**\n\n{context_block}\n\n"
                f"---\n\n**Question:** {question}"
            )
        else:
            user_content = f"**Question:** {question}"

        user_tokens = self._count_tokens(user_content)
        messages.append({"role": "user", "content": user_content})
        tokens_used += user_tokens

        logger.info(
            "ContextBuilder.build() — elements=%d tables=%d sources=%d tokens=%d",
            element_count,
            table_count,
            source_counter,
            tokens_used,
        )

        return BuiltContext(
            messages=messages,
            tokens_used=tokens_used,
            source_map=source_map,
            table_count=table_count,
            element_count=element_count,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_tokens(text: str) -> int:
        """
        Estimate the number of tokens in *text*.

        Uses *tiktoken* (cl100k_base) when available; otherwise applies
        the heuristic ``len(text.split()) * 1.33`` (rounded up).

        Parameters
        ----------
        text:
            Any string to estimate.

        Returns
        -------
        int
            Estimated token count.
        """
        if not text:
            return 0
        if _TIKTOKEN_AVAILABLE and _TIKTOKEN_ENC is not None:
            try:
                return len(_TIKTOKEN_ENC.encode(text))
            except Exception:  # pylint: disable=broad-except
                pass
        # Heuristic fallback
        return max(1, int(len(text.split()) * 1.33))

    @staticmethod
    def _format_element(element: Any, source_num: int) -> str:
        """
        Format a document element as a numbered citation block.

        Output format::

            [1] TABLE (p.3):
            | Col A | Col B |
            |-------|-------|
            | 1     | 2     |

        Parameters
        ----------
        element:
            A :class:`~src.engines.geometry.element.GeometricElement` or
            any object exposing ``element_type``, ``page_number``, and
            ``content`` attributes.
        source_num:
            The 1-based citation number to assign.

        Returns
        -------
        str
            Formatted text block ready for inclusion in the context.
        """
        elem_type = str(
            getattr(element, "element_type", getattr(element, "type", "ELEMENT"))
        ).upper()
        page = getattr(element, "page_number", getattr(element, "page", "?"))
        content = str(getattr(element, "content", getattr(element, "text", "")))

        header = f"[{source_num}] {elem_type} (p.{page}):"
        return f"{header}\n{content}"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _is_table_element(result: Any) -> bool:
    """
    Return ``True`` if the retrieval result represents a table element.

    Checks both the element's ``element_type`` attribute and common
    synonyms (``TABLE``, ``MATRIX``, ``GRID``).

    Parameters
    ----------
    result:
        A :class:`~src.engines.retrieval.amdi_retriever.RetrievalResult`.

    Returns
    -------
    bool
    """
    elem = getattr(result, "element", result)
    elem_type = str(
        getattr(elem, "element_type", getattr(elem, "type", ""))
    ).upper()
    return elem_type in {"TABLE", "MATRIX", "GRID"}
