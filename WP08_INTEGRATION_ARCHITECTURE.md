# AEGIS-DocIntel — WP-08: Integration Architecture

> **Work Package**: WP-08 — Integration  
> **Status**: **ARCHITECTURE SPECIFIED**  
> **Date**: 2026-11-04  
> **Target Branch**: `wp-08-integration`  

---

## 1. System Integration Overview

The AEGIS-DocIntel application integrates three primary layers into a cohesive document intelligence platform:
1. **Frontend Presentation & Governance Layer (`web/`)**: Next.js 16 App Router application providing document workspaces, query interfaces, cross-document comparison, and human governance review queues.
2. **API Gateway & Routing Layer (`src/`)**: High-performance FastAPI backend providing authentication, authorization, anti-IDOR tenant scoping, request validation, and asynchronous job coordination.
3. **Processing, Intelligence & Storage Core (`aegis/`)**: Verified multi-modal pipelines executing OCR extraction (WP-05), hybrid retrieval, claim-level citation validation, conflict extraction, report synthesis (WP-06), and security lifecycle enforcement (WP-07).

---

## 2. Integrated Product Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientBrowser["User Browser / E2E Client"]
        UI_DOC["/documents<br/>Workspace & Upload"]
        UI_ASK["/ask<br/>Query & Citations"]
        UI_CMP["/compare<br/>Cross-Doc Conflicts"]
        UI_REV["/reviews<br/>Governance Queue"]
    end

    subgraph IngressGateway["Nginx / API Gateway (:8000)"]
        NGX[Reverse Proxy / TLS Termination]
        AUTH_MW[AuthGuardMiddleware<br/>JWT RS256 · API Key · Brute-force Lockout]
        TENANT_MW[TenantIsolationGuard<br/>Anti-IDOR HTTP 404 Enforcement]
    end

    subgraph ApiService["FastAPI Application (src.main)"]
        ROUTER_DOC["/v1/documents/*<br/>Ingestion & Lifecycle"]
        ROUTER_ANS["/v1/answers/*<br/>Grounded QA & Citations"]
        ROUTER_QRY["/v1/queries/*<br/>Hybrid Retrieval & Search"]
        ROUTER_REV["/v1/admin/reviews/*<br/>Governance & Auditing"]
    end

    subgraph CorePipelines["Core Processing & Intelligence (aegis/)"]
        WP05_PROC["WP-05 Processing Pipeline<br/>OCR · Layout · Tables · Provenance"]
        WP06_INTEL["WP-06 Intelligence Pipeline<br/>RRF Fusion · Citation Engine · Conflict Engine · Report Renderer"]
        WP07_SEC["WP-07 Reliability & Deletion<br/>Privacy Masker · Cascading Deletion · Resilient Worker Queue"]
    end

    subgraph DataStorage["Data & Storage Infrastructure"]
        S3[MinIO S3 Object Storage<br/>Raw Documents & Rendered Reports]
        PG[(PostgreSQL Database<br/>Documents · Chunks · Reviews · Tombstones)]
        VEC[Vector Database / Index<br/>Tenant-Partitioned Dense Embeddings]
        REDIS[(Redis Queue / Cache<br/>Background Jobs · Lease Heartbeats · DLQ)]
    end

    ClientBrowser -->|HTTP / JSON / Multipart| NGX
    NGX --> AUTH_MW --> TENANT_MW
    TENANT_MW --> ROUTER_DOC & ROUTER_ANS & ROUTER_QRY & ROUTER_REV

    ROUTER_DOC --> WP05_PROC
    ROUTER_ANS --> WP06_INTEL
    ROUTER_QRY --> WP06_INTEL
    ROUTER_REV --> WP07_SEC

    WP05_PROC & WP06_INTEL & WP07_SEC --> S3 & PG & VEC & REDIS
```

---

## 3. Frontend-to-Backend Communication Protocol

### 3.1 Networking & Contract Handshake
- **Base URL Resolution**: Client reads `process.env.NEXT_PUBLIC_AEGIS_API_URL` (defaulting to `http://127.0.0.1:8000`).
- **Authentication Headers**:
  - `Authorization: Bearer <jwt_token>`
  - `X-API-Key: <api_key>` (for automated services)
  - `X-Tenant-ID: <tenant_id>` (validated against token claims; mismatch immediately rejected)
- **Runtime Zod Validation**:
  - The client wraps every fetch request in `apiRequest<T>(path, schema, init)` ([`web/src/lib/api-client.ts`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/web/src/lib/api-client.ts)).
  - Responses that violate TypeScript/Zod schemas fail closed with `ApiError("Response contract validation failed: ...")`.

### 3.2 Standardized Error Model
All backend HTTP error responses conform to a unified contract:
```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document is unavailable.",
    "request_id": "req-20261104-001",
    "details": {}
  }
}
```
**Security Invariant**: Error messages never expose database stack traces, file system paths, credentials, or other tenants' data. Cross-tenant access triggers `DOCUMENT_NOT_FOUND` (HTTP 404) to prevent IDOR enumeration.

---

## 4. End-to-End Document-to-Report Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Researcher
    participant Web as Next.js Workbench
    participant API as FastAPI Ingress
    participant Storage as Object Storage (S3)
    participant Worker as Background Worker
    participant Proc as WP-05 Processing
    participant Intel as WP-06 Intelligence
    participant Tomb as WP-07 Lifecycle

    User->>Web: Upload PDF Document
    Web->>API: POST /v1/documents/upload (Multipart)
    API->>Storage: Store raw file with SHA-256 Checksum
    API->>Worker: Enqueue Ingestion Job (Idempotency Key)
    API-->>Web: 202 Accepted {doc_id, status: "pending"}

    Worker->>Proc: Execute OCR, Layout & Table Extraction
    Proc->>Storage: Save Page Layouts, BBoxes & Chunks
    Proc->>Worker: Extraction Complete
    Worker->>Intel: Index Chunks in Vector & BM25 Stores
    Worker-->>API: Status updated to "ready"

    User->>Web: Ask Question / Compare Documents
    Web->>API: POST /v1/answers (Query + DocIDs)
    API->>Intel: Hybrid RRF Retrieval + Evidence Evaluation
    Intel->>Intel: Claim Decomposition + 7-Label Citation Check
    Intel->>Intel: 8-Stage Conflict Extraction
    Intel-->>Web: 200 OK {answer, citations, evidence, conflicts}

    User->>Web: Request Synthesized Report
    Web->>API: POST /v1/reports/generate
    API->>Intel: Pre-Render Report Validation (Citations & Conflicts)
    Intel->>Storage: Render & Persist Markdown / HTML / JSON
    API-->>Web: 201 Created {report_id, download_url}

    User->>Web: Delete Document
    Web->>API: DELETE /v1/documents/{doc_id}
    API->>Tomb: Multi-Target Cascade (Files, Chunks, Vectors, Cache)
    Tomb->>Tomb: Create 90-Day Verifiable Tombstone
    API-->>Web: 200 OK {status: "deleted", tombstone_id}
```

---

## 5. Architectural Quality Invariants

1. **End-to-End Grounding**: No factual claim may be presented in the frontend or in exportable reports without an entailed source citation and bounding box coordinates.
2. **Conflict Preservation**: Contradictions between multiple documents must never be resolved by silent overwriting; they must be surfaced in comparative views and reports with their conflicting values.
3. **Tenant Containment**: All vector similarity calculations, search indexes, and cache lookups must strictly pre-filter on `tenant_id`.
4. **Disaster Recoverability**: All database snapshots are verified via AES-256-GCM encryption and SHA-256 integrity checksums, with post-restoration tombstone replay.
