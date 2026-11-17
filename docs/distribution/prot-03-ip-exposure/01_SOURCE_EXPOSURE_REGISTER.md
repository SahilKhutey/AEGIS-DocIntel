# PROT-03: Source Exposure Register

**Document:** 01_SOURCE_EXPOSURE_REGISTER.md  
**Audit Scope:** Full repository source exposure inspection across client bundles, server modules, and build artifacts.  

---

## 1. Source Exposure Register (IP-001 through IP-015)

| ID | File / Component | Exposed Intellectual Property | Initial Risk | Residual Risk | Technical Mitigation & Architectural Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IP-001** | `aegis-docprep/aegis_docprep/context_packer.py` | Facility-location submodular optimization objective and $(1-1/e)/2$ greedy approximation logic. | **CRITICAL** | **LOW** | Maintained as an independent Apache-2.0 open-core utility. Advanced production packers remain server-side. |
| **IP-002** | `src/engines/graph_reading_order.py` | Spatial directed acyclic graph (DAG) construction, Kahn's topological sort, and OPW distance metrics. | **CRITICAL** | **NEGLIGIBLE** | **EXCLUDED** from the downloadable demo package. Reading-order computation runs exclusively in the cloud. |
| **IP-003** | `src/engines/retrieval/submodular_packer.py` | Submodular diversity knapsack integration and marginal gain token-entropy algorithms. | **CRITICAL** | **NEGLIGIBLE** | **EXCLUDED** from client distribution. Managed cloud-side behind the Evaluation Gateway. |
| **IP-004** | `src/core/orchestrator.py` | Multi-stage document pipeline state machine and execution coordination logic. | **CRITICAL** | **NEGLIGIBLE** | **EXCLUDED** from client distribution. Zero `.py` files in downloadable release archive. |
| **IP-005** | `src/api/routes/query.py` | Document ingestion and search endpoints; previously leaked internal exception strings. | **HIGH** | **NEGLIGIBLE** | **SANITIZED**: Exception handlers return generic messages with UUID tracking references. Excluded from client bundle. |
| **IP-006** | `src/main.py` | Platform microservice wiring, middleware pipeline, and CORS setup. | **HIGH** | **NEGLIGIBLE** | **EXCLUDED**: Downloadable client uses stock Nginx reverse proxy + Evaluation Gateway. |
| **IP-007** | `docs/Architecture.md` | Internal mathematical system design: Sheaf Laplacian topology and cohomology obstruction formulas. | **HIGH** | **NEGLIGIBLE** | **EXCLUDED**: Internal engineering documentation withheld from installer archives. |
| **IP-008** | `docs/docprep.md` | Theoretical approximation bound proofs and submodular greedy maximization analysis. | **MEDIUM** | **LOW** | Public documentation for open-core `aegis-docprep` under CC/Apache terms. |
| **IP-009** | `docs/api.md` | Unfiltered backend REST API contract exposing internal administration routes. | **HIGH** | **NEGLIGIBLE** | **FILTERED**: Client receives restricted, versioned schema defined in `public_api_allowlist.yaml`. |
| **IP-010** | `web/src/lib/auth/session.ts` | Development authentication bypass granting automatic `admin` role on `dev-` prefix. | **CRITICAL** | **NEGLIGIBLE** | **REMEDIATED**: `dev-` tokens rejected in production; default admin role removed; fails closed. |
| **IP-011** | `web/src/lib/api/client.ts` | Hardcoded localhost default (`127.0.0.1:8000`) and `devToken` fallback headers. | **CRITICAL** | **NEGLIGIBLE** | **REMEDIATED**: Hardcoded localhost and devToken headers stripped. Same-origin `/api` proxy enforced. |
| **IP-012** | `web/src/lib/validation/environment.ts` | `NEXT_PUBLIC_AEGIS_DEV_TOKEN` declared in browser-visible environment schema. | **HIGH** | **NEGLIGIBLE** | **REMEDIATED**: `NEXT_PUBLIC_AEGIS_DEV_TOKEN` removed from schema and validation logic. |
| **IP-013** | `src/engines/topology/sheaf.py` | Sheaf Laplacian spectral decomposition and consistency obstruction algorithms. | **CRITICAL** | **NEGLIGIBLE** | **EXCLUDED**: 100% private cloud engine; never distributed. |
| **IP-014** | `src/engines/governance/contracts.py` | Abstract interpretation contradiction detection and specification invariant verification. | **CRITICAL** | **NEGLIGIBLE** | **EXCLUDED**: Runs server-side behind the Evaluation Gateway. |
| **IP-015** | `services/evaluation_gateway/keys/private-key.pem` | Asymmetric 256-bit Ed25519 root private key used to sign evaluation licenses. | **CRITICAL** | **NEGLIGIBLE** | **AIR-GAPPED**: Stored strictly in secure server vault/KMS; barred from packaging scripts. |

---

## 2. Residual Risk Assessment

By implementing physical withholding (Zone 2 Cloud Architecture) and client hardening:
- **0 proprietary Python files** are shipped to the user.
- **0 development credentials** exist in the client JavaScript bundle.
- **0 administrative or internal endpoints** are exposed through the edge proxy.
- All residual risks are classified as **NEGLIGIBLE** or **LOW**.
