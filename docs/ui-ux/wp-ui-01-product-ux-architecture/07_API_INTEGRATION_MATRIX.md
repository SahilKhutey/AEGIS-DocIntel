# AEGIS-DocIntel — API Integration Matrix

## 1. Integration Contract Overview

Every UI capability maps strictly to existing, verified backend endpoints documented in `contracts/API_ENDPOINT_INVENTORY.csv` and implemented in `src/api/routers/`.

## 2. Core Endpoint Mappings

| Feature / UI Component | Route Path | Method | Endpoint | Operation ID | Scope | Schema |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **System Health Status** | Shell Header | `GET` | `/health` | `health_check_health_get` | System | `HealthResponse` |
| **Readiness Probe** | Shell Header | `GET` | `/health/ready` | `readiness_health_ready_get` | System | `ReadinessResponse` |
| **Document List** | `/documents` | `GET` | `/v1/documents` | `list_documents_v1_documents_get` | Tenant | `DocumentListSchema` |
| **Upload Document** | `/documents` | `POST` | `/v1/documents/upload` | `upload_document_v1_documents_upload_post`| Tenant | `DocumentSchema` |
| **Document Details** | `/documents/[id]` | `GET` | `/v1/documents/{doc_id}` | `get_document_v1_documents__doc_id__get` | Tenant | `DocumentSchema` |
| **Document Chunks** | `/documents/[id]` | `GET` | `/v1/documents/{doc_id}/chunks` | `list_chunks_v1_documents__doc_id__chunks_get` | Tenant | `DocumentChunkListSchema` |
| **Layout Elements** | `/documents/[id]` | `GET` | `/v1/documents/{doc_id}/elements` | `get_elements_v1_documents__doc_id__elements_get` | Tenant | `LayoutElementListSchema` |
| **Indexing Status** | `/documents/[id]` | `GET` | `/v1/documents/{doc_id}/status` | `get_indexing_status_v1_documents__doc_id__status_get` | Tenant | `IngestionStatusResponse` |
| **Grounded QA & Answer**| `/ask` | `POST` | `/v1/answers` | `create_answer_v1_answers_post` | Tenant | `AnswerSchema` |
| **RAG Query** | `/ask` | `POST` | `/v1/query` | `query_documents_v1_query_post` | Tenant | `QueryResponse` |
| **Query Decomposition** | `/ask` | `POST` | `/v1/advanced/query/decompose` | `decompose_query_v1_advanced_query_decompose_post` | Tenant | `DecomposeResponse` |
| **Compare Documents** | `/compare` | `POST` | `/v1/intelligence/compare` | `compare_documents_v1_intelligence_compare_post` | Tenant | `DocumentComparisonSchema` |
| **Detected Conflicts** | `/compare` | `GET` | `/v1/intelligence/conflicts` | `get_conflicts_v1_intelligence_conflicts_get` | Tenant | `ConflictListSchema` |
| **Review Queue** | `/reviews` | `GET` | `/v1/reviews` | `list_reviews_v1_reviews_get` | Tenant | `ReviewListSchema` |
| **Review Details** | `/reviews/[id]` | `GET` | `/v1/reviews/{review_id}` | `get_review_detail_v1_reviews__review_id__get` | Tenant | `ReviewItemSchema` |
| **Claim Review Item** | `/reviews/[id]` | `POST` | `/v1/reviews/{review_id}/claim` | `claim_review_v1_reviews__review_id__claim_post` | Tenant | `ReviewItemSchema` |
| **Submit Decision** | `/reviews/[id]` | `POST` | `/v1/reviews/{review_id}/decisions` | `submit_decision_v1_reviews__review_id__decisions_post` | Tenant | `DecisionResponseSchema` |
| **Review Audit History**| `/reviews/[id]` | `GET` | `/v1/reviews/{review_id}/history` | `get_history_v1_reviews__review_id__history_get` | Tenant | `AuditEventListSchema` |
| **Background Jobs** | `/processing` | `GET` | `/v1/jobs` | `list_jobs_v1_jobs_get` | Tenant | `JobListSchema` |
| **Job Events & History**| `/processing/[id]`| `GET` | `/v1/jobs/{job_id}/events` | `get_job_events_v1_jobs__job_id__events_get` | Tenant | `JobEventListSchema` |
| **Retry Failed Job** | `/processing/[id]`| `POST` | `/v1/jobs/{job_id}/retry` | `retry_job_v1_jobs__job_id__retry_post` | Tenant | `JobSchema` |

## 3. Strict Validation & Error Handling

- **Zod Contract Enforcement**: All API responses pass through strict Zod schemas (`web/src/lib/schemas.ts`). Malformed payloads immediately raise typed `ApiError` instances.
- **Request ID Tracing**: All API calls capture backend `X-Request-ID` headers to assist production support and correlation.
- **No Production Mocks**: Development mocks are strictly forbidden in production build artifacts.
