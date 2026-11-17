# Dossier 01: Evaluation Session Lifecycle Architecture

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Evaluation Gateway / Session Subsystem`  
**Compliance Target:** PROT-04 Specifications  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. Executive Summary

The AEGIS-DocIntel Protected Demo Edition enforces strict server-authoritative session lifecycle controls. A downloaded evaluator client can never self-issue, extend, or maintain a session without continuous, authenticated server consensus.

Every evaluator session couples:
1. **Authenticated Evaluator Identity:** Verified through cryptographic device challenge or activation code.
2. **Bound Registered Hardware Device:** Validated against hardware fingerprint and device keypair.
3. **Cryptographically Signed License:** Validated Ed25519 evaluation license.
4. **Isolated Tenant Sandbox:** Strict `tenant-{license_id}` isolation boundary.

```mermaid
flowchart TD
    subgraph Client["Evaluator Client (Local Desktop)"]
        UI["Protected Demo GUI"]
        CookieJar["Secure Cookie Store (__Host-aegis_refresh)"]
        Memory["In-Memory Bearer Token (600s TTL)"]
    end

    subgraph Gateway["Evaluation Gateway Boundary"]
        Ingress["Ingress Hardening & Error Sanitizer"]
        AuthFilter["Session Validation & Entitlement Filter"]
        RotationSvc["Atomic Refresh Rotation Engine"]
        RevokeReg["Real-Time Revocation Registry"]
    end

    subgraph Store["Server-Authoritative State"]
        SessRepo["Session Repository (Multi-Indexed)"]
        TokenRepo["Refresh Token Store (SHA-256 Hashes Only)"]
        AuditLog["Append-Only Audit Ledger"]
    end

    UI -->|Bearer at_xxx| Ingress
    CookieJar -.->|__Host Cookie| Ingress
    Ingress --> AuthFilter
    AuthFilter --> RevokeReg
    AuthFilter --> SessRepo
    RotationSvc --> TokenRepo
    RotationSvc --> AuditLog
    RevokeReg --> SessRepo
```

---

## 2. Core Security Invariants

1. **Server Authority Invariant:** Client-side deletion of local tokens or browser cookies is not considered revocation. The server maintains authoritative session and token-family state.
2. **Zero Plaintext Secret Storage:** Raw refresh tokens are never persisted in databases, memory caches, logs, or telemetry. Only SHA-256 digests are stored at rest.
3. **Short-Lived Ephemeral Access:** Access tokens expire strictly after 600 seconds (10 minutes). Evaluator clients must continuously prove possession of valid rotating refresh credentials.
4. **Atomic Rotation & Replay Lockdown:** Every refresh consumes the active refresh token and issues a replacement. Any attempt to present an already-consumed refresh token immediately revokes all sessions in that token family.
5. **Cascading Revocation Invariant:** Revoking an evaluation license, deactivating a device, or suspending an evaluator immediately terminates all dependent active sessions with sub-50ms latency.
