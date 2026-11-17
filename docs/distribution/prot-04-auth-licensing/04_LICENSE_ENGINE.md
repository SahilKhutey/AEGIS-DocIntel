# PROT-04.04: Evaluation License Engine & Cryptography

**Work Package:** PROT-04.04  
**Target:** Ed25519 Cryptographic Signing, Compact JWS Serialization, Key Rotation, Authoritative Server State & Tamper Resistance  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**  
**Detailed Dossiers:** [wp-04-04-license-validation/](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/docs/distribution/prot-04-auth-licensing/wp-04-04-license-validation/)

---

## 1. Cryptographic Foundation

Evaluation licenses are signed using **Ed25519 (Edwards-curve Digital Signature Algorithm over Curve25519)** via RFC 7515 Compact JWS serialization (`typ="AEGIS-EVALUATION-LICENSE"`, `alg="EdDSA"`, `kid`):
- **High Performance:** Microsecond signing and verification with low computational footprint.
- **Deterministic Signatures:** Eliminates signature malleability and entropy exhaustion risks.
- **Compact Representation:** 64-byte signatures and 32-byte public keys minimizing token transmission overhead.
- **Fail-Closed Protection:** Rejection of algorithm switching (HS256, none, RS256), token-controlled remote keys (`jku`/`x5u`/`jwk`), and tokens over 8,192 bytes.

### Key Separation & Distribution
| Key Material | Storage Location | Distributed to Client? | Purpose |
| :--- | :--- | :--- | :--- |
| **Root Private Signing Key** | In-Memory `SigningKeyRegistry` / Cloud KMS | **NEVER DISTRIBUTED** (`LIC-037`, `LIC-038`) | Signs evaluation licenses |
| **Gateway Public Verification Key** | Evaluation Gateway & Client Demo Bundle | Distributed publicly | Verifies Ed25519 signatures |
| **Client Device Private Key** | Client Device Secure Storage | **NEVER UPLOADED** | Signs proof-of-possession nonces |
| **Client Device Public Key** | Registered on Evaluation Gateway | Uploaded on activation | Binds session to client device |

---

## 2. Key Lifecycle & Rotation Management

The `SigningKeyRegistry` (`services/evaluation_gateway/signing_key_registry.py`) manages keys across four strict states:
1. `ACTIVE_SIGNING`: Current signing key for minting new licenses and verifying active tokens.
2. `VERIFY_ONLY`: Previous signing key maintained after rotation (`rotate_key()`) to verify in-flight tokens without permitting new signatures (`LIC-027`).
3. `RETIRED`: Decommissioned key that rejects all operations (`LIC-028`).
4. `COMPROMISED`: Quarantined key that immediately revokes all tokens bearing its `kid` (`LIC-026`).

---

## 3. Authoritative License Repository

The `LicenseRepository` (`services/evaluation_gateway/license_repository.py`) maintains server-side authoritative state:
- **Statuses:** `DRAFT`, `ISSUED`, `ACTIVE`, `SUSPENDED`, `REVOKED`, `EXPIRED`.
- **Idempotency:** Cached lookups for idempotency keys avoid duplicate license generation (`LIC-004`).
- **Administrative Lifecycle:** Endpoints for suspension (`/suspend`), revocation (`/revoke`), renewal (`/renew`), and reissuance (`/reissue`).
- **Fail-Closed Policy:** Authoritative verification fails closed if the database is unreachable (`LIC-031`).

---

## 4. Multi-Stage Validation Pipeline

The verification engine in `services/evaluation_gateway/license.py` enforces a seven-stage check:
1. **Size Guard:** Raw token length $\le 8,192\text{ bytes}$ (`LIC-035`).
2. **Format Guard:** Exact 3-part period-delimited Compact JWS (`LIC-036`).
3. **Header Guard:** Pinned to `alg="EdDSA"` and rejects `jku`, `x5u`, `x5c`, `jwk` (`LIC-008`, `LIC-034`).
4. **Key Registry Lookup:** Validates `kid` exists and is `ACTIVE_SIGNING` or `VERIFY_ONLY` (`LIC-009`, `LIC-026`).
5. **Cryptographic Verification:** Ed25519 signature verified against header and payload (`LIC-005`, `LIC-006`, `LIC-007`).
6. **Claim & Schema Guard:** Checks `iss`, `aud`, `exp`, `nbf`, `license_type`, `policy_version`, `device_limit`, `features`, and `quotas` (`LIC-010` - `LIC-018`).
7. **Authoritative Cross-Check:** Server-side validation of evaluator ID, tenant ID, device ID, and active status (`LIC-019` - `LIC-024`).

---

## 5. Formal Certification & Verification Evidence

- **Dedicated Suite:** 40/40 tests passed in `tests/security/evaluation/test_license_validation_protocol.py` (`LIC-001` through `LIC-040`).
- **Full System Regression:** 187/187 tests passed across evaluation security, production auth hardening, distribution security, and demo suites.
- **Audit Artifacts:** Full evidence generated in `audit/prot-04-04/` including `reports/findings.csv` and `reports/signoff.json`.
- **Dossiers:** Complete 12-document technical specification published in `docs/distribution/prot-04-auth-licensing/wp-04-04-license-validation/`.
