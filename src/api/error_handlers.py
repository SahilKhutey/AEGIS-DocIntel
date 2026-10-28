"""
src/api/error_handlers.py
=========================
AEGIS-DocIntel — Standardized Public API Error Handlers.
Guarantees predictable, non-disclosing error responses across all routes.
Never leaks stack traces, internal system paths, or model credentials.
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("aegis.errors")


class PublicServiceError(Exception):
    """Base class for all standardized public-facing service errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class InvalidRequestError(PublicServiceError):
    def __init__(self, message: str = "Invalid request payload or parameters.") -> None:
        super().__init__(code="INVALID_REQUEST", message=message, status_code=422)


class AuthenticationRequiredError(PublicServiceError):
    def __init__(self, message: str = "Authentication credentials required.") -> None:
        super().__init__(code="UNAUTHENTICATED", message=message, status_code=401)


class AccessDeniedError(PublicServiceError):
    def __init__(self, message: str = "Access denied for the requested resource.") -> None:
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class ResourceNotFoundError(PublicServiceError):
    def __init__(self, message: str = "The requested resource was not found.") -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class RateLimitExceededError(PublicServiceError):
    def __init__(self, message: str = "Rate limit exceeded. Please retry later.") -> None:
        super().__init__(code="RATE_LIMIT_EXCEEDED", message=message, status_code=429)


class DependencyTimeoutError(PublicServiceError):
    def __init__(self, message: str = "A required service did not respond in time.") -> None:
        super().__init__(code="DEPENDENCY_TIMEOUT", message=message, status_code=504)


class DependencyUnavailableError(PublicServiceError):
    def __init__(self, message: str = "A required downstream dependency is temporarily unavailable.") -> None:
        super().__init__(code="DEPENDENCY_UNAVAILABLE", message=message, status_code=503)


def register_error_handlers(app: FastAPI) -> None:
    """Register standardized PublicServiceError exception handler on FastAPI app."""

    @app.exception_handler(PublicServiceError)
    async def public_service_error_handler(
        request: Request,
        exc: PublicServiceError,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", "")
        logger.warning(
            "service_error code=%s status=%d request_id=%s",
            exc.code,
            exc.status_code,
            request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": request_id,
                }
            },
        )
