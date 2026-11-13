# PROT-03: Frontend & Browser Bundle Exposure Audit

**Document:** 03_FRONTEND_EXPOSURE_AUDIT.md  
**Audit Target:** `web/src/` Next.js 16 / React 19 Client Application  

---

## 1. Vulnerability Analysis: Development Authentication Bypass

### Initial Vulnerability (`web/src/lib/auth/session.ts`):
Prior to remediation, `session.ts` contained an automatic bypass for tokens prefixed with `dev-`:
```typescript
if (token.startsWith("dev-")) {
  const tenantId = token.slice(4) || "default-tenant";
  return {
    user: { id: "dev-user", email: "dev@aegis.corp", displayName: "AEGIS Developer" },
    workspaceId: `ws-${tenantId}`,
    tenantId,
    role: "admin",
    permissions: getPermissionsForRole("admin"),
    token,
  };
}
```
And defaulted to `"dev-default-tenant"` when no session storage token was found.

### Risk:
An external visitor evaluating the application could forge a `dev-` prefix in their browser session, causing the frontend UI to display an administrator identity and render restricted administrative UI views.

### Technical Remediation Implemented:
1. **Production Rejection:** Added strict environment checks. In production (`NODE_ENV === "production"` or `NEXT_PUBLIC_APP_ENV === "production"`), any token starting with `dev-` returns `null` (fails closed).
2. **Default Admin Removal:** Even in development fallback, `role: "admin"` was downgraded to `"viewer"`.
3. **Fallback Purge:** Removed `"dev-default-tenant"` string fallback and `NEXT_PUBLIC_AEGIS_DEV_TOKEN` lookup. If unauthenticated in demo mode, the application generates a guest session with `role: "viewer"` and read-only permissions.

---

## 2. Vulnerability Analysis: Browser Environment Variables

### Initial Vulnerability (`web/src/lib/validation/environment.ts`):
Declared:
```typescript
NEXT_PUBLIC_AEGIS_DEV_TOKEN: z.string().optional()
```
And `client.ts` transmitted this token in `Authorization: Bearer <devToken>` headers.

### Risk:
In Next.js, all environment variables prefixed with `NEXT_PUBLIC_` are statically compiled into client-side JavaScript bundles. Any evaluator inspecting browser sources (`F12 -> Sources`) could extract this token.

### Technical Remediation Implemented:
1. `NEXT_PUBLIC_AEGIS_DEV_TOKEN` was completely purged from `environment.ts` schema and validation parser.
2. In `client.ts`, `getDefaultAuthHeaders()` was updated to send scoped evaluation tokens or fail closed (`return {}`).
3. Automated static analysis verifies that `NEXT_PUBLIC_AEGIS_DEV_TOKEN` appears in **0 lines** of the production build.

---

## 3. Same-Origin Relative Proxy Routing

### Initial Vulnerability (`web/src/lib/api/client.ts`):
Client configuration defaulted to:
```typescript
return "http://127.0.0.1:8000";
```
Exposing internal server ports and bypassing reverse proxy controls.

### Technical Remediation Implemented:
1. In browser runtime (`typeof window !== "undefined"`), `getApiBaseUrl()` strictly returns `""` (empty string).
2. All client requests target same-origin relative paths (e.g., `/api/v1/gateway/...`).
3. The local `aegis-demo-proxy` (Nginx) captures all `/api/` traffic on port 3000, injects evaluation headers, strips administrative paths, and securely proxies to the remote Evaluation Gateway.

---

## 4. Sourcemap Stripping Verification

1. `next.config.ts` was audited to verify `productionBrowserSourceMaps: false`.
2. Static inspection of distribution assets confirmed that **zero `.map` files** are included in the downloadable package (verified by test `SEC-DEMO-003` and `IP-TEST-002`).
