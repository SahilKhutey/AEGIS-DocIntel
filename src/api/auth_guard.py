"""
AEGIS-DocIntel — Fail-closed authentication guard
==================================================
Deny-by-default HTTP authentication applied to EVERY route, regardless of which router
declared it.

Why this exists
---------------
Authentication used to be opt-in per route (``Depends(get_current_tenant)``). Probing the
live app without credentials showed that 45 of 59 operations accepted anonymous requests:
the whole legacy AEL tree (``src/api/routes/query.py``), annotations, admin, advanced and
webhook routers had simply never been wired to auth. Concretely, an anonymous caller could:

  * export another tenant's confidential document      (GET    /v1/documents/{id}/export)
  * wipe every document for every tenant               (DELETE /v1/document -> 204)
  * read/modify annotations and call compute endpoints

Opt-in security fails open: every new route is public until someone remembers. This guard
inverts that — a request is rejected with 401 unless it is for an explicitly allow-listed
public path, or carries credentials that the SAME validators used by
``get_current_tenant`` accept. New routes are therefore protected automatically.

The per-route ``Depends(get_current_tenant)`` is still needed (it supplies the
``TenantContext`` for tenant scoping); this guard is the safety net underneath it.

Not covered (by design): WebSocket connections — ``queries.py`` authenticates those inside
the route via ``get_current_tenant_ws`` (an HTTP middleware cannot see them).
"""
from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException, status
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# Exact public paths. Everything else requires credentials.
#   /health, /readiness : liveness/readiness probes (orchestrators cannot send credentials)
#   /docs, /redoc, /openapi.json : interactive docs (the app itself disables these when
#       settings.app.env == "production")
PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/live",
        "/health/ready",
        "/readiness",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }
)

# Path prefixes that are public.
#   /metrics : Prometheus scrape endpoint. Conventional to protect with network policy
#   rather than app auth. KNOWN EXPOSURE: series are labelled with tenant_id, so this must
#   not be internet-reachable (tracked for the operability phase).
PUBLIC_PREFIXES: tuple[str, ...] = ("/metrics",)


def _is_public(path: str, public_paths: frozenset[str], public_prefixes: Iterable[str]) -> bool:
    norm = path.rstrip("/") or "/"
    if norm in public_paths:
        return True
    return any(norm == p or norm.startswith(p + "/") for p in public_prefixes)


def _authenticate(headers: dict[str, str]):
    """Raise HTTPException(401) unless the headers carry credentials the real validators
    accept. Mirrors ``src.api.auth.get_current_tenant`` exactly (same functions)."""
    # Imported lazily: src.api.auth imports FastAPI security classes and we avoid import cycles.
    from src.api.auth import _validate_api_key, _validate_jwt

    authorization = headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return _validate_jwt(token.strip())
        return

    api_key = headers.get("x-api-key", "").strip()
    if api_key:
        return _validate_api_key(api_key)
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication. Provide Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthGuardMiddleware:
    """Pure-ASGI middleware (no BaseHTTPMiddleware buffering, safe for streaming responses)."""

    def __init__(
        self,
        app: ASGIApp,
        public_paths: frozenset[str] = PUBLIC_PATHS,
        public_prefixes: tuple[str, ...] = PUBLIC_PREFIXES,
    ) -> None:
        self.app = app
        self.public_paths = public_paths
        self.public_prefixes = public_prefixes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # CORS preflight carries no credentials by definition; CORSMiddleware (outer) answers it.
        if scope["method"] == "OPTIONS" or _is_public(scope["path"], self.public_paths, self.public_prefixes):
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        try:
            context = _authenticate(headers)
            if "state" not in scope:
                scope["state"] = {}
            scope["state"]["tenant_context"] = context
        except HTTPException as exc:
            response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
