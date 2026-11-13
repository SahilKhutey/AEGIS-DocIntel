"""
AEGIS Evaluation Security Tests — Adversarial Attack Scenarios (PROT-04 Section 9)
Covers the four required adversarial negative attack vectors:
- Scenario A: Frontend privilege escalation attempts
- Scenario B: License file tampering
- Scenario C: Real-time revocation propagation (< 1 second SLA)
- Scenario D: High-concurrency quota race conditions
"""

import concurrent.futures
import copy
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.license import issue_evaluation_license, export_license_token
from services.evaluation_gateway.quotas import quota_manager
from services.evaluation_gateway.revocation import registry as revocation_registry


def test_adversarial_a_frontend_privilege_escalation(client: TestClient):
    """
    Scenario A: Attacker activates a viewer/evaluator account, modifies local storage claims,
    injects administrator headers, and directly targets administrative APIs.
    Expected: Backend authoritatively denies access with HTTP 403 Forbidden.
    """
    # 1. Activate evaluator
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "attacker_device_key"},
    )
    token = res.json()["session"]["access_token"]

    # 2. Forge admin role and tenant headers
    malicious_headers = {
        "Authorization": f"Bearer {token}",
        "X-User-Role": "admin",
        "X-Tenant-Role": "platform_admin",
        "X-Workspace-ID": "ws-system-admin",
    }

    # 3. Call administrative API
    res_admin1 = client.post("/v1/admin/users", headers=malicious_headers, json={"user": "attacker"})
    assert res_admin1.status_code == 403
    assert res_admin1.json()["error"] == "FEATURE_NOT_ENTITLED"

    res_admin2 = client.post("/v1/admin/platform/config", headers=malicious_headers, json={"setting": "override"})
    assert res_admin2.status_code == 403


def test_adversarial_b_license_file_tampering(client: TestClient):
    """
    Scenario B: Attacker obtains a valid evaluation license, edits expiration date or adds
    administrative entitlements in the JSON structure, and attempts to authenticate.
    Expected: Cryptographic Ed25519 verification fails with HTTP 401 INVALID_SIGNATURE.
    """
    lic = issue_evaluation_license(user_id="legit-evaluator", duration_days=14)

    # Attacker extends expiration to year 2099 and adds platform.admin
    tampered = copy.deepcopy(lic)
    tampered["payload"]["expires_at"] = "2099-12-31T23:59:59Z"
    tampered["payload"]["entitlements"].append("platform.admin")
    tampered_token = export_license_token(tampered)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": tampered_token})
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_SIGNATURE"


def test_adversarial_c_revocation_sla(client: TestClient):
    """
    Scenario C: Attacker activates valid license, starts session, then license is revoked.
    Expected: Immediate denial (< 1 second) on next protected request.
    """
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-BETA-TEST", "device_public_key": "revocation_sla_key"},
    )
    token = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify session is operational
    res1 = client.get("/v1/evaluation/session", headers=headers)
    assert res1.status_code == 200

    # Administrative revocation
    revocation_registry.revoke(lic_id)

    # Next request immediately rejected
    res2 = client.get("/v1/evaluation/session", headers=headers)
    assert res2.status_code == 403
    assert res2.json()["error"] == "LICENSE_REVOKED"


def test_adversarial_d_quota_race_condition_concurrency(client: TestClient, valid_eval_license):
    """
    Scenario D: Concurrency race condition probe.
    Simultaneously dispatch 20 parallel requests against an endpoint with remaining quota of 2.
    Expected: Exactly 2 requests succeed; exactly 18 fail with HTTP 429. Zero quota leakage.
    """
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # Pre-consume 18 of 20 queries so exactly 2 remain
    for _ in range(18):
        quota_manager.record_query(lic_id, max_limit=20)

    results = []

    def run_query(i):
        res = client.post(
            "/v1/evaluation/query",
            headers=headers,
            json={"query": f"Concurrent burst test {i}"},
        )
        return res.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(run_query, i) for i in range(20)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    accepted = results.count(200)
    rejected = results.count(429)

    assert accepted == 2, f"Race condition permitted {accepted} operations when quota was 2!"
    assert rejected == 18, f"Expected 18 rejections with 429, got {rejected}"
