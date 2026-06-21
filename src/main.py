"""
AEGIS-DocIntel — FastAPI Application Entry Point
=================================================
Production-grade REST API with:
- JWT authentication
- Multi-tenant routing
- Document upload + query endpoints
- WebSocket progress notifications
- Prometheus metrics + OpenTelemetry tracing
- Graceful shutdown
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Request,
    UploadFile, WebSocket, WebSocketDisconnect, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from prometheus_client import make_asgi_app

from src.api.auth import get_current_tenant, require_role
from src.api.models import (
    DocumentResponse, QueryRequest, QueryResponse,
    IngestionStatusResponse, BatchUploadRequest,
    HealthResponse, ErrorResponse,
)
from src.api.routers import documents, queries, admin, webhooks
from src.config import settings
from src.observability.logging import configure_logging
from src.observability.metrics import start_observability, REQUEST_LATENCY


# ─────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: startup → serve → shutdown."""
    configure_logging(settings.app.log_level)
    log = structlog.get_logger("aegis.startup")

    log.info("Starting AEGIS-DocIntel", version=settings.app.version, env=settings.app.env)

    # Initialize all services
    from src.services.container import ServiceContainer
    container = ServiceContainer(settings)
    await container.startup()
    app.state.container = container

    # Start observability (Prometheus metrics endpoint)
    if settings.observability.enable_metrics:
        start_observability()

    log.info("AEGIS-DocIntel ready", host=settings.api.host, port=settings.api.port)

    yield  # ← Application serves requests here

    # Graceful shutdown
    log.info("Shutting down AEGIS-DocIntel")
    await container.shutdown()
    log.info("Shutdown complete")


# ─────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="AEGIS-DocIntel",
        description=(
            "Production-grade Multimodal Document Intelligence Platform. "
            "Reverse-engineered architecture of ChatGPT/Gemini/Claude document pipelines."
        ),
        version=settings.app.version,
        docs_url="/docs" if settings.app.env != "production" else None,
        redoc_url="/redoc" if settings.app.env != "production" else None,
        openapi_url="/openapi.json" if settings.app.env != "production" else None,
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID + latency middleware
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        latency = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{latency:.1f}"
        REQUEST_LATENCY.record(latency)
        return response

    # ── Prometheus metrics ──────────────────────────────────────
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # ── Routers ────────────────────────────────────────────────
    app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
    app.include_router(queries.router, prefix="/v1/query", tags=["Query"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])
    app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])

    # ── Health endpoints ────────────────────────────────────────
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check(request: Request):
        container = request.app.state.container
        checks = await container.health_check()
        status_code = 200 if all(v == "ok" for v in checks.values()) else 503
        return JSONResponse(
            content={"status": "healthy" if status_code == 200 else "degraded", "checks": checks},
            status_code=status_code,
        )

    @app.get("/readiness", tags=["System"])
    async def readiness():
        return {"ready": True}

    # ── Global exception handler ────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log = structlog.get_logger("aegis.error")
        log.error("Unhandled exception", exc=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", "")},
        )

    return app


app = create_app()
