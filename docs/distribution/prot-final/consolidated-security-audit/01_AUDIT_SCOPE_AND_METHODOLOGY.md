# PROT-FINAL-01: Audit Scope & Methodology
**Document ID:** `AEGIS-AUDIT-FINAL-01`  
**Distribution:** Protected Demo Edition  
**Initiative Baseline:** SahilKhutey/AEGIS-DocIntel  
**Classification:** Confidential — Engineering Verification  
**Status:** COMPLETE / VERIFIED  

---

## 1. Scope Definition
The consolidated audit spans all architectural boundaries and functional components across the Protected Demo Edition:

| Scope Boundary | Included Subsystems | Verification Method |
| :--- | :--- | :--- |
| **Downloadable Client** | React web application, Vite bundle, Electron shell packaging, public assets | Static AST inspection, entropy scan, secret pattern regex, auth guard |
| **Evaluation Gateway** | Fastify/FastAPI gateway, authentication endpoints, challenge-response API, session refresh | Pytest test harness, live mock HTTP client, invalid payload injection |
| **Licensing Subsystem** | Ed25519 signing key registry, license serialization, signature verification, revocation registry | Cryptographic fuzzing, signature corruption, key retirement & compromise tests |
| **Device Binding Layer** | Challenge generation, client public key parsing, PoP verification, 1-device slot lock | Concurrent race injection, challenge replay attacks, emergency recovery flow |
| **Entitlement & Quotas** | Policy engine, feature gates, atomic reservation ledger, idempotent settle/rollback | Multithreaded quota exhaustion tests, feature matrix evaluation |
| **Session Engine** | Session repository, refresh token rotation lineage, cascade revocation coordinator | Replay attack simulation, multi-device logout, license cascade tests |
| **Private Processing Engine** | Document parsing, LLM comparison worker, OCR pipeline, internal HMAC guard | Cross-tenant injection, unauthenticated direct probe, tampered HMAC sigs |
| **Operational Security** | Hash-chained audit ledger, security event redaction, alert evaluation, backup restore | Bit-flip tamper test, credential leak simulation, disaster recovery restore |

---

## 2. Audit Methodology

### 2.1 Threat Modeling & Adversary Personas
1. **Curious Evaluator:** Attempts to uncover hidden features, inspect client source maps, bypass client-side disabled buttons, or modify local storage tokens.
2. **Malicious Competitor:** Attempts to extract proprietary IP, core models, or private backend algorithms from downloadable distributions.
3. **Replay & Sharing Attacker:** Replays activation challenges, shares single license codes across multiple corporate workstations, or intercepts refresh tokens.
4. **Quota Exhaustion Flooder:** Floods expensive OCR or document comparison APIs with concurrent requests to cause denial-of-service or over-budget LLM spend.
5. **Cross-Tenant Snoop:** Exploits multi-tenant routing by manipulating headers or tenant IDs in API requests to access another customer's document summaries.

### 2.2 Verification Phases
1. **Phase 1: Baseline Freeze & Integrity Locking:** Freezing Git SHAs, lockfile digests, and tree status.
2. **Phase 2: Static Analysis & Secret Sanitization:** Multi-regex static scanning of all client source files for keys, tokens, and IP leakage.
3. **Phase 3: Cryptographic Proof Verification:** Pure Ed25519 digital signature validation and SHA-256 hash-chain ledger continuity checks.
4. **Phase 4: Dynamic Boundary & Invariant Testing:** 56 authoritative consolidated security tests executing directly against the live gateway services.
5. **Phase 5: Resiliency & Fail-Closed Validation:** Verifying disaster recovery non-resurrection and authority outage fail-closed responses.
