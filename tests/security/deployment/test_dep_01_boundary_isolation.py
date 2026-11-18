"""
Tests for PROT-FINAL-05: Network Boundary & Engine Isolation
Covers DEP-TEST-001, DEP-TEST-002, DEP-TEST-003, DEP-TEST-004, DEP-TEST-011, DEP-TEST-016
"""

import json
from pathlib import Path
import pytest

from src.gateway.request_context import TrustedInternalContext
from src.gateway.service_auth import GatewayServiceAuth
from src.gateway.upstream_client import PrivateEngineClient, UpstreamEngineError
from infrastructure.scripts.validate_deployment_manifests import validate_compose_file

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_dep_001_public_engine_port_scan():
    """DEP-TEST-001: Asserts that private engine has no public host port mappings."""
    compose_prod = REPO_ROOT / "infrastructure" / "compose" / "production" / "docker-compose.yml"
    assert compose_prod.exists()
    ok, violations = validate_compose_file(compose_prod)
    assert ok, f"Violations found: {violations}"

    text = compose_prod.read_text(encoding="utf-8")
    engine_section = text.split("\n  private-engine:")[1].split("\n  database:")[0]
    assert "expose:" in engine_section
    assert "8000" in engine_section
    # Must NOT have ports:
    assert "ports:" not in engine_section


def test_dep_002_direct_engine_request_rejected():
    """DEP-TEST-002: Direct request without valid internal service token is rejected."""
    auth = GatewayServiceAuth()
    
    # Missing token
    valid, err, _ = auth.verify_token("")
    assert not valid
    assert err == "MISSING_SERVICE_TOKEN"

    # Malformed token
    valid, err, _ = auth.verify_token("invalid-token-string")
    assert not valid
    assert err == "MALFORMED_SERVICE_TOKEN"

    # Forged token (tampered signature)
    ctx = TrustedInternalContext(
        principal_id="eval-user-1",
        tenant_id="tenant-1",
        license_id="lic-1",
        session_id="sess-1",
        device_id="dev-1",
        operation="intelligence.query",
    )
    raw_token = auth.issue_token(ctx)
    doc = json.loads(raw_token)
    doc["signature"] = "deadbeef" * 8  # Forged signature
    tampered_token = json.dumps(doc)

    valid, err, _ = auth.verify_token(tampered_token)
    assert not valid
    assert err == "INVALID_SERVICE_SIGNATURE"


def test_dep_003_evaluator_database_connection_denied():
    """DEP-TEST-003: Evaluator clients cannot directly connect to the private database."""
    compose_prod = REPO_ROOT / "infrastructure" / "compose" / "production" / "docker-compose.yml"
    text = compose_prod.read_text(encoding="utf-8")
    db_section = text.split("\n  database:")[1].split("\nnetworks:")[0]
    
    # Database is not exposed to public edge
    assert "public-edge" not in db_section
    assert "engine-data" in db_section
    assert "ports:" not in db_section

    # Check pg_hba.conf rules
    pg_hba = REPO_ROOT / "infrastructure" / "database" / "pg_hba.conf"
    assert pg_hba.exists()
    hba_text = pg_hba.read_text(encoding="utf-8")
    assert "host    all             all             all                     reject" in hba_text


def test_dep_004_gateway_to_engine_authentication():
    """DEP-TEST-004: Gateway-to-engine internal service authentication succeeds with valid signed context."""
    auth = GatewayServiceAuth()
    ctx = TrustedInternalContext(
        principal_id="eval-007",
        tenant_id="tenant-alpha",
        license_id="lic-eval-007",
        session_id="sess-007",
        device_id="dev-007",
        operation="intelligence.query",
        quota_reservation_id="res-007",
    )
    auth_doc = auth.issue_token(ctx)
    valid, err, payload = auth.verify_token(
        raw_token=auth_doc,
        expected_operation="intelligence.query",
        expected_tenant_id="tenant-alpha",
    )
    assert valid
    assert err is None
    assert payload["principal_id"] == "eval-007"
    assert payload["tenant_id"] == "tenant-alpha"
    assert payload["service_identity"] == "evaluation-gateway"


def test_dep_011_private_object_storage_access_denied():
    """DEP-TEST-011: Evaluator requests directly accessing storage internals are blocked."""
    net_policy_path = REPO_ROOT / "infrastructure" / "networking" / "network-policy.json"
    assert net_policy_path.exists()
    policy = json.loads(net_policy_path.read_text(encoding="utf-8"))
    
    # Ingress from 0.0.0.0/0 to internal databases/storage must be DENY
    deny_rules = [
        r for r in policy["rules"]
        if r.get("source") == "0.0.0.0/0" and r.get("action") == "DENY"
    ]
    assert len(deny_rules) >= 2


def test_dep_016_unauthorized_internal_network_connection_denied():
    """DEP-TEST-016: Network policy blocks unauthorized inter-service communication."""
    net_policy_path = REPO_ROOT / "infrastructure" / "networking" / "network-policy.json"
    policy = json.loads(net_policy_path.read_text(encoding="utf-8"))
    
    # Outbound from private-engine to non-whitelisted destinations is denied
    egress_denies = [
        r for r in policy["rules"]
        if r.get("direction") == "egress" and r.get("action") == "DENY"
    ]
    assert len(egress_denies) >= 1
