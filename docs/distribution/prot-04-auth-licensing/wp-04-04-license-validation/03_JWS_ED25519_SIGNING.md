# WP-04.04 Dossier 03: JWS Ed25519 Cryptographic Signing

**Work Package:** PROT-04.04  
**Title:** Compact JWS Ed25519 Serialization & Cryptographic Engine  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Cryptographic Primitive Selection: Ed25519 (EdDSA)

AEGIS-DocIntel selects **EdDSA over Curve25519 (Ed25519)** (RFC 8032, RFC 8037) as its primary licensing signature algorithm.

### Why Ed25519?
1. **High Security Margin**: Provides approximately 128-bit security level, equivalent to NIST P-256 or RSA-3072, without vulnerability to side-channel timing attacks or weak random number generation.
2. **Compact Signature Size**: Produces fixed 64-byte signatures and 32-byte public keys, minimizing token transmission overhead.
3. **Deterministic Signatures**: PureEdDSA is deterministic ($r = H(k \parallel M)$), eliminating entropy-drain risks on constrained environments.
4. **Performance**: Signature generation and verification are orders of magnitude faster than RSA-2048/4096 or ECDSA P-384, preventing cryptographic bottlenecks during high-frequency evaluation requests.

---

## 2. JWS Compact Serialization Format

In accordance with RFC 7515 Section 3.1, the evaluation license is serialized as three URL-safe Base64-encoded segments concatenated by periods (`.`):

$$\text{JWS} = \text{BASE64URL}(\text{Header}) \mathbin{\Vert} \text{"."} \mathbin{\Vert} \text{BASE64URL}(\text{Payload}) \mathbin{\Vert} \text{"."} \mathbin{\Vert} \text{BASE64URL}(\text{Signature})$$

### 2.1 Header Representation
```json
{
  "typ": "AEGIS-EVALUATION-LICENSE",
  "alg": "EdDSA",
  "kid": "aegis-license-ed25519-2026-01"
}
```
- `typ`: Explicitly declares the token media type to prevent token reuse across disparate security contexts (e.g., using an auth JWT as a license).
- `alg`: Pinned to `"EdDSA"`.
- `kid`: Identifies the server-side signing key in the `SigningKeyRegistry`.

### 2.2 Signature Calculation
$$\text{Signing Input} = \text{BASE64URL}(\text{Header}) \mathbin{\Vert} \text{"."} \mathbin{\Vert} \text{BASE64URL}(\text{Payload})$$
$$\text{Signature} = \text{Ed25519Sign}(K_{\text{private}}, \text{Signing Input})$$

---

## 3. Defense Against Known JWS Vulnerabilities

### 3.1 Algorithm Substitution Attack Prevention (`LIC-008`)
In traditional JWT libraries, attackers can swap `"alg": "EdDSA"` to `"HS256"` and sign the token using the server's public key as an HMAC secret, or switch to `"alg": "none"`.
- **Mitigation**: AEGIS explicitly pins allowed algorithms to `["EdDSA"]` during decoding. If a token arrives with `HS256`, `none`, `RS256`, or any unapproved algorithm, the decoding pipeline terminates immediately before inspecting keys.

### 3.2 Header Injection & Remote Key Injection (`LIC-034`)
Attackers may attempt to inject header parameters such as:
- `jku` (JSON Web Key Set URL): forcing the server to fetch keys from an attacker-controlled endpoint.
- `x5u` (X.509 URL): forcing remote certificate fetching.
- `jwk`: providing an embedded public key directly inside the token.
- `x5c`: embedding untrusted certificates.
- **Mitigation**: AEGIS inspects the raw unverified header prior to decoding. If any key matching `["jku", "x5u", "x5c", "jwk"]` is present, the token is rejected as hostile:
```python
forbidden_headers = {"jku", "x5u", "x5c", "jwk"}
if forbidden_headers.intersection(unverified_headers.keys()):
    raise LicenseVerificationError("Token contains disallowed header parameter (jku/x5u/x5c/jwk)")
```

### 3.3 Strict Size Limiting (`LIC-035`)
To protect the gateway from memory exhaustion or regex/parsing denial-of-service, tokens exceeding 8,192 bytes are rejected immediately:
```python
if len(token.encode("utf-8")) > 8192:
    raise LicenseVerificationError("License token exceeds maximum permitted size (8192 bytes)")
```

### 3.4 Key ID Binding & Status Verification (`LIC-009`, `LIC-026`)
The `kid` header must exist within the server's `SigningKeyRegistry`. The registry verifies that:
1. The key ID is recognized.
2. The key status is either `ACTIVE_SIGNING` or `VERIFY_ONLY`.
3. If the key is `RETIRED` or `COMPROMISED`, verification is denied unconditionally.
