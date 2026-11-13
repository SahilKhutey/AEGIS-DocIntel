# WP-04.01: Tenant Security Context & RBAC Architecture Review

**Document:** `03_TENANT_CONTEXT_AND_RBAC_REVIEW.md`  
**Work Package:** PROT-04.01 — Authentication Baseline & Threat Model  
**Component:** Tenant Isolation, Principal Context & Role-Based Access Control  
**Status:** **AUDITED & VERIFIED**  
**Classification:** Internal Security Architecture Reference  

---

## 1. Enterprise Tenant Context Model

Multi-tenancy in AEGIS-DocIntel is anchored by the `TenantContext` dataclass defined in `src/core/security_context.py`.

### 1.1 Structural Invariants & Immutability
- **Immutable Context:** `TenantContext` is declared as `@dataclass(frozen=True, init=False)`. Context fields cannot be reassigned or mutated after instantiation.
- **Fail-Closed Field Validation:** In `TenantContext.__init__`:
  - `tenant_id` is mandatory, non-empty, and stripped of whitespace; otherwise raises `ValueError("tenant_id is required")`.
  - `principal_id` (or `user_id`) is mandatory; otherwise raises `ValueError("principal_id is required")`.
  - `roles` must be a non-empty `frozenset[str]`; empty roles raise `ValueError("At least one role is required")`.
- **Tamper Resistance:** The security context is constructed exclusively by `_validate_jwt()` or `_validate_api_key()` inside the trusted authentication layer and bound to `request.state.tenant_context`. Client-supplied HTTP headers (e.g. `X-Tenant-ID`, `X-Role`, `X-User-ID`) are ignored by downstream business logic.

```python
@dataclass(frozen=True, init=False)
class TenantContext:
    tenant_id: str
    principal_id: str
    roles: frozenset[str]
    authentication_method: str
    monthly_token_limit: int
```

---

## 2. Role-Based Access Control (RBAC) Framework

### 2.1 Canonical Role Vocabulary
AEGIS enforces seven recognized enterprise roles defined in `src/core/security_context.py`:

| Role Name | Scope | Capabilities |
| :--- | :--- | :--- |
| `ROLE_VIEWER` (`viewer`) | Read-Only | Read documents, view audit events, query knowledge base. |
| `ROLE_EDITOR` (`editor`) | Read-Write | Ingest documents, extract tables, generate summaries. |
| `ROLE_REVIEWER` (`reviewer`) | Review Workflow | Inspect flagged extractions, annotate document anomalies. |
| `ROLE_REVIEW_ADMIN` (`review_admin`) | Compliance | Approve or reject compliance reviews, manage review queues. |
| `ROLE_TENANT_ADMIN` (`tenant_admin`) | Organization Admin | Delete documents, manage organization members, view billing. |
| `LEGACY_ADMIN` (`admin`) | Organization Admin | Backward-compatible alias mapped to `tenant_admin`. |
| `ROLE_PLATFORM_ADMIN` (`platform_admin`)| Global Infrastructure| Cross-tenant diagnostics, system health, platform metrics. |

### 2.2 Capability Methods
The security context exposes declarative boolean capability checks:
- `can_read_document()`: Granted to `viewer`, `editor`, `tenant_admin`, `admin`, and `platform_admin`.
- `can_write_document()`: Granted to `editor`, `tenant_admin`, and `admin`.
- `can_delete_document()`: Granted exclusively to `tenant_admin` and `admin`.
- `can_manage_members()`: Granted to `tenant_admin`, `admin`, and `platform_admin`.
- `can_manage_platform()`: Granted exclusively to `platform_admin`.

---

## 3. IDOR Defense: Cross-Tenant Resource Isolation

Insecure Direct Object Reference (IDOR) attacks occur when an authenticated user in Tenant A attempts to access or mutate a document belonging to Tenant B by guessing or enumerating the document ID.

### 3.1 `verify_resource_tenant` Protocol
In `src/core/authorization.py`, every document retrieval and modification endpoint invokes:
```python
def verify_resource_tenant(
    resource_tenant_id: Optional[str],
    context: TenantContext,
    resource_type: str = "document",
    allow_platform_admin: bool = False,
) -> None:
    if not resource_tenant_id:
        raise HTTPException(status_code=404, detail=f"{resource_type.capitalize()} not found")

    if str(resource_tenant_id) == str(context.tenant_id):
        return

    if allow_platform_admin and ROLE_PLATFORM_ADMIN in context.roles:
        return

    raise HTTPException(status_code=404, detail=f"{resource_type.capitalize()} not found")
```

### 3.2 Security Rationale: 404 Masking vs. 403 Disclosure
- **Standard Behavior (Vulnerable to Scanning):** Returning `HTTP 403 Forbidden` confirms to an attacker that the target document ID exists in the system.
- **AEGIS Behavior (Defensive Masking):** AEGIS returns `HTTP 404 Not Found` identical to a non-existent document ID. An attacker cannot enumerate whether an arbitrary UUID or document ID exists across another tenant boundary.

---

## 4. Evaluation License vs. Enterprise Tenant Context Decoupling

A critical architectural decision in WP-04.01 is **decoupling evaluation licensing from the enterprise `monthly_token_limit`**.

### 4.1 The Enterprise Quota Limitation
In the existing enterprise code, `TenantContext` includes:
```python
monthly_token_limit: int = 10_000_000
```
This field is designed for enterprise monthly billing contracts. It is unsuitable for the Protected Demo Edition because:
1. It only measures LLM tokens, whereas the demo requires multi-dimensional limits (documents ingested, pages parsed, comparison operations, concurrent queries).
2. It lacks temporal awareness (demo licenses expire after 14 days, regardless of remaining token balance).
3. It does not enforce device concurrency limits.

### 4.2 Decoupled Evaluation Context Hierarchy
For the Protected Demo Edition, four distinct context structures operate collaboratively:

```
┌────────────────────────────────────────────────────────┐
│  TenantContext (src/core/security_context.py)          │
│  - tenant_id: Evaluation workspace identifier          │
│  - principal_id: Evaluator identity                    │
│  - roles: frozenset({"viewer", "editor"})              │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  EvaluationLicenseContext (services/evaluation_gateway)│
│  - license_id: Cryptographic license identifier        │
│  - status: "ACTIVE" | "EXPIRED" | "REVOKED"            │
│  - max_devices: 1 (Strict device binding)              │
│  - expires_at: Explicit UTC timestamp                  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  EvaluationEntitlements (services/evaluation_gateway)  │
│  - capabilities: documents.read, documents.upload,     │
│    intelligence.query, documents.compare, etc.         │
│  - admin_capabilities: DENIED (HTTP 403)               │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  EvaluationQuotaContext (services/evaluation_gateway)  │
│  - max_documents: 15                                   │
│  - max_queries: 50                                     │
│  - max_comparisons: 10                                 │
│  - atomic reservations via threading.Lock              │
└────────────────────────────────────────────────────────┘
```

By separating identity (`TenantContext`), authorization (`EvaluationLicenseContext`), capabilities (`EvaluationEntitlements`), and consumption (`EvaluationQuotaContext`), the evaluation gateway prevents role overloading and ensures clean separation of concerns.
