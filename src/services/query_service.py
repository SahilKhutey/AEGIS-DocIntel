"""
AEGIS-DocIntel — Query Service
================================
Orchestrates the full RAG pipeline for a user query:
Semantic Cache → Query Transform → Hybrid Retrieval → Rerank → LLM → Response
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import numpy as np
import structlog

from src.config import settings
from src.llm_service.llm_client import LLMService, LLMStreamChunk, calc_cost
from src.observability.metrics import CACHE_HITS, LLM_TOKENS

log = structlog.get_logger("aegis.query_service")

SYSTEM_PROMPT = """You are AEGIS, an expert document intelligence assistant.

Rules:
1. Answer ONLY from the provided context. Never fabricate information.
2. Cite all claims using [Source-N] notation referencing the provided sources.
3. If the answer is not in the context, state: "This information is not available in the provided documents."
4. For tables and numerical data, be precise.
5. Structure complex answers with headings and bullet points.
6. Always end with a confidence indicator: **Confidence: HIGH / MEDIUM / LOW**

Source citation format: [Source-N] where N is the source number shown in the context."""


@dataclass
class Citation:
    source_num: int
    chunk_id: str
    doc_id: str
    page: int
    section: str
    snippet: str


@dataclass
class QueryResult:
    answer: str
    citations: list[Citation]
    confidence: float
    chunks: list
    tokens_used: dict[str, int]
    retrieval_latency_ms: float
    model: str
    cached: bool = False


class QueryService:
    """
    Full RAG query orchestration service.
    """

    def __init__(
        self,
        rag_engine,
        memory_engine,
        llm_service: LLMService,
        embedding_model,
        token_budget_enforcer=None,
    ):
        self.rag = rag_engine
        self.memory = memory_engine
        self.llm = llm_service
        self.embedder = embedding_model
        self.budget = token_budget_enforcer

    async def query(
        self,
        question: str,
        tenant_id: str,
        doc_ids: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> QueryResult:
        """Execute full RAG pipeline and return QueryResult."""
        t_start = time.perf_counter()

        # 1. Embed the question
        loop = asyncio.get_running_loop()
        q_embedding = await loop.run_in_executor(
            None, lambda: self.embedder.encode([question])[0]
        )

        # 2. Semantic cache lookup
        if self.memory:
            cached = await self.memory.query_cache(
                question_embedding=q_embedding,
                tenant_id=tenant_id,
                doc_ids=doc_ids,
            )
            if cached:
                CACHE_HITS.labels(cache_type="semantic").inc()
                log.info("Semantic cache hit", tenant=tenant_id)
                return QueryResult(
                    answer=cached["answer"],
                    citations=[Citation(**c) for c in cached.get("citations", [])],
                    confidence=cached.get("confidence", 0.8),
                    chunks=[],
                    tokens_used={"input": 0, "output": 0, "total": 0},
                    retrieval_latency_ms=0.0,
                    model="semantic_cache",
                    cached=True,
                )

        # 3. Retrieve conversation history
        history = []
        if self.memory and session_id:
            messages = await self.memory.get_history(session_id)
            history = [{"role": m.role, "content": m.content} for m in messages[-8:]]

        # 4. RAG pipeline
        rag_result = await self.rag.retrieve_and_build(
            query=question,
            tenant_id=tenant_id,
            doc_ids=doc_ids,
            history=history,
            top_k=top_k,
        )

        # 5. LLM inference
        messages = self.rag.context_builder.build_prompt(
            context=rag_result.context,
            query=question,
            system_prompt=SYSTEM_PROMPT,
            history=history,
            included_chunks=rag_result.chunks,
        )

        llm_response = await self.llm.complete(messages)

        # 6. Extract citations
        import re
        source_nums = set(
            int(m) for m in re.findall(r"\[Source-(\d+)\]", llm_response.text)
        )
        chunk_map = {i + 1: c for i, c in enumerate(rag_result.chunks)}
        citations = []
        for num in sorted(source_nums):
            chunk = chunk_map.get(num)
            if chunk:
                citations.append(Citation(
                    source_num=num,
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    page=chunk.page,
                    section=chunk.section,
                    snippet=chunk.text[:200],
                ))

        tokens_used = {
            "input": llm_response.in_tokens,
            "output": llm_response.out_tokens,
            "total": llm_response.in_tokens + llm_response.out_tokens,
        }

        # 7. Track token usage
        LLM_TOKENS.labels(tenant_id=tenant_id, model=self.llm.model_name, direction="input").inc(llm_response.in_tokens)
        LLM_TOKENS.labels(tenant_id=tenant_id, model=self.llm.model_name, direction="output").inc(llm_response.out_tokens)

        result = QueryResult(
            answer=llm_response.text,
            citations=citations,
            confidence=rag_result.confidence,
            chunks=rag_result.chunks,
            tokens_used=tokens_used,
            retrieval_latency_ms=rag_result.retrieval_latency_ms,
            model=self.llm.model_name,
        )

        # 8. Store in caches + episodic memory
        if self.memory:
            await self.memory.cache_response(
                question=question,
                embedding=q_embedding,
                response={
                    "answer": result.answer,
                    "citations": [
                        {"source_num": c.source_num, "chunk_id": c.chunk_id,
                         "doc_id": c.doc_id, "page": c.page, "section": c.section,
                         "snippet": c.snippet}
                        for c in citations
                    ],
                    "confidence": result.confidence,
                },
                tenant_id=tenant_id,
                doc_ids=doc_ids or [],
            )

        return result

    async def stream_query(
        self,
        question: str,
        tenant_id: str,
        doc_ids: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream query response as SSE-compatible dicts."""
        # Run retrieval (non-streaming)
        loop = asyncio.get_running_loop()
        q_embedding = await loop.run_in_executor(
            None, lambda: self.embedder.encode([question])[0]
        )

        # Semantic cache check
        if self.memory:
            cached = await self.memory.query_cache(q_embedding, tenant_id, doc_ids)
            if cached:
                yield {"type": "token", "content": cached["answer"]}
                yield {"type": "citations", "citations": cached.get("citations", [])}
                yield {"type": "done"}
                return

        rag_result = await self.rag.retrieve_and_build(
            query=question,
            tenant_id=tenant_id,
            doc_ids=doc_ids,
            top_k=top_k,
        )

        messages = self.rag.context_builder.build_prompt(
            context=rag_result.context,
            query=question,
            system_prompt=SYSTEM_PROMPT,
            history=[],
            included_chunks=rag_result.chunks,
        )

        # Stream LLM tokens
        full_text = ""
        async for chunk in self.llm.stream(messages):
            if chunk.delta:
                full_text += chunk.delta
                yield {"type": "token", "content": chunk.delta}

        # Extract citations after streaming completes
        import re
        source_nums = set(int(m) for m in re.findall(r"\[Source-(\d+)\]", full_text))
        chunk_map = {i + 1: c for i, c in enumerate(rag_result.chunks)}
        citations = []
        for num in sorted(source_nums):
            chunk = chunk_map.get(num)
            if chunk:
                citations.append({
                    "source_num": num,
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "page": chunk.page,
                    "section": chunk.section,
                    "snippet": chunk.text[:200],
                })

        yield {"type": "citations", "citations": citations}
        yield {"type": "metadata", "confidence": rag_result.confidence, "model": self.llm.model_name}
