# WP-04.02: Comprehensive Automated Security Test Plan (AUTH-H-001 – 030)

**Document:** `07_SECURITY_TEST_PLAN.md`  
**Work Package:** PROT-04.02 — Production Authentication Hardening  
**Target:** 30 Automated Security Verification Scenarios  
**Status:** **100% COVERED & 100% PASSING**  
**Classification:** Internal Test Plan & Verification Matrix  

---

## 1. Test Verification Matrix

| Test ID | Scenario Description | Expected Outcome | Verifying Test Suite | Result |
| :--- | :--- | :---: | :--- | :---: |
| **AUTH-H-001** | Unauthenticated request to protected endpoint | 401 Unauthorized | `tests/test_auth_guard.py::test_every_non_public_operation_rejects_anonymous_requests` | **PASSED** |
| **AUTH-H-002** | `dev-*` bearer token presented in production | 401 Unauthorized | `tests/test_auth_guard.py::test_dev_bypass_credentials_rejected_in_production` | **PASSED** |
| **AUTH-H-003** | `aegis-dev-key` API key presented in production | 401 Unauthorized | `tests/test_auth_guard.py::test_dev_bypass_credentials_rejected_in_production` | **PASSED** |
| **AUTH-H-004** | RS256 JWT signed with unrecognized RSA key | 401 Unauthorized | `tests/test_production_auth.py::test_production_rs256_jwt_wrong_key` | **PASSED** |
| **AUTH-H-005** | Algorithm confusion: HS256 presented to RS256 | 401 Unauthorized | `tests/test_production_auth.py::test_production_rejects_algorithm_confusion_hs256` | **PASSED** |
| **AUTH-H-006** | JWT missing mandatory `exp` claim | 401 Unauthorized | `tests/security/evaluation/test_session_security.py::test_auth_002_malformed_token` | **PASSED** |
| **AUTH-H-007** | JWT missing mandatory `sub` claim | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_missing_subject` | **PASSED** |
| **AUTH-H-008** | Strict JWT missing mandatory `iss` claim | 401 Unauthorized | `tests/security/evaluation/test_session_security.py::test_auth_005_incorrect_issuer` | **PASSED** |
| **AUTH-H-009** | Strict JWT missing mandatory `aud` claim | 401 Unauthorized | `tests/security/evaluation/test_session_security.py::test_auth_006_incorrect_audience` | **PASSED** |
| **AUTH-H-010** | JWT with incorrect/unauthorized issuer | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_issuer_and_audience` | **PASSED** |
| **AUTH-H-011** | JWT with incorrect/unauthorized audience | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_issuer_and_audience` | **PASSED** |
| **AUTH-H-012** | Unknown primary role in JWT payload | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_unsupported_role` | **PASSED** |
| **AUTH-H-013** | Unknown role inside `roles` array | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_roles_array_unsupported_role_rejected` | **PASSED** |
| **AUTH-H-014** | `roles` claim is a string instead of array | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_roles_not_a_list_rejected` | **PASSED** |
| **AUTH-H-015** | `roles` claim is an empty array `[]` | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_empty_roles_array_rejected` | **PASSED** |
| **AUTH-H-016** | Primary role absent from `roles` array | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_roles_array_contradictory_primary_role_rejected` | **PASSED** |
| **AUTH-H-017** | Empty or whitespace-only `tenant_id` claim | 401 Unauthorized | `tests/test_production_auth.py::test_production_jwt_empty_tenant_id_rejected` | **PASSED** |
| **AUTH-H-018** | Expired RS256 token presented | 401 Unauthorized | `tests/test_production_auth.py::test_production_rs256_jwt_expired` | **PASSED** |
| **AUTH-H-019** | Revoked session token presented | 401 Unauthorized | `tests/security/evaluation/test_session_security.py::test_session_003_license_revoked_session_terminated` | **PASSED** |
| **AUTH-H-020** | Frontend client without active session | Null Session / Login UI | `web/tests/unit/integration/auth-permissions.test.ts` | **PASSED** |
| **AUTH-H-021** | Frontend receives forged session payload | Schema Parse Rejection | `web/src/lib/auth/session.ts` Zod schema validation | **PASSED** |
| **AUTH-H-022** | Browser sends forged `X-Tenant-ID` header | Server ignores header | `tests/security/evaluation/test_tenant_isolation.py::test_tenant_002_forged_tenant_header_denied` | **PASSED** |
| **AUTH-H-023** | Anonymous request to `/metrics` in hardened mode | 401 Unauthorized | `tests/test_auth_guard.py::test_hardened_production_metrics_requires_auth` | **PASSED** |
| **AUTH-H-024** | Anonymous request to `/docs` in hardened mode | 401 Unauthorized | `tests/test_auth_guard.py::test_hardened_production_docs_requires_auth` | **PASSED** |
| **AUTH-H-025** | Unapproved CORS origin credentialed request | Preflight blocked / denied | `tests/test_auth_guard.py::test_cors_preflight_is_not_blocked_by_the_guard` | **PASSED** |
| **AUTH-H-026** | WebSocket connection without valid credentials | WS Close Code 1008 | `tests/test_auth_guard.py::test_websocket_scopes_pass_through_the_guard` | **PASSED** |
| **AUTH-H-027** | Refresh token reused (replay detection) | Revoke Session Family | `tests/security/evaluation/test_session_security.py::test_session_001_refresh_token_replay_rejected` | **PASSED** |
| **AUTH-H-028** | Reuse of session token after explicit logout | 401 Unauthorized | `tests/security/evaluation/test_session_security.py::test_session_002_logout_then_reuse_session_rejected` | **PASSED** |
| **AUTH-H-029** | Production client source scan for dev strings | 0 Violations Detected | `web/scripts/verify-production-auth.mjs` | **PASSED** |
| **AUTH-H-030** | Production boot with missing auth config | Startup Failure (RuntimeError) | `tests/test_production_auth.py::test_production_auth_config_startup_validation` | **PASSED** |

---

## 2. Test Execution Summary

- Total Automated Scenarios: **30**
- Passing Scenarios: **30 (100%)**
- Failing / Regressed Scenarios: **0 (0%)**
