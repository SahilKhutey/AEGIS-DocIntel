# Artifact Signing & Independent Cryptographic Verification

**Phase:** PROT-FINAL-04  
**Date:** 2026-11-18T03:48:37.665500+00:00  

---

## 1. Signing Specification
- **Algorithm:** Pure Ed25519 (EdDSA).
- **Key Identifier:** `aegis-release-ed25519-2026-01`.
- **Target:** Canonical sorted JSON `release/manifests/manifest.json`.
- **Signature Output:** `release/signatures/manifest.sig` (Base64-encoded).
- **Public Metadata:** `release/signatures/signing-key-metadata.json`.

## 2. Independent Verification Command
Evaluators can independently verify release authenticity using the included script:
```powershell
python scripts/release/verify_release.py
```
Verification checks the Ed25519 signature against the manifest, then verifies the SHA-256 digest of `AEGIS-DocIntel-Demo-Edition.zip` and `client-sbom.cdx.json`.
