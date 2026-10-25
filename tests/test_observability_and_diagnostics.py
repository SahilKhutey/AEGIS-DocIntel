"""
tests/test_observability_and_diagnostics.py
===========================================
Verification suite for P3.2:
1. Request ID sanitization, extraction, and propagation (X-Request-ID).
2. Request latency reporting (X-Response-Time-ms).
3. Sensitive data scrubbing in structured logs (tokens, credentials, raw text).
4. Tenant pseudonymization for safe aggregate telemetry.
5. Structured JSON log formatting.
"""
from __future__ import annotations

import io
import json
import logging
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import structlog
from fastapi.testclient import TestClient

from src.main import create_app
from src.observability.logging import (
    SENSITIVE_KEYS,
    configure_logging,
    pseudonymize_tenant,
    redact_sensitive_log_fields,
)
from src.services.container import ServiceContainer


@pytest.fixture
def test_client():
    with patch.object(ServiceContainer, "startup", new_callable=AsyncMock):
        app = create_app()
        with TestClient(app) as client:
            yield client


def test_request_id_generated_when_missing(test_client):
    """When client supplies no X-Request-ID, server generates a valid UUID."""
    res = test_client.get("/health")
    assert res.status_code in (200, 503)
    req_id = res.headers.get("X-Request-ID")
    assert req_id is not None
    # Validate it's a valid UUID
    uuid_obj = uuid.UUID(req_id)
    assert str(uuid_obj) == req_id


def test_request_id_propagated_when_valid(test_client):
    """When client supplies valid alphanumeric X-Request-ID, server preserves it."""
    custom_id = "test-client-trace-12345"
    res = test_client.get("/health", headers={"X-Request-ID": custom_id})
    assert res.status_code in (200, 503)
    assert res.headers.get("X-Request-ID") == custom_id


def test_request_id_sanitized_when_malicious_or_too_long(test_client):
    """Invalid characters or overly long Request IDs are safely replaced by a UUID."""
    # Malicious/injection attempt
    res_malicious = test_client.get("/health", headers={"X-Request-ID": "<script>alert(1)</script>"})
    bad_id = res_malicious.headers.get("X-Request-ID")
    assert bad_id != "<script>alert(1)</script>"
    uuid.UUID(bad_id)  # must parse as valid UUID

    # Overly long header (>64 chars)
    long_id = "a" * 80
    res_long = test_client.get("/health", headers={"X-Request-ID": long_id})
    assigned_id = res_long.headers.get("X-Request-ID")
    assert assigned_id != long_id
    uuid.UUID(assigned_id)


def test_response_time_header_present(test_client):
    """Every response includes an X-Response-Time-ms latency metric."""
    res = test_client.get("/health")
    resp_time_header = res.headers.get("X-Response-Time-ms")
    assert resp_time_header is not None
    latency = float(resp_time_header)
    assert latency >= 0.0


def test_tenant_pseudonymization_format_and_properties():
    """Verify tenant pseudonymization is deterministic, irreversible, and prefixed."""
    p1 = pseudonymize_tenant("tenant-enterprise-alpha")
    p2 = pseudonymize_tenant("tenant-enterprise-alpha")
    p3 = pseudonymize_tenant("tenant-enterprise-beta")

    assert p1 == p2, "Pseudonymization must be deterministic for identical tenants"
    assert p1 != p3, "Different tenants must produce distinct pseudonyms"
    assert p1.startswith("t_"), "Pseudonym must use 't_' prefix"
    assert len(p1) == 14, "Pseudonym must be prefix + 12 hex chars"

    # Edge cases
    assert pseudonymize_tenant("") == "anonymous"
    assert pseudonymize_tenant(None) == "anonymous"


def test_sensitive_log_field_redaction():
    """Verify structlog processor scrubs secrets, credentials, and raw text."""
    dummy_event = {
        "event": "document_uploaded",
        "doc_id": "doc-1234",
        "status": "success",
        "tenant_id": "tenant-corp",
        "authorization": "Bearer eyJhbGciOi...",
        "api_key": "sec_k1_abcdef1234567890",
        "jwt": "eyJhbGciOi...",
        "token": "secret-session-token",
        "password": "SuperSecretPassword123!",
        "raw_bytes": b"CONFIDENTIAL PATIENT RECORD DATA",
        "document_text": "Sensitive unredacted contract terms",
        "credit_card": "4111-2222-3333-4444",
        "ssn": "000-12-3456",
    }

    cleaned = redact_sensitive_log_fields(None, "info", dummy_event)

    # Safe fields preserved
    assert cleaned["event"] == "document_uploaded"
    assert cleaned["doc_id"] == "doc-1234"
    assert cleaned["status"] == "success"

    # Sensitive fields redacted
    for field in (
        "authorization", "api_key", "jwt", "token", "password",
        "raw_bytes", "document_text", "credit_card", "ssn",
    ):
        assert cleaned[field] == "[REDACTED]", f"Field {field} was not redacted"

    # Raw tenant_id removed and replaced by pseudonym
    assert "tenant_id" not in cleaned
    assert "tenant_id_hash" in cleaned
    assert cleaned["tenant_id_hash"].startswith("t_")


def test_structured_json_logging_output():
    """Verify configure_logging(force_json=True) formats logs as valid parseable JSON."""
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)

    # Configure structured logging in JSON mode
    configure_logging(level="INFO", force_json=True)
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    logger = structlog.get_logger("test_observability")
    logger.info(
        "processing_event",
        doc_id="test-doc-999",
        page_count=5,
        api_key="leaked_key_test",
        tenant_id="client-xyz",
    )

    output = log_capture.getvalue().strip()
    assert output, "Log output should not be empty"

    # Must parse as valid JSON
    log_record = json.loads(output)
    assert log_record["event"] == "processing_event"
    assert log_record["doc_id"] == "test-doc-999"
    assert log_record["page_count"] == 5
    assert log_record["api_key"] == "[REDACTED]"
    assert log_record["tenant_id_hash"].startswith("t_")
    assert "client-xyz" not in output, "Raw tenant ID should not appear in JSON log"
