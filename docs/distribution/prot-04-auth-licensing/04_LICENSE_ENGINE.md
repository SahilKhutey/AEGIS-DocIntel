# PROT-04.04: Evaluation License Engine & Cryptography

**Work Package:** PROT-04.04  
**Target:** Ed25519 Cryptographic Signing, Temporal Expiration, Key Rotation & Tamper Resistance  
**Status:** **IMPLEMENTED & VERIFIED**

---

## 1. Cryptographic Foundation

Evaluation licenses are signed using **Ed25519 (Edwards-curve Digital Signature Algorithm over Curve25519)**:
- High performance (microsecond signing/verification).
- Deterministic signatures (prevents signature malleability).
- Compact key representations (32-byte public keys, 64-byte signatures).
- Immune to side-channel cache attacks.

### Key Separation & Distribution
| Key Material | Storage Location | Distributed to Client? | Purpose |
| :--- | :--- | :--- | :--- |
| **Root Private Signing Key (`private-key.pem`)** | Protected Evaluation Authority / Secret Manager | **NEVER DISTRIBUTED** (`DIST-001`) | Signs evaluation licenses |
| **Gateway Public Verification Key (`public-key.pem`)** | Evaluation Gateway & Client Demo Bundle | Distributed publicly | Verifies Ed25519 signatures |
| **Client Device Private Key** | Client Device Secure Storage | **NEVER UPLOADED** | Signs proof-of-possession nonces |
| **Client Device Public Key** | Registered on Evaluation Gateway | Uploaded on activation | Binds session to client device |

---

## 2. Canonical License Claims Schema

The evaluation claims payload (`distribution/policy/evaluation-license.schema.json`) enforces strict structural validation:

```json
{
  "license_id": "67a14e9b-0294-4d89-9133-784f1b3c9b71",
  "product": "AEGIS_PROTECTED_EVALUATION",
  "tier": "evaluation",
  "version": "1.1.0",
  "policy_version": "1.0",
  "iss": "https://license.aegis.example",
  "aud": "aegis-protected-evaluation",
  "kid": "key-ed25519-v1",
  "status": "ACTIVE",
  "subject": "evaluator-primary",
  "user_id": "evaluator-primary",
  "max_devices": 1,
  "max_workspaces": 1,
  "issued_at": "2026-11-13T04:15:00Z",
  "not_before": "2026-11-13T04:15:00Z",
  "expires_at": "2026-11-27T04:15:00Z",
  "hardware_fingerprint": "workstation-windows",
  "entitlements": [
    "documents.read",
    "documents.upload",
    "intelligence.query",
    "documents.compare",
    "evidence.inspect"
  ],
  "quotas": {
    "max_documents": 5,
    "max_queries_per_day": 20,
    "max_comparisons_per_day": 5,
    "max_file_size_mb": 10,
    "max_storage_mb": 100
  }
}
```

---

## 3. License Validation Rules & State Machine

The verification function `verify_license()` in `services/evaluation_gateway/license.py` evaluates all checks before authorizing an evaluation license:

1. **Signature Verification (`LIC-002`):**
   - The payload dictionary is converted into canonical deterministic JSON bytes (`json.dumps(..., sort_keys=True, separators=(',', ':'))`).
   - The signature is verified with `public_key.verify(sig_bytes, payload_bytes)`. Any modification of claims or expiration results in `LicenseSignatureError` (HTTP 401).
2. **Product Identifier (`LIC-005`):**
   - Must match `AEGIS_PROTECTED_EVALUATION` or accepted aliases. Foreign products raise `LicenseProductMismatchError` (HTTP 403).
3. **Temporal Validity (`LIC-003`):**
   - If `current_utc_time > expires_at`, raises `LicenseExpiredError` (HTTP 403 `LICENSE_EXPIRED`).
   - System clock tampering on the client machine is ineffective because checks occur on the trusted server.
4. **Revocation Registry (`LIC-004`):**
   - Checked against the real-time `revocation_registry`. If `license_id` is present, raises `LicenseRevokedError` (HTTP 403 `LICENSE_REVOKED`).
5. **License Status (`LIC-006`):**
   - If `status == "SUSPENDED"`, raises `LicenseSuspendedError` (HTTP 403 `LICENSE_SUSPENDED`).
