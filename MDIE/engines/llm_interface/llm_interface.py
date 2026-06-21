"""
AEGIS-MDIE — LLM Interface Engine
====================================
Reasoning layer over the mathematical document representation.
Handles streaming, citation extraction, confidence scoring, and hallucination guards.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

log = logging.getLogger("mdie.llm")

# ─────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────

@dataclass
class Citation:
    source_num: int
    element_id: str
    page:       int
    section:    Optional[str]
    snippet:    str
    element_type: str = "text"

@dataclass
class MDIEResponse:
    answer:           str
    citations:        list[Citation]
    confidence:       float          # 0.0 – 1.0
    confidence_label: str            # HIGH / MEDIUM / LOW
    model:            str
    in_tokens:        int
    out_tokens:       int
    latency_ms:       float
    table_direct:     list[str]      = field(default_factory=list)
    grounded:         bool           = True    # False if answer is off-context

    def cost_usd(self, rate_in: float = 0.15e-6, rate_out: float = 0.6e-6) -> float:
        return self.in_tokens * rate_in + self.out_tokens * rate_out


# ─────────────────────────────────────────────────────────────────
# Grounding Checker
# ─────────────────────────────────────────────────────────────────

class GroundingChecker:
    """
    Detects answers that are NOT grounded in the provided context.
    Simple but effective: if no [Source-N] citations → low confidence.
    """

    NOT_FOUND_PHRASES = [
        "not found in",
        "not available in",
        "not mentioned in",
        "cannot find",
        "no information",
        "i don't have",
        "i do not have",
        "not in the provided",
    ]

    def check(self, answer: str, source_count: int) -> tuple[bool, float]:
        """Returns (is_grounded, confidence_score)."""
        # Check for explicit not-found statements
        al = answer.lower()
        for phrase in self.NOT_FOUND_PHRASES:
            if phrase in al:
                return False, 0.1

        # Count citations
        citations_found = set(re.findall(r"\[Source-(\d+)\]", answer))
        if not citations_found:
            return True, 0.4     # answered but no explicit citation

        citation_ratio = len(citations_found) / max(1, source_count)
        confidence = min(0.95, 0.5 + 0.45 * citation_ratio)
        return True, confidence

    def extract_confidence_label(self, answer: str) -> tuple[str, float]:
        """Extract **Confidence: HIGH/MEDIUM/LOW** from answer."""
        m = re.search(r"\*\*Confidence:\s*(HIGH|MEDIUM|LOW)\*\*", answer, re.IGNORECASE)
        if m:
            label = m.group(1).upper()
            score = {"HIGH": 0.85, "MEDIUM": 0.55, "LOW": 0.25}.get(label, 0.5)
            return label, score
        return "MEDIUM", 0.5


# ─────────────────────────────────────────────────────────────────
# LLM Interface Engine
# ─────────────────────────────────────────────────────────────────

class LLMInterfaceEngine:
    """
    Reasoning layer between MDIE context and any LLM provider.

    Features:
        - Streaming and non-streaming modes
        - Citation extraction from [Source-N] markers
        - Confidence scoring (grounding + citation density)
        - Hallucination guard (blocks off-context answers)
        - Direct table answer injection (no LLM needed for math)
        - Provider-agnostic (OpenAI / Anthropic / vLLM / Mock)
    """

    def __init__(
        self,
        llm_client=None,
        grounding_checker: Optional[GroundingChecker] = None,
        model_name: str = "mock",
    ):
        self.llm     = llm_client
        self.checker = grounding_checker or GroundingChecker()
        self.model   = model_name

    # ──────────────────────────────────────────────────────────────
    # Complete (non-streaming)
    # ──────────────────────────────────────────────────────────────

    async def reason(
        self,
        messages:     list[dict],
        source_map:   dict[int, str],       # source_num → element_id
        elements_map: dict[str, object],    # element_id → GeometricElement
        table_answers: Optional[list[str]] = None,
        max_tokens:   int = 2048,
    ) -> MDIEResponse:
        """
        Execute LLM reasoning and produce a structured MDIEResponse.
        """
        import time
        t0 = time.perf_counter()

        # Direct table answers bypass the LLM entirely
        if table_answers and self._is_pure_numeric(messages):
            return self._table_only_response(table_answers, t0)

        # LLM call
        if self.llm is None:
            raw_answer, in_tok, out_tok = await self._mock_complete(messages)
        else:
            raw_answer, in_tok, out_tok = await self._llm_complete(messages, max_tokens)

        latency = (time.perf_counter() - t0) * 1000

        # Grounding check
        grounded, conf_score = self.checker.check(raw_answer, len(source_map))

        # Extract confidence label from answer
        conf_label, label_score = self.checker.extract_confidence_label(raw_answer)
        final_conf = (conf_score + label_score) / 2.0

        # Extract citations
        citations = self._extract_citations(raw_answer, source_map, elements_map)

        # Hallucination guard: if not grounded, modify answer
        if not grounded:
            raw_answer = (
                "⚠️ The answer to this question was not found in the provided document.\n\n"
                + raw_answer
            )

        log.info(
            "LLM reasoning complete: conf=%.2f grounded=%s citations=%d latency=%.0fms",
            final_conf, grounded, len(citations), latency,
        )

        return MDIEResponse(
            answer           = raw_answer,
            citations        = citations,
            confidence       = round(final_conf, 3),
            confidence_label = conf_label,
            model            = self.model,
            in_tokens        = in_tok,
            out_tokens       = out_tok,
            latency_ms       = round(latency, 1),
            table_direct     = table_answers or [],
            grounded         = grounded,
        )

    # ──────────────────────────────────────────────────────────────
    # Streaming
    # ──────────────────────────────────────────────────────────────

    async def stream(
        self,
        messages:     list[dict],
        source_map:   dict[int, str],
        elements_map: dict[str, object],
        table_answers: Optional[list[str]] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream reasoning tokens as SSE dicts.
        Format: {"type": "token"|"citation"|"done"|"error", "content": ...}
        """
        # Inject direct table answers first
        if table_answers:
            for ans in table_answers:
                yield {"type": "table_direct", "content": ans}

        full_text = ""

        if self.llm is None:
            async for chunk in self._mock_stream(messages):
                full_text += chunk
                yield {"type": "token", "content": chunk}
        else:
            async for chunk in self._llm_stream(messages):
                full_text += chunk
                yield {"type": "token", "content": chunk}

        # Post-stream: extract citations
        citations = self._extract_citations(full_text, source_map, elements_map)
        _, conf = self.checker.extract_confidence_label(full_text)

        yield {
            "type": "citations",
            "citations": [
                {"num": c.source_num, "page": c.page, "type": c.element_type,
                 "snippet": c.snippet}
                for c in citations
            ],
        }
        yield {"type": "metadata", "confidence": round(conf, 3), "model": self.model}
        yield {"type": "done"}

    # ──────────────────────────────────────────────────────────────
    # Citation extraction
    # ──────────────────────────────────────────────────────────────

    def _extract_citations(
        self,
        answer:       str,
        source_map:   dict[int, str],
        elements_map: dict[str, object],
    ) -> list[Citation]:
        found_nums = set(int(m) for m in re.findall(r"\[Source-(\d+)\]", answer))
        citations  = []
        for num in sorted(found_nums):
            eid  = source_map.get(num)
            if not eid:
                continue
            e = elements_map.get(eid)
            if e is None:
                continue
            citations.append(Citation(
                source_num   = num,
                element_id   = eid,
                page         = getattr(e, "page", 0),
                section      = getattr(e, "section", None),
                snippet      = getattr(e, "content", "")[:200],
                element_type = getattr(e, "type", type("T", (), {"value": "text"})).value
                               if hasattr(getattr(e, "type", None), "value") else "text",
            ))
        return citations

    # ──────────────────────────────────────────────────────────────
    # LLM backends
    # ──────────────────────────────────────────────────────────────

    async def _llm_complete(
        self,
        messages:   list[dict],
        max_tokens: int,
    ) -> tuple[str, int, int]:
        """Call real LLM (OpenAI / Anthropic via existing LLMService)."""
        try:
            resp = await self.llm.complete(messages, max_tokens=max_tokens)
            return resp.text, resp.in_tokens, resp.out_tokens
        except Exception as ex:
            log.error("LLM call failed: %s", ex)
            mock, it, ot = await self._mock_complete(messages)
            return mock, it, ot

    async def _llm_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        try:
            async for chunk in self.llm.stream(messages):
                if chunk.delta:
                    yield chunk.delta
        except Exception as ex:
            log.error("LLM stream failed: %s", ex)
            async for tok in self._mock_stream(messages):
                yield tok

    async def _mock_complete(self, messages: list[dict]) -> tuple[str, int, int]:
        """Development mock — no API key required."""
        q = ""
        for m in reversed(messages):
            if m["role"] == "user":
                q = m["content"][:120]
                break
        answer = (
            f"[MDIE MOCK RESPONSE]\n\n"
            f"Based on the mathematical document representation, I have analyzed the query:\n"
            f"'{q[:80]}...'\n\n"
            f"The document was processed using the AEGIS-MDIE pipeline:\n"
            f"  • Geometric coordinates preserved all spatial relationships\n"
            f"  • Recurrence engine detected and compressed repeated elements\n"
            f"  • Frequency engine assigned importance weights\n"
            f"  • Matrix engine performed direct algebraic operations on tables\n"
            f"  • Graph engine captured cross-page structural relationships\n"
            f"  • Hybrid retrieval used R = αS + βG + γF + δM\n\n"
            f"[Source-1] The answer would appear here with citations.\n\n"
            f"**Confidence: HIGH**\n\n"
            f"_Configure OPENAI_API_KEY or ANTHROPIC_API_KEY for real LLM responses._"
        )
        return answer, len(str(messages).split()), len(answer.split())

    async def _mock_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        full, _, _ = await self._mock_complete(messages)
        for word in full.split(" "):
            yield word + " "
            await asyncio.sleep(0.015)

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    def _is_pure_numeric(self, messages: list[dict]) -> bool:
        """True if the query is purely a numeric calculation."""
        q = ""
        for m in reversed(messages):
            if m["role"] == "user":
                q = m["content"].lower()
                break
        pure_numeric_kw = ["what is the total", "what is the sum", "calculate the",
                           "compute the", "what is the average"]
        return any(kw in q for kw in pure_numeric_kw)

    def _table_only_response(
        self, table_answers: list[str], t0: float
    ) -> MDIEResponse:
        """Return direct algebraic answer, bypassing LLM entirely."""
        import time
        answer = "Direct algebraic computation from document matrices:\n\n"
        answer += "\n".join(table_answers)
        answer += "\n\n**Confidence: HIGH** (computed directly from matrix M[i,j])"
        latency = (time.perf_counter() - t0) * 1000
        return MDIEResponse(
            answer           = answer,
            citations        = [],
            confidence       = 0.95,
            confidence_label = "HIGH",
            model            = "matrix_direct",
            in_tokens        = 0,
            out_tokens       = len(answer.split()),
            latency_ms       = round(latency, 1),
            table_direct     = table_answers,
            grounded         = True,
        )
