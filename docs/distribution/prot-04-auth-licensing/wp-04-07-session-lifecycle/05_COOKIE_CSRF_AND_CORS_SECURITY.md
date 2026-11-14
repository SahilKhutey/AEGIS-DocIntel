# Dossier 05: Cookie, CSRF & CORS Security Architecture

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Browser Security Layer`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. `__Host-` Cookie Security Specification

For web and electron-based demo evaluator clients, refresh tokens are transmitted using the hardened `__Host-` cookie prefix:

```http
Set-Cookie: __Host-aegis_refresh=aegis_eval_rt_...; 
            Path=/; 
            Secure; 
            HttpOnly; 
            SameSite=Strict; 
            Max-Age=604800
```

### Security Guarantees of `__Host-`:
1. **Host-Only Scope:** Must be set from a secure (HTTPS) origin; cannot include a `Domain` attribute. This prevents subdomain spoofing or session fixation across sibling demo environments.
2. **Path Restriction:** Must have `Path=/`, preventing path-restricted cookie manipulation.
3. **HttpOnly:** JavaScript cannot read or extract the cookie value, neutralizing cross-site scripting (XSS) credential theft.
4. **SameSite=Strict:** The cookie is never sent along with cross-site requests, mitigating cross-site request forgery (CSRF).

---

## 2. Cross-Origin Resource Sharing (CORS) Defense

The Evaluation Gateway validates request `Origin` headers before processing session refresh operations:
- **Allowed Origins:** Dedicated evaluator client origins (e.g. `http://localhost:3000`, `http://127.0.0.1:8000`, explicit evaluation domains).
- **Adversarial Origin Rejection:** Hostile cross-origins (e.g. `https://attacker.com`, `http://evil.com`, `null`) are rejected immediately with HTTP 403 `CORS_ORIGIN_DENIED`.

---

## 3. Cross-Site Request Forgery (CSRF) Protection

When browser sessions present refresh cookies:
- Evaluator clients must provide an anti-forgery token in the `X-CSRF-Token` header.
- The gateway verifies that `X-CSRF-Token` matches the cryptographically signed `csrf_token` cookie.
- If a mismatch or missing CSRF header is detected on cookie-based refresh, the gateway aborts with HTTP 403 `CSRF_MISMATCH`.
