"""
Tests for PROT-FINAL-05: Health Probes & Outage Resilience
Covers DEP-TEST-013, DEP-TEST-015
"""

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from src.gateway.upstream_client import PrivateEngineClient, UpstreamEngineError
from src.gateway.request_context import TrustedInternalContext
from src.gateway.response_sanitizer import response_sanitizer
from infrastructure.monitoring.health_monitor import audit_health_response

client = TestClient(app)


def test_dep_013_engine_and_db_outage_fails_closed():
    """DEP-TEST-013: When downstream engine or database fails, gateway fails closed without disclosing tracebacks."""
    engine_client = PrivateEngineClient()
    engine_client.set_availability(False)

    ctx = TrustedInternalContext(
        principal_id="eval-user",
        tenant_id="tenant-outage",
        license_id="lic-outage",
        session_id="sess-outage",
        device_id="dev-outage",
        operation="intelligence.query",
    )

    with pytest.raises(UpstreamEngineError) as exc_info:
        engine_client.forward_request(ctx, {"query": "What is the TDP?"})

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "ENGINE_UNAVAILABLE"

    # Verify sanitized error payload
    sanitized_err = response_sanitizer.sanitize_error(exc_info.value, request_id=ctx.request_id)
    assert sanitized_err["status"] == "FAILED"
    assert "Traceback" not in sanitized_err["message"]
    assert "File \"" not in sanitized_err["message"]


def test_dep_015_health_endpoints_zero_infrastructure_disclosure():
    """DEP-TEST-015: Health probes (/health/live, /health/ready) disclose operational status without leaking sensitive data."""
    # 1. /health/live
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    data_live = res_live.json()
    assert data_live["status"] == "healthy"
    audit_live = audit_health_response(data_live)
    assert audit_live.is_safe, f"Disclosures found in /health/live: {audit_live.violations}"

    # 2. /health/ready
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    data_ready = res_ready.json()
    assert data_ready["status"] == "ready"
    audit_ready = audit_health_response(data_ready)
    assert audit_ready.is_safe, f"Disclosures found in /health/ready: {audit_ready.violations}"

    # 3. Simulate an error payload with accidental IP/DB disclosure and verify sanitizer redacts it
    leaky_payload = {
        "status": "degraded",
        "db_host": "10.0.4.15",
        "connection_string": "postgresql://aegis_app:secret123@172.18.0.5:5432/aegis",
        "message": "Failed to connect to 192.168.1.100",
    }
    cleaned = response_sanitizer.sanitize_payload(leaky_payload)
    audit_cleaned = audit_health_response(cleaned)
    assert audit_cleaned.is_safe, f"Sanitizer failed to clean leaky payload: {audit_cleaned.violations}"
    assert "db_host" not in cleaned
    assert "connection_string" not in cleaned
    assert "[REDACTED_INTERNAL_IP]" in cleaned["message"]
