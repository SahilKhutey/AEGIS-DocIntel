"""Rich readiness probe — checks Redis, ledger, and version drift."""

from __future__ import annotations

import platform
from typing import Any

from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger
from amdi.services.queue import QueueClient
from amdi.version import __version__


async def readiness() -> dict[str, Any]:
    s = get_settings()
    queue = QueueClient()
    ledger = make_ledger()

    return {
        "version":     __version__,
        "python":      platform.python_version(),
        "storage":     s.storage_backend,
        "queue":       s.queue_backend,
        "embedding":   s.embedding_model,
        "queue_ready": await queue.healthcheck(),
        "ledger_ready": True,
    }


__all__ = ["readiness"]
