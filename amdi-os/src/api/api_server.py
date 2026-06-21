"""
AMDI-OS — FastAPI Application Server
======================================
REST API: ingest documents + query via 7-layer adaptive fusion.

Endpoints:
  POST /ingest              — Upload & process document
  POST /query               — Query with adaptive fusion
  GET  /query/stream        — SSE streaming response
  GET  /documents           — List ingested documents
  DELETE /documents/{id}    — Remove document
  GET  /health              — Health check
  GET  /metrics             — Prometheus metrics
"""
from __future__ import annotations

import asyncio
import io
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    HAS_PROM = True
except ImportError:
    HAS_PROM = False

from src.core.document_object import DocumentObject
from src.core.orchestrator import AMDIOrchestrator

log = logging.getLogger("amdi.api")

# ─────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────
if HAS_PROM:
    INGEST_COUNTER   = Counter("amdi_ingests_total", "Total documents ingested")
    QUERY_COUNTER    = Counter("amdi_queries_total", "Total queries executed")
    INGEST_LATENCY   = Histogram("amdi_ingest_latency_seconds", "Ingest latency")
    QUERY_LATENCY    = Histogram("amdi_query_latency_seconds", "Query latency")
    TOKEN_REDUCTION  = Gauge("amdi_token_reduction_pct", "Token reduction vs. naive")

# ─────────────────────────────────────────────────────────────────
# Global orchestrator state
# ─────────────────────────────────────────────────────────────────
_orchestrator: Optional[AMDIOrchestrator] = None
_doc_registry: dict[str, dict] = {}     # doc_id → metadata


@asynccontextmanager
async def lifespan(app: 'FastAPI'):  # type: ignore[name-defined]
    global _orchestrator
    log.info('AMDI-OS starting up...')
    _orchestrator = AMDIOrchestrator()
    app.state.orchestrator = _orchestrator
    app.state.doc_registry = _doc_registry
    yield
    log.info('AMDI-OS shutting down...')
    if _orchestrator:
        await _orchestrator.close()


if HAS_FASTAPI:
    app = FastAPI(
        title="AEGIS-AMDI-OS",
        description="Adaptive Mathematical Document Intelligence Operating System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from src.api.routes import router as api_router
    app.include_router(api_router)
    app.include_router(api_router, prefix="/v1")

    from src.api.annotations import router as annotations_router
    app.include_router(annotations_router)
    app.include_router(annotations_router, prefix="/v1")


def run():
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "src.api.api_server:app",
        host="0.0.0.0", port=8000, reload=False, workers=1,
    )
