"""Prometheus metrics + safe OpenTelemetry init."""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


REQUESTS_TOTAL = Counter(
    "amdi_http_requests_total",
    "HTTP requests handled",
    labelnames=("method", "route", "status"),
)

REQUEST_LATENCY = Histogram(
    "amdi_http_request_duration_seconds",
    "HTTP latency in seconds",
    labelnames=("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

JOBS_RUNNING = Gauge(
    "amdi_jobs_running",
    "In-flight ingestion jobs",
)

JOBS_FAILED_TOTAL = Counter(
    "amdi_jobs_failed_total",
    "Total failed jobs",
    labelnames=("reason",),
)

RETRIEVAL_RECALL = Histogram(
    "amdi_retrieval_recall_at_k",
    "Per-query retrieval Recall@K",
    labelnames=("k",),
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)


class PrometheusMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        route_template = _match_route_template(scope)

        with REQUEST_LATENCY.labels(method=method, route=route_template).time():
            status_holder = {"code": 500}
            async def _send(message):
                if message["type"] == "http.response.start":
                    status_holder["code"] = message["status"]
                await send(message)
            await self.app(scope, receive, _send)
            REQUESTS_TOTAL.labels(
                method=method, route=route_template,
                status=str(status_holder["code"]),
            ).inc()


def _match_route_template(scope) -> str:
    app = scope.get("app")
    if app is not None and hasattr(app, "router"):
        for r in app.router.routes:
            path = getattr(r, "path", None)
            if path and _matches(path, scope["path"]):
                return path
    return scope["path"]


def _matches(template: str, path: str) -> bool:
    t_parts = template.strip("/").split("/")
    p_parts = path.strip("/").split("/")
    if len(t_parts) != len(p_parts):
        return False
    for t, p in zip(t_parts, p_parts, strict=False):
        if t.startswith("{") and t.endswith("}"):
            continue
        if t != p:
            return False
    return True


def metrics_endpoint(request: Request) -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def install_metrics_route(app) -> None:
    app.router.routes.append(Route("/metrics", metrics_endpoint))


__all__ = [
    "PrometheusMiddleware",
    "REQUESTS_TOTAL", "REQUEST_LATENCY", "JOBS_RUNNING",
    "JOBS_FAILED_TOTAL", "RETRIEVAL_RECALL",
    "install_metrics_route",
]
