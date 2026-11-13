# PROT-04.01: Authentication Baseline & Threat Model

**Work Package:** PROT-04.01  
**Target:** Ingress Authentication Architecture, Claim Enforcement & Threat Boundaries  
**Auditor:** Core Security Engineering  
**Status:** **AUDITED & VERIFIED**

---

## 1. Authentication Ingress Architecture

AEGIS-DocIntel employs a defense-in-depth, fail-closed authentication architecture composed of two layers:
1. **Global Deny-by-Default Middleware (`src/api/auth_guard.py`):**
   - Intercepts 100% of incoming HTTP requests prior to router dispatch.
   - Maintains an explicit, minimal allowlist of public unauthenticated paths:
     - `/`, `/ui`, `/health`, `/health/live`, `/health/ready`, `/readiness`, `/docs`, `/openapi.json`
     - `/metrics` (Prometheus scrape endpoint, protected via network-level container isolation)
   - Every other route is rejected immediately with HTTP 401 Unauthorized unless verified credentials (RS256 JWT or hashed API key) are present.
2. **Per-Route Tenant Context Dependency (`src/api/auth.py` -> `get_current_tenant`):**
   - Validates credential signatures and claims.
   - Extracts immutable `TenantContext` containing `tenant_id`, `principal_id`, `roles`, and `monthly_token_limit`.
   - Attaches context to `request.state.tenant_context` for downstream database tenant isolation.

---

## 2. JWT Verification & Cryptographic Standards

Production JWT authentication enforces RS256 asymmetric cryptographic validation:
- **Algorithm Allowlist:** Strictly pinned to `["RS256"]`. Symmetric HMAC algorithms (e.g. HS256) are explicitly rejected to defend against key-confusion attacks (CVE-2015-9235 defense).
- **Key Type Enforcement:** The configured public key (`AEGIS_JWT_PUBLIC_KEY` or `AEGIS_JWT_PUBLIC_KEY_PATH`) is parsed via Cryptography HAZMAT primitives; non-RSA keys or malformed structures trigger an immediate fail-closed exception.
- **Mandatory Claims:**
  - `sub`: Unique principal identifier (evaluator or tenant user).
  - `exp`: Expiration UNIX timestamp; tokens exceeding `exp` + 30s leeway are rejected with HTTP 401.
  - `tenant_id` / `tid`: Organization / tenant boundary identifier.
  - `iss`: Validated against `AEGIS_JWT_ISSUER` when configured.
  - `aud`: Validated against `AEGIS_JWT_AUDIENCE` when configured.
- **Role Validation:** Roles embedded in tokens must strictly belong to `STANDARD_ROLES` (`viewer`, `editor`, `tenant_admin`, `platform_admin`). Unknown roles are rejected.

---

## 3. Threat Model & Attack Vectors

| Threat ID | Threat Vector | Target Component | Gateway / Backend Countermeasure | Test Verification |
| :--- | :--- | :--- | :--- | :--- |
| **THREAT-01** | **Unauthenticated Route Access** | All protected APIs | `AuthGuardMiddleware` blocks all unlisted routes with 401 | `AUTH-001`, `SEC-DEMO-005` |
| **THREAT-02** | **Algorithm Confusion (HMAC Spoof)** | `src/api/auth.py` | PyJWT algorithm pinned strictly to `["RS256"]` | `AUTH-007`, `test_production_rejects_algorithm_confusion_hs256` |
| **THREAT-03** | **Development Token Bypass** | Frontend & Backend | `dev-*` tokens banned in production; fail closed | `AUTH-008`, `npm run verify:auth` |
| **THREAT-04** | **Expired Session Reuse** | Gateway / API | Server validates `exp` timestamp on every request | `AUTH-004`, `LIC-003` |
| **THREAT-05** | **Cross-Tenant IDOR Probing** | Document Store | Partitioned by `license_id`; foreign doc ID returns 404 | `TENANT-001`, `SEC-DEMO-011` |
| **THREAT-06** | **Forged Client Role Claims** | Header / Payload | Client headers ignored; server context is source of truth | `ENT-004`, `ENT-005` |
| **THREAT-07** | **Burst Quota Exhaustion Race** | Query / Ingestion | Atomic reservation via `threading.Lock` | `QUOTA-003`, `test_adversarial_d` |
| **THREAT-08** | **Device Identity Spoofing** | Activation | Asymmetric device key registered; 1-device limit enforced | `DEV-001`-`DEV-004` |
