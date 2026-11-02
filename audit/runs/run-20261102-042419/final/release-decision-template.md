# AEGIS-DocIntel — Formal Release Decision Template

**Release Candidate:** `{{RELEASE_CANDIDATE_VERSION}}`  
**Git Commit SHA:** `{{COMMIT_SHA}}`  
**Git Branch:** `{{BRANCH}}`  
**Audit Evaluation Date:** `{{AUDIT_TIMESTAMP_UTC}}`  
**Release Gate Determination:** **[{{GO_OR_NO_GO}}]**  
**Classification:** Alpha / Experimental (Evaluation Baseline — Not Production-Ready)  

---

## 1. Release Acceptance Criteria Checklist

Every gate must be evaluated and recorded as `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, or `NOT APPLICABLE`.
*Release Rule: An unexecuted check may never be marked as passed. No unresolved critical security defect, cross-tenant data leak, unsupported factual claim, data-loss defect, or failed mandatory test may be waived.*

| Gate ID | Release Scope | Required Threshold | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **GATE-01** | Repository Integrity & Clean Imports | Zero syntax errors, Ruff clean, lock sync | `{{GATE_01_RESULT}}` | `{{GATE_01_STATUS}}` |
| **GATE-02** | Reading Order & Table Fidelity | $\tau \ge 0.80$, Cell F1 $\ge 0.90$ | `{{GATE_02_RESULT}}` | `{{GATE_02_STATUS}}` |
| **GATE-03** | Context Packing & Knapsack Ratio | 0% budget violation, ratio $\ge 0.316$ | `{{GATE_03_RESULT}}` | `{{GATE_03_STATUS}}` |
| **GATE-04** | Retrieval & Grounded Generation | MRR $\ge 0.70$, Abstention $100\%$, 0% hall | `{{GATE_04_RESULT}}` | `{{GATE_04_STATUS}}` |
| **GATE-05** | Intelligence & Conflict Detection | Fact F1 $\ge 0.85$, Conflict Recall $\ge 0.90$ | `{{GATE_05_RESULT}}` | `{{GATE_05_STATUS}}` |
| **GATE-06** | Security, AuthGuard & Tenant Isolation | Deny-by-default, 0 IDOR leaks, 0 secret leak | `{{GATE_06_RESULT}}` | `{{GATE_06_STATUS}}` |
| **GATE-07** | Review Governance & Audit Immutability | Optimistic locking, append-only tamper-proof | `{{GATE_07_RESULT}}` | `{{GATE_07_STATUS}}` |
| **GATE-08** | Durable Background Jobs & Crash Recovery | Idempotent lease, crash recovery verified | `{{GATE_08_RESULT}}` | `{{GATE_08_STATUS}}` |
| **GATE-09** | OpenAPI Specification Integrity | Exact match with openapi.json (0 diff) | `{{GATE_09_RESULT}}` | `{{GATE_09_STATUS}}` |
| **GATE-10** | Document Intelligence Workbench SPA | Responsive HTTP 200 SPA at root & /ui | `{{GATE_10_RESULT}}` | `{{GATE_10_STATUS}}` |

---

## 2. Risk & Limitation Summary

- **Documented Status:** Alpha / Experimental (Evaluation Baseline).
- **Research Boundaries:** Topological persistent homology and distributed clustering are explicitly scoped as research prototypes and excluded from the release gate requirements.
- **Semantic Fallback:** Deterministic feature vector mock fallback is operational when third-party embeddings are unconfigured.
- **Concurrency:** SQLite WAL mode validated for single-node development; PostgreSQL migration path required for high-concurrency production deployments.

---

## 3. Final Determination & Authority Sign-Off

### Decision: **[{{GO_OR_NO_GO}}]**

**Audit Execution Summary:**
- Total Checks Evaluated: `{{TOTAL_CHECKS}}`
- Checks Passed: `{{PASSED_CHECKS}}`
- Checks Failed: `{{FAILED_CHECKS}}`
- Checks Blocked: `{{BLOCKED_CHECKS}}`
- Checks Not Run / Excluded: `{{NOT_RUN_CHECKS}}`

**Sign-off:**
- **Lead Verification Auditor:** ___________________________  Date: ____________
- **Security & Governance Officer:** ___________________________  Date: ____________
- **Principal Software Architect:** ___________________________  Date: ____________
