# PROT-04.09 — Dossier 02: Component Integration Matrix

## 1. System Integration Overview

The AEGIS-DocIntel Protected Demo Edition integrates multiple specialized security subsystems developed across PROT-04.01 through PROT-04.08. This matrix defines the precise component boundaries, communication protocols, and cryptographic data exchanges.

---

## 2. Component Interaction Matrix

| Subsystem | Originating Package | Integrated Upstream | Integrated Downstream | Communication Boundary | Cryptographic Protocol |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Authentication Guard** | WP-04.02 | Evaluator Web / Desktop UI | Evaluation Gateway Ingress | HTTP Reverse Proxy / ASGI Middleware | Strict JWT Bearer Validation |
| **Activation Service** | WP-04.03 | Evaluation Ingress | Key Registry & Device Store | Internal In-Memory / SQLite Repository | Ed25519 Canonical PoP Challenge |
| **License Authority** | WP-04.04 | Activation Service | License Repository & Revocation Registry | In-Memory Authoritative Store | Ed25519 JWS Compact Serialization (RFC 7515) |
| **Entitlement Service** | WP-04.05 | Gateway Dependency (`get_current_entitlement`) | Application API Handlers | ASGI Dependency Injection | Server-Evaluated Capability Bitmask |
| **Quota Manager** | WP-04.06 | Application API Handlers | Counter Repository & Usage Ledger | Thread-Safe ThreadPool / Lock | Two-Phase Atomic Reservation & Settlement |
| **Session Manager** | WP-04.07 | Session Refresh & Logout Handlers | Session Repository & Family Registry | Redis / In-Memory Session Table | Rotating Opaque Hashes (SHA-256) |
| **Private Engine Guard** | WP-04.09 | Evaluation Gateway Handlers | Private Engine Ingress | Local RPC / Unix Domain Socket / VPC | HMAC-SHA256 Token with Reservation Nonce |
| **Security Ops & Audit** | WP-04.08 | All Gateway Subsystems | SIEM / Audit Append-Only Ledger | Async Event Bus / Local Ring Buffer | SHA-256 Chained Hash Log |

---

## 3. Inter-Service Handshake & Data Flow

### 3.1 First-Time Evaluator Activation Handshake

```mermaid
sequenceDiagram
    autonumber
    actor Evaluator as Evaluator Client
    participant Gateway as Evaluation Gateway
    participant ActSvc as Activation Service
    participant LicSvc as License Authority
    participant DevStore as Device Registry
    participant SessSvc as Session Manager
    participant Audit as Audit Logger

    Evaluator->>Gateway: POST /v1/evaluation/device/challenge {activation_code, device_pubkey, installation_id}
    Gateway->>ActSvc: create_device_challenge(...)
    ActSvc->>DevStore: Check device quota (< max_devices)
    ActSvc-->>Evaluator: 200 OK {challenge_id, canonical_message, nonce, expires_at}
    
    Evaluator->>Evaluator: Ed25519 Sign canonical_message with private device key
    Evaluator->>Gateway: POST /v1/evaluation/device/activate {challenge_id, signature, installation_id}
    Gateway->>ActSvc: activate_device_with_challenge(...)
    ActSvc->>ActSvc: Verify signature against device_pubkey
    ActSvc->>LicSvc: Issue signed evaluation license (Ed25519 JWS)
    ActSvc->>DevStore: Register active device record
    ActSvc->>SessSvc: Initialize session & token family
    ActSvc->>Audit: Record AUTH_SUCCESS event
    ActSvc-->>Evaluator: 200 OK {license_doc, access_token, refresh_token, recovery_code}
```

### 3.2 Private Engine Operation Handshake

```mermaid
sequenceDiagram
    autonumber
    actor Evaluator as Authenticated Evaluator
    participant Gateway as Evaluation Gateway
    participant Quota as Quota Manager
    participant Guard as Private Engine Guard
    participant Engine as Private Intelligence Engine

    Evaluator->>Gateway: POST /v1/evaluation/query {query: "What is peak FP32?", document_id: "doc-1"}
    Gateway->>Gateway: Validate Session & Entitlement ("intelligence.query")
    Gateway->>Quota: reserve_quota(lic_id, "queries", 1)
    Quota-->>Gateway: reservation_id = "res-94b1..."
    Gateway->>Guard: create_authorized_token(user, tenant, lic, op="doc.query", res_id)
    Guard-->>Gateway: hmac_token
    Gateway->>Engine: POST /internal/v1/engine/execute {token: hmac_token, payload: {...}}
    Engine->>Guard: verify_engine_request(token, expected_op="doc.query")
    Guard-->>Engine: Authorized (EngineAuthContext)
    Engine->>Engine: Run proprietary ingestion & analysis pipeline
    Engine-->>Gateway: 200 OK {response: "...", citations: [...]}
    Gateway->>Quota: settle_reservation(lic_id, res_id, actual_amount=1)
    Gateway-->>Evaluator: 200 OK {answer: "...", citations: [...]}
```
