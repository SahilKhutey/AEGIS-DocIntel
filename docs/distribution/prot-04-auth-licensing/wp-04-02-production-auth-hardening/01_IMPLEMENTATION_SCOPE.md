# WP-04.02: Production Authentication Hardening — Implementation Scope

**Document:** `01_IMPLEMENTATION_SCOPE.md`  
**Work Package:** PROT-04.02 — Production Authentication Hardening  
**Target:** Client Ingress, Environment Schemas, Token Validation, Operational Endpoints & Build Isolation  
**Status:** **AUDITED, HARDENED & VERIFIED**  
**Classification:** Internal Security Implementation Specification  

---

## 1. Executive Objective

The objective of **WP-04.02** is to eliminate all development credentials, authentication bypasses, client-side session manufacturing, unvalidated claim parsing, and operational metadata leakage from the AEGIS-DocIntel platform before introducing evaluation licensing (WP-04.03).

A downloaded evaluation client executing on an untrusted, user-controlled computer must **never** be capable of:
1. Creating an arbitrary session or granting itself administrative capabilities (`admin`, `platform_admin`).
2. Silently assuming a default tenant identity (`default-tenant`, `workspace-default`).
3. Attaching hardcoded development credentials (`dev-*`, `aegis-dev-key`) to outgoing API requests.
4. Deriving authorization permissions from client-decoded, unverified JWT payloads.
5. Accessing operational telemetry (such as tenant-labeled `/metrics` series) anonymously.

---

## 2. Priority Modification Matrix

| Priority | Component | Path | Implemented Hardening | Verification Status |
| :---: | :--- | :--- | :--- | :---: |
| **P0** | Frontend Session Authority | `web/src/lib/auth/session.ts` | Removed dev token admin escalation; implemented trusted server session contract (`/evaluation/session`) with Zod validation. | **PASSED** |
| **P0** | Browser API Client | `web/src/lib/api/client.ts` | Removed fallback demo tokens and localhost origin defaults; enforced relative same-origin routing and `credentials: "include"`. | **PASSED** |
| **P0** | Environment Schema | `web/src/lib/validation/environment.ts` | Deleted `NEXT_PUBLIC_AEGIS_DEV_TOKEN` from Zod validation schema. | **PASSED** |
| **P0** | Request Context | `web/src/lib/api/request-context.ts` | Removed default tenant and workspace identifiers; initialized context to empty `{}`. | **PASSED** |
| **P0** | Backend JWT Engine | `src/api/auth.py` | Added `validate_production_auth_config()` startup check; enforced role array validation; returned generic HTTP 401 errors. | **PASSED** |
| **P0** | Ingress Auth Guard | `src/api/auth_guard.py` | Hardened allowlist removes `/metrics`, `/docs`, `/redoc`, and `/openapi.json` in evaluation production mode. | **PASSED** |
| **P0** | Application Entrypoint | `src/main.py` | Hardened CORS configuration (no wildcard with credentials); disabled OpenAPI schemas in production. | **PASSED** |
| **P1** | UI Presentation Hints | `web/src/lib/auth/permissions.ts` | Formalized that frontend permissions are strictly UI presentation hints, never security gates. | **PASSED** |
| **P1** | Backend Auth Tests | `tests/test_production_auth.py` | Added 4 new test scenarios for malformed roles, empty roles, empty tenant IDs, and startup validation. | **PASSED (19/19)** |
| **P1** | Ingress Guard Tests | `tests/test_auth_guard.py` | Added tests verifying operational endpoints reject anonymous requests in hardened mode. | **PASSED (29/29)** |
| **P1** | Build-Time Security Guard | `web/scripts/verify-production-auth.mjs` | Automated CI scan detecting banned development tokens and bypass strings. | **PASSED** |

---

## 3. Defense-in-Depth Trust Boundaries

```
[ ZONE A: Evaluator Client ] ──(HTTPS + Cookie)──► [ ZONE B: Gateway / BFF ] ──(RS256 JWT)──► [ ZONE C: Core API ]
  - Browser UI state only                             - Evaluator identity auth                 - Microservice token decode
  - No client tokens manufactured                     - Session lifecycle & refresh             - Tenant database isolation
  - Context derived from server                       - Entitlement & quota ledger              - Proprietary compute engine
```

Every tier strictly validates incoming state from lower trust zones and fails closed upon encountering missing, malformed, or unauthorized claims.
