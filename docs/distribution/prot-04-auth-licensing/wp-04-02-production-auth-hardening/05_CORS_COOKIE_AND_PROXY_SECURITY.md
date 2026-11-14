# WP-04.02: CORS, Cookie Architecture & Local Proxy Hardening

**Document:** `05_CORS_COOKIE_AND_PROXY_SECURITY.md`  
**Work Package:** PROT-04.02 — Production Authentication Hardening  
**Target:** Cross-Origin Resource Sharing, Cookie Attributes, CSRF Defense & Local Reverse Proxy  
**Status:** **AUDITED, HARDENED & VERIFIED**  
**Classification:** Internal Security Architecture Specification  

---

## 1. Cross-Origin Resource Sharing (CORS) Hardening

In `src/main.py`, CORS policy is configured via FastAPI's `CORSMiddleware`:
1. **Explicit Origin Allowlist:** In production mode, origins must be explicitly declared in `cors_origins`. Wildcard `*` origins are strictly prohibited whenever `allow_credentials=True`.
2. **Preflight Passthrough:** CORS `OPTIONS` preflight requests pass through `AuthGuardMiddleware` without credentials, allowing browser preflight checks to complete cleanly while denying actual resource access to unauthorized origins (`AUTH-H-025`).
3. **Restricted Headers & Methods:** Standard client headers (`Authorization`, `Content-Type`, `X-Request-ID`, `X-Workspace-ID`, `X-Tenant-ID`) are permitted, while arbitrary headers are ignored.

---

## 2. Session Cookie Specification

For browser evaluation clients interacting with the Evaluation Gateway (BFF), credentials are held in secure cookies:

| Cookie Attribute | Production Setting | Security Objective |
| :--- | :--- | :--- |
| **HttpOnly** | `true` | Prevents XSS scripts in browser context from stealing session identifiers. |
| **Secure** | `true` | Enforces transmission exclusively over TLS 1.3 HTTPS channels. |
| **SameSite** | `Lax` (or `Strict`) | Mitigates Cross-Site Request Forgery (CSRF) on cross-origin navigations. |
| **Path** | `/evaluation` | Narrowly scopes cookie transmission to evaluation gateway endpoints. |
| **Max-Age / Expiry**| `600` seconds (10 min) | Limits window of vulnerability for stolen session cookies. |

---

## 3. Local Reverse Proxy Architecture

The downloaded demo package runs on the user's host machine. A local reverse proxy coordinates communication between the browser and remote infrastructure:

```
[ Evaluator Browser ]
       │  (Same-Origin HTTP on http://127.0.0.1:3000)
       ▼
[ Local Reverse Proxy (Docker / Launcher) ]
       │  - Routes /ui and static assets locally
       │  - Strips administrative headers
       │  - Does NOT store shared gateway secrets or private keys
       │  (Outbound HTTPS / TLS 1.3 to https://gateway.aegis-docintel.org)
       ▼
[ Remote AEGIS Evaluation Gateway ]
       │  - Authenticates evaluator session independently
       │  - Checks license, quotas, and revocation registry
```

### The Local Proxy Security Axiom
Because an evaluator has full administrator access to their local workstation, the local proxy must **never** be trusted to store shared master secrets or bypass authentication. The remote gateway independently authenticates every incoming request via short-lived session tokens and device signatures.
