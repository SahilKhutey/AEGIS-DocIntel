"""
tests/test_mvp4_error_handling.py
=================================
Unit tests for standardized error handling contract and RequestIdMiddleware.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.error_handlers import (
    PublicServiceError,
    DependencyTimeoutError,
    DependencyUnavailableError,
    RateLimitExceededError,
    AccessDeniedError,
    InvalidRequestError,
    register_error_handlers,
)
from src.api.middleware.request_id import RequestIdMiddleware
from src.api.middleware.security_headers import SecurityHeadersMiddleware


def make_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app)

    @app.get("/test/timeout")
    def fail_timeout():
        raise DependencyTimeoutError()

    @app.get("/test/unavailable")
    def fail_unavailable():
        raise DependencyUnavailableError()

    @app.get("/test/ratelimit")
    def fail_ratelimit():
        raise RateLimitExceededError()

    @app.get("/test/forbidden")
    def fail_forbidden():
        raise AccessDeniedError()

    @app.get("/test/invalid")
    def fail_invalid():
        raise InvalidRequestError()

    @app.get("/test/custom")
    def fail_custom():
        raise PublicServiceError(
            code="CUSTOM_FAILURE",
            message="Custom failure explanation.",
            status_code=400,
        )

    @app.get("/test/ok")
    def ok_route():
        return {"status": "ok"}

    return app


def test_service_error_has_stable_contract():
    client = TestClient(make_test_app())
    response = client.get("/test/timeout")
    assert response.status_code == 504
    payload = response.json()
    assert "error" in payload
    assert payload["error"]["code"] == "DEPENDENCY_TIMEOUT"
    assert "did not respond in time" in payload["error"]["message"]
    assert "request_id" in payload["error"]
    assert len(payload["error"]["request_id"]) > 0


def test_request_id_propagated_and_echoed():
    client = TestClient(make_test_app())
    custom_id = "trace-client-12345"
    response = client.get("/test/timeout", headers={"X-Request-ID": custom_id})
    assert response.status_code == 504
    assert response.headers["X-Request-ID"] == custom_id
    payload = response.json()
    assert payload["error"]["request_id"] == custom_id


def test_malformed_client_request_id_is_sanitized():
    client = TestClient(make_test_app())
    # Client passes injection or invalid chars in X-Request-ID
    malicious_id = "bad id with spaces and <script>alert(1)</script>"
    response = client.get("/test/ok", headers={"X-Request-ID": malicious_id})
    assert response.status_code == 200
    returned_id = response.headers["X-Request-ID"]
    assert returned_id != malicious_id
    assert len(returned_id) >= 16


def test_security_headers_middleware():
    client = TestClient(make_test_app())
    response = client.get("/test/ok")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers


@pytest.mark.parametrize(
    "path,expected_code,expected_status",
    [
        ("/test/unavailable", "DEPENDENCY_UNAVAILABLE", 503),
        ("/test/ratelimit", "RATE_LIMIT_EXCEEDED", 429),
        ("/test/forbidden", "FORBIDDEN", 403),
        ("/test/invalid", "INVALID_REQUEST", 422),
        ("/test/custom", "CUSTOM_FAILURE", 400),
    ],
)
def test_all_public_errors(path, expected_code, expected_status):
    client = TestClient(make_test_app())
    response = client.get(path)
    assert response.status_code == expected_status
    payload = response.json()
    assert payload["error"]["code"] == expected_code
