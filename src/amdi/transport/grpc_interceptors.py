"""Auth, logging, metrics for the gRPC server.

Implements the three interceptors every production gRPC service needs:

* AuthServerInterceptor   — JWT validation; populates context.auth
* LoggingServerInterceptor — request/response + timing log
* MetricsServerInterceptor — Prometheus counters + latency hist
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import grpc

from amdi.config import get_settings

logger = logging.getLogger("amdi.transport")

CTX_AUTH_USER = "auth.user"


class AuthServerInterceptor(grpc.ServerInterceptor):
    """JWT (HS256) bearer-token validator."""

    UNAUTH_ALLOWLIST = frozenset({
        "/amdi.v1.DocumentIntelligence/Health",
    })

    def __init__(self, validator: Callable[[str], dict[str, Any]] | None = None) -> None:
        self._validator = validator or self._default_validator

    @staticmethod
    def _default_validator(token: str) -> dict[str, Any]:
        import jwt
        s = get_settings()
        return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])

    def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        method = handler_call_details.method
        if method in self.UNAUTH_ALLOWLIST:
            return continuation(handler_call_details)

        meta = dict(handler_call_details.invocation_metadata or [])
        auth = meta.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return _abort_handler(grpc.StatusCode.UNAUTHENTICATED, "missing bearer token")

        token = auth.split(" ", 1)[1]
        try:
            claims = self._validator(token)
        except Exception as exc:  # noqa: BLE001
            return _abort_handler(grpc.StatusCode.UNAUTHENTICATED, f"invalid token: {exc}")

        return _wrap(continuation(handler_call_details), claims)


def _wrap(handler: grpc.RpcMethodHandler, claims: dict[str, Any]) -> grpc.RpcMethodHandler:
    def _bind(request, context):
        from amdi.transport.grpc_server import _set_auth
        _set_auth(context, claims)
        if handler.unary_unary:
            return handler.unary_unary(request, context)
        return handler(request, context)
    return grpc.unary_unary_rpc_method_handler(_bind)


def _abort_handler(code: grpc.StatusCode, msg: str) -> grpc.RpcMethodHandler:
    def abort(request, context):
        context.abort(code, msg)
    return grpc.unary_unary_rpc_method_handler(abort)


class LoggingServerInterceptor(grpc.ServerInterceptor):
    def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        method = handler_call_details.method
        meta = dict(handler_call_details.invocation_metadata or [])
        t0 = time.perf_counter()

        handler = continuation(handler_call_details)

        def _log(context):
            ms = (time.perf_counter() - t0) * 1000.0
            logger.info("grpc.call", extra={
                "method": method,
                "peer": context.peer() if hasattr(context, "peer") else "",
                "user_agent": meta.get("user-agent", ""),
                "latency_ms": round(ms, 3),
            })

        def _unary(request, context):
            try:
                return handler.unary_unary(request, context)
            finally:
                _log(context)

        if handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                _unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        return handler


class MetricsServerInterceptor(grpc.ServerInterceptor):
    def __init__(self) -> None:
        try:
            from prometheus_client import Counter, Histogram  # type: ignore
            self._counter = Counter(
                "amdi_grpc_requests_total",
                "gRPC requests handled",
                labelnames=("method", "code"),
            )
            self._hist = Histogram(
                "amdi_grpc_request_duration_ms",
                "gRPC latency in ms",
                labelnames=("method",),
                buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
            )
            self._prom = True
        except ImportError:  # pragma: no cover
            self._prom = False

    def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        if not self._prom:
            return continuation(handler_call_details)
        method = handler_call_details.method
        t0 = time.perf_counter()
        handler = continuation(handler_call_details)

        def _finalize(code: str = "OK") -> None:
            dt = (time.perf_counter() - t0) * 1000.0
            self._counter.labels(method=method, code=code).inc()
            self._hist.labels(method=method).observe(dt)

        def _unary(request, context):
            try:
                return handler.unary_unary(request, context)
            except grpc.RpcError as e:
                _finalize(e.code().name if hasattr(e, "code") else "ERROR")
                raise
            finally:
                _finalize()

        if handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                _unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        return handler


__all__ = [
    "AuthServerInterceptor",
    "LoggingServerInterceptor",
    "MetricsServerInterceptor",
    "CTX_AUTH_USER",
]
