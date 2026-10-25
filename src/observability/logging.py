"""
src/observability/logging.py
============================
Structured operational logging for AEGIS-DocIntel:
1. Standardized JSON schema for machine ingestion.
2. Sensitive field redaction (removes credentials, raw text, and JWTs).
3. Pseudonymized tenant identifiers for safe aggregate observability.
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
from typing import Any, Dict

import structlog

# Sensitive keys that must NEVER be written to logs
SENSITIVE_KEYS = frozenset({
    "authorization",
    "token",
    "jwt",
    "api_key",
    "password",
    "secret",
    "raw_bytes",
    "document_text",
    "extracted_text",
    "prompt",
    "credit_card",
    "ssn",
})


def pseudonymize_tenant(tenant_id: str, salt: str = "aegis-telemetry-salt") -> str:
    """Computes a non-reversible, pseudonymous monitoring label for tenant identity."""
    if not tenant_id:
        return "anonymous"
    salted = f"{salt}:{tenant_id}".encode("utf-8")
    return f"t_{hashlib.sha256(salted).hexdigest()[:12]}"


def redact_sensitive_log_fields(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Structlog processor scrubbing credentials, secrets, and raw text from log records."""
    clean_dict: Dict[str, Any] = {}
    for key, val in event_dict.items():
        k_lower = key.lower()
        if any(s in k_lower for s in SENSITIVE_KEYS):
            clean_dict[key] = "[REDACTED]"
        elif k_lower == "tenant_id":
            # Mask or pseudonymize raw tenant ID in logs
            clean_dict["tenant_id_hash"] = pseudonymize_tenant(str(val))
        else:
            clean_dict[key] = val
    return clean_dict


def configure_logging(level: str = "INFO", force_json: bool = False) -> None:
    """Configure structlog + stdlib logging with security-hardened processors."""
    env = os.getenv("AEGIS_ENVIRONMENT", "development").lower()
    use_json = force_json or (env in {"staging", "production"})

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        redact_sensitive_log_fields,
        structlog.processors.UnicodeDecoder(),
        (
            structlog.processors.JSONRenderer()
            if use_json
            else structlog.dev.ConsoleRenderer(colors=True)
        ),
    ]

    structlog.reset_defaults()
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )
    logging.getLogger().setLevel(log_level)


__all__ = [
    "configure_logging",
    "pseudonymize_tenant",
    "redact_sensitive_log_fields",
    "SENSITIVE_KEYS",
]
