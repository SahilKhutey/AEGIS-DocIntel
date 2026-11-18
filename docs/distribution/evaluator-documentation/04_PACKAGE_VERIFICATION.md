# 04 - Package Verification
Before launching, verify that your download has not been corrupted or tampered with.

### Checksum Verification
Compute the SHA-256 digest of your downloaded zip file:
```powershell
Get-FileHash -Algorithm SHA256 "AEGIS-Evaluation-0.1.0.zip"
```
Compare the output against the hash published in `release-manifest-0.1.0.json`.

### Cryptographic Signature Verification
The release manifest is cryptographically signed using Ed25519:
```powershell
powershell -ExecutionPolicy Bypass -File launcher\verify-package.ps1
```
Expected output: `[+] Release manifest verified compliant with Ed25519 key ID aegis-release-ed25519-2026-01`.
