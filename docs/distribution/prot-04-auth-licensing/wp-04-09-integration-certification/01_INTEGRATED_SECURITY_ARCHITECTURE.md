# PROT-04.09 — Dossier 01: Integrated Security Architecture

## 1. Executive Summary

Work Package **PROT-04.09** represents the final release gate and end-to-end integration verification for the entire **PROT-04** security initiative (*Authentication, Licensing & Entitlement Security*) within the **AEGIS-DocIntel Protected Demo Edition**.

This dossier specifies the integrated, multi-tier security architecture that unifies:
1. **WP-04.01 / 04.02**: Production Authentication Hardening & Identity Assurance
2. **WP-04.03**: Evaluation Activation & Device Proof-of-Possession
3. **WP-04.04**: Cryptographic License Issuance, Verification & Key Lifecycle
4. **WP-04.05**: Entitlement Enforcement, RBAC & Capability Governance
5. **WP-04.06**: Quotas, Atomic Reservations & Resource Limiting
6. **WP-04.07**: Session Lifecycle, Rotating Tokens & Instant Revocation
7. **WP-04.08**: Security Audit, Monitoring & Operations
8. **WP-04.09**: Private Engine Isolation & Gateway Boundary Defense

---

## 2. Integrated Security Topology

```
+---------------------------------------------------------------------------------------+
|                                EVALUATOR ENVIRONMENT                                   |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                       AEGIS Protected Desktop / Web Client                    |   |
|   |  - Zero Local Private Keys / Signing Authority                                |   |
|   |  - Ephemeral Memory Session Access Tokens (TTL 15m)                           |   |
|   |  - HttpOnly SameSite Secure __Host-aegis_refresh Cookie                       |   |
|   |  - Hardware Bound Ed25519 Device Key Pair                                     |   |
|   +---------------------------------------+---------------------------------------+   |
+-------------------------------------------|-------------------------------------------+
                                            | HTTPS / WSS (Strict TLS 1.3)
                                            v
+---------------------------------------------------------------------------------------+
|                               SECURE EVALUATION GATEWAY                               |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   | [1. Ingress & Auth Guard]                                                     |   |
|   | - CORS Strict Origin Enforcement                                              |   |
|   | - Token Format Validation (Reject dev-* tokens & unauthenticated metrics)     |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|   +---------------------------------------v---------------------------------------+   |
|   | [2. Device Proof & Session Validation]                                        |   |
|   | - Ed25519 Canonical Challenge-Response Proof-of-Possession                      |   |
|   | - Refresh Token Rotation & Replay Family Revocation                           |   |
|   | - Instant Revocation Registry Check (< 50ms propagation SLA)                   |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|   +---------------------------------------v---------------------------------------+   |
|   | [3. Authoritative Entitlement & Quota Enforcement]                            |   |
|   | - Server-Side Capability Evaluation (Ignoring client role/tenant claims)      |   |
|   | - Dynamic Administrative Overrides                                            |   |
|   | - Atomic Quota Reservations (Sliding-window daily & concurrency caps)        |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|   +---------------------------------------v---------------------------------------+   |
|   | [4. Private Engine Guard (HMAC Internal Attestation)]                         |   |
|   | - Single-Use Quota Reservation Binding                                         |   |
|   | - Expiring Service Tokens (TTL 60s)                                           |   |
|   | - Evaluator Role Isolation (Zero platform administration allowed)             |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           | Internal Service Network (Loopback/VPC)   |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                             PRIVATE INTELLIGENCE ENGINE                       |   |
|   |  - Proprietary Document Ingestion & Parser Pipelines                          |   |
|   |  - Multi-Document Contradiction Analysis                                      |   |
|   |  - LLM Provider Credentials & Prompt Templates                                |   |
|   +-------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------+
```

---

## 3. Core Architectural Security Invariants

The integrated platform enforces eight non-negotiable architectural guarantees:

1. **Zero Client Trust Invariant**: No security decisions, entitlement calculations, role assignments, or tenant boundaries are derived from unverified client inputs. All claims are verified against authoritative backend repositories.
2. **Private Engine Isolation**: The core intelligence engine and provider credentials are never distributed in evaluator packages. Gateway-to-engine calls require cryptographic HMAC-SHA256 tokens linked to single-use reservation nonces.
3. **Cryptographic Device Binding**: Activation requires digital signature proof-of-possession over a server-issued challenge nonce using an Ed25519 key pair generated on the client machine.
4. **Atomic Resource Reservations**: Every metered action reserves capacity in memory and ledger before heavy computational execution begins, preventing concurrent race conditions.
5. **Rotating Refresh Token Family Protection**: Refresh tokens are single-use. Presentation of an already-consumed refresh token immediately revokes the entire token family.
6. **Instant Revocation Propagation**: Administrative license revocation cascades to all active sessions, WebSocket connections, and pending engine jobs within < 50ms.
7. **Tamper-Evident Audit Hash Chain**: Every security event is recorded in a cryptographically chained, append-only ledger `H_i = SHA-256(H_{i-1} || Canonical(E_i))`.
8. **Fail-Closed Disaster Recovery**: Database snapshot restoration explicitly re-applies post-snapshot revocations, preventing the resurrection of compromised access.
