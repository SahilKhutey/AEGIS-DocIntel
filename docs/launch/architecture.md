# AEGIS-DocIntel — Launch Edition Architecture

## 1. System Topology Overview

AEGIS-DocIntel is structured into a modern three-tier topology for the Product Launch Edition:

```
[ Visitor Browser / API Client / SDK ]
                  │
                  ▼
         [ Nginx Reverse Proxy ]
       (Port 80/443, Rate Limiter)
         │                     │
         │ ( / , static )      │ ( /api/ , /v1/ , /health )
         ▼                     ▼
[ Next.js Web Workbench ]   [ FastAPI Core Engine ]
   (Port 3000, React 19)       (Port 8000, Uvicorn)
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        [ SQLite Store ]  [ FAISS / Vector ] [ Audit Logger ]
        (Documents &      (Dense Embeddings)  (SHA-256 Chain)
         Raw Payloads)
```

---

## 2. Component Breakdown

### A. Ingress & Reverse Proxy (`deploy/nginx/`)
- Directs traffic based on path:
  - `/` and static assets route to `aegis-web:3000`.
  - `/api/` and `/v1/` route to `aegis-api:8000`.
  - `/v1/query/ws` handles WebSocket upgrade for streaming token delivery.
- Enforces HTTP rate limits (20 req/s, burst 30) and security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
- Protects operational metrics by returning `404 Not Found` on `/metrics`.

### B. Web Workbench (`web/`)
- Built with **Next.js 16.4.3**, **React 19.3.0**, and **TypeScript 5**.
- Uses same-origin relative URLs (`/api/v1/...`) with Next.js rewrites or Nginx ingress, eliminating cross-origin CORS complexity and host leaking.
- Implements interactive workspaces for Document Inspection, Ask AEGIS, Spec Comparison, and Governance Audit.

### C. Core API & Intelligence Engine (`src/`)
- **FastAPI Application:** Implements fail-closed auth guard, schema validation with Pydantic v2, and ASGI request correlation middleware (`X-Request-ID`, `X-Response-Time-ms`).
- **Layout-Aware Parsing (`aegis-docprep`):** Recovers topological reading order DAGs from spatial document geometry.
- **Submodular Context Compiler:** Packs tokens under knapsack constraints with provable $(1 - 1/e)/2$ approximation guarantees.
- **Evidence Provenance & Verification:** Resolves citations to exact page bounding boxes and enforces honest model abstention.

### D. Persistence & Isolation
- **SQLite Engine (Schema v2):** Stores document metadata, state machine transitions, and raw byte payloads. Re-hydrates state automatically across container restarts.
- **Tenant Context (`TenantContext`):** Every operation is strictly parameterized by `tenant_id`, verified by constant-time JWT/API-key checks.
