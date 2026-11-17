# WP-04.01: Ingress Authentication Architecture & Call Graph

**Document:** `01_AUTHENTICATION_ARCHITECTURE.md`  
**Work Package:** PROT-04.01 — Authentication Baseline & Threat Model  
**Component:** Backend Ingress Security, Middleware Pipeline & Context Propagation  
**Status:** **AUDITED & VERIFIED**  
**Classification:** Internal Security Architecture Reference  

---

## 1. Executive Architectural Overview

AEGIS-DocIntel implements a defense-in-depth, fail-closed authentication model designed to ensure that no protected API endpoint or compute pipeline can be executed anonymously, under an assumed tenant identity, or without validated cryptographic credentials.

The authentication subsystem is structured into two complementary layers:
1. **Global Deny-by-Default ASGI Middleware (`src/api/auth_guard.py`):**
   - Intercepts 100% of incoming HTTP requests before FastAPI router dispatch.
   - Evaluates request paths against an immutable, minimal allowlist of public operational endpoints.
   - For all non-public paths, validates incoming credentials (`Bearer` JWT or `X-API-Key`) using the canonical validation engine.
   - Immediately terminates unauthenticated requests with `HTTP 401 Unauthorized` and an RFC-compliant `WWW-Authenticate: Bearer` challenge header.
2. **Per-Route Context & Dependency Injection (`src/api/auth.py`, `src/core/authorization.py`):**
   - Injects the authenticated `TenantContext` into route handlers via FastAPI `Depends(get_current_tenant)`.
   - Enforces Role-Based Access Control (RBAC) via `require_roles(...)`.
   - Enforces Tenant Resource Isolation via `verify_resource_tenant(...)`, masking cross-tenant document queries as `HTTP 404 Not Found` rather than `HTTP 403 Forbidden` to prevent IDOR enumeration.

```
Incoming Request (HTTP / HTTPS)
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  AuthGuardMiddleware (ASGI Layer - src/api/auth_guard) │
│  - Path in PUBLIC_PATHS? (e.g. /health, /openapi.json) │
│    ├── YES ──► Pass through to Router                  │
│    └── NO  ──► Check Credentials                       │
│                 ├── Invalid / Missing ──► HTTP 401     │
│                 └── Valid ──────────────► Set State    │
└──────────────────────────┬─────────────────────────────┘
                           │ Authenticated scope["state"]["tenant_context"]
                           ▼
┌────────────────────────────────────────────────────────┐
│  FastAPI Router Dispatch (src/api/routers/*)           │
│  - Endpoint Dependency: Depends(get_current_tenant)    │
│  - RBAC Guard: Depends(require_roles("editor", ...))   │
│    ├── Insufficient Role ──► HTTP 403 Forbidden        │
│    └── Authorized ─────────► Execute Service Logic     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  Data Layer & Tenant Isolation (src/services/*)        │
│  - verify_resource_tenant(resource.tenant_id, context) │
│    ├── Cross-Tenant Mismatch ──► HTTP 404 Not Found    │
│    └── Verified Match ─────────► Process Document      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Ingress Pipeline & Call Graph

### 2.1 HTTP Request Lifecycle
1. **ASGI Ingress:** The raw ASGI connection enters `AuthGuardMiddleware.__call__(scope, receive, send)`.
2. **Protocol Filter:**
   - If `scope["type"] != "http"`, the middleware yields control immediately (WebSockets are authenticated inside route handlers; see Section 3).
   - If `scope["method"] == "OPTIONS"`, preflight passes through to `CORSMiddleware`.
3. **Allowlist Matching:**
   - The path is normalized (trailing slashes stripped) and checked against `PUBLIC_PATHS` and `PUBLIC_PREFIXES`.
   - If public, control passes directly to the inner ASGI application.
4. **Credential Extraction & Validation:**
   - Headers are parsed in lowercase.
   - If `Authorization: Bearer <token>` is present, `_validate_jwt(token)` is executed.
   - If `X-API-Key: <key>` is present, `_validate_api_key(key)` is executed.
   - If neither is present, and environment is `production`, an `HTTPException(401)` is raised immediately.
5. **Context Binding:**
   - The resulting frozen `TenantContext` is saved to `scope["state"]["tenant_context"]`.
6. **Router Execution:**
   - FastAPI dependencies retrieve the verified `TenantContext` without repeating cryptographic verification or database round-trips.

---

## 3. WebSocket Connection Architecture

Because WebSockets establish a persistent, bidirectional channel via an ASGI upgrade rather than standard HTTP request-response cycles, they require specialized authentication handling:
- **Middleware Policy:** `AuthGuardMiddleware` explicitly skips ASGI `websocket` scopes, as terminating an unauthenticated WebSocket via raw HTTP 401 before protocol handshake causes protocol anomalies on client web sockets.
- **Route-Level Guard:** WebSocket endpoints (e.g. `/v1/query/ws/{session_id}` in `src/api/routers/queries.py`) declare `tenant: TenantContext = Depends(get_current_tenant_ws)`.
- **Handshake Verification:** `get_current_tenant_ws` inspects the initial handshake headers and query parameters:
  - Supports `Authorization: Bearer <token>` and `X-API-Key`.
  - Supports query parameter fallback `?token=<jwt>` for browser environments unable to set custom headers during `new WebSocket(...)`.
- **Fail-Closed Disconnect:** If credentials are missing or invalid, `get_current_tenant_ws` issues a close frame with code `status.WS_1008_POLICY_VIOLATION` (Policy Violation) and raises `HTTPException(401)`, ensuring unauthenticated connections cannot read stream chunks or inject questions.

---

## 4. Evaluation Gateway vs. Backend Core Boundary

For the **AEGIS-DocIntel Protected Demo Edition**, a strict boundary separates the public evaluation tier from the core enterprise platform:

| Security Property | Enterprise Platform (`src/api/auth.py`) | Evaluation Gateway (`services/evaluation_gateway/`) |
| :--- | :--- | :--- |
| **Identity Authority** | Enterprise IdP (OAuth2 / OIDC / SAML) | AEGIS Evaluation License Service |
| **Token Format** | RS256 JWT (`iss: Enterprise IdP`) | RS256 JWT (`iss: https://auth.aegis-docintel.org`) |
| **Token Audience** | Enterprise Microservices | `aud: aegis-evaluation-gateway` |
| **Session Lifetime** | 8 to 24 hours | 600 seconds (10 minutes) with rotating refresh |
| **Licensing Mechanism**| Enterprise Contract & Organization DB | Asymmetric Ed25519 Signed License (`*.lic`) |
| **Device Binding** | Optional / Mobile MDM | Cryptographic public-key device signature (Strict 1-Device Limit) |
| **Quota Enforcement**| Monthly token contract (10M default) | Atomic real-time reservations (Documents, Queries, Pages) |
| **Revocation Propagation**| Periodic CRL / Token Expiry | Authoritative in-memory blacklist (<15 ms SLA) |

---

## 5. Architectural Invariants

1. **Deny-by-Default:** Every newly introduced API router or path is protected automatically unless explicitly added to `PUBLIC_PATHS`.
2. **Single Identity Truth:** Client-provided tenant identifiers (e.g. query params, request bodies, or custom headers) are strictly ignored during authorization; all operations strictly derive tenancy from `request.state.tenant_context.tenant_id`.
3. **No Unauthenticated Compute:** No document parser, OCR pipeline, vector similarity search, or LLM prompt generation can be triggered without an authenticated, active `TenantContext`.
