"""
src/core/settings.py
====================
Authoritative, validated runtime configuration for AEGIS-DocIntel.
Centralizes environment variable parsing, strict production invariants,
and security controls without exposing sensitive secrets in errors or logs.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ConfigurationError(RuntimeError):
    """Raised when application configuration violates security or operational invariants."""
    pass


def _get_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, "").strip().lower()
    if not val:
        return default
    return val in {"true", "1", "yes", "on"}


def _get_int(key: str, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    val_str = os.getenv(key, "").strip()
    if not val_str:
        return default
    try:
        val = int(val_str)
    except ValueError:
        raise ConfigurationError(f"Configuration key '{key}' must be an integer, got '{val_str}'")
    if min_val is not None and val < min_val:
        raise ConfigurationError(f"Configuration key '{key}' must be >= {min_val}, got {val}")
    if max_val is not None and val > max_val:
        raise ConfigurationError(f"Configuration key '{key}' must be <= {max_val}, got {val}")
    return val


def _get_float(key: str, default: float, min_val: Optional[float] = None) -> float:
    val_str = os.getenv(key, "").strip()
    if not val_str:
        return default
    try:
        val = float(val_str)
    except ValueError:
        raise ConfigurationError(f"Configuration key '{key}' must be a float, got '{val_str}'")
    if min_val is not None and val < min_val:
        raise ConfigurationError(f"Configuration key '{key}' must be >= {min_val}, got {val}")
    return val


@dataclass(frozen=True)
class RuntimeSettings:
    """Immutable, strongly-typed application runtime configuration."""
    environment: str = "development"
    database_path: str = "data/documents.db"
    max_upload_bytes: int = 200 * 1024 * 1024  # 200 MB
    request_timeout_seconds: float = 30.0
    max_concurrent_jobs: int = 10
    log_level: str = "INFO"
    enable_docs: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"])
    
    # Auth invariants
    jwt_public_key: Optional[str] = None
    jwt_public_key_path: Optional[str] = None
    jwt_issuer: Optional[str] = None
    jwt_audience: Optional[str] = None
    api_keys: Optional[str] = None
    
    # External data transfer policy
    llm_provider: str = "mock"
    allow_external_llm: bool = False
    
    # Observability
    enable_metrics: bool = True
    metrics_port: int = 9090
    pseudonymize_telemetry: bool = True


def load_runtime_settings(validate_production: bool = True) -> RuntimeSettings:
    """Load configuration from environment variables with strict validation."""
    env = os.getenv("AEGIS_ENVIRONMENT", "development").strip().lower()
    valid_envs = {"development", "test", "staging", "production"}
    if env not in valid_envs:
        raise ConfigurationError(
            f"Unsupported AEGIS_ENVIRONMENT: '{env}'. Must be one of {sorted(valid_envs)}"
        )

    log_level = os.getenv("AEGIS_LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError(f"Invalid AEGIS_LOG_LEVEL: '{log_level}'")

    db_path = os.getenv("AEGIS_SQLITE_PATH", "data/documents.db").strip()
    max_upload_bytes = _get_int("AEGIS_MAX_UPLOAD_BYTES", 200 * 1024 * 1024, min_val=1024)
    request_timeout = _get_float("AEGIS_REQUEST_TIMEOUT_SECONDS", 30.0, min_val=0.5)
    max_concurrent = _get_int("AEGIS_MAX_CONCURRENT_JOBS", 10, min_val=1, max_val=1000)

    # Docs: by default enabled in development/test, disabled in staging/production unless explicit
    default_enable_docs = (env in {"development", "test"})
    enable_docs = _get_bool("AEGIS_ENABLE_DOCS", default=default_enable_docs)

    # CORS origins
    raw_cors = os.getenv("AEGIS_CORS_ORIGINS", "")
    if raw_cors:
        cors_origins = [orig.strip() for orig in raw_cors.split(",") if orig.strip()]
    else:
        cors_origins = ["http://localhost:3000", "http://localhost:8080"]

    jwt_pub_key = os.getenv("AEGIS_JWT_PUBLIC_KEY")
    jwt_pub_key_path = os.getenv("AEGIS_JWT_PUBLIC_KEY_PATH")
    jwt_issuer = os.getenv("AEGIS_JWT_ISSUER")
    jwt_audience = os.getenv("AEGIS_JWT_AUDIENCE")
    api_keys = os.getenv("AEGIS_API_KEYS")

    llm_provider = os.getenv("AEGIS_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "mock")).strip().lower()
    allow_external_llm = _get_bool("AEGIS_ALLOW_EXTERNAL_LLM", default=False)

    settings = RuntimeSettings(
        environment=env,
        database_path=db_path,
        max_upload_bytes=max_upload_bytes,
        request_timeout_seconds=request_timeout,
        max_concurrent_jobs=max_concurrent,
        log_level=log_level,
        enable_docs=enable_docs,
        cors_origins=cors_origins,
        jwt_public_key=jwt_pub_key,
        jwt_public_key_path=jwt_pub_key_path,
        jwt_issuer=jwt_issuer,
        jwt_audience=jwt_audience,
        api_keys=api_keys,
        llm_provider=llm_provider,
        allow_external_llm=allow_external_llm,
        enable_metrics=_get_bool("AEGIS_ENABLE_METRICS", default=True),
        metrics_port=_get_int("AEGIS_METRICS_PORT", 9090, min_val=1024, max_val=65535),
        pseudonymize_telemetry=_get_bool("AEGIS_PSEUDONYMIZE_TELEMETRY", default=True),
    )

    if validate_production:
        validate_production_invariants(settings)

    return settings


def validate_production_invariants(settings: RuntimeSettings) -> None:
    """Enforce strict security and operational constraints in staging and production."""
    if settings.environment not in {"staging", "production"}:
        return

    # 1. Database path invariants
    if not settings.database_path or settings.database_path == ":memory:":
        raise ConfigurationError(
            f"In-memory database '{settings.database_path}' is forbidden in {settings.environment} mode"
        )
    db_file = Path(settings.database_path)
    parent = db_file.parent
    if parent and not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(
                f"Database directory '{parent}' cannot be created: {e}"
            )

    # 2. CORS security
    if "*" in settings.cors_origins:
        raise ConfigurationError(
            f"Wildcard CORS origin '*' is strictly forbidden in {settings.environment} mode"
        )

    # 3. JWT validation configuration
    has_jwt_key = bool(settings.jwt_public_key)
    if settings.jwt_public_key_path:
        key_path = Path(settings.jwt_public_key_path)
        if not key_path.exists():
            raise ConfigurationError(
                f"Configured AEGIS_JWT_PUBLIC_KEY_PATH file not found: {settings.jwt_public_key_path}"
            )
        has_jwt_key = True

    has_api_keys = bool(settings.api_keys)

    if not has_jwt_key and not has_api_keys:
        raise ConfigurationError(
            "Production mode requires at least one authenticated credential provider "
            "(AEGIS_JWT_PUBLIC_KEY / AEGIS_JWT_PUBLIC_KEY_PATH or AEGIS_API_KEYS)"
        )

    if has_jwt_key:
        if not settings.jwt_issuer:
            raise ConfigurationError("AEGIS_JWT_ISSUER is required in production mode")
        if not settings.jwt_audience:
            raise ConfigurationError("AEGIS_JWT_AUDIENCE is required in production mode")

    # 4. API keys hash-only validation
    if has_api_keys and settings.api_keys:
        for entry in settings.api_keys.split(";"):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":", 2)
            if len(parts) != 3:
                raise ConfigurationError(
                    "Invalid AEGIS_API_KEYS format. Expected 'tenant:role:hash'"
                )
            key_hash = parts[2]
            if not key_hash.startswith("sha256:") or len(key_hash) != 71 or not re.match(r"^sha256:[0-9a-f]{64}$", key_hash):
                raise ConfigurationError(
                    "Raw API keys in AEGIS_API_KEYS are forbidden in production; "
                    "keys must be stored as SHA-256 hashes ('sha256:<64-hex>')"
                )

    # 5. External data transfer & LLM provider invariants
    external_providers = {"openai", "anthropic", "google"}
    if settings.llm_provider in external_providers and not settings.allow_external_llm:
        raise ConfigurationError(
            f"External LLM provider '{settings.llm_provider}' requested in {settings.environment} "
            f"without explicit data-transfer authorization (AEGIS_ALLOW_EXTERNAL_LLM=true)"
        )
    if settings.llm_provider == "mock":
        raise ConfigurationError(
            f"Mock LLM provider is forbidden in {settings.environment} mode"
        )
