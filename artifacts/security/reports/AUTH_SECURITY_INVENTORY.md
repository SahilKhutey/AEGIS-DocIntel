# AEGIS-DocIntel — Authentication & Authorization Security Inventory

> **Document ID**: `AUTH_SECURITY_INVENTORY.md`  
> **Work Item**: WP-07.01  
> **Status**: **VERIFIED**  
> **Component**: Access Control & Identity Architecture  

---

## 1. Authentication Mechanisms

| Mechanism | Description | Implementation File | Key Algorithms / Standards |
| :--- | :--- | :--- | :--- |
| **JWT Bearer Token** | RS256 asymmetric cryptographic tokens signed with enterprise RSA private key and verified via public key. | `src/api/auth.py` | RS256, PyJWT, Cryptography RSA public key verification (`load_pem_public_key`). |
| **API Key Header** | Direct integration key passed via `X-API-Key` header. Validated using constant-time SHA-256 hash lookup. | `src/api/auth.py` | SHA-256, `hmac.compare_digest` for timing attack immunity. |
| **Development Credential** | Explicit development token (`dev-{tenant}`) and key (`aegis-dev-key`). Strictly inactive in production. | `src/api/auth.py` | Guarded by `AEGIS_ENVIRONMENT=development` check. |

---

## 2. Token Lifecycle & Expiration

1. **Required Claims**: `sub` (principal identity), `exp` (expiration timestamp), `tenant_id` (or `tid`).
2. **Optional Claims**: `iss` (issuer verification), `aud` (audience verification), `roles` (array of assigned role strings).
3. **Clock Skew Toleration**: Leeway set to maximum 30 seconds (`leeway=30`).
4. **Revocation & Lockout**:
   - Expired tokens produce `HTTP 401 Unauthorized` with `error="invalid_token"`.
   - Repeated invalid attempts trigger audit logging and rate-limiting lockout.

---

## 3. Server-Side Identity & Tenant Resolution

- **Security Context Model**: `src/core/security_context.py` (`TenantContext`).
- **Context Properties**:
  - `tenant_id`: Mandatory string representing the isolated tenant partition.
  - `principal_id`: Mandatory string representing the authenticated user / service.
  - `roles`: Immutable `frozenset[str]` containing verified roles.
  - `authentication_method`: `bearer` or `api_key`.
- **Fail-Closed Guarantees**:
  - Identity cannot be supplied or overridden via URL query parameters, path elements, or request bodies.
  - Missing or invalid context immediately terminates request processing with `HTTP 401 Unauthorized`.

---

## 4. Role & Privilege Hierarchy

The system defines 6 standard enterprise roles with strict least-privilege scoping:
1. `viewer`: Read-only access to own tenant's approved documents and published reports.
2. `editor`: Can upload, ingest, and process documents within own tenant.
3. `reviewer`: Can inspect extraction quality, review citations, and annotate facts.
4. `review_admin`: Can approve or reject document reviews and publish comparative reports.
5. `tenant_admin`: Administrative management of own tenant's users, settings, and deletion operations.
6. `platform_admin`: Cross-tenant system maintenance and infrastructure health diagnostics (strictly prohibited from unauthorized access to tenant confidential document text).
