# PROT-04.02: Production Authentication Hardening

**Work Package:** PROT-04.02  
**Target:** Client-Side Session Security, Elimination of Development Bypasses & Automated Build Guards  
**Status:** **REMEDIATED & VERIFIED**

---

## 1. Vulnerability Background & Remediation

During the PROT-03 exposure audit, several development fallbacks were identified in the frontend client codebase that presented risk if distributed to untrusted recipients:
1. `web/src/lib/auth/session.ts`: `dev-*` tokens were automatically granted `role: "admin"` with full system permissions, and `"dev-default-tenant"` was used as an unauthenticated fallback.
2. `web/src/lib/api/client.ts`: Default authentication headers sent fallback bearer tokens and hardcoded localhost URLs.
3. `web/src/lib/validation/environment.ts`: Included `NEXT_PUBLIC_AEGIS_DEV_TOKEN` in the browser-visible environment schema.

### Actions Executed
- **Frontend Session Fail-Closed (`session.ts`):**
  - Updated `resolveSessionFromToken()` to immediately return `null` if a `dev-*` token is encountered in production (`NODE_ENV === "production"` or `NEXT_PUBLIC_APP_ENV === "production"`).
  - Eliminated automatic `admin` privilege assignment; unauthenticated visitors fall back only to read-only viewer evaluation or `null`.
- **API Client Hardening (`client.ts`):**
  - Stripped `NEXT_PUBLIC_AEGIS_DEV_TOKEN` from `getDefaultAuthHeaders()`.
  - Replaced hardcoded `http://127.0.0.1:8000` with relative same-origin `/api` routing to leverage the local reverse proxy (`deploy/nginx-demo-proxy.conf`).
- **Environment Schema Sanitation (`environment.ts`):**
  - Purged `NEXT_PUBLIC_AEGIS_DEV_TOKEN` entirely from the Zod schema.

---

## 2. Automated Build-Time Production Guard

To guarantee that development bypasses or credentials can never accidentally re-enter client builds, a dedicated build guard was implemented:
- **Script Location:** `web/scripts/verify-production-auth.mjs`
- **NPM Script:** `npm run verify:auth` in `web/package.json`

### Verification Logic
The guard recursively parses all TypeScript/JavaScript files in `web/src/` and fails the build with exit code 1 if any of the following patterns are detected:
- `NEXT_PUBLIC_AEGIS_DEV_TOKEN`
- `"dev-default-tenant"`
- Automatic admin privilege escalation in token resolution (`role: "admin"`)

### Execution Output
```bash
$ node web/scripts/verify-production-auth.mjs
Running PROT-04 Production Authentication Guard...
✅ PROT-04 Guard Passed: No development tokens or auth bypasses found in web/src.
```
