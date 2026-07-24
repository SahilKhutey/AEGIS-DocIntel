"""
AEGIS-DocIntel — Query API Router
===================================
RAG query endpoint with streaming and WebSocket support.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from src.api.auth import TenantContext, get_current_tenant, get_current_tenant_ws
from src.api.models import (
    QueryRequest, QueryResponse, StreamChunk,
    CitationModel, ConfidenceLevel,
)

router = APIRouter()
log = structlog.get_logger("aegis.api.query")


def _confidence_level(score: float) -> ConfidenceLevel:
    if score >= 0.7:
        return ConfidenceLevel.HIGH
    elif score >= 0.4:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


@router.post(
    "",
    response_model=QueryResponse,
    summary="Query documents with RAG",
)
async def query_documents(
    body: QueryRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """
    Submit a natural language question against indexed documents.

    The system will:
    1. Check semantic cache (cosine ≥ 0.95 → instant response)
    2. Run hybrid BM25 + dense retrieval
    3. Cross-encoder reranking
    4. Build token-budget-aware context
    5. Query LLM with citations
    6. Return structured answer with source citations
    """
    t_start = time.perf_counter()
    session_id = body.session_id or uuid.uuid4()
    container = request.app.state.container

    # Streaming response
    if body.stream:
        return StreamingResponse(
            _stream_query(body, tenant, container, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Session-ID": str(session_id),
            },
        )

    try:
        result = await container.query_service.query(
            question=body.question,
            tenant_id=tenant.tenant_id,
            doc_ids=[str(d) for d in body.doc_ids] if body.doc_ids else None,
            session_id=str(session_id),
            top_k=body.top_k,
        )

        total_ms = (time.perf_counter() - t_start) * 1000

        citations = []
        if body.include_citations:
            for c in result.citations:
                citations.append(CitationModel(
                    source_num=c.source_num,
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    page=c.page,
                    section=c.section,
                    snippet=c.snippet,
                ))

        log.info(
            "Query served",
            tenant=tenant.tenant_id,
            session=str(session_id),
            cached=result.cached,
            latency_ms=f"{total_ms:.0f}",
            chunks=len(result.chunks),
            confidence=result.confidence,
        )

        return QueryResponse(
            answer=result.answer,
            citations=citations,
            confidence=_confidence_level(result.confidence),
            confidence_score=result.confidence,
            session_id=session_id,
            tokens_used=result.tokens_used,
            retrieval_latency_ms=result.retrieval_latency_ms,
            total_latency_ms=total_ms,
            cached=result.cached,
            model=result.model,
        )

    except Exception as e:
        log.error("Query failed", error=str(e), tenant=tenant.tenant_id)
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


async def _stream_query(
    body: QueryRequest,
    tenant: TenantContext,
    container,
    session_id: uuid.UUID,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for streaming query responses."""

    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    try:
        async for chunk in container.query_service.stream_query(
            question=body.question,
            tenant_id=tenant.tenant_id,
            doc_ids=[str(d) for d in body.doc_ids] if body.doc_ids else None,
            session_id=str(session_id),
            top_k=body.top_k,
        ):
            yield sse(chunk)
    except Exception as e:
        yield sse({"type": "error", "error": str(e)})
    finally:
        yield sse({"type": "done"})


@router.websocket("/ws/{session_id}")
async def query_websocket(
    websocket: WebSocket,
    session_id: uuid.UUID,
    tenant: TenantContext = Depends(get_current_tenant_ws),
):
    """
    WebSocket endpoint for real-time interactive query sessions.
    Supports multi-turn conversation with streaming responses.

    Tenant-isolation fix (Repository Audit follow-up): this endpoint
    previously had NO authentication dependency at all -- it accepted any
    WebSocket connection unconditionally, then read tenant_id directly out
    of each client-supplied message body with no verification whatsoever.
    That meant any client could query or stream any other tenant's
    documents simply by putting that tenant's id in their message JSON;
    it did not matter whether query_service.stream_query() itself enforced
    tenant_id correctly downstream, because the value being enforced was
    never actually authenticated in the first place. Fixed by requiring
    the same Depends(get_current_tenant) dependency every other route in
    this project uses, and deriving tenant_id from that verified identity
    rather than from the message body -- the client-supplied tenant_id (if
    any) is now ignored entirely, not merely double-checked.
    """
    await websocket.accept()
    container = websocket.app.state.container
    log.info("WebSocket connected", session=str(session_id), tenant=tenant.tenant_id)

    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "").strip()
            doc_ids = data.get("doc_ids")

            if not question:
                await websocket.send_json({"type": "error", "error": "Empty question"})
                continue

            await websocket.send_json({"type": "start"})

            async for chunk in container.query_service.stream_query(
                question=question,
                tenant_id=tenant.tenant_id,
                doc_ids=doc_ids,
                session_id=str(session_id),
            ):
                await websocket.send_json(chunk)

    except WebSocketDisconnect:
        log.info("WebSocket disconnected", session=str(session_id))
    except Exception as e:
        log.error("WebSocket error", error=str(e), session=str(session_id))
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass

