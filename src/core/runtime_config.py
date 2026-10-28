"""
src/core/runtime_config.py
==========================
AEGIS-DocIntel — Validated Runtime Configuration for Production Operations.
Enforces runtime boundaries, rate limits, request budgets, and environment safety.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import FrozenSet


VALID_ENVIRONMENTS: FrozenSet[str] = frozenset({
    "development",
    "test",
    "staging",
    "production",
})

VALID_LOG_LEVELS: FrozenSet[str] = frozenset({
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
})


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got '{raw}'") from exc
    if value < 1:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    environment: str
    request_timeout_seconds: int
    max_request_bytes: int
    max_question_chars: int
    max_top_k: int
    rate_limit_per_minute: int
    log_level: str

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        # Support both AEGIS_ENV and AEGIS_ENVIRONMENT
        raw_env = os.getenv("AEGIS_ENV")
        if raw_env is None:
            raw_env = os.getenv("AEGIS_ENVIRONMENT", "development")
        environment = raw_env.strip().lower()

        if environment not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"Unsupported environment '{environment}'. Must be one of {sorted(VALID_ENVIRONMENTS)}"
            )

        raw_log = os.getenv("AEGIS_LOG_LEVEL", "INFO").strip().upper()
        if raw_log not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log level '{raw_log}'. Must be one of {sorted(VALID_LOG_LEVELS)}"
            )

        return cls(
            environment=environment,
            request_timeout_seconds=_positive_int("AEGIS_REQUEST_TIMEOUT_SECONDS", 60),
            max_request_bytes=_positive_int("AEGIS_MAX_REQUEST_BYTES", 1048576),
            max_question_chars=_positive_int("AEGIS_MAX_QUESTION_CHARS", 4000),
            max_top_k=_positive_int("AEGIS_MAX_TOP_K", 20),
            rate_limit_per_minute=_positive_int("AEGIS_RATE_LIMIT_PER_MINUTE", 60),
            log_level=raw_log,
        )
