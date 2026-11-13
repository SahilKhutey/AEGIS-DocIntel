# WP-04.01: Strategic Security Architecture Decisions

**Document:** `07_SECURITY_DECISIONS.md`  
**Work Package:** PROT-04.01 — Authentication Baseline & Threat Model  
**Component:** Security Governance, Cryptographic Choices & Design Invariants  
**Status:** **RATIFIED & RECORDED**  
**Classification:** Internal Architectural Decision Record (ADR)  

---

## 1. Architectural Decisions Matrix

The following thirteen decisions govern the security architecture of the **AEGIS-DocIntel Protected Demo Edition**:

### Decision 1: Preserve and Strengthen Existing Authentication
- **Selection:** Retain FastAPI `src/api/auth.py` and `src/api/auth_guard.py`; remediate identified gaps.
- **Rationale:** The repository already possesses a mature, tested PyJWT RS256 and API-key verification engine. Replacing it with a greenfield authentication framework would introduce unnecessary regression risks, delay the launch timeline, and split codebase maintenance.

### Decision 2: Distinct Cryptographic Algorithms for Distinct Purposes
- **Selection:** 
  - **RS256 (RSA 2048/4096):** Used for session tokens and backend microservice communication.
  - **Ed25519 (Edwards-curve Digital Signature):** Used exclusively for evaluation license issuance and offline/online integrity verification.
- **Rationale:** Ed25519 provides compact 64-byte signatures, fast verification performance, and complete immunity to side-channel timing attacks, making it ideal for license files. RS256 remains the enterprise standard for OpenID Connect compatibility.

### Decision 3: Mandatory Issuer and Audience Enforcement
- **Selection:** The Evaluation Gateway strictly mandates:
  - `AEGIS_JWT_ISSUER = "https://auth.aegis-docintel.org"`
  - `AEGIS_JWT_AUDIENCE = "aegis-evaluation-gateway"`
- **Rationale:** Prevents cross-service token replay where a valid enterprise microservice token is reused to access the evaluation tier.

### Decision 4: Principle of Least Privilege in Evaluator Roles
- **Selection:** Evaluators are restricted to `viewer` or `editor` roles. Administrative permissions (`users.manage`, `platform.admin`, `review_admin`) return `HTTP 403 Forbidden` at the gateway layer (`ENT-001`, `ENT-002`).
- **Rationale:** Even if an evaluator patches their local frontend JavaScript to display administrative UI buttons, the trusted gateway denies the underlying API calls.

### Decision 5: Elimination of API Keys from Demo Packaging
- **Selection:** API keys are restricted to trusted server-to-server automation. No static API keys or shared gateway secrets are bundled into the downloadable demo package.
- **Rationale:** Static keys in client binaries or configuration files are immediately discoverable by reverse engineers.

### Decision 6: Remote License State Authority
- **Selection:** The evaluation license is verified by the remote Evaluation Gateway, not by a local Python script running inside the user's container.
- **Rationale:** A license engine executed entirely on the client machine can be easily patched or bypassed.

### Decision 7: Public-Key Cryptographic Device Binding
- **Selection:** The demo launcher generates an asymmetric keypair locally on first launch and registers the public key with the gateway during activation, enforcing a strict 1-device limit (`DEV-002`).
- **Rationale:** Avoids privacy concerns and false positives associated with collecting MAC addresses, motherboard serials, or OS telemetry, while cryptographically binding sessions to a specific client installation.

### Decision 8: Short-Lived Sessions with Rotating Refresh Tokens
- **Selection:** Access tokens expire in 600 seconds (10 minutes). Refresh tokens are single-use; reusing a previously consumed refresh token revokes the entire session family (`SESSION-001`).
- **Rationale:** Limits exposure window if tokens are extracted from memory and detects token theft automatically.

### Decision 9: Sub-15ms Real-Time Revocation Registry
- **Selection:** Authoritative in-memory blacklist checked on every incoming gateway request.
- **Rationale:** Enables instant revocation of compromised licenses, terms violations, or expired trials without waiting for token TTL expiration.

### Decision 10: Two-Phase Atomic Quota Accounting
- **Selection:** Quotas (documents, pages, queries) use a two-phase reservation protocol (`reserve_quota` -> `commit_quota` / `rollback_quota`) protected by `threading.Lock`.
- **Rationale:** Eliminates concurrent race conditions (e.g. sending 50 parallel requests to exceed a 15-document limit).

### Decision 11: Zero-Leakage Sanitized Audit Telemetry
- **Selection:** Gateway audit logs pass through regex redactors that strip JWTs, API keys, activation codes, and raw document contents before writing to disk.
- **Rationale:** Ensures compliance with security audit standards and prevents credential leakage into log analysis pipelines.

### Decision 12: Deny-by-Default Ingress & Telemetry Containment
- **Selection:** Outermost ASGI `AuthGuardMiddleware` blocks all unlisted paths with 401. The `/metrics` Prometheus scrape endpoint is isolated to an internal Docker network.
- **Rationale:** Prevents tenant enumeration and unauthorized access to newly registered API routes.

### Decision 13: Absolute Protection of Core Intellectual Property
- **Selection:** The core proprietary intelligence platform, model weights, prompts, and vector pipelines remain hosted exclusively on private infrastructure and are never packaged into the demo distribution.
- **Rationale:** Technical obfuscation is insufficient against a determined reverse engineer with root access; architectural isolation is the only defensible IP boundary.
