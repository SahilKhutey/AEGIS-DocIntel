"""
PT-08: Private Engine Isolation Adversarial Tests
Covers PT-ENG-001 through PT-ENG-010.
Asserts that private algorithms (submodular, sheaf, topological analysis), internal orchestration,
private model weights/prompts, and backend engines are completely isolated from client access.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from unittest.mock import patch

from tests.security.penetration_testing.conftest import make_evaluator_jwt

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_pt_eng_001_direct_access_internal_network_endpoint(evaluator_a_license, gateway_client):
    """PT-ENG-001: Client attempting direct call to internal engine socket/endpoint is denied."""
    headers = evaluator_a_license["headers"]
    internal_endpoints = [
        "/engine/v1/orchestrate",
        "/internal/v1/dag/execute",
        "/engine/private/prompt",
    ]
    for ep in internal_endpoints:
        res = gateway_client.get(ep, headers=headers)
        assert res.status_code in (403, 404)


def test_pt_eng_002_engine_calls_without_service_auth(core_client):
    """PT-ENG-002: Direct engine execution requires internal service mutual TLS / service token; raw calls rejected."""
    # Attempting to call query pipeline without any service identity
    res = core_client.post("/api/v1/query", json={"query": "test"})
    assert res.status_code == 401


def test_pt_eng_003_engine_calls_using_evaluator_credentials(staging_rsa_keypair, core_client):
    """PT-ENG-003: Evaluator JWT lacks internal service scope; engine administrative routes rejected (403)."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="evaluation_user")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post(
            "/api/v1/admin/evaluation/quotas/policies",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "test"}
        )
        assert res.status_code == 403


def test_pt_eng_004_reuse_expired_internal_service_tokens(staging_rsa_keypair, core_client):
    """PT-ENG-004: Internal service tokens past their TTL are rejected immediately (401)."""
    priv, pub = staging_rsa_keypair
    expired_srv_tok = make_evaluator_jwt(
        priv, tenant_id="tenant-system", user_id="service-engine",
        role="service_account", exp_delta=-3600
    )

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {expired_srv_tok}"})
        assert res.status_code == 401


def test_pt_eng_005_modify_gateway_tenant_context(staging_rsa_keypair, core_client):
    """PT-ENG-005: Client attempting to inject synthetic gateway internal context headers is rejected."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Gateway-Internal-Tenant": "tenant-superadmin",
            "X-Internal-Service-Identity": "aegis-core-engine",
        }
        res = core_client.get("/api/v1/protected", headers=headers)
        assert res.status_code == 200
        # Authority strictly reflects authenticated token, internal headers ignored
        assert res.json()["tenant_id"] == "tenant-eval-a"


def test_pt_eng_006_access_private_prompts_or_orchestration(evaluator_a_license, gateway_client):
    """PT-ENG-006: Probing endpoints for system prompts, decomposition templates, or orchestration rules is denied."""
    headers = evaluator_a_license["headers"]
    prompt_routes = [
        "/api/v1/prompts/system",
        "/engine/prompts/decomposition",
        "/api/internal/rag/prompts",
    ]
    for r in prompt_routes:
        res = gateway_client.get(r, headers=headers)
        assert res.status_code in (403, 404)


def test_pt_eng_007_download_private_model_configuration(evaluator_a_license, gateway_client):
    """PT-ENG-007: Probing for private neural weights, embedding checkpoints, or model configs is denied."""
    headers = evaluator_a_license["headers"]
    res = gateway_client.get("/api/v1/models/weights/config.json", headers=headers)
    assert res.status_code in (403, 404)


def test_pt_eng_008_access_internal_debugging_endpoints(evaluator_a_license, gateway_client):
    """PT-ENG-008: Profiling, heap dumps, debug traces, and stack introspections are blocked in evaluation edition."""
    headers = evaluator_a_license["headers"]
    debug_endpoints = [
        "/debug/pprof",
        "/debug/vars",
        "/api/debug/dump",
        "/metrics/internal",
    ]
    for ep in debug_endpoints:
        res = gateway_client.get(ep, headers=headers)
        assert res.status_code in (403, 404)


def test_pt_eng_009_path_traversal_into_proprietary_packages(evaluator_a_license, gateway_client):
    """PT-ENG-009: Attempting path traversal on file ingestion to leak private engine files is strictly rejected (400)."""
    headers = evaluator_a_license["headers"]
    traversal_filenames = [
        "../../src/core/dag_engine.py",
        "....//....//src/security/license_signing.py",
        "/etc/passwd",
        "..\\..\\src\\main.py",
    ]
    for fname in traversal_filenames:
        res = gateway_client.post(
            "/api/v1/gateway/documents",
            headers=headers,
            files={"file": (fname, io.BytesIO(b"malicious traversal payload"), "text/plain")}
        )
        assert res.status_code in (400, 403, 404)
        if res.status_code == 400:
            assert res.json().get("error") in ("INVALID_FILENAME", "PATH_TRAVERSAL_DETECTED", "UNSUPPORTED_MEDIA_TYPE")


def test_pt_eng_010_validate_zero_private_engine_in_client_bundle():
    """PT-ENG-010: Client distribution bundle contains zero proprietary engine source files."""
    dist_dir = REPO_ROOT / "distribution" / "demo-edition"
    proprietary_files = [
        "dag_engine.py",
        "submodular_optimizer.py",
        "sheaf_laplacian.py",
        "quantum_circuit.py",
        "orchestration_engine.py",
    ]
    for p in dist_dir.rglob("*.py"):
        assert p.name not in proprietary_files, f"Leaked proprietary engine file in distribution: {p}"
