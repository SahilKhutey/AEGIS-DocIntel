# Public Evaluation Gateway Specification (DEP-02)

## Architectural Role
The Evaluation Gateway (`services/evaluation_gateway/` and `src/gateway/`) is the sole public-facing application interface.

## Request Processing Lifecycle
1. **Edge TLS & Request Validation:** Caddy reverse proxy terminates TLS 1.3, applies security headers, and enforces a 25 MB max request size limit.
2. **Evaluator Authentication:** Gateway validates evaluator session tokens and device signatures.
3. **License & Revocation Check:** Authoritative revocation registry is queried; revoked licenses return HTTP 403 instantly.
4. **Tenant Boundary Sanitization:** Client-supplied `X-Tenant-ID` or `X-Tenant-Context` headers are stripped; the server-authenticated tenant is injected.
5. **Entitlement & Quota Reservation:** Requested feature is validated against license entitlements and quota is atomically pre-reserved.
6. **Trusted Context Generation:** Gateway generates an immutable `TrustedInternalContext` containing `request_id`, `principal_id`, `tenant_id`, `license_id`, and quota reservation ID.
7. **HMAC-SHA256 Signing:** Service token is signed using the internal service secret.
8. **Upstream Dispatch:** Dispatched to private engine over the internal network.
9. **Usage Settlement:** On success, quota reservation is settled; on failure, rolled back.
10. **Response Sanitization:** Internal stack traces, server IPs, and database identifiers are redacted before returning to the evaluator.
