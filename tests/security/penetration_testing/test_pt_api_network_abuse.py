"""
Adversarial Penetration Testing Suite — API & Network Abuse
PROT-FINAL-03: Workstream 10 (PT-API-001 through PT-API-020)

Validates API defense-in-depth, input validation, SQL/NoSQL injection resistance,
XSS mitigation, SSRF immunity, header injection protection, CORS controls,
and defensive response header enforcement.
"""

from __future__ import annotations

import io
import json
import pytest
from fastapi.testclient import TestClient


def test_pt_api_001_http_verb_tampering(evaluator_a_license, gateway_client):
    """PT-API-001: Submitting inappropriate HTTP verbs to POST-only endpoint returns 405 Method Not Allowed."""
    headers = evaluator_a_license["headers"]
    
    # Target endpoint /api/v1/gateway/query is POST-only
    res_get = gateway_client.get("/api/v1/gateway/query", headers=headers)
    assert res_get.status_code == 405

    res_put = gateway_client.put("/api/v1/gateway/query", headers=headers, json={"query": "test"})
    assert res_put.status_code == 405

    res_delete = gateway_client.delete("/api/v1/gateway/query", headers=headers)
    assert res_delete.status_code == 405


def test_pt_api_002_content_type_manipulation(evaluator_a_license, gateway_client):
    """PT-API-002: Sending incompatible Content-Type to JSON endpoints is rejected with 415 or 422."""
    headers = {**evaluator_a_license["headers"], "Content-Type": "text/xml"}
    xml_payload = "<query>What is the thermal design power?</query>"
    
    res = gateway_client.post("/api/v1/gateway/query", headers=headers, content=xml_payload)
    assert res.status_code in (415, 422)


def test_pt_api_003_malformed_json_syntax(evaluator_a_license, gateway_client):
    """PT-API-003: Submitting truncated or corrupted JSON returns 422 Unprocessable Entity."""
    headers = {**evaluator_a_license["headers"], "Content-Type": "application/json"}
    corrupt_json = '{"query": "unterminated string, missing closing bracket'
    
    res = gateway_client.post("/api/v1/gateway/query", headers=headers, content=corrupt_json)
    assert res.status_code == 422


def test_pt_api_004_giant_payload_rejection(evaluator_a_license, gateway_client):
    """PT-API-004: Sending an oversized query payload exceeding maximum schema limits is rejected."""
    headers = evaluator_a_license["headers"]
    oversized_query = "A" * 50000  # Schema max_length is 1000
    
    res = gateway_client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": oversized_query}
    )
    assert res.status_code == 422


def test_pt_api_005_deeply_nested_json_recursion(evaluator_a_license, gateway_client):
    """PT-API-005: Deeply nested JSON structures do not cause stack overflow or service termination."""
    headers = evaluator_a_license["headers"]
    
    # Build a 100-level deeply nested JSON object
    nested = {"key": "leaf"}
    for _ in range(100):
        nested = {"nested": nested}
    
    # Pass nested structure where a simple query string was expected
    res = gateway_client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": nested}
    )
    assert res.status_code == 422


def test_pt_api_006_sql_injection_query_strings(evaluator_a_license, gateway_client):
    """PT-API-006: Classic and advanced SQL injection payloads are safely sanitized and treated as literal text."""
    headers = evaluator_a_license["headers"]
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE documents; --",
        "' UNION SELECT username, password FROM users --",
        "1; WAITFOR DELAY '0:0:5'--",
    ]
    for sqli in sqli_payloads:
        res = gateway_client.post(
            "/api/v1/gateway/query",
            headers=headers,
            json={"query": sqli}
        )
        # Should execute query safely or return 200 without leaking DB errors or crashing
        assert res.status_code in (200, 400, 422)
        if res.status_code == 200:
            data = res.json()
            assert "SELECT" not in data.get("answer", "")
            assert "error" not in data


def test_pt_api_007_nosql_json_injection(evaluator_a_license, gateway_client):
    """PT-API-007: NoSQL / MongoDB operator injection payloads are safely handled or rejected."""
    headers = evaluator_a_license["headers"]
    res = gateway_client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": {"$gt": ""}}
    )
    assert res.status_code == 422


def test_pt_api_008_xss_payload_escaping(evaluator_a_license, gateway_client):
    """PT-API-008: Stored and reflected XSS script tags are sanitized / escaped in API responses."""
    headers = evaluator_a_license["headers"]
    xss_payload = "<script>alert('AEGIS_XSS')</script><img src=x onerror=alert(1)>"
    
    res = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("safe_name.txt", io.BytesIO(xss_payload.encode()), "text/plain")}
    )
    assert res.status_code == 200
    
    # Query referencing the document
    q_res = gateway_client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": "test query"}
    )
    assert q_res.status_code == 200
    # Confirm no executable HTML rendering in JSON string response
    assert "<script>alert('AEGIS_XSS')</script>" not in q_res.text or q_res.headers.get("content-type", "").startswith("application/json")


def test_pt_api_009_path_traversal_document_ids(evaluator_a_license, gateway_client):
    """PT-API-009: Path traversal in document IDs (/documents/../../etc/passwd) is rejected or isolated."""
    headers = evaluator_a_license["headers"]
    res = gateway_client.get(
        "/api/v1/gateway/documents/../../etc/passwd",
        headers=headers
    )
    assert res.status_code in (400, 404)


def test_pt_api_010_null_byte_injection(evaluator_a_license, gateway_client):
    """PT-API-010: Null byte injection in uploaded filenames is cleanly rejected."""
    headers = evaluator_a_license["headers"]
    res = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("test.pdf\x00.exe", io.BytesIO(b"data"), "application/pdf")}
    )
    # Rejection due to null byte or extension validation
    assert res.status_code in (400, 422)


def test_pt_api_011_unicode_homoglyphs_and_rtl(evaluator_a_license, gateway_client):
    """PT-API-011: Unicode right-to-left override and Cyrillic homoglyphs do not crash parsing."""
    headers = evaluator_a_license["headers"]
    homoglyph_query = "\u202e\u202d\u0430\u0435\u0433\u0456\u0455 query test"
    res = gateway_client.post(
        "/api/v1/gateway/query",
        headers=headers,
        json={"query": homoglyph_query}
    )
    assert res.status_code in (200, 400, 422)


def test_pt_api_012_ssrf_loopback_metadata_blocking(evaluator_a_license, gateway_client):
    """PT-API-012: SSRF attempts to query local or cloud metadata endpoints are not fetched or dereferenced."""
    headers = evaluator_a_license["headers"]
    ssrf_targets = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8000/internal",
        "http://localhost:22",
    ]
    for ssrf in ssrf_targets:
        res = gateway_client.post(
            "/api/v1/gateway/query",
            headers=headers,
            json={"query": f"Fetch data from {ssrf}"}
        )
        assert res.status_code in (200, 400, 422)
        # Server should not return cloud metadata content
        assert "ami-id" not in res.text
        assert "instance-id" not in res.text


def test_pt_api_013_crlf_header_injection(evaluator_a_license, gateway_client):
    """PT-API-013: CRLF injection in HTTP headers is rejected by client / ASGI transport."""
    headers = dict(evaluator_a_license["headers"])
    # Attempting newline insertion in a header value
    try:
        headers["X-Custom-Param"] = "value\r\nSet-Cookie: rogue=injected"
        res = gateway_client.get("/api/v1/gateway/health", headers=headers)
        # If transport strips or rejects:
        assert "rogue" not in res.headers.get("set-cookie", "")
    except ValueError:
        # Client library / ASGI server cleanly raised ValueError on CRLF
        pass


def test_pt_api_014_pagination_limit_clamping(evaluator_a_license, gateway_client):
    """PT-API-014: Outrageous pagination limits are clamped to maximum limits to prevent memory exhaustion."""
    headers = evaluator_a_license["headers"]
    res = gateway_client.get(
        "/v1/evaluation/usage/history?limit=9999999",
        headers=headers
    )
    # Either successfully clamped or rejected with 422
    assert res.status_code in (200, 422)
    if res.status_code == 200:
        data = res.json()
        assert len(data.get("history", [])) <= 100


def test_pt_api_015_host_header_poisoning(evaluator_a_license, gateway_client):
    """PT-API-015: Host header manipulation does not poison response links or redirects."""
    headers = {**evaluator_a_license["headers"], "Host": "evil.attacker.com"}
    res = gateway_client.get("/health", headers=headers)
    assert res.status_code == 200
    assert "evil.attacker.com" not in res.text


def test_pt_api_016_cors_disallowed_origin(evaluator_a_license, gateway_client):
    """PT-API-016: Disallowed cross-origin requests to sensitive endpoints are strictly blocked."""
    res = gateway_client.post(
        "/v1/evaluation/session/refresh",
        headers={"Origin": "https://attacker.com"},
        json={"refresh_token": "some-token"}
    )
    assert res.status_code == 403
    body = res.json()
    err_msg = body.get("error", "") if isinstance(body, dict) else ""
    if not err_msg and isinstance(body.get("detail"), dict):
        err_msg = body["detail"].get("error", "")
    assert "CORS_ORIGIN_DENIED" in err_msg


def test_pt_api_017_volumetric_quota_burst_resilience(evaluator_a_license, gateway_client):
    """PT-API-017: Rapid volumetric bursts cleanly exhaust quota and yield HTTP 429 Too Many Requests."""
    headers = evaluator_a_license["headers"]
    
    # Evaluator has max_queries_per_day = 20
    statuses = []
    for _ in range(25):
        res = gateway_client.post(
            "/api/v1/gateway/query",
            headers=headers,
            json={"query": "test burst query"}
        )
        statuses.append(res.status_code)
    
    assert 429 in statuses
    assert statuses.count(429) >= 5


def test_pt_api_018_concurrent_duplicate_document_uploads(evaluator_a_license, gateway_client):
    """PT-API-018: Uploading identical documents sequentially or concurrently does not corrupt quota state."""
    headers = evaluator_a_license["headers"]
    doc_content = b"Duplicate Document Ingestion Content Test"
    
    res1 = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("dup1.txt", io.BytesIO(doc_content), "text/plain")}
    )
    res2 = gateway_client.post(
        "/api/v1/gateway/documents",
        headers=headers,
        files={"file": ("dup2.txt", io.BytesIO(doc_content), "text/plain")}
    )
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["document_id"] != res2.json()["document_id"]


def test_pt_api_019_security_response_headers(evaluator_a_license, gateway_client):
    """PT-API-019: Evaluates the presence of defensive HTTP security headers on API responses."""
    res = gateway_client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in res.headers


def test_pt_api_020_http_parameter_pollution(evaluator_a_license, gateway_client):
    """PT-API-020: HTTP Parameter Pollution (HPP) with duplicate query params is safely handled."""
    headers = evaluator_a_license["headers"]
    # Provide duplicate limit parameters
    res = gateway_client.get(
        "/v1/evaluation/usage/history?limit=5&limit=10",
        headers=headers
    )
    assert res.status_code in (200, 422)
