"""
AEGIS-DocIntel — Query Service
================================
Orchestrates the full RAG pipeline for a user query, delegating to AMDIOrchestrator.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import numpy as np
import structlog

from src.config import settings
from src.llm_service.llm_client import LLMService

log = structlog.get_logger("aegis.query_service")


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
    Orchestration wrapper using AMDIOrchestrator.
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
        """Execute query using the real AMDIOrchestrator."""
        t_start = time.perf_counter()
        doc_id = doc_ids[0] if doc_ids else None

        # Call the orchestrator
        res = await self.rag.query(question, doc_id=doc_id, top_k=top_k or 12)

        # Map citations
        citations = []
        for i, c in enumerate(res.get("citations", [])):
            citations.append(Citation(
                source_num=c.get("num", i + 1),
                chunk_id=c.get("chunk_id", ""),
                doc_id=c.get("doc_id", doc_id or ""),
                page=c.get("page", 1),
                section=c.get("section", ""),
                snippet=c.get("snippet", c.get("text", "")),
            ))

        total_latency = (time.perf_counter() - t_start) * 1000

        # Confidence level score mapping
        conf_label = res.get("confidence", "HIGH")
        conf_score = 0.9 if conf_label == "HIGH" else 0.5 if conf_label == "MEDIUM" else 0.2

        tokens = res.get("tokens_used", 0)
        if isinstance(tokens, dict):
            tokens_used = tokens
        else:
            tokens_used = {"input": tokens, "output": 0, "total": tokens}

        return QueryResult(
            answer=res.get("answer", ""),
            citations=citations,
            confidence=conf_score,
            chunks=[],
            tokens_used=tokens_used,
            retrieval_latency_ms=res.get("latency_ms", 0.0),
            model=res.get("model", "default"),
            cached=res.get("cached", False),
        )

    async def stream_query(
        self,
        question: str,
        tenant_id: str,
        doc_ids: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream tokens from AMDIOrchestrator."""
        doc_id = doc_ids[0] if doc_ids else None
        
        # Stream from the orchestrator
        async for token in self.rag.stream_query(question):
            yield {"type": "token", "content": token}
        
        yield {"type": "done"}
