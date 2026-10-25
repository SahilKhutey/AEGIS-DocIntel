"""
tests/test_runtime_configuration.py
===================================
P3.1 Runtime, Configuration and Startup Invariant Tests:
1. Validates authoritative settings parsing from environment variables.
2. Enforces fail-closed production security constraints (JWT, API keys, CORS, LLM policy).
3. Verifies deterministic startup and /readiness failure when storage is unavailable.
4. Verifies process liveness via /health and payload size limits.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.core.settings import (
    ConfigurationError,
    RuntimeSettings,
    load_runtime_settings,
    validate_production_invariants,
)
from src.main import create_app


def test_supported_environments_parsing():
    """P3.1: Validates environment variable parsing across development, test, staging, production."""
    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "development"}):
        s = load_runtime_settings(validate_production=False)
        assert s.environment == "development"

    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "production"}):
        s = load_runtime_settings(validate_production=False)
        assert s.environment == "production"

    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "invalid_env"}):
        with pytest.raises(ConfigurationError, match="Unsupported AEGIS_ENVIRONMENT"):
            load_runtime_settings(validate_production=False)


def test_production_forbids_in_memory_database():
    """P3.1: Production mode strictly forbids ephemeral in-memory databases."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": ":memory:",
        "AEGIS_JWT_PUBLIC_KEY": "dummy-key",
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-docintel",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_LLM_PROVIDER": "vllm",
    }):
        with pytest.raises(ConfigurationError, match="In-memory database ':memory:' is forbidden"):
            load_runtime_settings(validate_production=True)


def test_production_forbids_wildcard_cors():
    """P3.1: Wildcard CORS origin is forbidden in staging and production."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp,*",
        "AEGIS_JWT_PUBLIC_KEY": "dummy-key",
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-docintel",
        "AEGIS_LLM_PROVIDER": "vllm",
    }):
        with pytest.raises(ConfigurationError, match=r"Wildcard CORS origin '\*' is strictly forbidden"):
            load_runtime_settings(validate_production=True)


def test_production_requires_authentication_provider():
    """P3.1: Production startup fails if neither JWT nor API key provider is configured."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_LLM_PROVIDER": "vllm",
    }, clear=True):
        with pytest.raises(ConfigurationError, match="Production mode requires at least one authenticated credential provider"):
            load_runtime_settings(validate_production=True)


def test_production_jwt_requires_issuer_and_audience():
    """P3.1: When JWT is configured in production, issuer and audience must be defined."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_JWT_PUBLIC_KEY": "dummy-key",
        "AEGIS_LLM_PROVIDER": "vllm",
    }, clear=True):
        with pytest.raises(ConfigurationError, match="AEGIS_JWT_ISSUER is required"):
            load_runtime_settings(validate_production=True)

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_JWT_PUBLIC_KEY": "dummy-key",
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_LLM_PROVIDER": "vllm",
    }, clear=True):
        with pytest.raises(ConfigurationError, match="AEGIS_JWT_AUDIENCE is required"):
            load_runtime_settings(validate_production=True)


def test_production_rejects_raw_api_keys():
    """P3.1: Storing raw API keys instead of SHA-256 hashes is strictly forbidden."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_API_KEYS": "tenant-a:admin:raw-unhashed-secret-key",
        "AEGIS_LLM_PROVIDER": "vllm",
    }, clear=True):
        with pytest.raises(ConfigurationError, match="Raw API keys in AEGIS_API_KEYS are forbidden"):
            load_runtime_settings(validate_production=True)


def test_production_forbids_mock_llm_and_unauthorized_external_transfer():
    """P3.1: Mock LLM is rejected in production, and cloud LLMs require explicit consent."""
    valid_key_hash = "sha256:" + "a" * 64
    # Mock provider forbidden
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_API_KEYS": f"tenant-a:admin:{valid_key_hash}",
        "AEGIS_LLM_PROVIDER": "mock",
    }, clear=True):
        with pytest.raises(ConfigurationError, match="Mock LLM provider is forbidden in production mode"):
            load_runtime_settings(validate_production=True)

    # External LLM without authorization forbidden
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_SQLITE_PATH": "data/prod.db",
        "AEGIS_CORS_ORIGINS": "https://app.aegis.corp",
        "AEGIS_API_KEYS": f"tenant-a:admin:{valid_key_hash}",
        "AEGIS_LLM_PROVIDER": "openai",
        "AEGIS_ALLOW_EXTERNAL_LLM": "false",
    }, clear=True):
        with pytest.raises(ConfigurationError, match="without explicit data-transfer authorization"):
            load_runtime_settings(validate_production=True)


@patch("src.services.container.ServiceContainer.startup", new_callable=AsyncMock)
def test_health_and_readiness_endpoints_behavior(mock_startup):
    """P3.1: /health reports liveness (200), /readiness reports dependency state."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        # Mock container on app state
        mock_container = MagicMock()
        mock_container.health_check = AsyncMock(return_value={"api": "ok", "embedding_model": "ok"})
        mock_container.verify_readiness = AsyncMock(return_value=(True, {"database": "ok", "container": "ok"}))
        app.state.container = mock_container

        # 1. /health returns 200
        res_health = client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        # 2. /readiness returns 200 when healthy
        res_ready = client.get("/readiness")
        assert res_ready.status_code == 200
        assert res_ready.json()["ready"] is True

        # 3. /readiness returns 503 when database is unhealthy
        mock_container.verify_readiness = AsyncMock(return_value=(False, {"database": "unhealthy: disk I/O error"}))
        res_unready = client.get("/readiness")
        assert res_unready.status_code == 503
        assert res_unready.json()["ready"] is False


@patch("src.services.container.ServiceContainer.startup", new_callable=AsyncMock)
def test_payload_size_limit_middleware_rejection(mock_startup):
    """P3.1: Requests exceeding max upload size are rejected with HTTP 413."""
    with patch.dict(os.environ, {"AEGIS_MAX_UPLOAD_BYTES": "1024"}):
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            # Request with oversized content-length header
            res = client.post(
                "/v1/documents/upload",
                headers={"Authorization": "Bearer dev-token", "Content-Length": "2048"},
                content=b"x" * 2048,
            )
            assert res.status_code == 413
            assert "exceeds limit" in res.json()["detail"]


def test_docs_endpoints_disabled_when_configured():
    """P3.1: API documentation endpoints can be disabled in production."""
    with patch.dict(os.environ, {"AEGIS_ENABLE_DOCS": "false"}):
        app = create_app()
        assert app.docs_url is None
        assert app.redoc_url is None
        assert app.openapi_url is None


def test_production_rejects_missing_authentication(monkeypatch):
    """Contract: Production startup must fail when no valid authentication mechanism is configured."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "production")
    monkeypatch.delenv("AEGIS_JWT_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("AEGIS_JWT_PUBLIC_KEY_PATH", raising=False)
    monkeypatch.delenv("AEGIS_JWT_SECRET", raising=False)
    monkeypatch.delenv("AEGIS_API_KEY_HASHES", raising=False)
    monkeypatch.delenv("AEGIS_API_KEYS", raising=False)

    with pytest.raises(ConfigurationError):
        load_runtime_settings(validate_production=True)


def test_production_rejects_placeholder_secrets(monkeypatch):
    """Contract: Insecure placeholders (e.g., 'change-me', 'changeme') must be rejected in production."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "production")
    monkeypatch.setenv("AEGIS_JWT_PUBLIC_KEY", "change-me")
    monkeypatch.setenv("AEGIS_JWT_ISSUER", "https://auth.example.com")
    monkeypatch.setenv("AEGIS_JWT_AUDIENCE", "aegis-docintel")
    monkeypatch.delenv("AEGIS_API_KEYS", raising=False)

    with pytest.raises(ConfigurationError, match="Insecure placeholder"):
        load_runtime_settings(validate_production=True)
