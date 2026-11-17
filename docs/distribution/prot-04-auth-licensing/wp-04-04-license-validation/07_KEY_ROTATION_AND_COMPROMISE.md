# WP-04.04 Dossier 07: Key Rotation & Compromise Response

**Work Package:** PROT-04.04  
**Title:** Cryptographic Key Rotation Protocol & Emergency Incident Response  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Zero-Downtime Key Rotation Protocol

Cryptographic hygiene requires periodic rotation of signing keys without disrupting currently active evaluation sessions.

### 1.1 Rotation Sequence
```mermaid
sequenceDiagram
    autonumber
    actor Admin as Security Admin
    participant Gateway as Evaluation Gateway
    participant KeyReg as SigningKeyRegistry
    participant Issuer as License Issuer
    actor ClientA as Existing Evaluator (Old Token)
    actor ClientB as New Evaluator (New Token)

    Admin->>Gateway: POST /v1/admin/evaluation/signing-keys/rotate (new_kid)
    Gateway->>KeyReg: rotate_key(new_kid)
    Note over KeyReg: Current active key (kid-01) -> VERIFY_ONLY<br/>New key (kid-02) -> ACTIVE_SIGNING
    KeyReg-->>Gateway: Rotation Complete
    Gateway-->>Admin: HTTP 200 OK

    Note over ClientA,Gateway: Verification of in-flight license
    ClientA->>Gateway: Request with Token (signed with kid-01)
    Gateway->>KeyReg: Query kid-01
    KeyReg-->>Gateway: Key is VERIFY_ONLY (Valid)
    Gateway-->>ClientA: Signature Verified (Success)

    Note over ClientB,Gateway: Issuance of new license
    Admin->>Gateway: POST /v1/admin/evaluation/licenses
    Gateway->>KeyReg: Get Active Key
    KeyReg-->>Gateway: kid-02 (ACTIVE_SIGNING)
    Gateway->>Issuer: Sign with kid-02
    Issuer-->>ClientB: Token signed with kid-02
```

### 1.2 Administrative API: Key Rotation (`LIC-029`)
- **Route:** `POST /v1/admin/evaluation/signing-keys/rotate`
- **Guarded by:** `require_admin_auth`
- **Action:** Generates a new Ed25519 key pair, assigns the new `kid`, sets status to `ACTIVE_SIGNING`, and moves the predecessor key to `VERIFY_ONLY`.
- **Guarantee:** Pre-existing licenses continue to pass signature verification until their expiry dates (`LIC-027`), but new licenses are immediately signed with the new key (`LIC-029`).

---

## 2. Emergency Compromise Response Protocol

In the event that an Ed25519 private key is compromised, leaked, or exposed, the platform must react immediately to prevent unauthorized license forging.

### 2.1 Compromise Sequence
```mermaid
sequenceDiagram
    autonumber
    actor SecOps as Incident Response Lead
    participant Gateway as Evaluation Gateway
    participant KeyReg as SigningKeyRegistry
    participant LicenseRepo as LicenseRepository
    actor Attacker as Attacker (Possessing Leaked Key)
    actor Victim as Legitimate Evaluator (Token with Leaked Key)

    SecOps->>Gateway: POST /v1/admin/evaluation/signing-keys/{kid}/compromise
    Gateway->>KeyReg: compromise_key(kid, reason="Private key leaked")
    Note over KeyReg: Key status -> COMPROMISED<br/>Public key retained ONLY for audit/identification
    Gateway->>LicenseRepo: Mark associated active licenses as REVOKED
    Gateway-->>SecOps: Compromise Confirmed (HTTP 200)

    Note over Attacker,Gateway: Forged token attempt
    Attacker->>Gateway: Submit Forged Token (signed with compromised kid)
    Gateway->>KeyReg: Query key status for kid
    KeyReg-->>Gateway: Key status is COMPROMISED
    Gateway-->>Attacker: HTTP 401 Unauthorized (LicenseVerificationError)

    Note over Victim,Gateway: Victim token re-issuance
    Victim->>Gateway: Submit Request with Old Token
    Gateway-->>Victim: HTTP 401 Unauthorized (Key Compromised)
    SecOps->>Gateway: POST /v1/admin/evaluation/licenses/{id}/reissue
    Gateway-->>Victim: New Token signed with rotated, secure key
```

### 2.2 Administrative API: Key Compromise (`LIC-026`)
- **Route:** `POST /v1/admin/evaluation/signing-keys/{kid}/compromise`
- **Guarded by:** `require_admin_auth`
- **Action:**
  1. Sets key status to `COMPROMISED`.
  2. Permanently removes the private key from active memory.
  3. Rejects any subsequent signature verification requests presenting this `kid` immediately.
  4. Optionally updates `LicenseRepository` to revoke or flag all licenses originally issued with this `kid`.
