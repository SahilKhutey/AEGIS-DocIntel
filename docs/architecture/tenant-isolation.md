# Tenant Isolation & Multi-Tenancy Architecture

## 1. Core Security Principle

In AEGIS-DocIntel, tenant isolation is enforced at the **authoritative data-access boundary**, never merely at the HTTP routing or middleware layer. 

```
                                      ┌──────────────────────────────────────────────┐
                                      │              FastAPI Ingress                 │
                                      │      (AuthGuardMiddleware / Bearer JWT)       │
                                      └──────────────────────┬───────────────────────┘
                                                             │
                                                             ▼
                                      ┌──────────────────────────────────────────────┐
                                      │           TenantContext Factory              │
                                      │   (tenant_id, principal_id, frozenset[roles])│
                                      └──────────────────────┬───────────────────────┘
                                                             │
                                ┌────────────────────────────┴───────────────────────────┐
                                │                                                        │
                                ▼                                                        ▼
                ┌───────────────────────────────┐                        ┌───────────────────────────────┐
                │   Persistence Boundary        │                        │   AI & Search Boundary        │
                │  - SQLite: WHERE doc_id = ?   │                        │  - VectorStore: expr filter   │
                │    AND tenant_id = ?          │                        │    tenant_id == 'alpha'       │
                │  - Non-disclosing 404         │                        │  - SemanticCache:             │
                │    (no 403 leaking presence)  │                        │    alpha:sha256(query)        │
                └───────────────────────────────┘                        └───────────────────────────────┘
```

1. **Authentication** identifies the principal and proves their credential validity.
2. **Authorization** determines the permissions granted to that principal within the tenant scope.
3. **Tenant-Scoped Data Access** mechanically constrains every query, cache lookup, index traversal, and file I/O to resources owned by that tenant.

---

## 2. Security Context & Role-Based Access Control (RBAC)

The foundational security context is the immutable `TenantContext` defined in `src/core/security_context.py`.

```python
@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    principal_id: str
    roles: frozenset[str]
    authentication_method: str = "bearer"
    monthly_token_limit: Optional[int] = None
```

### RBAC Permission Matrix

| Role | Read Document / Chunks | Upload / Ingest | Reindex / Batch | Delete Document | Manage Webhooks | Data Governance (Hold/Purge) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`viewer`** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **`editor`** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **`tenant_admin`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **`platform_admin`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Any attempt by a `viewer` to invoke mutating endpoints (`POST /v1/documents/upload`, `DELETE /v1/documents/{doc_id}`, `POST /v1/webhooks/subscriptions`) immediately triggers `403 Forbidden`.

---

## 3. Data-Access Boundary Enforcement

### 3.1 SQL Parameterized Constraints
All database queries explicitly bind the caller's authenticated `tenant_id` at the SQL driver parameter level:

```sql
SELECT raw_bytes, sha256 
FROM documents 
WHERE doc_id = ? AND tenant_id = ? AND status = 'ready';
```

Cross-tenant access cannot occur via SQL injection or parameter omission because SQLite parameters are strictly positional and mandatory.

### 3.2 Non-Disclosing 404 (IDOR Defense)
When a request attempts to access or mutate a `doc_id` belonging to a different tenant:
- The system returns `404 Not Found`.
- It does **not** return `403 Forbidden` for other tenants' documents, preventing attackers from probing valid resource IDs across organizations (Insecure Direct Object Reference enumeration defense).

### 3.3 Semantic Cache & Vector Isolation
- **Semantic Cache Keys**: Partitioned strictly using `f"{tenant_id}:{query_sha256}"`. A query from Tenant A will never hit or populate Tenant B's cached query responses or embeddings.
- **Vector Search Constraints**: In Milvus and Elasticsearch, every vector similarity search applies an mandatory boolean filter: `tenant_id == :tenant_id`. Unfiltered searches across multiple tenants are blocked by architecture.
