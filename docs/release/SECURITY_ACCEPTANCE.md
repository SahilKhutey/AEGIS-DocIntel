# AEGIS-DocIntel — Security Acceptance and Hardening Specification

## 1. Security Baseline & Threat Model

AEGIS-DocIntel implements a defense-in-depth model for privacy-sensitive document intelligence. The platform enforces strict boundary controls across authentication, role-based authorization, tenant data isolation, and payload ingestion.

> [!IMPORTANT]
> AEGIS-DocIntel has undergone automated internal security acceptance testing, but has not completed an independent third-party external security audit. The software is **not production-ready** for unmanaged public cloud deployments or multi-tenant hosting without isolated network boundaries.

---

## 2. Authentication & Credential Verification

Automated acceptance tests in `tests/security/test_auth_acceptance.py` verify the following controls:

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

## 3. Role-Based Access Control (RBAC)

Automated tests in `tests/security/test_role_boundaries.py` verify role privilege boundaries:

| Role | Query & Retrieval | Document Upload | Document Deletion | System Admin |
| :--- | :--- | :--- | :--- | :--- |
| **Viewer** | Allowed | Denied (HTTP 403) | Denied (HTTP 403) | Denied (HTTP 403) |
| **Editor** | Allowed | Allowed | Denied (HTTP 403) | Denied (HTTP 403) |
| **Admin**  | Allowed | Allowed | Allowed | Allowed |

---

## 4. Multi-Tenant IDOR and Route Isolation

Automated tests in `tests/security/test_tenant_route_isolation.py` enforce strict tenant boundaries:

1. **Document Access Isolation**: Attempting to retrieve, query, export, or delete a document belonging to Tenant A using credentials from Tenant B returns HTTP 404 Not Found (preventing tenant enumeration).
2. **Database Namespace Separation**: All database queries parameterize `tenant_id` at the query boundary; documents and chunks from different tenants are never co-mingled in retrieval candidate pools.

---

## 5. Denial of Service & Payload Restrictions

1. **Payload Size Guard**: Ingestion endpoints enforce `AEGIS_MAX_UPLOAD_BYTES` (default: 200 MB, minimum: 1024 bytes). Requests with payload sizes exceeding this limit are terminated early with HTTP 413 Payload Too Large.
2. **Credential Masking in Logs**: Telemetry and audit loggers filter `Authorization`, `X-API-Key`, and secret tokens, replacing them with `[MASKED]`.
