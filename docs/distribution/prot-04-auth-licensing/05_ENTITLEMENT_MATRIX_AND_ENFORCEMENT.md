# PROT-04.05: Entitlement Matrix & Server-Side Enforcement

**Work Package:** PROT-04.05  
**Target:** Dynamic Policy Evaluation, Evaluator RBAC, Administrative Overrides, Multi-Tenant IDOR Defense & Anti-Spoofing  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**  
**Detailed Dossiers:** [wp-04-05-entitlement-enforcement/](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/docs/distribution/prot-04-auth-licensing/wp-04-05-entitlement-enforcement/)

---

## 1. Architectural Four-Factor Authorization

In the AEGIS-DocIntel Protected Demo Edition, feature entitlement enforcement operates strictly on the trusted Evaluation Gateway. Every protected operation evaluates the four-factor authorization formula:

$$\mathbf{ALLOW} = \mathbf{I} \land \mathbf{L} \land \mathbf{D} \land \mathbf{E} \land \mathbf{R} \land \mathbf{Q}$$

1. $\mathbf{I}$ (**Identity**): Authenticated evaluator principal context with anti-escalation enforcement (`ROLE_EVALUATOR`).
2. $\mathbf{L}$ (**License**): Cryptographically verified Ed25519 Compact JWS license with active status.
3. $\mathbf{D}$ (**Device**): Registered evaluation device proof-of-possession.
4. $\mathbf{E}$ (**Entitlement**): Evaluated versioned policy features, action-level permissions, and administrative overrides.
5. $\mathbf{R}$ (**Resource Scope**): Multi-tenant ownership verification with uniform `HTTP 404 Not Found` IDOR defense.
6. $\mathbf{Q}$ (**Quota**): Server-enforced capacity and rate limits.

---

## 2. Canonical Capability Vocabulary & RBAC Matrix

The system establishes an immutable capability catalogue in `src/schemas/evaluation/entitlement_catalogue.py`:

| Capability / Feature Key | Category | Evaluation Basic | Evaluation Pro | Admin Forbidden? |
| :--- | :--- | :---: | :---: | :---: |
| `document.upload` | Documents | **ALLOWED** | **ALLOWED** | No |
| `document.preview` | Documents | **ALLOWED** | **ALLOWED** | No |
| `query.ask_aegis` | Intelligence | **ALLOWED** | **ALLOWED** | No |
| `query.cross_document` | Intelligence | **ALLOWED** | **ALLOWED** | No |
| `table.view` | Tables | **ALLOWED** | **ALLOWED** | No |
| `export.json` | Export | **ALLOWED** | **ALLOWED** | No |
| `comparison.view` | Comparison | **DENIED (403)** | **ALLOWED** | No |
| `batch.processing` | Batch | **DENIED (403)** | **ALLOWED** | No |
| `redaction.tools` | Security | **DENIED (403)** | **ALLOWED** | No |
| `export.pdf` | Export | **DENIED (403)** | **ALLOWED** | No |
| `export.excel` | Export | **DENIED (403)** | **ALLOWED** | No |
| `streaming.events` | Realtime | **DENIED (403)** | **ALLOWED** | No |
| `users.manage` | Administrative | **DENIED (403)** | **DENIED (403)** | **YES (Forbidden)** |
| `platform.admin` | Administrative | **DENIED (403)** | **DENIED (403)** | **YES (Forbidden)** |
| `workspaces.create` | Administrative | **DENIED (403)** | **DENIED (403)** | **YES (Forbidden)** |
| `models.configure` | Administrative | **DENIED (403)** | **DENIED (403)** | **YES (Forbidden)** |
| `integrations.manage`| Administrative | **DENIED (403)** | **DENIED (403)** | **YES (Forbidden)** |

### Evaluator Anti-Escalation Boundary
- Evaluator sessions (`PrincipalContext`) are strictly prohibited from holding `ROLE_ADMIN`, `ROLE_PLATFORM_ADMIN`, or `ROLE_TENANT_ADMIN` (`RBAC-001`, `RBAC-002`, `RBAC-003`).
- Client-supplied role or tenant headers (`X-User-Role`, `X-Tenant-ID`) are ignored; only signed token claims govern security state (`RBAC-004`, `RBAC-005`).

---

## 3. Versioned Policy Engine & Administrative Overrides

Authorization rules are decoupled from application code and stored in versioned repositories:
- **`EntitlementPolicyRepository`**: Manages immutable versioned policy documents (`evaluation-basic` v1.0, `evaluation-pro` v1.0). Only `ACTIVE` versions grant access (`ENT-010`, `ENT-016`).
- **`EntitlementRepository`**: Handles license assignments and fine-grained administrative overrides (`EvaluationEntitlementOverride`). Supports dynamic temporary grants and immediate emergency feature revokes (`ENT-012`, `ENT-013`).
- **`EntitlementCache`**: Revision-aware short-lived cache providing sub-millisecond evaluation (< 0.25 ms) with proactive instantaneous invalidation upon override additions or policy updates (`ENT-011`).

---

## 4. Multi-Tenant Scoping & Strict IDOR Defense

Cross-tenant isolation is enforced on every target resource (documents, queries, comparisons, jobs, WebSocket streams):
- A resource belonging to Tenant $B$ does not exist from the perspective of Tenant $A$.
- Any attempt to access, query, or compare unowned resources returns **`HTTP 404 Not Found`** rather than `403 Forbidden` (`TENANT-ENT-002` - `TENANT-ENT-006`).
- Completely eliminates enumeration oracles and side-channel existence probing.

---

## 5. Formal Certification & Verification Evidence

- **Dedicated Protocol Suite:** 43/43 tests passed in `tests/security/evaluation/test_entitlement_enforcement_protocol.py` (`ENT-001` - `018`, `RBAC-001` - `010`, `TENANT-ENT-001` - `010`, `BYPASS-001` - `005`).
- **Full System Regression:** 230/230 tests passed across all security and gateway suites in 23.65s.
- **Frontend Security Check:** `npm --prefix web run verify:auth` passed with 0 violations.
- **Audit Artifacts:** Full evidence generated in `audit/prot-04-05/` (including 11 inventories, test captures, findings, and signoff).
- **Dossiers:** Complete 13-document engineering specification published in `docs/distribution/prot-04-auth-licensing/wp-04-05-entitlement-enforcement/`.
