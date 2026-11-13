# PROT-03: Protected Distribution Boundary Specification

**Document:** 08_PROTECTED_BOUNDARY.md  
**Audit Scope:** Boundary definition separating downloadable client software from protected server capabilities.  

---

## 1. The Definitive Distribution Boundary

```
+─────────────────────────────────────────────────────────────────────────────+
| DOWNLOADABLE DEMO CLIENT (Allowed for Public Distribution)                  |
|                                                                             |
|  [x] Compiled Next.js 16 Standalone Frontend (Minified JS, HTML, CSS)       |
|  [x] Local Nginx Reverse Proxy (Port 3000 -> Gateway TLS)                   |
|  [x] Windows PowerShell Orchestration Scripts (start-demo.ps1, etc.)        |
|  [x] Cross-Platform Bash Scripts (start-demo.sh, stop-demo.sh)              |
|  [x] Synthetic Demonstration Data (Hardware Specs v1/v2, Security Paper)    |
|  [x] Public Verification Material (package-manifest.json, public-key.pem)  |
|  [x] Signed 14-Day Evaluation License (evaluation.lic)                      |
|  [x] Legal Notices (LICENSE-EVALUATION.md, THIRD-PARTY-NOTICES/)            |
+─────────────────────────────────────────────────────────────────────────────+
                                       ▲
                                       │ SECURE EVALUATION GATEWAY (HTTPS)
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| PROTECTED AEGIS INFRASTRUCTURE (Confidential & Air-Gapped)                  |
|                                                                             |
|  [!] Proprietary Sheaf Laplacian Spectral Graph Engine                      |
|  [!] Advanced Submodular Context Knapsack Packing Engine                    |
|  [!] Abstract Interpretation Contradiction Verification Solver              |
|  [!] Hierarchical Document Memory Hypergraph & Causal Index                 |
|  [!] Document Orchestrator State Machine (src/core/orchestrator.py)         |
|  [!] Production LLM Provider Integrations & Private API Keys                |
|  [!] Root Asymmetric Private Key (services/evaluation_gateway/keys/)        |
|  [!] Internal Testing Suites, Benchmarking Runners, and Fixtures            |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Public vs. Private Interface Contracts

### Public Evaluation Contracts:
- Evaluators interact solely with the public schemas in `public_api_allowlist.yaml`.
- Data exchange formats are bounded to:
  - `IngestResponse`: Document ID, page count, filename, status.
  - `QueryResponse`: Question, grounded answer text, verbatim citations (quote, page, confidence), abstention flag.
  - `ComparisonResponse`: Left/Right metadata, alignment score, detected contradictions, preserved invariants.

### Private Engine Contracts:
- Stalk mapping matrices, boundary operators $d: C^0 \to C^1$, intermediate attention weights, and tokenizer entropy distributions remain internal to private services.

---

## 3. Protecting Future Intellectual Property

Because the initial research prototype baseline is accessible in a public GitHub repository, future commercial differentiation relies on **architectural air-gapping of novel inventions**:

1. **Trade Secret Preservation:** Future algorithmic iterations (dynamic sheaf laplacians, neural-symbolic verification models) must never be committed to public repositories.
2. **Feature Gating:** Advanced features (custom enterprise connectors, direct Snowflake/S3 integrations, multi-tenant RBAC) are deployed as cloud microservices rather than client code.
3. **Intellectual Property Filing:** Novel mathematical representations should be evaluated for patent protection prior to public whitepaper publication.
