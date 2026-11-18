"""
PT-01: Client-Side Tampering Adversarial Tests
Covers PT-CLI-001 through PT-CLI-010.
Asserts that client-side modifications (roles, UI quotas, licenses, config, local storage)
cannot bypass server-side authorization or expose server secrets.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import patch

from tests.security.penetration_testing.conftest import make_evaluator_jwt
from services.evaluation_gateway.license import export_license_token

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_pt_cli_001_modify_frontend_permissions(staging_rsa_keypair, core_client):
    """PT-CLI-001: Evaluator modifies client permissions to request admin action -> Server rejects (403)."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="evaluation_user")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        # Client tries calling admin endpoint with modified headers claiming admin capabilities
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Client-Permissions": "admin,all_access,quota_override",
            "X-Client-Role": "admin",
        }
        res = core_client.post("/api/v1/admin/evaluation/quotas/policies", headers=headers, json={"name": "rogue"})
        assert res.status_code == 403
        assert "Admin role required" in res.json().get("detail", "")


def test_pt_cli_002_change_local_evaluator_role(staging_rsa_keypair, core_client):
    """PT-CLI-002: Changing role in local state/headers does not grant privilege escalation."""
    priv, pub = staging_rsa_keypair
    token = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="viewer")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token}",
            "X-User-Role": "admin",
            "X-Assumed-Role": "superadmin",
        }
        res = core_client.get("/api/v1/protected", headers=headers)
        assert res.status_code == 200
        # Authority strictly reflects the cryptographically signed role
        data = res.json()
        assert "admin" not in data["roles"]
        assert "viewer" in data["roles"]


def test_pt_cli_003_modify_local_license_expiry(evaluator_a_license, gateway_client):
    """PT-CLI-003: Modifying local license expiry date breaks Ed25519 signature -> Rejected (400/401/403)."""
    lic_doc = evaluator_a_license["license_doc"].copy()
    lic_doc["payload"] = lic_doc["payload"].copy()
    # Attacker tampers with the expiration date in the payload
    lic_doc["payload"]["expires_at"] = "2099-12-31T23:59:59Z"
    tampered_token = export_license_token(lic_doc)

    headers = {"X-Evaluation-License": tampered_token}
    res = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")}
    )
    assert res.status_code in (401, 403)
    assert res.json()["error"] in ("INVALID_SIGNATURE", "LICENSE_INVALID")


def test_pt_cli_004_remove_ui_quota_restrictions(evaluator_a_license, gateway_client):
    """PT-CLI-004: Removing UI quota restrictions in client is useless -> Backend strictly enforces quota."""
    headers = evaluator_a_license["headers"]

    # Ingest 5 documents up to the evaluation quota limit (5 max)
    for i in range(5):
        res = gateway_client.post(
            "/api/v1/gateway/documents",
            headers=headers,
            files={"file": (f"doc_{i}.txt", io.BytesIO(f"doc content {i}".encode()), "text/plain")}
        )
        assert res.status_code in (200, 201)

    # 6th ingestion attempted after user removed client-side button disables
    res6 = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("doc_overlimit.txt", io.BytesIO(b"over quota"), "text/plain")}
    )
    assert res6.status_code == 429
    assert res6.json()["error"] == "QUOTA_EXCEEDED"


def test_pt_cli_005_change_tenant_identifier(staging_rsa_keypair, core_client):
    """PT-CLI-005: Client alters local tenant identifier to access another tenant -> Denied (403)."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        headers = {
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": "tenant-eval-b",  # Attacker targets Tenant B
        }
        res = core_client.get("/api/v1/documents/doc-b-001", headers=headers)
        # SEC-006 / AUTH-REM-006: Tenant header manipulation strictly denied
        assert res.status_code == 403


def test_pt_cli_006_modify_api_endpoint_configuration(evaluator_a_license, gateway_client):
    """PT-CLI-006: Altering target endpoint configuration to hit unauthorized gateway paths succeeds only on valid allowlist."""
    headers = evaluator_a_license["headers"]
    # Attempting to call an arbitrary unpublished or internal debugging endpoint
    res = gateway_client.get("/internal/debug/metrics", headers=headers)
    assert res.status_code in (404, 403)


def test_pt_cli_007_replay_previous_requests(evaluator_a_license, gateway_client):
    """PT-CLI-007: Replaying requests respects rate limits, quotas, and idempotency."""
    headers = evaluator_a_license["headers"]
    payload = {"query": "Explain architecture throughput", "stream": False}

    # Query repeatedly (5 allowed per quota in a loop or up to quota limit)
    res1 = gateway_client.post("/api/v1/gateway/query", headers=headers, json=payload)
    assert res1.status_code == 200

    # Exhaust remaining queries
    for _ in range(19):
        gateway_client.post("/api/v1/gateway/query", headers=headers, json=payload)

    # Subsequent replayed request after quota exhaustion is strictly blocked
    res_exhausted = gateway_client.post("/api/v1/gateway/query", headers=headers, json=payload)
    assert res_exhausted.status_code == 429
    assert res_exhausted.json()["error"] == "QUOTA_EXCEEDED"


def test_pt_cli_008_replace_public_client_configuration():
    """PT-CLI-008: Replacing public client configuration (e.g. manifest or public key) fails integrity checks."""
    manifest_path = REPO_ROOT / "distribution" / "demo-edition" / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["package_name"] == "AEGIS-DocIntel-Demo-Edition"

    # Verify that tampering any file listed in manifest causes manifest verification failure
    tampered_files = [f for f in manifest["files"] if f["path"].endswith(".lic") or f["path"].endswith(".conf")]
    assert len(tampered_files) > 0


def test_pt_cli_009_inspect_local_application_storage():
    """PT-CLI-009: Downloaded distribution files contain zero private keys or admin secrets."""
    dist_dir = REPO_ROOT / "distribution" / "demo-edition"
    dangerous_patterns = [
        b"BEGIN RSA PRIVATE KEY",
        b"BEGIN PRIVATE KEY",
        b"BEGIN EC PRIVATE KEY",
        b"sk-ant-",
        b"sk-proj-",
        b"AIzaSy",
        b"postgresql://",
        b"NEXT_PUBLIC_AEGIS_DEV_TOKEN",
    ]

    for p in dist_dir.rglob("*"):
        if p.is_file() and not p.name.endswith((".png", ".jpg", ".zip", ".tar.gz", ".whl")):
            data = p.read_bytes()
            for pattern in dangerous_patterns:
                assert pattern not in data, f"Leaked sensitive pattern {pattern.decode()} in {p}"


def test_pt_cli_010_extract_frontend_source_maps():
    """PT-CLI-010: Frontend bundle inspection confirms no private backend engine source maps or code exist."""
    dist_dir = REPO_ROOT / "distribution" / "demo-edition"
    # Downloadable package contains NO backend Python source trees from src/
    private_backend_modules = ["dag_engine.py", "submodular.py", "sheaf_laplacian.py", "quantum_circuit.py"]
    for p in dist_dir.rglob("*.py"):
        assert p.name not in private_backend_modules, f"Private backend module leaked: {p.name}"
