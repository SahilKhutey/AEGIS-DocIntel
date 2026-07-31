"""
AEGIS-DocIntel — Observability: Metrics & Logging
==================================================
Prometheus metrics definitions + structured logging setup.
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

try:
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    HAS_OPENTELEMETRY = True
except ImportError:
    MeterProvider = None  # type: ignore
    PeriodicExportingMetricReader = None  # type: ignore
    HAS_OPENTELEMETRY = False

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
except ImportError:
    # Minimal fallback mock for prometheus metrics
    class _MockMetric:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    Counter = Gauge = Histogram = _MockMetric  # type: ignore
    start_http_server = lambda *args, **kwargs: None  # type: ignore

from src.config import settings


# ─────────────────────────────────────────────────────────────────
# Prometheus Metrics Registry
# ─────────────────────────────────────────────────────────────────

DOCUMENTS_INGESTED = Counter(
    "aegis_documents_ingested_total",
    "Total documents ingested",
    ["tenant_id", "status"],
)

CHUNKS_INDEXED = Counter(
    "aegis_chunks_indexed_total",
    "Total chunks indexed",
    ["tenant_id", "block_type"],
)

RETRIEVAL_LATENCY = Histogram(
    "aegis_retrieval_latency_seconds",
    "Retrieval stage latency",
    ["stage"],  # bm25 | dense | visual | rerank | total
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

LLM_TOKENS = Counter(
    "aegis_llm_tokens_total",
    "LLM tokens consumed",
    ["tenant_id", "model", "direction"],  # direction: input | output
)

CACHE_HITS = Counter(
    "aegis_cache_hits_total",
    "Cache hits by type",
    ["cache_type"],  # semantic | kv | prefix | document
)

CACHE_MISSES = Counter(
    "aegis_cache_misses_total",
    "Cache misses by type",
    ["cache_type"],
)

ACTIVE_DOCUMENTS = Gauge(
    "aegis_active_documents",
    "Currently indexed documents",
    ["tenant_id"],
)

QUERY_ERRORS = Counter(
    "aegis_query_errors_total",
    "Query pipeline errors",
    ["tenant_id", "error_type"],
)

INGEST_QUEUE_LAG = Gauge(
    "aegis_ingest_queue_lag",
    "Kafka consumer lag for ingest topic",
)


class _NoOpHistogram:
    """Stub used before OTel is initialized."""
    def record(self, value, **attrs):
        pass

REQUEST_LATENCY: _NoOpHistogram = _NoOpHistogram()  # replaced in start_observability()


# ─────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────

def start_observability() -> None:
    """Start Prometheus /metrics HTTP server and OpenTelemetry."""
    global REQUEST_LATENCY

    if settings.observability.enable_metrics:
        try:
            start_http_server(settings.observability.metrics_port)
        except OSError:
            pass  # Port already in use (e.g., in tests)

    # OpenTelemetry metrics
    try:
        from opentelemetry import metrics as otel_metrics
        meter = otel_metrics.get_meter("aegis-docintel", settings.app.version)
        REQUEST_LATENCY = meter.create_histogram(
            "aegis.request.latency",
            unit="ms",
            description="HTTP request latency in milliseconds",
        )
    except Exception:
        pass  # Keep the NoOp stub if OTel not fully configured


# ─────────────────────────────────────────────────────────────────
# Structured Logging
# ─────────────────────────────────────────────────────────────────

def configure_logging(level: str = "INFO") -> None:
    """Configure structlog + stdlib logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if settings.app.env == "production"
                else structlog.dev.ConsoleRenderer(colors=True)
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )


# ─────────────────────────────────────────────────────────────────
# Trace Span Context Manager
# ─────────────────────────────────────────────────────────────────

from contextlib import contextmanager
from typing import Generator


@contextmanager
def trace_span(name: str, **attrs) -> Generator:
    """OpenTelemetry trace span context manager."""
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("aegis-docintel")
        with tracer.start_as_current_span(name, attributes=attrs) as span:
            try:
                yield span
            except Exception as exc:
                span.record_exception(exc)
                raise
    except ImportError:
        yield None  # No-op if OTel not installed
