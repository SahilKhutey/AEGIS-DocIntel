# WP-04.03 Dossier 02: Device Identity and Key Management

**Work Package:** PROT-04.03  
**Title:** Cryptographic Key Primitives, Fingerprinting & Key Lifecycle  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  

---

## 1. Supported Asymmetric Cryptographic Primitives

The evaluation gateway enforces strong asymmetric cryptography for client device authentication. Two asymmetric algorithms are supported:

| Parameter | Primary Algorithm (Recommended) | Compatibility Algorithm |
| :--- | :--- | :--- |
| **Algorithm** | **Ed25519 (Edwards-curve Digital Signature)** | **RSA-2048 / PKCS#1 v1.5 & PSS** |
| **Standard** | RFC 8032 / FIPS 186-5 | PKCS#1 v2.2 / RFC 8017 |
| **Public Key Size** | 32 bytes (256 bits) raw or DER SubjectPublicKeyInfo | 2048-bit modulus (256 bytes) |
| **Signature Size** | 64 bytes | 256 bytes |
| **Performance** | Sub-millisecond signing and verification | Fast verification (~0.1 ms), slower signing |
| **Encoding** | Base64 raw bytes or PEM `SubjectPublicKeyInfo` | PEM `SubjectPublicKeyInfo` |

---

## 2. Public Key Parsing and Normalization

When a client submits `device_public_key` during Stage 1 challenge creation, the server validates and normalizes the key through `parse_and_validate_public_key()`:

```python
def parse_and_validate_public_key(pub_key_str: str) -> Tuple[Any, bytes, str]:
    # 1. Strips whitespace and validates non-empty string.
    # 2. If PEM header ('-----BEGIN'):
    #    Parses SubjectPublicKeyInfo via cryptography.hazmat.primitives.serialization.
    # 3. If raw Base64:
    #    - If exactly 32 bytes: parses as raw Ed25519 public key.
    #    - Else: attempts DER SubjectPublicKeyInfo parse.
    # 4. Fails closed with ValueError("Malformed or unsupported public key") if invalid.
```

Any syntax error, malformed Base64 string, or unsupported curve triggers an immediate `HTTP 400 Bad Request` with `MALFORMED_PUBLIC_KEY` (`DEV-006`).

---

## 3. Cryptographic Key Fingerprinting (`DEV-015`)

To track registered devices without storing large PEM structures in secondary indexes and telemetry, the gateway generates a deterministic SHA-256 fingerprint:

$$\text{Fingerprint} = \text{SHA-256}(\text{Canonical SubjectPublicKeyInfo DER Bytes})$$

### Fingerprint Properties:
- **Deterministic:** The same key always yields the exact same 64-character hexadecimal fingerprint (`DEV-015`).
- **Collision Resistant:** Inherits standard SHA-256 second-preimage and collision resistance.
- **Privacy Preserving:** Emitted in audit telemetry and management endpoints without exposing raw key material.

```json
{
  "key_fingerprint": "8d3e91f16f2c0cbba5b0981b2dae2ec112bf8bfa2e9a3b632dbb73e5bf2ecb61"
}
```

---

## 4. Key Storage and Security Invariants on Evaluator Client

| Rule ID | Invariant | Enforcement Mechanism |
| :--- | :--- | :--- |
| **KEY-01** | **Private Key Isolation** | Client private keys are generated locally and NEVER transmitted over network APIs. |
| **KEY-02** | **Zero Hardcoded Private Keys** | Distribution packages (`demo/`, `dist/`) contain ZERO private keys (`test_sec_demo_002`, `test_dist_001`). |
| **KEY-03** | **Hardware/OS Key Sealing** | Evaluator clients store generated private keys in OS DPAPI (Windows) or encrypted memory segments. |
| **KEY-04** | **Ephemeral Challenge Nonce** | Challenges contain a 256-bit cryptographically secure random nonce (`secrets.token_urlsafe(32)`). |
