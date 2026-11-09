# WP-UI-08: Frontend-Backend Integration Layer

## 1. Architectural Strategy

Prior to WP-UI-08, various components utilized differing fetch implementations and error shapes. WP-UI-08 standardizes all communication through a single unified API client in `web/src/lib/api/`:

```text
web/src/lib/api/
├── client.ts             Standardized fetch wrapper with header injection & Zod validation
├── errors.ts             Structured ApiError hierarchy with status predicate helpers
├── request-context.ts    Thread-safe context propagation for headers
└── index.ts              Central barrel exports
```

---

## 2. Standardized Request Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User Action / Hook
    participant Ctx as Request Context
    participant Client as apiRequest Client
    participant Zod as Zod Schema Validator
    participant Backend as FastAPI Backend (/v1)

    User->>Client: apiRequest(path, Schema, options)
    Client->>Ctx: getContextHeaders()
    Ctx-->>Client: Returns X-Workspace-ID, X-Tenant-ID, X-Correlation-ID
    Client->>Backend: HTTP Request + Bearer Auth + Context Headers
    alt 200/201 Success
        Backend-->>Client: JSON Body
        Client->>Zod: safeParse(body)
        Zod-->>Client: Validated Typed Data
        Client-->>User: Resolved Promise(data)
    else 400/401/403/404/409/429/500 Error
        Backend-->>Client: Error Response
        Client->>Client: Extract detail, code, request_id
        Client-->>User: Throw ApiError(status, code, detail)
    end
```

---

## 3. Contextual Header Propagation

Every outgoing HTTP request automatically includes:
- `Authorization`: Bearer token (resolved via session or development bypass).
- `X-Workspace-ID`: Currently selected workspace ID (e.g. `workspace-default`).
- `X-Tenant-ID`: Active sovereign tenant identifier (e.g. `tenant-default`).
- `X-Correlation-ID`: Trace UUID (`corr-<timestamp>-<random>`) for cross-service tracing.

---

## 4. Centralized Error Hierarchy (`ApiError`)

The `ApiError` class standardizes HTTP failure representation across all frontend features:

| Predicate Helper | Status Code | Standard Response Meaning |
| :--- | :--- | :--- |
| `err.isUnauthorized` | `401` | Session expired, invalid JWT, or missing credentials |
| `err.isForbidden` | `403` | User authenticated but lacks required permission |
| `err.isNotFound` | `404` | Requested document, job, or review does not exist |
| `err.isConflict` | `409` | Optimistic locking version mismatch during decision submit |
| `err.isValidationError` | `422` | Request body or query parameters violate backend schema |
| `err.isRateLimited` | `429` | Request threshold exceeded; back off before retrying |
| `err.isServerError` | `>= 500` | Gateway, database, or worker service error |
