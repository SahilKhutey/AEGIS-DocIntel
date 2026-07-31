"""Access-log middleware: emits one JSON line per request."""

from __future__ import annotations

import time
import uuid

from amdi.observability.logging import get_logger

_log = get_logger("amdi.access")


async def access_log_middleware(request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    try:
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000.0
        _log.info(
            "http.access",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(ms, 3),
            request_id=rid,
        )
        response.headers["x-request-id"] = rid
        return response
    except Exception as exc:  # noqa: BLE001
        _log.exception("http.error", error=str(exc), request_id=rid)
        raise


__all__ = ["access_log_middleware"]
