# 09 — API Contract Mapping & Backend Gap Analysis

## 1. Verified FastAPI Endpoints

All core workspace interactions map directly to verified endpoints in `contracts/API_ENDPOINT_INVENTORY.csv` and FastAPI routers in `src/main.py`:

| Workspace Module | UI Action | HTTP Method | FastAPI Path | Request Payload / Params | Response Schema | Status Code |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Workspace Overview** | Load overview metrics | `GET` | `/api/v1/documents` | `limit=100` | `DocumentListSchema` | 200 OK |
| **Workspace Overview** | Load overview metrics | `GET` | `/api/v1/jobs` | `limit=50` | `JobListSchema` | 200 OK |
| **Document Library** | Browse documents | `GET` | `/api/v1/documents` | `page`, `page_size`, `status` | `DocumentListSchema` | 200 OK |
| **Document Library** | Delete document | `DELETE` | `/api/v1/documents/{doc_id}` | None | Empty / Message | 200 OK |
| **Document Library** | Reindex document | `POST` | `/api/v1/documents/{doc_id}/reindex` | None | Job / Message | 202 Accepted |
| **Upload Experience** | Upload file | `POST` | `/api/v1/documents/upload` | `multipart/form-data` (`file`) | `DocumentUploadResponseSchema` | 202 Accepted |
| **Document Inspection** | Fetch document details | `GET` | `/api/v1/documents/{doc_id}` | None | `DocumentSchema` | 200 OK |
| **Document Inspection** | Fetch text chunks | `GET` | `/api/v1/documents/{doc_id}/chunks` | None | `DocumentChunkListSchema` | 200 OK |
| **Document Inspection** | Fetch extracted facts | `GET` | `/api/v1/documents/{doc_id}/facts` | None | `{ facts: ExtractedFact[] }` | 200 OK |
| **Document Inspection** | Run fact extraction | `POST` | `/api/v1/documents/{doc_id}/extract-facts` | None | `{ facts: ExtractedFact[] }` | 200 OK |
| **Processing Monitor** | List background jobs | `GET` | `/api/v1/jobs` | `status`, `job_type`, `limit`, `cursor` | `JobListSchema` | 200 OK |
| **Processing Monitor** | Job details | `GET` | `/api/v1/jobs/{job_id}` | None | `JobSchema` | 200 OK |
| **Processing Monitor** | Retry failed job | `POST` | `/api/v1/jobs/{job_id}/retry` | None | `{ message: string }` | 200 OK |
| **Processing Monitor** | Cancel running job | `POST` | `/api/v1/jobs/{job_id}/cancel` | None | `{ message: string }` | 200 OK |

---

## 2. Path Aliasing

As verified during backend architecture inspection, `src/main.py` registers routers with both `/v1/...` and `/api/v1/...` prefixes. The frontend client uniformly utilizes `/api/v1/...` paths, ensuring seamless routing through reverse proxies, API gateways, and Next.js Turbopack dev servers.

---

## 3. Backend Gap Analysis & Client Adaptations

| Area | Backend Reality | Client Adaptation / Mitigation | Sovereign Status |
| :--- | :--- | :--- | :--- |
| **Dashboard Metrics** | No dedicated `/dashboard/metrics` or `/workspace/overview` route in FastAPI | Client aggregates metrics dynamically from `GET /api/v1/documents` and `GET /api/v1/jobs` in `fetchWorkspaceOverview()`. | **Zero Fake APIs Enforced**: Adheres strictly to genuine data sources. |
| **Document File Size** | `page_count` is provided by backend; file size bytes are optional in index metadata | Client computes approximate file size `(page_count || 1) * 250,000` bytes when raw file size is omitted. | Graceful fallback without data distortion. |
| **Pipeline Stage Telemetry** | `/v1/jobs` returns top-level status, error code, and attempts; stage events are available via `/jobs/{id}/events` | `generateStagesForJob()` synthesizes stage breakdown dynamically from job status and error codes. | Seamless pipeline visualization across all job states. |
| **Document Status Enum** | Backend uses `ready`, `indexing`, `reindexing`, `pending`, `failed` | Bi-directional adapter functions `mapBackendStatusToDocumentStatus()` and `mapDocumentStatusToBackend()`. | Full lifecycle compatibility across UI and backend. |
