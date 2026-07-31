"""Centralized configuration via pydantic-settings.

Replaces ad-hoc os.environ reads scattered across the codebase.
Validation at startup prevents silent misconfiguration.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AMDISettings(BaseSettings):
    """Validated runtime configuration."""

    model_config = SettingsConfigDict(
        env_prefix="AMDI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_log_level: Literal["debug", "info", "warning", "error"] = "info"
    api_cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # ── Storage ──────────────────────────────────────────────────────────────
    storage_backend: Literal["memory", "filesystem", "s3"] = "filesystem"
    storage_root: Path = Path("./.amdi_data")
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB

    # ── Async job queue ──────────────────────────────────────────────────────
    queue_backend: Literal["memory", "arq"] = "arq"
    redis_url: str = "redis://localhost:6379/0"
    worker_concurrency: int = 4
    job_max_retries: int = 3
    job_default_timeout_s: int = 1800      # 30 min hard ceiling
    job_soft_timeout_s: int = 1500        # soft warn threshold
    job_keep_results_s: int = 86_400      # 24h

    # ── SSE / streaming ─────────────────────────────────────────────────────
    sse_heartbeat_s: int = 15            # keepalive ping interval
    sse_buffer_max_events: int = 1024
    sse_backpressure_timeout_s: float = 5.0

    # ── Ingestion limits ────────────────────────────────────────────────────
    allowed_mime: tuple[str, ...] = (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/html",
        "text/markdown",
        "text/plain",
        "image/png",
        "image/jpeg",
        "image/tiff",
        "audio/wav",
        "audio/mpeg",
        "audio/flac",
        "audio/ogg",
        "audio/x-m4a",
    )

    # ── Retrieval ────────────────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    retrieval_top_k: int = 10
    enable_reranker: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── Token budget ────────────────────────────────────────────────────────
    default_token_budget: int = 8000
    max_token_budget: int = 200_000

    # ── Security ─────────────────────────────────────────────────────────────
    jwt_secret: str = "INSECURE-DEV-SECRET-CHANGE-ME-MUST-BE-32-BYTES"

    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 60
    password_min_length: int = 12
    max_login_failures_per_minute: int = 5
    enable_audit_chain: bool = True
    audit_backend: Literal["file", "stdout"] = "file"

    # ── Rate limiting ──────────────────────────────────────────────────────────
    rate_limit_per_minute: int = 600
    rate_limit_window_s: int = 60

    # ── Observability ────────────────────────────────────────────────────────
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_json: bool = False
    service_name: str = "amdi"
    otlp_endpoint: str | None = None


    @field_validator("storage_root")
    @classmethod
    def _ensure_storage_root(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("max_token_budget")
    @classmethod
    def _budget_sane(cls, v: int) -> int:
        if v < 1000 or v > 2_000_000:
            raise ValueError("max_token_budget must be in [1000, 2_000_000]")
        return v

    @field_validator("redis_url")
    @classmethod
    def _redis_is_url(cls, v: str) -> str:
        if not v.startswith(("redis://", "rediss://", "unix://")):
            raise ValueError("redis_url must be redis://, rediss://, or unix://")
        return v


@lru_cache(maxsize=1)
def get_settings() -> AMDISettings:
    """Process-wide singleton (cheap to call repeatedly)."""
    return AMDISettings()


__all__ = ["AMDISettings", "get_settings"]
