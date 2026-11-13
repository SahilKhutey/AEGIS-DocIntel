# PROT-03: Runtime Leakage, Network & Logging Hygiene Audit

**Document:** 07_RUNTIME_LEAKAGE_AUDIT.md  
**Audit Scope:** HTTP headers, network payloads, server-side and client-side logging, and cross-tenant data boundaries.  

---

## 1. Network Traffic & Header Hygiene

The edge reverse proxy (`distribution/demo-edition/deploy/nginx-demo-proxy.conf`) strips identifying internal banners and injects strict security headers:

```nginx
# Server Fingerprint Minimization
server_tokens off;

# Hardened Security Headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Network Payload Audit:
1. **Request Headers:**
   - Client sends standard browser headers to same-origin `http://localhost:3000/api/...`.
   - Proxy forwards request over TLS to Evaluation Gateway, attaching `X-Evaluation-License: <token>`.
   - Internal credentials or cloud API keys never pass through the evaluator's browser.
2. **Response Payloads:**
   - Server responses contain clean JSON: answer strings, structured citation offsets, confidence scores, and invariant tags.
   - Internal scoring vectors, raw embedding matrices, and facility-location trace dumps are omitted.

---

## 2. Server-Side Logging & Telemetry Hygiene

### Rules Enforced:
1. **Zero Credential Logging:** API keys, license private keys, and user password hashes are masked or omitted in all logger configurations (`amdi.api`, `amdi.gateway`).
2. **Document Content Protection:** Uploaded raw document text is not written to standard container logs (`stdout`/`stderr`), preventing data leakage into centralized log aggregators.
3. **Reference-Based Error Logging:**
   - Server logs full exception tracebacks tagged with a short random UUID:
     `log.error('Ingest failed [ref=%s]: %s', req_id, exc, exc_info=True)`
   - Client response receives only the reference ID:
     `{"detail": "Document ingestion failed. Internal error ref: a1b2c3d4"}`
   - Support engineers can look up the error internally without exposing details to the user.

---

## 3. Cross-Tenant IDOR Defense Verification

To prevent evaluators from accessing other users' documents on the shared Evaluation Gateway:
1. Every uploaded document is associated with the `license_id` extracted from the cryptographically signed `X-Evaluation-License` token.
2. In `services/evaluation_gateway/app.py`:
   - `list_documents()` filters strictly where `doc.license_id == ctx.license_id`.
   - `get_document(doc_id)` checks `doc.license_id == ctx.license_id`. If it belongs to another evaluator, it returns **HTTP 404 Not Found** (not 403), preventing ID enumeration.
3. Verified by test `SEC-DEMO-011` and `IP-TEST-005`.
