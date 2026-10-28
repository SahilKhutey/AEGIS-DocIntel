"""
AEGIS-DocIntel — FastAPI Application Entry Point
=================================================
Production-grade REST API with:
- Strict runtime configuration & validation
- Fail-closed JWT & API-key authentication
- Multi-tenant routing & pre-retrieval isolation
- Durable document upload with idempotency keys
- WebSocket progress notifications
- Prometheus metrics + OpenTelemetry tracing
- Graceful shutdown & readiness probes
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
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

from src.api.auth_guard import AuthGuardMiddleware
from src.api.auth import get_current_tenant, require_role
from src.api.models import (
    DocumentResponse, QueryRequest, QueryResponse,
    IngestionStatusResponse, BatchUploadRequest,
    HealthResponse, ErrorResponse,
)
from src.api.routers import documents, queries, admin, webhooks, answers
from src.config import settings
from src.core.resilience import (
    DocumentStorageError,
    ExtractionError,
    IdempotencyConflictError,
    IdempotencyInProgressError,
    IdempotencyStore,
    InvalidDocumentError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ResourceLimitError,
)
from src.core.settings import ConfigurationError, load_runtime_settings
from src.observability.logging import configure_logging
from src.observability.metrics import start_observability, REQUEST_LATENCY


# ─────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: startup → serve → shutdown."""
    validate_prod = (
        not bool(os.environ.get("PYTEST_CURRENT_TEST"))
        or os.environ.get("AEGIS_ENFORCE_PRODUCTION_VALIDATION", "").lower() == "true"
    )
    runtime_settings = load_runtime_settings(validate_production=validate_prod)
    configure_logging(runtime_settings.log_level)
    log = structlog.get_logger("aegis.startup")

    log.info(
        "Starting AEGIS-DocIntel",
        version=settings.app.version,
        env=runtime_settings.environment,
        max_upload_bytes=runtime_settings.max_upload_bytes,
    )

    # Initialize all services
    from src.services.container import ServiceContainer
    container = ServiceContainer(settings)
    await container.startup()
    app.state.container = container
    app.state.orchestrator = container.rag_engine
    app.state.doc_registry = {}
    app.state.runtime_settings = runtime_settings
    app.state.intelligence_service = container.intelligence_service
    app.state.review_service = container.review_service

    # Start observability (Prometheus metrics endpoint)
    if settings.observability.enable_metrics:
        start_observability()

    log.info("AEGIS-DocIntel ready", host=settings.api.host, port=settings.api.port)

    yield  # ← Application serves requests here

    # Graceful shutdown with deadline
    log.info("Shutting down AEGIS-DocIntel")
    shutdown_timeout = runtime_settings.request_timeout_seconds
    try:
        await asyncio.wait_for(container.shutdown(), timeout=shutdown_timeout)
    except asyncio.TimeoutError:
        log.warning("Container shutdown timed out", timeout_seconds=shutdown_timeout)
    except Exception as exc:
        log.warning("Container shutdown error", error=str(exc))
    log.info("Shutdown complete")


# ─────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    runtime_settings = load_runtime_settings(validate_production=False)

    app = FastAPI(
        title="AEGIS-DocIntel",
        description=(
            "Production-grade Multimodal Document Intelligence Platform. "
            "Reverse-engineered architecture of ChatGPT/Gemini/Claude document pipelines."
        ),
        version=settings.app.version,
        docs_url="/docs" if runtime_settings.enable_docs else None,
        redoc_url="/redoc" if runtime_settings.enable_docs else None,
        openapi_url="/openapi.json" if runtime_settings.enable_docs else None,
        lifespan=lifespan,
    )

    app.state.runtime_settings = runtime_settings
    app.state.intelligence_service = None
    app.state.idempotency_store = IdempotencyStore(ttl_seconds=3600.0)

    # ── Middleware ──────────────────────────────────────────────
    app.add_middleware(AuthGuardMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID + Payload Limit + Latency Middleware
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        # 1. Enforce payload size limit prior to streaming large files
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                cl_int = int(content_length)
                max_bytes = getattr(request.app.state, "runtime_settings", runtime_settings).max_upload_bytes
                if cl_int > max_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        content={"detail": f"Payload size {cl_int} bytes exceeds limit of {max_bytes} bytes"},
                    )
            except ValueError:
                pass

        # 2. Extract or generate sanitized Request ID
        incoming_id = request.headers.get("X-Request-ID", "").strip()
        if incoming_id and len(incoming_id) <= 64 and re.match(r"^[a-zA-Z0-9_\-]+$", incoming_id):
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            latency = (time.perf_counter() - start) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-ms"] = f"{latency:.1f}"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            REQUEST_LATENCY.record(latency)
            return response
        finally:
            structlog.contextvars.clear_contextvars()

    # ── Prometheus metrics ──────────────────────────────────────
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # ── Routers ────────────────────────────────────────────────
    app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
    app.include_router(queries.router, prefix="/v1/query", tags=["Query"])
    app.include_router(answers.router, prefix="/v1/answers", tags=["Answers"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])
    app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])

    from src.api.routers import annotations
    app.include_router(annotations.router, prefix="/v1")

    from src.api.routes import router as ael_router
    app.include_router(ael_router, prefix="/v1")

    from src.api.routers import advanced_features
    app.include_router(advanced_features.router)

    from src.api.routers import health as health_router_mod
    app.include_router(health_router_mod.router)

    from src.api.routers import intelligence as intelligence_router_mod
    app.include_router(intelligence_router_mod.router, prefix="/v1")

    from src.api.routers import reviews as reviews_router_mod
    app.include_router(reviews_router_mod.router, prefix="/v1")
    app.include_router(reviews_router_mod.router, prefix="/api/v1", include_in_schema=False)
    app.include_router(documents.router, prefix="/api/v1/documents", include_in_schema=False)
    app.include_router(answers.router, prefix="/api/v1/answers", include_in_schema=False)
    app.include_router(answers.router, prefix="/api/v1/ask", include_in_schema=False)
    app.include_router(intelligence_router_mod.router, prefix="/api/v1", include_in_schema=False)

    from src.api.error_handlers import register_error_handlers
    register_error_handlers(app)

    # ── Stats endpoint ──────────────────────────────────────────
    @app.get("/v1/stats", tags=["System"])
    @app.get("/stats", tags=["System"])
    async def get_stats(request: Request):
        container = getattr(request.app.state, "container", None)
        if container is None:
            return {}
        orchestrator = container.rag_engine
        doc_service = container.document_service
        if not doc_service or not doc_service._docs:
            return {}
        try:
            doc_info = max(doc_service._docs.values(), key=lambda d: d.get('created_at', 0))
        except ValueError:
            return {}
            
        doc_id = doc_info['doc_id']
        elements = orchestrator.get_document_elements(doc_id) if orchestrator else []
        tables = orchestrator.get_document_tables(doc_id) if orchestrator else []
        templates = orchestrator.get_document_templates(doc_id) if orchestrator else []
        graph = orchestrator.get_document_graph() if orchestrator else None
        
        n_nodes = 0
        n_edges = 0
        if graph is not None:
            if hasattr(graph, 'graph'):
                nx_g = graph.graph
                n_nodes = len(nx_g.nodes) if hasattr(nx_g, 'nodes') else 0
                n_edges = len(nx_g.edges) if hasattr(nx_g, 'edges') else 0
            elif hasattr(graph, 'nodes'):
                n_nodes = len(graph.nodes)
                n_edges = len(graph.edges)

        return {
            'filename': doc_info.get('filename', '?'),
            'doc_id': doc_id,
            'n_elements': len(elements),
            'n_tables': len(tables),
            'n_templates': len(templates),
            'graph_nodes': n_nodes,
            'graph_edges': n_edges,
        }

    # ── Health & Readiness Probes ────────────────────────────────
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check(request: Request):
        """Liveness probe: verifies process is alive and responsive."""
        container = getattr(request.app.state, "container", None)
        if container is None:
            return JSONResponse(
                content={"status": "degraded", "checks": {"api": "initializing"}},
                status_code=503,
            )
        checks = await container.health_check()
        status_code = 200 if checks.get("api") == "ok" else 503
        return JSONResponse(
            content={"status": "healthy" if all(v == "ok" for v in checks.values()) else "degraded", "checks": checks},
            status_code=status_code,
        )

    @app.get("/readiness", tags=["System"])
    async def readiness(request: Request):
        """Readiness probe: verifies persistent storage and dependencies can serve traffic."""
        container = getattr(request.app.state, "container", None)
        if container is None:
            return JSONResponse(
                status_code=503,
                content={"ready": False, "reason": "initializing"},
            )
        is_ready, details = await container.verify_readiness()
        status_code = 200 if is_ready else 503
        return JSONResponse(
            status_code=status_code,
            content={"ready": is_ready, "details": details},
        )

    # ── Exception Handlers ──────────────────────────────────────
    @app.exception_handler(InvalidDocumentError)
    async def invalid_doc_handler(request: Request, exc: InvalidDocumentError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(IdempotencyConflictError)
    async def idempotency_conflict_handler(request: Request, exc: IdempotencyConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(IdempotencyInProgressError)
    async def idempotency_in_progress_handler(request: Request, exc: IdempotencyInProgressError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            headers={"Retry-After": "1"},
            content={"detail": str(exc), "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(ExtractionError)
    async def extraction_error_handler(request: Request, exc: ExtractionError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exc), "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(ResourceLimitError)
    async def resource_limit_handler(request: Request, exc: ResourceLimitError):
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": str(exc), "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(ProviderTimeoutError)
    async def provider_timeout_handler(request: Request, exc: ProviderTimeoutError):
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": "Downstream model provider timed out", "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(ProviderRateLimitError)
    async def provider_ratelimit_handler(request: Request, exc: ProviderRateLimitError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": "5"},
            content={"detail": "Downstream model provider throttled requests", "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(ProviderUnavailableError)
    async def provider_unavailable_handler(request: Request, exc: ProviderUnavailableError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Downstream model provider temporarily unavailable", "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(DocumentStorageError)
    async def storage_error_handler(request: Request, exc: DocumentStorageError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Durable document storage operation failed", "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(ConfigurationError)
    async def config_error_handler(request: Request, exc: ConfigurationError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Configuration validation error", "request_id": getattr(request.state, "request_id", "")},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log = structlog.get_logger("aegis.error")
        log.error("Unhandled exception", exc_info=False, error_type=type(exc).__name__, path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", "")},
        )

    return app


app = create_app()
