# WP-UI-09 — 07: Backend Feature Integration & API Contract Verification

**Work Package**: WP-UI-09 — Visual, Interaction & End-to-End Experience Validation  
**Document**: 07 — Backend API Contract Matrix & Header Injection Traces  
**Status**: Approved & Baseline Verified  
**Execution File**: `web/tests/integration/backend-features.spec.ts` (7 tests passing)  

---

## 1. Integration Architecture & Verification Model

The AEGIS-DocIntel frontend communicates with the FastAPI backend through a unified, resilient HTTP client (`web/src/lib/api/client.ts`). Every outgoing request is intercepted to ensure:
1. **Contextual Headers**: Automatic propagation of `X-Workspace-ID`, `X-Tenant-ID`, and `Authorization: Bearer <token>`.
2. **Authoritative Schema Parsing**: Inbound JSON payloads are validated through Zod schemas before rendering to prevent UI runtime exceptions from schema drift.
3. **Traceability**: Unique `X-Correlation-ID` header injected into every transaction for distributed logging across frontend and backend services.
4. **CORS Compliance**: Safe preflight handling across local development origins (`http://127.0.0.1:3000`, `http://localhost:3000`) and sovereign production domains.

---

## 2. API Integration Register (API-FE-001 through API-FE-020)

| Integration ID | Method & Endpoint | Frontend Feature Component | Contract Payload / Response | Status |
| :--- | :--- | :--- | :--- | :---: |
| **API-FE-001** | `GET /api/v1/workspace/overview` | `OverviewMetrics` (`/`) | Workspace summary counts, storage usage | **VERIFIED** |
| **API-FE-002** | `GET /api/v1/documents` | `DocumentTable` (`/documents`) | Paginated document metadata, status enum | **VERIFIED** |
| **API-FE-003** | `POST /api/v1/documents` | `UploadDialog` (`/documents`) | Multipart form upload, job UUID creation | **VERIFIED** |
| **API-FE-004** | `GET /api/v1/documents/{id}` | `DocumentInspector` (`/documents/[id]`)| Document page text chunks, bounding boxes | **VERIFIED** |
| **API-FE-005** | `DELETE /api/v1/documents/{id}` | `DocumentTable` (`/documents`) | Soft/hard document deletion confirmation | **VERIFIED** |
| **API-FE-006** | `POST /api/v1/ask` | `QuestionComposer` (`/ask`) | Question submission, streaming answer chunks | **VERIFIED** |
| **API-FE-007** | `GET /api/v1/evidence/{id}` | `EvidenceDrawer` (`/ask`) | Verbatim evidence span, coordinates, confidence | **VERIFIED** |
| **API-FE-008** | `POST /api/v1/feedback` | `FeedbackButtons` (`/ask`) | Grounded answer rating (thumbs up/down) | **VERIFIED** |
| **API-FE-009** | `POST /api/v1/compare` | `CompareWorkspace` (`/compare`) | Pairwise document diff, semantic alignment | **VERIFIED** |
| **API-FE-010** | `GET /api/v1/governance/reviews` | `ReviewQueue` (`/reviews`) | Pending review items, confidence flags | **VERIFIED** |
| **API-FE-011** | `POST /api/v1/governance/decisions`| `DecisionPanel` (`/reviews`) | Reviewer decision, mandatory rationale | **VERIFIED** |
| **API-FE-012** | `GET /api/v1/governance/audit` | `AuditTimeline` (`/reviews`) | Immutable chronological audit entries | **VERIFIED** |
| **API-FE-013** | `GET /api/v1/analytics/usage` | `AnalyticsDashboard` (`/analytics`) | Token usage, query volume timeseries | **VERIFIED** |
| **API-FE-014** | `GET /api/v1/analytics/export` | `ExportButton` (`/analytics`) | CSV / JSON metric report generation | **VERIFIED** |
| **API-FE-015** | `GET /api/v1/pipelines/{id}` | `PipelineGraph` (`/pipelines`) | Directed acyclic graph execution nodes | **VERIFIED** |
| **API-FE-016** | `GET /api/v1/monitoring/health` | `ServiceHealthList` (`/monitoring`) | Microservice health status, memory, CPU | **VERIFIED** |
| **API-FE-017** | `GET /api/v1/monitoring/telemetry`| `LatencyPercentiles` (`/monitoring`) | p50, p95, p99 latency distributions | **VERIFIED** |
| **API-FE-018** | `GET /api/v1/developer/keys` | `ApiCredentialManager` (`/developer`) | Active API keys, permission scopes | **VERIFIED** |
| **API-FE-019** | `POST /api/v1/developer/keys` | `CreateKeyModal` (`/developer`) | Generate scoped bearer API key | **VERIFIED** |
| **API-FE-020** | `POST /api/v1/developer/webhooks`| `WebhookForm` (`/developer`) | Webhook endpoint registration, SSRF check | **VERIFIED** |

---

## 3. Integration Defect Remediation & Verification

### DEF-002: Backend CORS Configuration for Local Development
- **Issue**: During automated browser execution, API requests from `http://127.0.0.1:3000` to `http://127.0.0.1:8000` failed CORS preflight checks (`400 Bad Request / Cross-Origin Request Blocked`).
- **Root Cause**: `src/core/settings.py` default `cors_origins` list included `http://localhost:3000` but omitted `http://127.0.0.1:3000`.
- **Remediation**: Updated `cors_origins` in `src/core/settings.py` to include `"http://127.0.0.1:3000"`.
- **Verification**: Verified zero CORS errors in Playwright integration suite `backend-features.spec.ts`.

### DEF-001: Next.js Turbopack HMR Cross-Origin Allowed Origins
- **Issue**: Next.js 16 development server rejected WebSocket HMR connections when accessed via IP `127.0.0.1:3000`.
- **Root Cause**: Turbopack strictly validates dev origins and requires explicit configuration.
- **Remediation**: Added `allowedDevOrigins: ["127.0.0.1", "localhost"]` to `web/next.config.ts`.
- **Verification**: Verified clean WebSocket connection and HMR lifecycle.
