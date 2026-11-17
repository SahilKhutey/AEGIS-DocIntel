# PROT-04.08 — Dossier 05: Secrets & Cryptographic Key Management

## 1. Cryptographic Key Lifecycle Architecture
AEGIS-DocIntel employs asymmetric cryptography (Ed25519) to sign evaluation licenses and protect client-server integrity. Private keys reside strictly on the server; clients receive only public verification keys.

```
                      +-----------------------------+
                      |         GENERATE            |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |      ACTIVE_SIGNING         |
                      | (Signs new eval licenses)   |
                      +-----------------------------+
                                     |
                       [Rotate Key]  |  [Emergency Leak]
                                     +-------------------+
                                     |                   |
                                     v                   v
+-----------------------------+               +-----------------------------+
|        VERIFY_ONLY          |               |         COMPROMISED         |
| (Verifies circulating       |               | (Immediately denies any     |
|  unexpired licenses)        |               |  license signed with key)   |
+-----------------------------+               +-----------------------------+
               |
 [All expired] |
               v
+-----------------------------+
|           RETIRED           |
| (Archived for audit only)   |
+-----------------------------+
```

---

## 2. Key Lifecycle States & Transition Rules

1. **ACTIVE_SIGNING**:
   - Authorized to sign new evaluation licenses and external audit checkpoints.
   - Exactly one key per algorithm is in this state at any given moment.
2. **VERIFY_ONLY**:
   - Key has been demoted following scheduled rotation.
   - Private key is purged from active memory; public key is retained to verify existing, unexpired licenses issued during its active tenure.
3. **RETIRED**:
   - All licenses issued under this key have reached their cryptographic expiration date.
   - Retained only for historical forensic audits.
4. **COMPROMISED**:
   - Key has been reported or suspected leaked.
   - **Immediate Invalidation**: The registry immediately denies any license or token bearing this key ID, regardless of signature validity.

---

## 3. Automated Key & Secret Rotation Procedures

### 3.1 Ed25519 License Signing Key Rotation
```python
def rotate_license_signing_key(self) -> Tuple[str, str]:
    # 1. Demote current active key to VERIFY_ONLY
    # 2. Generate new Ed25519 key pair with unique timestamp/KID
    # 3. Promote new key to ACTIVE_SIGNING
    # 4. Update KeyMetadataRepository state
    # 5. Emit KEY_ROTATION audit event
```
- **Zero-Downtime**: Existing evaluation clients continue verifying without interruption because their signing key remains valid in `VERIFY_ONLY` state.

### 3.2 High-Entropy API Key Rotation (IR-003)
- API keys are hashed with SHA-256 prior to storage; raw secrets are never retained in plaintext.
- Rotation generates a cryptographically secure token (`secrets.token_urlsafe(32)`), updates the repository hash, and atomically invalidates the predecessor key.

---

## 4. Emergency Key Compromise Handling (IR-02)
When an emergency compromise is reported (`emergency_compromise_key(kid)`):
1. `SigningKeyRegistry.compromise_key(kid)` transitions key state to `COMPROMISED`.
2. Active signing key is unset if it matches the compromised ID.
3. `KeyMetadataRepository` records the compromise timestamp and actor.
4. A `CRITICAL` audit event `KEY_COMPROMISE_REPORTED` is emitted.
5. All evaluation gateway verification endpoints deny tokens signed by this key within $< 50\text{ms}$.
