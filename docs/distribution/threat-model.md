# AEGIS-DocIntel — Distribution Threat Model & Attack Analysis

**Target:** Protected Downloadable Demo Edition (Product Hunt Release)  
**Classification:** Public Release Threat Assessment  
**Standard:** STRIDE & Defense-in-Depth  

---

## 1. Assets to Protect

1. **Proprietary Mathematical & Optimization Algorithms:** Sheaf Laplacian topological representations, submodular knapsack context optimizers, invariant propagation engines.
2. **Production Credentials & Secrets:** LLM provider API keys (OpenAI, Anthropic, Gemini), cloud infrastructure credentials, root Ed25519 signing private keys.
3. **Gateway Infrastructure & Availability:** Protection against denial-of-service, scraping, and unauthorized resource exhaustion.
4. **Tenant Data Confidentiality:** Evaluation documents uploaded by one user must be completely invisible to other evaluators.
5. **Commercial Licensing Integrity:** Preventing unauthorized commercial exploitation or tampering with evaluation quotas.

---

## 2. Threat Analysis & Defensive Controls

| Threat ID | Threat Description | Attack Vector | Defensive Control & Mitigation | Automated Test |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | **Source Code Exfiltration** | Attacker extracts files from Docker container or zip archive to steal proprietary algorithms. | Core engines (`src/engines/*`, `src/core/orchestrator.py`) are **excluded** from the package. Only compiled UI and proxy are distributed. | `SEC-DEMO-001` |
| **T-02** | **Credential Harvesting** | Attacker inspects environment files or binary strings for API keys. | Build pipeline enforces `.env` exclusion and scan checks. Ed25519 root private key is kept in cloud vault. | `SEC-DEMO-002` |
| **T-03** | **Client Sourcemap Reverse Engineering** | Attacker downloads `.map` files to reconstruct frontend typescript sources and unreleased features. | Production Next.js build strips all `.map` files and disables `sourceMappingURL`. | `SEC-DEMO-003` |
| **T-04** | **Administrative Route Probing** | Attacker discovers internal management or admin URLs through frontend inspection. | Nginx reverse proxy explicitly intercepts `/api/v*/admin*` and drops requests with HTTP 403. | `SEC-DEMO-004` |
| **T-05** | **Client Quota Bypass** | Attacker modifies local client code or patches UI javascript to bypass 5-document or 20-query limits. | **Strict Server-Side Enforcement**: Quotas are tracked and enforced on the Evaluation Gateway, returning HTTP 429. | `SEC-DEMO-005`<br/>`SEC-DEMO-009`<br/>`SEC-DEMO-010` |
| **T-06** | **License Signature Forgery** | Attacker alters `evaluation.lic` to extend expiration or grant unlimited entitlements. | Licenses are signed with 256-bit Ed25519 asymmetric cryptography. Tampered licenses fail signature verification. | `SEC-DEMO-006`<br/>`SEC-DEMO-007` |
| **T-07** | **License Reuse After Revocation** | Attacker attempts to reuse an expired or compromised evaluation token. | Gateway maintains an active revocation registry and validates timestamps against UTC reference time. | `SEC-DEMO-008`<br/>`SEC-DEMO-018` |
| **T-08** | **Cross-Tenant IDOR Attack** | Attacker attempts to access another user's documents by guessing or incrementing document UUIDs. | Strict tenant boundary enforcement: `get_document()` requires `doc.license_id == ctx.license_id`, returning HTTP 404 on mismatch. | `SEC-DEMO-011` |
| **T-09** | **Internal Path / Stack Trace Leak** | Attacker triggers unexpected exceptions to discover filesystem layout or database schema. | Global exception handlers sanitize all gateway errors, stripping tracebacks, system paths, and internals. | `SEC-DEMO-012` |
| **T-10** | **Malicious Binary Upload** | Attacker uploads executable payloads (`.exe`, `.sh`, `.bat`) or path-traversing filenames. | File extension blacklist and filename sanitization reject dangerous binaries with HTTP 400. | `SEC-DEMO-013` |
| **T-11** | **Resource Exhaustion via File Bombs** | Attacker uploads multi-gigabyte files to crash server memory. | Hard upload payload limit (10 MB) enforced; oversized payloads return HTTP 413. | `SEC-DEMO-015` |
| **T-12** | **Package Tampering / MITM** | Attacker modifies distributed launcher scripts or seed files in transit. | Package manifest with SHA-256 digests and `verify-package.ps1` script validates integrity before execution. | `SEC-DEMO-016`<br/>`SEC-DEMO-020` |
| **T-13** | **Automated Activation Spam** | Scripted bots flood the activation endpoint to exhaust licenses or cloud resources. | IP sliding-window rate limiting restricts activation attempts per hour. | `SEC-DEMO-019` |

---

## 3. Residual Risks & Accepted Posture

1. **Network Dependency for Evaluation:**  
   Because proprietary engines run on private cloud infrastructure, evaluation requires an active internet connection. Offline operation is limited to synthetic health checks.  
   *Risk Acceptance:* Accepted. Delivering full engine source locally is an unacceptable trade secret risk.
2. **Client Inspection of Compiled UI:**  
   A sophisticated user can inspect compiled React components.  
   *Risk Acceptance:* Accepted. The frontend contains presentation logic only, no proprietary mathematical intelligence.
