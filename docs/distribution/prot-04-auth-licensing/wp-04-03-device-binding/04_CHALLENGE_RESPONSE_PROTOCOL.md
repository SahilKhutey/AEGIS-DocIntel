# WP-04.03 Dossier 04: Challenge-Response Protocol

**Work Package:** PROT-04.03  
**Title:** Two-Stage Asymmetric Proof-of-Possession Challenge Protocol  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  

---

## 1. Protocol Sequence Flow

The two-stage proof-of-possession handshake binds the evaluator's local key pair to their evaluation license without transmitting private credentials.

```mermaid
sequenceDiagram
    autonumber
    actor Evaluator as Evaluator
    participant Client as Downloadable Demo App
    participant Gateway as AEGIS Evaluation Gateway
    participant Registry as Device Registry & Quota Store

    Note over Evaluator,Client: Local Initialization
    Client->>Client: Generate Local Key Pair (priv_key, pub_key)
    Client->>Client: Read local installation_id (e.g. inst-uuid)

    Note over Client,Gateway: Stage 1: Challenge Request
    Client->>Gateway: POST /v1/evaluation/device/challenge<br/>{activation_code, device_public_key, installation_id}
    Gateway->>Gateway: Check Ingress Rate Limit (Max 10 / IP / hr)
    Gateway->>Gateway: Lookup activation_code via HMAC-SHA256
    Gateway->>Gateway: Parse device_public_key & Compute SHA-256 Fingerprint
    Gateway->>Registry: Pre-check Active Devices (Limit: 1)
    alt Device Limit Exceeded (> 1)
        Gateway-->>Client: HTTP 409 Conflict (DEVICE_LIMIT_EXCEEDED)
    else Slot Available
        Gateway->>Gateway: Generate challenge_id (UUIDv4) & nonce (256-bit random)
        Gateway->>Gateway: Construct canonical_message & set expires_at (now + 300s)
        Gateway->>Gateway: Store ChallengeRecord (consumed=False)
        Gateway-->>Client: HTTP 200 OK<br/>{challenge_id, nonce, canonical_message, expires_at, algorithm}
    end

    Note over Client,Gateway: Stage 2: Proof-of-Possession Activation
    Client->>Client: Sign canonical_message using local priv_key
    Client->>Gateway: POST /v1/evaluation/device/activate<br/>{challenge_id, signature, installation_id}
    Gateway->>Gateway: Retrieve ChallengeRecord by challenge_id (404 if missing)
    Gateway->>Gateway: Check consumed == False (400 if replayed: DEV-010)
    Gateway->>Gateway: Check now < expires_at (400 if expired: DEV-009)
    Gateway->>Gateway: Check installation_id matches challenge (400 if mismatch: DEV-012)
    Gateway->>Gateway: Verify digital signature with registered public_key (401 if invalid: DEV-007)
    Gateway->>Gateway: Mark challenge consumed = True (Single-Use Invariant)
    Gateway->>Registry: Atomically Register Device (Max 1 Device Enforcement: DEV-002)
    Gateway->>Gateway: Issue Ed25519-Signed License & Session Tokens (access_token, refresh_token)
    Gateway->>Gateway: Generate Emergency Recovery Code (REC-XXXX-YYYY)
    Gateway-->>Client: HTTP 200 OK<br/>{license, session, entitlements, recovery_code, public_key_pem}
    Client->>Client: Store access_token in memory & display Recovery Code
```

---

## 2. Canonical Challenge Message Specification

To prevent signature repurposing, replay attacks, or cross-protocol manipulation, the message signed by the client is formatted canonically:

```
AEGIS-EVAL-DEVICE-PROOF-V1
challenge_id=45c43d83-4a11-4770-b49c-f127cb46db07
nonce=7n8K_P9xR2tL6mQ0vW4yZ1aC3eG5iK8m
public_key_fingerprint=8d3e91f16f2c0cbba5b0981b2dae2ec112bf8bfa2e9a3b632dbb73e5bf2ecb61
installation_id=inst-win-dev01
```

### Protocol Fields:
1. **Header:** Pinned protocol identifier `AEGIS-EVAL-DEVICE-PROOF-V1`.
2. **`challenge_id`:** Server-generated UUID uniquely indexing this challenge instance.
3. **`nonce`:** Cryptographic 256-bit entropy ensuring signature uniqueness across time.
4. **`public_key_fingerprint`:** SHA-256 fingerprint of the client's public key, preventing key substitution.
5. **`installation_id`:** Hardware/installation identifier binding proof to specific machine instance.

---

## 3. Cryptographic Invariants & Verification Guarantees

| Invariant ID | Security Property | Guaranteed Outcome |
| :--- | :--- | :--- |
| **INV-CH-01** | **Single-Use Consumption** | A `challenge_id` can be activated exactly once (`consumed=True`). Subsequent activations reject with `HTTP 400 CHALLENGE_ALREADY_CONSUMED` (`DEV-010`). |
| **INV-CH-02** | **Strict TTL Expiration** | Challenges expire 300 seconds after creation. Expired submissions reject with `HTTP 400 CHALLENGE_EXPIRED` (`DEV-009`). |
| **INV-CH-03** | **Non-Repudiation** | Only the possessor of the private key corresponding to `device_public_key` can generate a valid signature (`DEV-007`). |
| **INV-CH-04** | **Message Integrity** | Flipping any bit in `canonical_message` invalidates the signature and fails verification (`DEV-008`, `DEV-029`). |
| **INV-CH-05** | **Installation ID Binding** | If `installation_id` in Stage 2 differs from Stage 1, the request fails with `HTTP 400 INSTALLATION_MISMATCH` (`DEV-012`). |
