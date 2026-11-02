# AEGIS-DocIntel — Comprehensive Security Test Plan

**Classification:** Security Architecture & Qualification Specification  
**Status:** Canonical Security Test Plan  
**Release Target:** Alpha / Experimental (MVP Evaluation Baseline)  

---

## 1. Scope & Security Objectives

This test plan defines the mandatory security verification procedures for AEGIS-DocIntel. The primary security objective is to ensure fail-closed authentication, strict multi-tenant data isolation, tamper-proof governance audit trails, prompt injection resistance, and zero plaintext secret leakage across all API and processing pipelines.

---

## 2. Security Test Matrix

| Area | Test Identifier | Attack Scenario / Vector | Expected Security Defense | Automated Test Reference | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Authentication** | `SEC-AUTH-01` | Missing credentials on protected route | HTTP 401 Unauthorized with `WWW-Authenticate` header | `tests/security/test_auth_guard_acceptance.py::test_missing_credentials_fail_closed` | **PASS** |
| **Authentication** | `SEC-AUTH-02` | Forged JWT RS256 signature with untrusted key | Signature verification fails; HTTP 401 Unauthorized | `tests/security/test_auth_acceptance.py::test_invalid_signature_wrong_key_rejected` | **PASS** |
| **Authentication** | `SEC-AUTH-03` | Expired JWT token (`exp` timestamp in past) | Token expired; HTTP 401 Unauthorized | `tests/security/test_auth_acceptance.py::test_expired_jwt_rejected_with_401` | **PASS** |
| **Authorization** | `SEC-AUTHZ-01` | Viewer role attempting document upload | HTTP 403 Forbidden; insufficient role permissions | `tests/security/test_role_boundaries.py::test_viewer_role_cannot_upload_document` | **PASS** |
| **Authorization** | `SEC-AUTHZ-02` | Non-admin role attempting legal hold override | HTTP 403 Forbidden; admin role strictly required | `tests/security/test_role_boundaries.py::test_admin_required_for_legal_hold` | **PASS** |
| **Tenant Isolation** | `SEC-TENANT-01` | Tenant A attempting to access Tenant B document ID | HTTP 404 Not Found (non-disclosing IDOR defense) | `tests/security/test_tenant_route_isolation.py::test_http_api_cross_tenant_lifecycle_idor_defense` | **PASS** |
| **Tenant Isolation** | `SEC-TENANT-02` | Cross-tenant element query in memory orchestrator | `PermissionError` or empty result; zero data leak | `tests/security/test_tenant_route_isolation.py::test_orchestrator_cross_tenant_isolation` | **PASS** |
| **Tenant Isolation** | `SEC-TENANT-03` | Tenant A reviewing Tenant B review queue items | HTTP 404 / 403; cross-tenant items isolated | `tests/test_mvp6_review_security.py::test_tenant_review_isolation` | **PASS** |
| **Input Validation** | `SEC-INPUT-01` | Oversized payload upload (> 200MB limit) | HTTP 413 Payload Too Large enforced before parse | `tests/security/test_auth_acceptance.py::test_payload_limit_enforced` | **PASS** |
| **Prompt Injection** | `SEC-INJECT-01` | Malicious system instructions embedded in doc text | Document text treated strictly as data, not instruction | `tests/test_mvp3_security.py::test_prompt_injection_resistance` | **PASS** |
| **Secret Scanning** | `SEC-LEAK-01` | Accidental credentials in code, logs, or commits | Gitleaks / regex scanning detects 0 plaintext secrets | `tests/test_repo_hygiene.py::test_no_plaintext_secrets` | **PASS** |
| **Audit Integrity** | `SEC-AUDIT-01` | Direct `UPDATE` or `DELETE` on audit trail table | Blocked; append-only cryptographic event integrity | `tests/test_mvp6_review_audit.py::test_audit_event_immutability` | **PASS** |
| **Data Deletion** | `SEC-DELETE-01` | Deletion request cascades to all derived chunks | Chunks, vectors, and facts purged within tenant | `tests/test_document_deletion.py::test_cascading_document_deletion` | **PASS** |

---

## 3. Execution Verification

All security tests are automated and executed under the security audit profile:

```powershell
python scripts/run_mvp_audit.py --profile security
```
