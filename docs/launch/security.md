# AEGIS-DocIntel — Security & Governance Architecture

This document describes the security controls, threat mitigations, and data governance guarantees in AEGIS-DocIntel.

---

## 1. Threat Model & Ingress Defenses

```
                        Threat: Unauthenticated probes / IDOR
                                      │
                                      ▼
                        [ Deny-by-Default Route Guard ]
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │ (Missing/Invalid Creds)                           │ (Valid Credentials)
            ▼                                                   ▼
   [ 401 Unauthorized ]                               [ Extract TenantContext ]
                                                                │
                                                                ▼
                                                Threat: Cross-Tenant Data Access
                                                                │
                                                                ▼
                                                [ Parameterized SQL WHERE tenant_id = ? ]
                                                                │
                                            ┌───────────────────┴───────────────────┐
                                            │ (Foreign Tenant ID)                   │ (Matching Tenant ID)
                                            ▼                                       ▼
                                   [ 404 Not Found ]                        [ Authorized Result ]
```

---

## 2. Authentication Architecture

AEGIS enforces three distinct authentication tiers:

### A. Production RS256 JWT
- Token verification strictly uses asymmetric RSA signatures (RS256).
- The public key is cryptographically verified to be an `rsa.RSAPublicKey` upon startup to prevent algorithm confusion attacks (e.g. HS256 key forgery).
- Enforces claims: `exp` (expiration), `sub` (principal identity), `tenant_id`, and allowed `role`.

### B. Production SHA-256 API Keys
- Keys are never stored in plaintext. Configuration stores only lowercase 64-character SHA-256 hashes (`AEGIS_API_KEYS`).
- Verification executes in constant time using `hmac.compare_digest` to eliminate timing side-channel attacks.
- Plaintext API keys are scrubbed from logs and never written to audit trails.

### C. Scoped Demo Mode Authentication
- When `AEGIS_DEMO_MODE=true`, scoped demo credentials (`aegis-demo-token-sandbox`) resolve to a restricted `TenantContext(tenant_id="demo-tenant", roles={"viewer", "editor"})`.
- If `AEGIS_DEMO_MODE=false`, demo tokens are unconditionally rejected with `401 Unauthorized`.

---

## 3. Data Governance & Right to Erasure

1. **Tamper-Evident Audit Logging:**
   - Append-only log file (`data/audit.log`) using cryptographic SHA-256 hash chaining.
   - Each event hash is computed as:
     $$\text{Hash}_i = \text{SHA256}(\text{Hash}_{i-1} \parallel \text{JSON}(\text{Event}_i))$$
   - Rooted at genesis hash $0^{64}$. Tamper detection completes in $O(N)$ and halts on checksum divergence.
2. **Cascading Document Deletion (GDPR Article 17):**
   - Atomically deletes document metadata, raw byte payloads, extracted chunks, and vector index embeddings within 500ms.
   - Generates a cryptographic audit event logging the deletion inventory.
3. **Automated PII Redaction:**
   - Detects and redacts SSNs, credit card numbers, phone numbers (E.164 and local 7-digit), email addresses, and API keys before indexing.
