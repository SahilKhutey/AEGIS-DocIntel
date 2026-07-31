"""Rate-limit middleware."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from amdi.config import get_settings
from amdi.security.auth import Principal
from amdi.security.rate_limit import RateLimiter

_LIMITER: RateLimiter | None = None


def _get_limiter() -> RateLimiter:
    global _LIMITER
    if _LIMITER is None:
        s = get_settings()
        _LIMITER = RateLimiter(
            limit=s.rate_limit_per_minute,
            window_s=s.rate_limit_window_s,
        )
    return _LIMITER


class RateLimitMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = frozenset({"/healthz", "/readyz", "/metrics"})

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        identity = self._identity(request)
        if identity is None:
            return await call_next(request)


        limiter = _get_limiter()
        decision = await limiter.check(identity)
        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": {"code": "rate_limited",
                                    "limit": decision.limit,
                                    "window_s": 60}},
                headers=decision.headers(),
            )
        response = await call_next(request)
        for k, v in decision.headers().items():
            response.headers[k] = v
        return response

    @staticmethod
    def _identity(request: Request) -> str | None:
        p: Principal | None = getattr(request.state, "principal", None)
        if p is not None:
            return f"u:{p.user_id}"
        host = request.client.host if request.client else "unknown"
        return f"ip:{host}"


__all__ = ["RateLimitMiddleware"]
