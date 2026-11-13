# AEGIS-DocIntel — Source and IP Separation Audit Report

**Distribution Target:** Product Hunt Launch — Protected Downloadable Demo Edition  
**Version:** v1.1.0  
**Audit Date:** November 12, 2026  
**Status:** Certified & Reconciled  

---

## 1. Executive Summary

AEGIS-DocIntel combines open-source document preparation utilities with proprietary document intelligence algorithms, sheaf topological representations, submodular context packing, and automated governance verification.

To enable **frictionless Product Hunt adoption** while **strictly protecting proprietary intellectual property**, AEGIS-DocIntel employs a **Hybrid Distribution Architecture**:
1. **The User Receives:** A lightweight, self-contained local evaluation package containing the pre-compiled Next.js frontend, local reverse proxy, synthetic evaluation corpus, launch scripts, and cryptographic verification tools.
2. **The Core Remains Protected:** Proprietary mathematical engines, sheaf Laplacian decomposition algorithms, submodular knapsack optimizers, and production LLM credentials are hosted exclusively on infrastructure managed by the AEGIS team, accessed solely through an authenticated, quota-enforced **Evaluation Gateway**.

This document certifies the classification of all codebase components, defines the distribution boundary, and sets the acceptance criteria for the SEC-DEMO security test suite.

---

## 2. Intellectual Property Classification Matrix

| Component | Repository Path | Classification | Upstream / Distribution License | Protection Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Document Prepper** | `aegis-docprep/` | `DISTRIBUTABLE` | Apache-2.0 | Public open-source repository; standalone wheel |
| **Web Frontend** | `web/` | `DISTRIBUTABLE` | AEGIS Evaluation License | Compiled standalone Node.js bundle; `.map` sourcemaps stripped |
| **Synthetic Corpus** | `demo/seed/` | `DISTRIBUTABLE` | CC-BY-4.0 | 100% synthetic hardware specs & security paper; no proprietary customer data |
| **Launch Automation** | `distribution/demo-edition/launcher/` | `DISTRIBUTABLE` | Apache-2.0 | PowerShell & Bash scripts (`start-demo.ps1`, `verify-package.ps1`, etc.) |
| **Public Signing Key** | `distribution/demo-edition/license/public-key.pem` | `DISTRIBUTABLE` | Public Domain | Ed25519 Public Key for asymmetric local license validation |
| **Distribution Docs** | `docs/distribution/` | `DISTRIBUTABLE` | CC-BY-ND-4.0 | Evaluation guides, threat model, license notices |
| **Demo Reverse Proxy** | `distribution/demo-edition/deploy/` | `RESTRICTED` | AEGIS Evaluation License | Hardened Nginx configuration forwarding `/api` to Gateway |
| **Package Manifest** | `distribution/demo-edition/package-manifest.json` | `RESTRICTED` | AEGIS Evaluation License | Signed SHA-256 integrity manifest |
| **Context Optimizer** | `src/engines/context/` | `PRIVATE` | Proprietary Closed Source | **NEVER DISTRIBUTED**; runs behind Evaluation Gateway |
| **Topology Engine** | `src/engines/topology/` | `PRIVATE` | Proprietary Closed Source | **NEVER DISTRIBUTED**; runs behind Evaluation Gateway |
| **Governance Engine** | `src/engines/governance/` | `PRIVATE` | Proprietary Closed Source | **NEVER DISTRIBUTED**; runs behind Evaluation Gateway |
| **Memory Graph** | `src/memory_engine/` | `PRIVATE` | Proprietary Closed Source | **NEVER DISTRIBUTED**; runs behind Evaluation Gateway |
| **Orchestrator** | `src/core/orchestrator.py` | `PRIVATE` | Proprietary Closed Source | **NEVER DISTRIBUTED**; runs behind Evaluation Gateway |
| **License Private Key** | `services/evaluation_gateway/keys/` | `PRIVATE` | Proprietary Secret | Ed25519 Root Private Key; secured in vault / KMS |
| **Secrets & Keys** | `.env.production`, Vault | `PRIVATE` | Proprietary Secret | Stripped by `.dockerignore` and release packaging scripts |
| **PyMuPDF / fitz** | External dependency | `THIRD_PARTY` | AGPL-3.0 / Commercial | Isolated in standalone docprep layer |
| **React / Next.js** | External dependency | `THIRD_PARTY` | MIT | Attributed in `THIRD-PARTY-NOTICES.md` |
| **FastAPI / Uvicorn** | External dependency | `THIRD_PARTY` | BSD-3-Clause / Apache-2.0 | Attributed in `THIRD-PARTY-NOTICES.md` |

---

## 3. Boundary & Protection Enforcement Rules

### Rule 1: No Proprietary Python Source in Downloadable Artifacts
The downloadable package (`AEGIS-DocIntel-Demo-Edition.zip`) MUST NOT contain any files from:
- `src/engines/`
- `src/core/orchestrator.py`
- `src/math_concepts/`
- `src/ael/`
- `src/llm_service/`
- `services/evaluation_gateway/` (gateway implementation runs server-side)

Any release package containing `.py` files corresponding to the core intelligence engine fails build verification (Test `SEC-DEMO-001`).

### Rule 2: Sourcemap Stripping
Production frontend containers and distributed assets MUST NOT contain `.map` files or source-map comments (`sourceMappingURL`). All client JavaScript is bundled, minified, and tree-shaken (Test `SEC-DEMO-003`).

### Rule 3: No Hardcoded Secrets or Private Keys
The release package MUST NOT include `.env`, `.env.production`, SSH keys, or private signing keys (`private-key.pem`). The only key present in the evaluation package is the Ed25519 public key `public-key.pem` (Test `SEC-DEMO-002`).

### Rule 4: Server-Side Entitlement & Quota Verification
Client-side UI checks (e.g. disabling a button after 5 uploads) are UX conveniences only. The **Evaluation Gateway** strictly validates:
1. Ed25519 cryptographic signature of the `evaluation.lic` token.
2. Device fingerprint and active session count.
3. Expiration date (default 14 days from activation).
4. Hard server-side quota limits (e.g. 5 document uploads, 20 queries/day, 5 comparisons/day).
Requests exceeding limits return HTTP 429 / 403 regardless of client tampering (Tests `SEC-DEMO-005`, `009`, `010`).

### Rule 5: Dual Licensing Model Integrity
- Standalone `aegis-docprep` is licensed under **Apache-2.0**.
- The AEGIS Demo Edition and web workbench are licensed under the **AEGIS Evaluation License Agreement** (`LICENSE-EVALUATION.md`), permitting personal, non-commercial evaluation only, prohibiting decompilation, reverse-engineering, benchmarking publication, and redistribution.

---

## 4. Verification Checkpoint
This classification audit is formally verified by the automated test suite in `tests/distribution-security/`.
