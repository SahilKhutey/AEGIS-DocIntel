"""
Security Middleware
===================

FastAPI / Starlette ASGI middleware for threat scanning, rate limiting, and token validation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitExceededError,
    ThreatDetectedError,
)
from .audit_log import AuditEventType, AuditSeverity


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware enforcing security controls at the request lifecycle.
    """

    def __init__(
        self,
        app: Any,
        security_engine: Any,
        exclude_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(app)
        self.security_engine = security_engine
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Check if the path is excluded from security checks
        path = request.url.path
        if any(path.startswith(ex_path) for ex_path in self.exclude_paths):
            return await call_next(request)

        # 1. Threat Detection (Heuristic checks on Path and Query Parameters)
        query_params = dict(request.query_params)
        body_str = None
        
        # Safe read of the request body (avoid consuming the stream for downstream routers)
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                body_str = body_bytes.decode("utf-8", errors="ignore")
                # Reset stream so downstream route handlers can read it
                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                request._receive = receive
            except Exception:
                pass

        try:
            # Threat check
            self.security_engine.threat_detector.check_threats(
                path=path,
                query_params=query_params,
                body=body_str,
            )
        except ThreatDetectedError as exc:
            self.security_engine.audit_log.log(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                actor_id="anonymous",
                resource_type="request",
                resource_id=path,
                action="scan",
                outcome="denied",
                severity=AuditSeverity.CRITICAL,
                source_ip=request.client.host if request.client else None,
                details={"reason": str(exc), "query": query_params, "body_snippet": (body_str[:200] if body_str else None)},
            )
            # Increment threat metrics
            self.security_engine._metrics.threats_detected += 1
            return JSONResponse(
                status_code=400,
                content={"detail": "Bad Request: Security threat detected."},
            )

        # 2. Authentication (Extract JWT Token or API Key)
        token_info = None
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")
        
        actor_id = "anonymous"
        client_ip = request.client.host if request.client else None

        try:
            if auth_header:
                if not auth_header.startswith("Bearer "):
                    raise AuthenticationError("Invalid Authorization header format. Use 'Bearer <token>'.")
                parts = auth_header.split(" ")
                if len(parts) != 2:
                    raise AuthenticationError("Invalid Authorization header format.")
                jwt_token = parts[1]
                token_info = self.security_engine.authentication.verify_token(jwt_token)
                actor_id = token_info.user_id
            elif api_key_header:
                token_info = self.security_engine.authentication.verify_api_key(api_key_header)
                actor_id = token_info.user_id
            else:
                raise AuthenticationError("Authentication credentials are required.")
        except AuthenticationError as exc:
            self.security_engine.audit_log.log(
                event_type=AuditEventType.LOGIN_FAILURE,
                actor_id="anonymous",
                resource_type="session",
                resource_id=path,
                action="authenticate",
                outcome="failure",
                severity=AuditSeverity.WARNING,
                source_ip=client_ip,
                details={"reason": str(exc)},
            )
            self.security_engine._metrics.failed_authentications += 1
            return JSONResponse(
                status_code=401,
                content={"detail": f"Unauthorized: {exc}"},
            )

        # 3. Rate Limiting
        # Define rule fallback key (rate limit using authenticated user or IP address)
        limiter_id = actor_id if actor_id != "anonymous" else (client_ip or "global")
        
        # Enforce IP or client rate limit (using a default rule 'global_api' if set)
        if "global_api" in self.security_engine.rate_limiter.rules:
            try:
                self.security_engine.rate_limiter.check_rate_limit("global_api", limiter_id)
            except RateLimitExceededError as exc:
                self.security_engine.audit_log.log(
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    actor_id=actor_id,
                    resource_type="rate_limiter",
                    resource_id="global_api",
                    action="request",
                    outcome="denied",
                    severity=AuditSeverity.WARNING,
                    source_ip=client_ip,
                    details={"reason": str(exc)},
                )
                self.security_engine._metrics.rate_limits_triggered += 1
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too Many Requests: Rate limit exceeded."},
                )

        # Store authenticated user context on request state
        request.state.user = token_info

        # 4. Call Downstream Application
        self.security_engine._metrics.total_requests += 1
        response = await call_next(request)
        return response
