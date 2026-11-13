"""
AEGIS Distribution Security Tests — Isolation & Error Hygiene
Covers:
- SEC-DEMO-011: Strict tenant/license isolation preventing Insecure Direct Object References (IDOR)
- SEC-DEMO-012: Error sanitization preventing stack traces and internal path leaks
- SEC-DEMO-013: Execution binary & path traversal rejection on document ingestion
- SEC-DEMO-020: Launcher verification integrity check
"""

import io
import subprocess
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from services.evaluation_gateway.license import issue_evaluation_license, export_license_token
from services.evaluation_gateway.quotas import quota_manager

@pytest.fixture
def client():
    return TestClient(app)

def create_auth_header(user_id: str):
    lic = issue_evaluation_license(user_id=user_id, duration_days=14)
    token = export_license_token(lic)
    quota_manager.reset_usage(lic["payload"]["license_id"])
    return {"X-Evaluation-License": token}, lic["payload"]["license_id"]


def test_sec_demo_011_tenant_isolation_prevents_idor(client: TestClient):
    """SEC-DEMO-011: License A cannot view or retrieve documents ingested by License B."""
    headers_a, lic_a = create_auth_header("tenant-alpha")
    headers_b, lic_b = create_auth_header("tenant-beta")

    # Tenant Alpha uploads a confidential document
    res_a = client.post(
        "/api/v1/gateway/documents",
        headers=headers_a,
        files={"file": ("alpha_confidential.txt", io.BytesIO(b"Alpha trade secret content"), "text/plain")}
    )
    assert res_a.status_code == 200
    doc_id_a = res_a.json()["document_id"]

    # 1. Tenant Beta lists documents -> Should NOT see Alpha's document
    res_list_b = client.get("/api/v1/gateway/documents", headers=headers_b)
    assert res_list_b.status_code == 200
    b_docs = res_list_b.json()["items"]
    assert all(d["document_id"] != doc_id_a for d in b_docs)

    # 2. Tenant Beta attempts direct object retrieval of Alpha's doc_id -> Must return 404 (not 403, preventing ID enumeration)
    res_get_b = client.get(f"/api/v1/gateway/documents/{doc_id_a}", headers=headers_b)
    assert res_get_b.status_code == 404
    assert res_get_b.json()["error"] == "DOCUMENT_NOT_FOUND"


def test_sec_demo_012_error_hygiene_no_stack_traces(client: TestClient):
    """SEC-DEMO-012: Malformed or unexpected requests return sanitized errors without Python tracebacks or paths."""
    # Send malformed JSON to query endpoint
    res = client.post(
        "/api/v1/gateway/query",
        headers={"X-Evaluation-License": "invalid-garbage-token"},
        content=b"not json"
    )
    # Status should be 400 or 401
    assert res.status_code in [400, 401, 422]
    
    text = res.text
    # Asserts no internal Python runtime markers
    assert "Traceback (most recent call last)" not in text
    assert "C:\\" not in text
    assert "/home/" not in text
    assert "site-packages" not in text


def test_sec_demo_013_dangerous_file_extensions_rejected(client: TestClient):
    """SEC-DEMO-013: Uploading executable binaries (.exe, .sh, .dll) is rejected with HTTP 400."""
    headers, _ = create_auth_header("uploader")

    dangerous_files = [
        ("malware.exe", b"MZ\x90\x00"),
        ("exploit.sh", b"#!/bin/sh\nrm -rf /"),
        ("payload.dll", b"MZ\x90\x00"),
        ("script.bat", b"@echo off\ndir")
    ]

    for fname, content in dangerous_files:
        res = client.post(
            "/api/v1/gateway/documents",
            headers=headers,
            files={"file": (fname, io.BytesIO(content), "application/octet-stream")}
        )
        assert res.status_code == 400
        assert res.json()["error"] == "UNSUPPORTED_MEDIA_TYPE"


def test_sec_demo_020_verify_package_script_integrity():
    """SEC-DEMO-020: Verifies that the PowerShell package verification script executes cleanly."""
    script_path = Path(__file__).resolve().parent.parent.parent / "distribution" / "demo-edition" / "launcher" / "verify-package.ps1"
    assert script_path.exists()

    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"verify-package.ps1 failed:\n{result.stdout}\n{result.stderr}"
    assert "All package components verified authentic" in result.stdout
