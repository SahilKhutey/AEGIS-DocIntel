# AEGIS-DocIntel Packaging Architecture & Distribution Boundary Specification

**Specification Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-11 (Release Engineering & Distribution Readiness)  
**Classification:** Canonical Architecture Document  
**Status:** APPROVED & ADOPTED  

---

## 1. Executive Summary

This specification governs the production packaging architecture for AEGIS-DocIntel's controlled evaluation distribution. The governing architectural principle is strict trust boundary separation:
1. The **Public Evaluation Client** is a lightweight, verifiable, downloadable package designed for an evaluator's local Windows x64 workstation.
2. The **AEGIS Evaluation Gateway** acts as the secure perimeter boundary enforcing Ed25519 license validation, device binding, and atomic quota metering.
3. The **Private Intelligence Infrastructure** hosts proprietary algorithms (Kahn DAG topological sort, submodular knapsack context packing, tensor decompositions, coordinate grounders) and sensitive database/LLM credentials behind private network isolation.

```
+-----------------------------------------------------------------------------------+
|                        EVALUATOR'S LOCAL WINDOWS WORKSTATION                      |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                     AEGIS-DocIntel Evaluation Client                        |  |
|  |                                                                             |  |
|  |  +--------------------+  +--------------------+  +-----------------------+  |  |
|  |  | Compiled Frontend  |  |   Local Launcher   |  |     Local Proxy       |  |  |
|  |  | (Next.js Standalone|  | (Health supervisor |  | (Same-origin loopback |  |  |
|  |  |  Loopback: 3000)   |  |  Process monitor)  |  |  Binding: 127.0.0.1)  |  |  |
|  |  +---------+----------+  +---------+----------+  +-----------+-----------+  |  |
|  |            |                       |                         |              |  |
|  |  +---------v-----------------------v-------------------------v-----------+  |  |
|  |  |       Offline License Verifier (Ed25519 Public Key Embedded)          |  |  |
|  |  +---------------------------------+-------------------------------------+  |  |
|  +------------------------------------|----------------------------------------+  |
+---------------------------------------|-------------------------------------------+
                                        |
                 HTTPS / TLS 1.3 (Authenticated & Rate-Limited)
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                           AEGIS EVALUATION GATEWAY                                |
|  - Ed25519 License Validation & Key Registry                                      |
|  - Hardware Device Challenge-Response Activation                                  |
|  - Short-Lived Session Lifecycle & Sub-Second Revocation Propagation              |
|  - Server-Side Atomic Quota Reservation & Settlement (Hold/Settle/Release)        |
|  - Tamper-Evident Security Audit Telemetry Ledger                                 |
+---------------------------------------+-------------------------------------------+
                                        |
                    Private Internal Network (mTLS / VPC)
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                    PRIVATE AEGIS INTELLIGENCE INFRASTRUCTURE                      |
|  - Core Extraction Engines (PyMuPDF, Spatial Parsers)                             |
|  - Structural Normalization & Kahn DAG Reading Order (Monograph Theorems 6.1/6.2) |
|  - Submodular Knapsack Facility-Location Context Packer ((1 - 1/e)/2 bound)       |
|  - Multi-Modal Hybrid Retrieval Engine (Dense + BM25 + Spatial Coordinates)       |
|  - LLM Orchestrator & Multi-Provider Gateway (Litellm / Server-Side API Keys)     |
|  - Relational & Vector Persistence (SQLite / Chroma / Tenant-Isolated Schemas)     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Packaging Strategy Decision: Path A vs Path B

### 2.1 Empirical Evaluation

To decide between **Path A (Static Frontend Export)** and **Path B (Standalone Production Frontend Server)**, the repository baseline was audited:
1. `web/next.config.ts` declares:
   ```typescript
   output: "standalone",
   async rewrites() {
     return [
       { source: "/api/:path*", destination: `${apiHost}/api/:path*` },
       { source: "/v1/:path*", destination: `${apiHost}/v1/:path*` },
       { source: "/health", destination: `${apiHost}/health` },
     ];
   }
   ```
2. The frontend utilizes dynamic server-side rewrites to proxy `/api/*`, `/v1/*`, and `/health` requests to the configured target gateway (`INTERNAL_API_URL` / `NEXT_PUBLIC_API_BASE_URL`).
3. Static export (`next export` / `output: "export"`) disables Next.js dynamic rewrites, Server Actions, and runtime reverse proxying, which would force the client to manage cross-origin CORS requests directly against third-party endpoints.

### 2.2 Decision: Path B Adopted (Standalone Server + Local Proxy)

**Decision:** Adopt **Path B — Standalone Frontend Server with Local Loopback Proxy**.
- **Runtime Model:** Standalone Next.js production build (`web/.next/standalone`).
- **Loopback Enforcement:** Binds exclusively to `127.0.0.1` (never `0.0.0.0`).
- **Same-Origin Guarantee:** Local reverse proxy routes frontend requests to the Evaluation Gateway, eliminating CORS browser warnings and protecting against DNS rebinding attacks.
- **Source Map Scrubbing:** Production build strips `.map` files, TypeScript source files, and development server hooks.

---

## 3. Distribution Boundary & Allowlist Rules

### 3.1 What is Included in Downloadable Package
- Compiled frontend standalone runtime and assets (`app/frontend/`).
- Local application launcher and process supervisor (`app/launcher/`).
- Local loopback proxy (`app/proxy/`).
- Sanitized client configuration (`config/client.json`, `config/defaults.json`).
- Public license verification key (`keys/license-verification-public.pem`).
- Synthetic sample evaluation documents (`assets/demo/`).
- Comprehensive end-user documentation (`docs/`).
- Open-source third-party license notices (`licenses/THIRD_PARTY_NOTICES.txt`).
- Release version manifest and cryptographic signature (`release/manifest.json`).

### 3.2 Explicit Exclusions (Build Fails Immediately if Detected)
The build pipeline enforces an absolute zero-leak scan. The build aborts if any of the following exist within the client bundle:
1. Any `.env`, `.env.local`, `.env.production` file.
2. Private keys (`*.key`, `*.pem` containing `PRIVATE KEY`).
3. Development tokens or hardcoded bearer credentials (`dev-token`, `aegis-dev-key`).
4. Database connection strings (`postgresql://`, `mysql://`, `mongodb://`).
5. Third-party cloud credentials (`sk-`, `ghp_`, `AKIA`, `AIzaSy`).
6. Core proprietary backend source code (`src/engines/`, `src/services/`, `src/api/`).
7. Private Python processing engine or full backend Docker container.
8. Unredacted user documents or internal test credentials.

---

## 4. Local Launcher & Process Lifecycle

The local launcher (`AEGIS-DocIntel.exe` / `AEGIS-DocIntel.ps1`) manages the client application lifecycle:

```
[User Launches AEGIS-DocIntel]
              |
              v
[1. Verify Installation Integrity & SHA-256 Hashes]
              |
              v
[2. Load Sanitized Configuration (config/client.json)]
              |
              v
[3. Check Local Prerequisites (Node.js/Loopback ports)]
              |
              v
[4. Start Local Standalone Server & Loopback Proxy (127.0.0.1)]
              |
              v
[5. Await Local Health Check Probe (http://127.0.0.1:3000/health)]
              |
              v
[6. Open Desktop Application Window / Default Web Browser]
              |
              v
[7. Probe Evaluation Gateway Connectivity (HTTPS)]
        /           \
     (Online)     (Offline)
        v             v
[8a. Activate /  [8b. Verify Offline Ed25519
 Authenticate]     Signed License Token]
        \             /
         v           v
[9. Load Permitted Workspace & Feature Entitlements]
              |
              v
    [Application READY]
```

### Process Supervision Invariants
1. **No Orphan Processes:** On application exit, the launcher terminates all child server and proxy processes within a 5-second graceful deadline.
2. **Loopback Isolation:** The proxy and frontend reject any non-loopback interface traffic (`Host` header validation).
3. **Fail-Closed Offline Mode:** If remote connectivity is lost and no valid offline license token is present, the client displays a clear connection error and safely halts without fallback to privileged developer modes.
