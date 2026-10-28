"""
src/api/middleware/request_id.py
================================
Request correlation middleware.
Ensures every request has a validated, server-controlled or sanitized correlation ID.
"""

from __future__ import annotations

import re
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        supplied = request.headers.get("X-Request-ID", "").strip()
        # Treat client-provided IDs as untrusted input: sanitize or generate
        if supplied and _REQUEST_ID_PATTERN.fullmatch(supplied):
            request_id = supplied
        else:
            request_id = uuid.uuid4().hex

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
