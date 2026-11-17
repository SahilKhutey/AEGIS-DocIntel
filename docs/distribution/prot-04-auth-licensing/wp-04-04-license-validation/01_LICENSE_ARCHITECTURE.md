# WP-04.04 Dossier 01: License Architecture

**Work Package:** PROT-04.04  
**Title:** License Issuance & Cryptographic Validation Subsystem Architecture  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Executive Architectural Overview

The AEGIS-DocIntel Protected Demo Edition requires a tamper-proof, cryptographically verifiable licensing mechanism that guarantees evaluators cannot forge licenses, extend evaluation periods, alter usage quotas, or bypass device limits on untrusted client hardware.

To achieve this without relying on brittle client-side obfuscation or easily patched local checks, WP-04.04 establishes a **Cryptographically Signed, Authoritatively Validated Licensing Architecture**.

The core principles of this architecture are:
1. **Asymmetric JWS Serialization**: All evaluation licenses are encoded as RFC 7515 Compact JSON Web Signatures (JWS) using **EdDSA with Curve25519 (`Ed25519`)**, ensuring signatures cannot be forged without the private signing key.
2. **Private Signing Authority**: The private Ed25519 signing keys reside strictly within the secure Evaluation Gateway infrastructure. Zero private signing keys are bundled into downloadable client builds or stored in public repositories.
3. **Authoritative Server Cross-Check**: While the evaluation client can inspect license claims offline for display purposes, **authorization and entitlement grant are strictly authoritative and server-enforced**. Every API call verifies the license signature, key validity, tenant identity, device binding, and current status against the server-side `LicenseRepository`.
4. **Fail-Closed Governance**: Any anomaly—tampered payload, invalid signature, unknown key ID (`kid`), expired timestamp, suspended or revoked status, or network authority failure—results in immediate, fail-closed denial of service.

---

## 2. Security Trust Boundary

```mermaid
flowchart TD
    subgraph Admin ["AEGIS Administrative Boundary (Protected)"]
        AdminUser["AEGIS Administrator"]
        AdminCLI["Admin Management Route / CLI"]
        AdminKey["X-Admin-Key / Bearer Token"]
    end

    subgraph Gateway ["AEGIS Evaluation Gateway (Authoritative Server)"]
        AuthCheck["Admin Auth Guard (require_admin_auth)"]
        Issuer["Private License Issuer"]
        KeyRegistry["SigningKeyRegistry<br/>(ACTIVE, VERIFY_ONLY, RETIRED, COMPROMISED)"]
        Ed25519Signer["Ed25519 Signer Engine"]
        LicenseRepo["LicenseRepository<br/>(DRAFT, ISSUED, ACTIVE, SUSPENDED, REVOKED, EXPIRED)"]
        RevocationReg["RevocationRegistry & In-Flight Cache"]
        ValidationEngine["License Validation Pipeline"]
    end

    subgraph Client ["Evaluator Client Machine (Untrusted Boundary)"]
        DemoClient["AEGIS Demo Desktop / Web Client"]
        LocalTokenStore["Local License Token Store (compact JWS)"]
        ReqVerify["API Requests (Bearer License Token)"]
    end

    AdminUser --> AdminCLI
    AdminCLI -->|Admin Credentials| AdminKey
    AdminKey --> AuthCheck
    AuthCheck --> Issuer
    Issuer --> KeyRegistry
    KeyRegistry --> Ed25519Signer
    Ed25519Signer --> LicenseRepo
    LicenseRepo -->|Issued Compact JWS| DemoClient

    DemoClient --> LocalTokenStore
    LocalTokenStore --> ReqVerify
    ReqVerify --> ValidationEngine

    ValidationEngine -->|1. Parse & Size Check <8KB| ValidationEngine
    ValidationEngine -->|2. Check Algorithm EdDSA & kid| KeyRegistry
    ValidationEngine -->|3. Cryptographic Signature Verify| ValidationEngine
    ValidationEngine -->|4. Timestamp & Claim Checks| ValidationEngine
    ValidationEngine -->|5. DB Cross-Check (Tenant/Device/Status)| LicenseRepo
    ValidationEngine -->|6. Revocation Check| RevocationReg
```

---

## 3. Subsystem Component Breakdown

| Subsystem Component | Path in Repository | Primary Responsibility |
| :--- | :--- | :--- |
| **Signing Key Registry** | `services/evaluation_gateway/signing_key_registry.py` | Manages Ed25519 key lifecycle, status transitions (`ACTIVE_SIGNING`, `VERIFY_ONLY`, `RETIRED`, `COMPROMISED`), key rotation, and emergency compromise invalidation. |
| **Authoritative License Repository** | `services/evaluation_gateway/license_repository.py` | Serves as authoritative database for evaluation licenses, lifecycle tracking, idempotency enforcement, suspension, revocation, renewal, and reissuance. |
| **License Engine & JWS Serialization** | `services/evaluation_gateway/license.py` | Generates RFC 7515 Compact JWS tokens, parses headers, executes strict cryptographic verification, claim validation, and server-side state cross-checks. |
| **Revocation Registry** | `services/evaluation_gateway/revocation.py` | In-memory and persistent revocation list for high-speed checking with explicit cache-clearing mechanisms. |
| **Evaluation Gateway App & Admin Routes** | `services/evaluation_gateway/app.py` | Exposes authenticated administrative issuance/management endpoints and public evaluator verification endpoints. |
| **Comprehensive Verification Protocol** | `tests/security/evaluation/test_license_validation_protocol.py` | Automated test suite verifying 40 security scenarios (`LIC-001` through `LIC-040`). |

---

## 4. Threat Mitigation Summary

| Threat ID | Threat Description | Architectural Mitigation | Test Evidence |
| :--- | :--- | :--- | :--- |
| **TH-LIC-01** | License Tampering / Quota Elevation | RFC 7515 Compact JWS signed with Ed25519. Any bit flip in header or payload invalidates the signature. | `LIC-006`, `LIC-007` |
| **TH-LIC-02** | Algorithm Substitution Attack | Validation engine strictly pins `alg="EdDSA"`. Tokens signed with `HS256`, `none`, or `RS256` are rejected prior to evaluation. | `LIC-008` |
| **TH-LIC-03** | Token-Controlled Key Injection (`jku`/`x5u`) | Header validation rejects tokens containing remote key URLs or inline JWKs, enforcing server-managed key IDs only. | `LIC-034` |
| **TH-LIC-04** | Denial of Service via Huge Payloads | Ingress size check rejects any license token exceeding 8,192 bytes before cryptographic parsing. | `LIC-035` |
| **TH-LIC-05** | Unauthorized License Issuance | Admin endpoints protected by `require_admin_auth` verifying secret administrative credentials. | `LIC-002` |
| **TH-LIC-06** | Compromised Signing Key Abuse | Key registry allows immediate transition of a key to `COMPROMISED`, atomically invalidating all tokens signed by that key. | `LIC-026` |
| **TH-LIC-07** | Clock Manipulation / Rollback | Expiration (`exp`) and Not-Before (`nbf`) claims evaluated against server-side monotonic time; client clock skew rejected. | `LIC-014`, `LIC-015`, `LIC-032` |
| **TH-LIC-08** | Offline / Disconnected State Spoofing | Authoritative server DB cross-check validates evaluator ID, tenant ID, device ID, and lifecycle status on every request. | `LIC-019`, `LIC-020`, `LIC-022` |
