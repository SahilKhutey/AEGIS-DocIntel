"""
src/core/observability.py
=========================
AEGIS-DocIntel — Structured Logging, Request Correlation & Stage Telemetry.
Emits safe structured metadata for operational tracing and monitoring.
Strict invariant: Never log raw document content, prompt texts, or credentials.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger("aegis.events")

# Canonical stage events
EVENT_REQUEST_ACCEPTED = "request.accepted"
EVENT_AUTH_DENIED = "auth.denied"
EVENT_RETRIEVAL_COMPLETED = "retrieval.completed"
EVENT_GENERATION_COMPLETED = "generation.completed"
EVENT_CITATION_VALIDATION_FAILED = "citation.validation_failed"
EVENT_REQUEST_COMPLETED = "request.completed"
EVENT_DEPENDENCY_UNAVAILABLE = "dependency.unavailable"

# Background Job Events
EVENT_JOB_ENQUEUED = "job.enqueued"
EVENT_JOB_CLAIMED = "job.claimed"
EVENT_JOB_COMPLETED = "job.completed"
EVENT_JOB_FAILED = "job.failed"
EVENT_JOB_RETRIED = "job.retried"
EVENT_JOB_CANCELLED = "job.cancelled"


def configure_logging() -> None:
    """Configure structured logging based on AEGIS_LOG_LEVEL environment variable."""
    level_name = os.getenv("AEGIS_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def log_event(
    event: str,
    *,
    request_id: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> None:
    """
    Emit structured metadata record.
    Never pass document text, model prompts, or authentication tokens.
    """
    safe_fields = dict(fields or {})
    record = {
        "event": event,
        "request_id": request_id,
        "fields": safe_fields,
    }
    logger.info(json.dumps(record, ensure_ascii=False, default=str))


class StageTimer:
    """High-precision stage timer measuring wall-clock latency in milliseconds."""

    def __init__(self) -> None:
        self._started = time.perf_counter()

    def elapsed_ms(self) -> float:
        """Return elapsed time in milliseconds with 2 decimal precision."""
        return round((time.perf_counter() - self._started) * 1000.0, 2)
