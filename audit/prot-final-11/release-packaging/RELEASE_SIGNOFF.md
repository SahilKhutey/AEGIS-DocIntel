# AEGIS-DocIntel Final Release Signoff Charter (PROT-FINAL-11)

**Release Phase:** PROT-FINAL-11 — Production Package Engineering, Release Assembly & Distribution Readiness  
**Release Version:** `1.0.0-beta.1`  
**Target Platform:** Windows x64 (Installer + Portable Archive)  
**Date:** 2026-11-19  
**Decision:** **GO (UNCONDITIONAL RELEASE APPROVAL FOR CONTROLLED EVALUATION DISTRIBUTION)**  

---

## 1. Executive Summary

This charter certifies that the AEGIS-DocIntel evaluation release (`1.0.0-beta.1`) has met all 25 release acceptance criteria across product functionality, client packaging, security and licensing, and release operations. The release artifacts are cryptographically signed, scanned for zero IP/credential leakage, packaged with CycloneDX SBOMs, and validated against reproducible empirical tests.

---

## 2. Release Signoff Checklist (25 / 25 Satisfied)

### Product Functionality (7 / 7)
- [x] **Production Frontend Loads Correctly:** Standalone Next.js UI builds cleanly and renders all 17 routes.
- [x] **Document Upload & Storage Work:** Ingestion gate enforces 10MB evaluation ceiling, MIME validation, and SQLite persistence.
- [x] **Extraction & Parsing Work:** PyMuPDF, DOCX, and Kahn DAG reading order recover structural hierarchies and tables.
- [x] **Processing Jobs Complete Reliably:** Durable jobs transition monotonically through `QUEUED` $\to$ `READY`.
- [x] **Retrieval Returns Relevant Evidence:** Multi-modal dense/sparse hybrid search returns relevant chunks with tenant isolation.
- [x] **Context Optimization Respects Limits:** Submodular knapsack optimizer guarantees $(1 - 1/e)/2$ bound within token budget.
- [x] **LLM Responses & Citations Verified:** Bounding-box coordinate citations resolve to exact source page locations.

### Client Package (6 / 6)
- [x] **Allowlisted Package Assembled:** Client bundle built strictly from explicit allowlist template.
- [x] **No Private Backend or Engine Included:** Proprietary algorithms, engine source, and private microservices excluded.
- [x] **No Secrets or Credentials Included:** Gitleaks and boundary scanner confirm zero API keys, private keys, or DB strings.
- [x] **Launcher Starts & Stops Correctly:** `ClientLauncher` supervises loopback processes with zero orphaned processes.
- [x] **Windows Installer Operates Correctly:** Inno Setup script `AEGIS-DocIntel-Setup.iss` configures user directory setup.
- [x] **Portable Archive Operates Independently:** `AEGIS-DocIntel-Portable.zip` extracts and runs self-contained.

### Security and Licensing (6 / 6)
- [x] **Authentication & Activation Verified:** Ed25519 asymmetric signature validation and hardware challenge-response verified.
- [x] **Entitlements & Quotas Enforced:** Server-side atomic quota ledger (5 docs, 20 queries) prevents overages and race conditions.
- [x] **Revocation & Expiry Tested:** Suspended or revoked licenses fail closed with immediate sub-second propagation.
- [x] **Artifact Integrity & Signatures Verified:** Release manifest signed with release key `aegis-release-ed25519-2026-01`.
- [x] **Dependency & Secret Scans Reviewed:** CycloneDX 1.5 SBOM and dependency audits confirm zero high/critical vulnerabilities.
- [x] **Privacy & Notices Included:** Zero model training disclosures and third-party notices bundled.

### Release Operations (6 / 6)
- [x] **Release Manifest & SBOM Generated:** `release-manifest.json` and `client.cdx.json` created with actual SHA-256 hashes.
- [x] **Checksums Verified:** `checksums.sha256` generated and cryptographically verifiable.
- [x] **Update / Upgrade Procedure Tested:** Signed update verification and atomic snapshot backup documented and verified.
- [x] **Uninstall Procedure Tested:** Clean removal removes application binaries and prompts for user data retention.
- [x] **Known Limitations Documented:** Format boundaries, quotas, and browser support published in `KNOWN_LIMITATIONS.md`.
- [x] **Support & Rollback Procedures Ready:** Rollback protocol documented in `docs/distribution/UPDATE_AND_ROLLBACK.md`.

---

## 3. Certified Release Deliverables

| Deliverable | Path | SHA-256 / Checksum Status |
| :--- | :--- | :--- |
| **Windows Installer** | `release/client/windows-x64/installer/AEGIS-DocIntel-Setup.exe` | Verified |
| **Portable ZIP Archive** | `release/client/windows-x64/portable/AEGIS-DocIntel-Portable.zip` | Verified |
| **Release Manifest** | `release/client/windows-x64/manifests/release-manifest.json` | Signed (Ed25519) |
| **Cryptographic Signature** | `release/signatures/release-manifest.sig` | Key: `aegis-release-ed25519-2026-01` |
| **SLSA Provenance** | `release/signatures/provenance/release-provenance.json` | Verified |
| **CycloneDX SBOM** | `release/sbom/client.cdx.json` | Spec v1.5 Validated |
| **Integrity Checksums** | `release/client/windows-x64/manifests/checksums.sha256` | Formatted & Verified |
| **User Documentation** | `release/client-template/docs/` (10 documents) | Complete & Bundled |

---

## 4. Final Signoff Determination

**Verdict:** **RELEASE GO**  
The release is certified for controlled external distribution to invited evaluators, research partners, and technical design participants.
