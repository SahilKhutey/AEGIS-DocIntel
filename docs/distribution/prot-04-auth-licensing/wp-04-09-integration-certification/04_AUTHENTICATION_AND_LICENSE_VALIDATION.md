# PROT-04.09 — Dossier 04: Authentication & License Validation

## 1. Scope & Objective

This dossier details the integrated verification of **Authentication** (WP-04.01, WP-04.02), **Device Binding** (WP-04.03), and **Cryptographic License Issuance & Validation** (WP-04.04). It confirms that an evaluator cannot spoof identity, forge license claims, or activate unauthorized devices.

---

## 2. Integrated Authentication Flow

The client authentication flow operates in two sequential phases:

### Phase 1: Cryptographic Device Proof-of-Possession
1. The client generates an in-memory **Ed25519 key pair** upon initial installation.
2. The client requests a challenge from `/v1/evaluation/device/challenge` containing:
   - `activation_code`: Authoritative alphanumeric code issued by sales/security.
   - `device_public_key`: Base64/PEM-encoded Ed25519 public key.
   - `installation_id`: Client-generated hardware/instance GUID.
3. The server computes a canonical message:
   $$\text{canonical} = \text{challenge\_id} \parallel \text{nonce} \parallel \text{fingerprint} \parallel \text{installation\_id}$$
   and sets a strict 5-minute expiration window.
4. The client signs $\text{canonical}$ with its Ed25519 private key.
5. The client submits the challenge response to `/v1/evaluation/device/activate`.
6. The server validates:
   - Single-use challenge consumption (anti-replay).
   - Cryptographic signature against `device_public_key`.
   - Activation code status (`ACTIVE`, not `SUSPENDED`, `REVOKED`, or `EXPIRED`).
   - Active device count against `max_devices` limit.

### Phase 2: Authoritative License & Session Issuance
1. Upon successful proof-of-possession, the server signs an authoritative evaluation license with its private Ed25519 key ($K_{\text{issuer}}$).
2. The license document contains:
   - `jti`: Unique license GUID.
   - `sub`: Authoritative evaluator ID.
   - `tenant_id`: Authoritative tenant ID.
   - `product`: `aegis-docintel-protected-demo`.
   - `entitlements`: List of permitted evaluation features.
   - `quotas`: Allowed metric limits.
   - `iat`, `nbf`, `exp`: Validity timeframe (default 14 days).
3. The server issues short-lived session access tokens (`aegis_eval_at_...`, TTL 15 min) and an opaque rotating refresh token.

---

## 3. Cryptographic Verification Results

Empirical results from [device_proof_validation.json](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-09/integration/authentication/device_proof_validation.json) and [cryptographic_verification.json](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-09/integration/licensing/cryptographic_verification.json):

| Test Case | Scenario Description | Expected Outcome | Observed Result |
| :--- | :--- | :--- | :--- |
| **INT-AUTH-001** | Valid activation code + Ed25519 PoP signature | 200 OK (license + session) | **PASSED** |
| **INT-AUTH-003** | Submitting expired challenge response | 400 Bad Request | **PASSED** |
| **INT-AUTH-004** | Submitting replayed challenge response | 400 Bad Request | **PASSED** |
| **INT-AUTH-005** | Forged / corrupted device signature | 400/401 Unauthorized | **PASSED** |
| **INT-AUTH-006** | Exceeding 1-device limit | 409 Conflict | **PASSED** |
| **INT-AUTH-007** | Activation code marked SUSPENDED | 403 Forbidden | **PASSED** |
| **INT-AUTH-008** | Activation code marked REVOKED | 403 Forbidden | **PASSED** |
| **INT-LIC-001** | Cryptographically valid Ed25519 license | Validated successfully | **PASSED** |
| **INT-LIC-002** | Payload tampering (changing `max_documents`) | `LicenseSignatureError` | **PASSED** |
| **INT-LIC-004** | Presentation of unknown `kid` | `LicenseVerificationError` | **PASSED** |
| **INT-LIC-009** | Key rotation produces valid new licenses | New key ID validated | **PASSED** |
| **INT-LIC-010** | Retired key in `VERIFY_ONLY` validates circulating licenses | Historical licenses valid | **PASSED** |
| **INT-LIC-012** | Key compromise marks key invalid | Immediate invalidation | **PASSED** |

---

## 4. Architectural Guarantees Established

1. **No Self-Registration**: Evaluator clients cannot create their own accounts, generate activation codes, or extend their validity periods.
2. **Device Slot Protection**: Each license strictly limits active devices (default 1). Transferring to a new machine requires an emergency recovery code.
3. **Cryptographic Anti-Tamper**: Any modification to license claims immediately breaks the EdDSA signature.
