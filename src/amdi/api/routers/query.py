"""POST /v1/query/ — streaming hybrid retrieval over SSE."""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from amdi.api.deps import get_container
from amdi.retrieval import HybridRetriever
from amdi.retrieval.schemas import Query, QueryExpansion, RetrievalConfig
from amdi.services.container import ServiceContainer

router = APIRouter()


class QueryRequest(BaseModel):
    raw: str
    top_k: int = Field(default=10, ge=1, le=200)
    token_budget: int | None = None
    enable_reranker: bool | None = None
    fusion: str | None = None


@router.post("/", summary="Hybrid 7-method retrieval, streamed via SSE")
async def query_stream(req: QueryRequest) -> StreamingResponse:
    settings = req.model_dump()
    container: ServiceContainer = get_container()
    retriever: HybridRetriever = container.retriever()

    cfg = RetrievalConfig(
        enable_reranker=(
            settings["enable_reranker"]
            if settings["enable_reranker"] is not None
            else container.retriever_config().enable_reranker
        ),
        fusion=settings["fusion"] or container.retriever_config().fusion,
    )
    q = Query(
        raw=req.raw,
        expanded=QueryExpansion(original=req.raw),
        top_k=req.top_k,
        token_budget=req.token_budget,
    )

    async def event_source() -> AsyncIterator[str]:
        # 1) Server: hello
        yield _sse("start", {"top_k": req.top_k})

        # 2) Hand the search off to the retriever
        result = await retriever.search(q)

        # 3) Stream each evidence block as it is decided
        for i, ev in enumerate(result.evidence):
            yield _sse("evidence", {
                "i": i,
                "score_fused": ev.score_fused,
                "score_rerank": ev.score_rerank,
                "text": ev.text,
                "citations": [c.model_dump() for c in ev.citations],
            })

        # 4) Final summary block
        yield _sse("done", {
            "timings_ms": result.timings_ms,
            "counters": result.counters,
            "evidence_count": len(result.evidence),
        })

    return StreamingResponse(event_source(), media_type="text/event-stream")


def _sse(kind: str, payload: dict) -> str:
    return f"event: {kind}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


__all__ = ["router", "QueryRequest"]
