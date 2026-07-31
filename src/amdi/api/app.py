"""FastAPI application factory with queue, ledger, bus, and async jobs.

Replaces a monolithic `src/main.py` in favor of:
    * a factory that builds a configured app
    * centralized middleware + error handling
    * clean router inclusion
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from amdi.api.routers import advanced, documents, health, jobs, query
from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger
from amdi.jobs.progress import ProgressBus
from amdi.jobs.shutdown import wait_for_drain
from amdi.services.queue import QueueClient
from amdi.version import __version__


logger = logging.getLogger("amdi")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: build ledger + bus, connect to Redis. Shutdown: drain queue."""
    settings = get_settings()

    # Ledger + bus are always needed (even in queue_backend=memory)
    ledger = make_ledger()
    bus = ProgressBus(max_buffer=settings.sse_buffer_max_events,
                      heartbeat_s=settings.sse_heartbeat_s)
    await bus.start()

    # Queue is optional in dev mode
    queue = QueueClient()
    if settings.queue_backend == "arq":
        try:
            await queue.connect()
            app.state.queue_ready = True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"queue.connect.failed error={exc}")
            app.state.queue_ready = False

    else:
        app.state.queue_ready = False

    from amdi.services.container import ServiceContainer
    from amdi.api.deps import set_container

    container = ServiceContainer(settings=settings)
    await container.startup()

    app.state.container = container
    app.state.ledger = ledger
    app.state.bus = bus
    app.state.queue = queue
    set_container(container)

    try:
        yield
    finally:
        try:
            await wait_for_drain(deadline_s=15.0)
        except Exception:  # noqa: BLE001
            pass
        await bus.stop()
        await queue.disconnect()
        await container.shutdown()



def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AEGIS-DocIntel / AMDI-OS",
        version=__version__,
        description="Pre-LLM Document Intelligence Operating System.",
        lifespan=_lifespan,
        openapi_tags=[
            {"name": "health", "description": "Liveness and readiness probes"},
            {"name": "documents", "description": "Upload + Document Explorer"},
            {"name": "jobs", "description": "Async ingestion job ledger + streaming"},
            {"name": "query", "description": "Hybrid 7-method RAG query"},
            {"name": "advanced", "description": "Math / Compliance / Advanced APIs"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValidationError)
    async def _validation_handler(request, exc):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def _unhandled(request, exc):
        logger.exception(f"unhandled.error path={request.url.path}")
        return JSONResponse(status_code=500, content={"detail": "internal_error"})


    from amdi.api.middleware.logging import access_log_middleware
    from amdi.api.middleware.rate_limit import RateLimitMiddleware
    from amdi.observability.health import readiness
    from amdi.observability.logging import configure as configure_logging
    from amdi.observability.metrics import PrometheusMiddleware, install_metrics_route

    configure_logging()
    install_metrics_route(app)
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.middleware("http")(access_log_middleware)

    @app.get("/readyz", tags=["health"])
    async def readyz_full():
        return await readiness()

    app.include_router(health.router, prefix="", tags=["health"])
    app.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
    app.include_router(jobs.router,     prefix="/v1/jobs",      tags=["jobs"])
    app.include_router(query.router,    prefix="/v1/query",     tags=["query"])
    app.include_router(advanced.router, prefix="/v1/advanced",  tags=["advanced"])

    return app



__all__ = ["create_app"]
