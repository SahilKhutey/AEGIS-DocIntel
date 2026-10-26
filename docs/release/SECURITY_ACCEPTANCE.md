# AEGIS-DocIntel — Security Acceptance and Hardening Specification

## 1. Security Baseline & Threat Model

AEGIS-DocIntel implements a defense-in-depth security model for privacy-sensitive document intelligence. The platform enforces strict boundary controls across authentication, role-based authorization, tenant data isolation, metrics protection, and payload ingestion.

> [!IMPORTANT]
> AEGIS-DocIntel has undergone automated internal security acceptance testing, but has not completed an independent third-party external security audit. The software is **not production-ready** for unmanaged public cloud deployments or multi-tenant hosting without isolated network boundaries.

---

## 2. Fail-Closed Authentication Guard

Automated acceptance tests in `tests/security/test_auth_guard_acceptance.py` verify that `AuthGuardMiddleware` enforces deny-by-default behavior across the entire HTTP route tree:

1. **Deny-by-Default Protection**: Newly introduced endpoints not explicitly present in public allowlists fail closed, returning HTTP 401 Unauthorized for anonymous callers.
2. **Missing and Malformed Credentials**: Requests lacking `Authorization` or `X-API-Key` headers, or bearing invalid/tampered tokens, are rejected with HTTP 401 and appropriate `WWW-Authenticate` headers.
3. **Public Operational Allowlist**: The liveness probe `/health` is allow-listed for orchestration health checks.
4. **CORS Preflight Compatibility**: HTTP `OPTIONS` requests bypass authentication checks, allowing standard browser preflight negotiation.

---

## 3. Cryptographic Token & Credential Verification

Automated acceptance tests in `tests/security/test_auth_acceptance.py` verify cryptographic credential handling:

### Cryptographic JWT Verification
1. **Algorithm Confusion Protection**: Tokens signed with symmetric HMAC (`HS256`) using an RSA public key as the secret are explicitly rejected.
2. **Signature Tampering**: Tokens with altered payloads or forged signatures return HTTP 401 Unauthorized.
3. **Token Expiration**: Expired tokens (`exp` in the past) are rejected.
4. **Issuer and Audience Enforcement**: Tokens lacking the configured `AEGIS_JWT_ISSUER` or `AEGIS_JWT_AUDIENCE` are rejected in production mode.

### Hash-Only API Keys
1. **No Raw Key Persistence**: In staging and production environments, API keys must be configured as SHA-256 hashes (`sha256:<64-hex>`).
2. **Lookup Validation**: Request keys provided in `X-API-Key` headers are hashed with SHA-256 prior to constant-time lookup. Raw keys stored in configuration trigger immediate startup failure.

### Development Bypass Rejection
- When `AEGIS_ENVIRONMENT` is set to `production` or `staging`, anonymous requests without valid credentials return HTTP 401. Development bypass flags are strictly ignored.

---

## 4. Role-Based Access Control (RBAC) & WebSocket Protection

Automated tests in `tests/security/test_role_boundaries.py` verify role privilege boundaries across HTTP and WebSocket transports:

| Role | Query & Retrieval | Document Upload | Document Deletion | System Admin |
| :--- | :--- | :--- | :--- | :--- |
| **Viewer** | Allowed | Denied (HTTP 403) | Denied (HTTP 403) | Denied (HTTP 403) |
| **Editor** | Allowed | Allowed | Denied (HTTP 403) | Denied (HTTP 403) |
| **Admin**  | Allowed | Allowed | Allowed | Allowed |

### WebSocket Handshake Authorization
- Interactive query streams (`/v1/queries/ws/{session_id}`) require valid authentication during the connection handshake via `get_current_tenant_ws`.
- Unauthenticated WebSocket connections are rejected with policy violation (WS 1008 / HTTP 401).
- Authenticated identities are bound strictly to their cryptographic token tenant, preventing spoofing via request headers or message payload parameters.

---

## 5. Multi-Tenant IDOR and Route Isolation

Automated tests in `tests/security/test_tenant_route_isolation.py` enforce strict tenant boundaries:

1. **Document Access Isolation**: Attempting to retrieve, query, export, or delete a document belonging to Tenant A using credentials from Tenant B returns HTTP 404 Not Found (preventing tenant enumeration).
2. **Database Namespace Separation**: All database queries parameterize `tenant_id` at the query boundary; documents and chunks from different tenants are never co-mingled in retrieval candidate pools.

---

## 6. Metrics & Deployment Topology Security

Automated tests in `tests/security/test_metrics_deployment_security.py` verify that:

1. **Loopback Host Binding**: The API service in `deploy/docker-compose.yml` binds host ports strictly to `127.0.0.1:8000:8000`, preventing direct internet exposure.
2. **Internal Network Isolation**: Prometheus and Grafana communicate with `aegis-api` over an isolated internal bridge network (`aegis-internal`).
3. **No Unintentional Host Ports**: Monitoring ports (9090 for Prometheus, 3000 for Grafana) are not published to host interfaces.
4. **Internal Scrape Path**: Prometheus scrapes `aegis-api:8000/metrics` over internal DNS.
5. **Telemetry Pseudonymization**: Tenant identifiers in Prometheus metrics and traces are pseudonymized by default (`AEGIS_PSEUDONYMIZE_TELEMETRY=true`).

---

## 7. Denial of Service & Payload Restrictions

1. **Payload Size Guard**: Ingestion endpoints enforce `AEGIS_MAX_UPLOAD_BYTES` (default: 200 MB, minimum: 1024 bytes). Requests with payload sizes exceeding this limit are terminated early with HTTP 413 Payload Too Large.
2. **Credential Masking in Logs**: Telemetry and audit loggers filter `Authorization`, `X-API-Key`, and secret tokens, replacing them with `[MASKED]`.
