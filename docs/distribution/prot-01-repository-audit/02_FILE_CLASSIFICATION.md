# PROT-01: File Inventory & IP Classification Breakdown

**Document:** 02_FILE_CLASSIFICATION.md  
**Audit Target:** All 4,668 tracked files in `distribution/audit/distribution_inventory.csv`  

---

## 1. Classification Criteria & Definitions

| Classification | Meaning & Policy | Distribution Action |
| :--- | :--- | :--- |
| **`DISTRIBUTABLE`** | Intended for inclusion in the public downloadable evaluation package. Contains zero proprietary trade secrets, algorithms, or private keys. | `INCLUDE` |
| **`RESTRICTED`** | Permitted to be shipped only in compiled, minified, sanitized, or proxy-configured form after formal security review. Source code is withheld. | `INCLUDE_COMPILED_ONLY` or `REBUILD_FOR_DEMO` |
| **`PRIVATE`** | PROPRIETARY & CONFIDENTIAL. Intellectual property, mathematical core, orchestrators, backend services, tests, CI workflows, and secrets. **NEVER SHIPPED**. | `EXCLUDE` |
| **`THIRD_PARTY`** | External dependencies and open-source packages governed by their respective licenses (e.g., Apache 2.0, MIT, BSD). | `THIRD_PARTY_NOTICE_REQUIRED` |

---

## 2. Component-by-Component Classification Breakdown

### A. Core Platform Source (`src/`) — **PRIVATE (100% EXCLUDED)**
- **Engines (`src/engines/`):** Contains Sheaf Laplacian spectral graph models (`src/engines/topology/`), submodular knapsack context packing algorithms (`src/engines/context/`), and invariant contradiction solvers (`src/engines/governance/`). **Classification: PRIVATE.**
- **Mathematics & Logic (`src/math_concepts/`, `src/ael/`):** Abstract interpretation models and custom logic solvers. **Classification: PRIVATE.**
- **Orchestration & Memory (`src/core/orchestrator.py`, `src/memory_engine/`):** Document hypergraph memory and execution workflows. **Classification: PRIVATE.**
- **Action:** All 847 files in `src/` are assigned `distribution_action: EXCLUDE` with `risk: CRITICAL` or `HIGH`.

### B. Legacy Backend & Modules (`backend/`, `aegis/`) — **PRIVATE (100% EXCLUDED)**
- `backend/benchmarks/`, `backend/optimization/`, `backend/security/`: Internal performance benchmarks and optimization profiling.
- `aegis/security/`, `aegis/release/`, `aegis/reliability/`: Release gates and security orchestrators.
- **Action:** All files are assigned `distribution_action: EXCLUDE`.

### C. Open-Source Document Prepper (`aegis-docprep/`) — **DISTRIBUTABLE / THIRD_PARTY**
- Extracted standalone document preparation library providing spatial reading-order extraction and PII redaction.
- **License:** Apache License 2.0.
- **Action:** `distribution_action: THIRD_PARTY_NOTICE_REQUIRED`. May be distributed as source or wheel under Apache 2.0 terms.

### D. Web Frontend (`web/`) — **RESTRICTED (COMPILED ONLY)**
- **UI Source (`web/src/`):** Next.js 16 / React 19 single-page workbench.
- **Action:** `distribution_action: INCLUDE_COMPILED_ONLY`. The source code is withheld; only the compiled standalone Docker image (`aegis-demo-web`) is shipped.
- **Sourcemaps:** Stripped completely (`.map` files omitted).
- **Environment Sanitation:** `web/src/lib/validation/environment.ts` audited to ensure `NEXT_PUBLIC_AEGIS_DEV_TOKEN` is stripped in production builds (`PROT-F02`).

### E. Deployment Configurations (`deploy/`) — **RESTRICTED (REBUILD FOR DEMO)**
- `deploy/docker-compose.yml`: Deploys internal API, Prometheus, and Grafana (`PROT-F03`). Not suitable for demo distribution.
- **Action:** Rebuilt into `distribution/demo-edition/deploy/compose.yaml` which runs only `aegis-demo-web` and `aegis-demo-proxy`.

### F. Demo Distribution Bundle (`distribution/demo-edition/`) — **DISTRIBUTABLE (APPROVED)**
- Exactly 24 sanctioned files:
  1. `deploy/compose.yaml` (demo compose)
  2. `deploy/nginx-demo-proxy.conf` (hardened edge proxy)
  3. `launcher/start-demo.ps1`, `stop-demo.ps1`, `status-demo.ps1`, `reset-demo.ps1`, `verify-package.ps1`
  4. `launcher/start-demo.sh`, `stop-demo.sh`
  5. `license/public-key.pem` (Ed25519 public key)
  6. `license/evaluation.lic` (14-day signed evaluation license)
  7. `demo-data/` (synthetic specs v1.0/v2.0, governance whitepaper, ground-truth QA maps)
  8. `package-manifest.json` (SHA-256 integrity manifest)
  9. `LICENSE-EVALUATION.md`, `THIRD-PARTY-NOTICES.md`, `README.md`
- **Action:** `distribution_action: INCLUDE`.

### G. Evaluation Gateway (`services/evaluation_gateway/`) — **PRIVATE (CLOUD ONLY)**
- Server-side licensing, activation, entitlement, and quota services.
- `services/evaluation_gateway/keys/private-key.pem`: Root Ed25519 private key.
- **Action:** `distribution_action: EXCLUDE`. Stored exclusively on cloud infrastructure.
