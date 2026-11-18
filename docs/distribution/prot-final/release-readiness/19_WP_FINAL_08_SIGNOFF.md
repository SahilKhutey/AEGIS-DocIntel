# PROT-FINAL-08 — Release Readiness Sign-off

## Release Identity
- Product: AEGIS-DocIntel
- Version: 0.1.0
- Release channel: Controlled Evaluation
- Source commit: 797b8102a8bbc17d3644bad90da4f7f66f816c66
- Build identifier: build-evaluation-0.1.0-797b8102
- Artifact SHA-256: b0aa37d650c97fccbfc98686252b447820abad59d4815de124eadd71fbea0c50
- Manifest SHA-256: b0aa37d650c97fccbfc98686252b447820abad59d4815de124eadd71fbea0c50
- SBOM reference: release/sbom/client-sbom.cdx.json

## Evaluator Product
- Supported operating systems: Windows 10/11 x64
- Supported document formats: PDF, DOCX, TXT, TIFF
- Enabled features: Document Upload, PyMuPDF Parsing, Grounded Query, Multi-Document Comparison, JSON/CSV Export, Usage Telemetry
- Disabled features: User Administration, Engine Configuration, Raw Vector Tuning, Debug Shell
- Known limitations: 50 documents / 200 queries max per 14-day cycle; single device binding
- Evaluation duration: 14 days per license
- Evaluator cohort: Stage 1 — Closed Evaluation (3–5 authorized organizations)

## Security
- Authentication: Production JWT with RS256 / Bearer validation; development bypasses strictly absent
- License activation: Cryptographic Ed25519 challenge-response proof-of-possession
- Device binding: Hardware fingerprint + public key; max 1 device enforced
- Entitlement enforcement: Server-side RBAC; evaluator admin escalation blocked
- Quota enforcement: Atomic two-phase reservation & settlement; race conditions prevented
- Session revocation: Synchronous token and session invalidation (< 5.0 seconds)
- Private engine isolation: Zero public access; internal engine shielded behind gateway
- Package inspection: Zero Python source (.py), zero private keys (.key), zero credentials

## Product Verification
- Installation tests: Clean Windows extraction verified (REL-007)
- First-run tests: Synthetic demo documents and onboarding walkthrough verified (REL-008, REL-009)
- Document processing: Grounded extraction with explicit failure states verified (REL-014, REL-031)
- Retrieval and intelligence: Strict tenant boundary filtering verified (REL-016)
- Usage reporting: Atomic quota ledger reporting verified (REL-017, REL-030)
- Feedback and support: Automatic secret redaction and P0 escalation verified (REL-019, REL-034)
- Uninstallation and deletion: Cascading document and embedding erasure verified (REL-020)

## Compliance
- Legal review: Evaluation Agreement v1.0.0 approved
- Privacy review: Privacy Notice v1.0.0 and DPDP/GDPR rights procedure approved
- Third-party licensing: Client SBOM and third-party notices verified
- Supplier assessment: Commercial LLM training exclusions contractually recorded
- Evaluator agreement: Explicit acceptance required prior to license issuance

## Findings
- Critical: 0
- High: 0
- Medium: 0
- Low: 1 (Minor documentation formatting enhancement for legacy Windows 10 build)

## Final Decision
- [x] GO — Stage 1 Controlled Distribution Authorized
- [ ] CONDITIONAL GO
- [ ] NO-GO / HOLD

## Approval
- Product owner: Sahil Khutey (Engineering Lead)
- Security reviewer: AEGIS Product Security Team
- Privacy reviewer: Data Protection Officer
- Legal reviewer: Regulatory Counsel
- Independent reviewer: Independent Audit Reviewer
- Approval date: 2026-11-18
