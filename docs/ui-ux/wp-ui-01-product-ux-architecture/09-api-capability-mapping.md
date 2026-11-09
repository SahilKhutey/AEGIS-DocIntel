# API Capability Mapping & OpenAPI Contract Traceability

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Integration Engineering |
| Dependencies | `contracts/openapi.yaml`, `contracts/API_ENDPOINT_INVENTORY.csv`, `src/api/routers/` |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Maps every frontend UI module, view, and operation to verified backend REST endpoints from the official OpenAPI contract. Ensures zero fictitious endpoints and provides comprehensive UI state and error expectations.

---

## 2. Verified Endpoint Mappings

### API-UI-001 — Document Library
- **Frontend Route**: `/documents`
- **HTTP Method**: `GET`
- **Endpoint**: `/v1/documents` (also supported at `/api/v1/documents`)
- **Operation ID**: `list_documents_v1_documents_get`
- **Request Parameters**: `page: int = 1`, `page_size: int = 20`, `status: Optional[str] = None`
- **Response Schema**: `DocumentListSchema` (items: `DocumentSchema[]`, total: `int`)
- **Authentication**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Tenant Scope**: Backend enforced via `TenantContext`
- **UI States**: Loading (table skeleton), Loaded (data grid), Empty (upload call-to-action), Error (recoverable alert with request ID), Unauthorized (401 redirect).
- **Tests**: Document list renders from API; empty state renders when total is 0; 401/403 triggers error boundary.

---

### API-UI-002 — Document Ingestion & Upload
- **Frontend Route**: `/documents` (Upload Modal)
- **HTTP Method**: `POST`
- **Endpoint**: `/v1/documents/upload`
- **Operation ID**: `upload_document_v1_documents_upload_post`
- **Request Schema**: `multipart/form-data` (`file: UploadFile`, `idempotency_key: str`, `tags: Optional[str]`)
- **Response Schema**: `DocumentResponse` (`doc_id`, `status: "pending"|"indexing"`, `page_count`, `job_id`)
- **Authentication**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Tenant Scope**: Backend enforced via `TenantContext`
- **UI States**: Staging, Validating, Uploading (progress bar), Queued (202 Accepted), Error (size exceeded / format unsupported).
- **Tests**: Multipart payload submission; SHA-256 idempotency key generation; server error response parsing.

---

### API-UI-003 — Document Detail & Inspection
- **Frontend Route**: `/documents/[documentId]`
- **HTTP Method**: `GET`
- **Endpoint**: `/v1/documents/{doc_id}`
- **Operation ID**: `get_document_v1_documents__doc_id__get`
- **Request Parameters**: `doc_id: str` (path parameter)
- **Response Schema**: `DocumentSchema`
- **Authentication**: Required
- **Tenant Scope**: Backend enforced
- **UI States**: Loading, Loaded, Not Found (404 notice), Error.
- **Tests**: Detail card renders metadata; 404 displays actionable missing document banner.

---

### API-UI-004 — Document Chunks & Layout Elements
- **Frontend Route**: `/documents/[documentId]` (Tabs: Chunks & Layout)
- **HTTP Method**: `GET`
- **Endpoints**:
  - Chunks: `/v1/documents/{doc_id}/chunks` (`list_chunks_v1_documents__doc_id__chunks_get`)
  - Layout: `/v1/documents/{doc_id}/elements` (`get_elements_v1_documents__doc_id__elements_get`)
- **Response Schemas**: `DocumentChunkListSchema`, `LayoutElementListSchema` (bounding boxes: `[ymin, xmin, ymax, xmax]`)
- **Authentication**: Required
- **Tenant Scope**: Backend enforced
- **UI States**: Loading, Rendered chunk table, Rendered canvas with vector bounding boxes, Error.
- **Tests**: Chunks pagination; element coordinates map to canvas highlight polygons.

---

### API-UI-005 — Grounded Question Answering ("Ask AEGIS")
- **Frontend Route**: `/ask`
- **HTTP Method**: `POST`
- **Endpoint**: `/v1/answers`
- **Operation ID**: `create_answer_v1_answers_post`
- **Request Schema**: `application/json` (`question: str`, `document_ids: List[str]`, `filter_metadata: Optional[dict]`)
- **Response Schema**: `AnswerSchema` (`answer: str`, `citations: Citation[]`, `evidence: Evidence[]`, `insufficient_evidence: bool`)
- **Authentication**: Required
- **Tenant Scope**: Backend enforced
- **UI States**: Formulating, Submitting, Token Streaming, Citation Illuminated, Insufficient Evidence Warning, Error.
- **Tests**: Streaming token delivery; citation click syncs to evidence panel; warning banner on insufficient evidence.

---

### API-UI-006 — Cross-Document Comparison
- **Frontend Route**: `/compare`
- **HTTP Method**: `POST`
- **Endpoint**: `/v1/intelligence/compare`
- **Operation ID**: `compare_documents_v1_intelligence_compare_post`
- **Request Schema**: `application/json` (`doc_a_id: str`, `doc_b_id: str`, `attributes: Optional[List[str]]`)
- **Response Schema**: `DocumentComparisonSchema` (`comparisons: list`, `conflicts: list`, `total_pairs: int`)
- **Authentication**: Required
- **Tenant Scope**: Backend enforced
- **UI States**: Document selection, Computing matrix, Rendered comparison table, Highlighted conflicts, Error.
- **Tests**: Validation preventing comparing identical documents; conflict rows flagged with warning badge.

---

### API-UI-007 — Governance Review Queue
- **Frontend Route**: `/reviews`
- **HTTP Method**: `GET`
- **Endpoint**: `/v1/reviews`
- **Operation ID**: `list_reviews_v1_reviews_get`
- **Request Parameters**: `status: Optional[str]`, `candidate_type: Optional[str]`, `cursor: Optional[str]`
- **Response Schema**: `ReviewListSchema` (`items: ReviewItemSchema[]`, `next_cursor: Optional[str]`)
- **Authentication**: Required (`reviewer` or `admin` role)
- **Tenant Scope**: Backend enforced
- **UI States**: Loading, Queue populated, Queue clear (all reviewed), Filtered empty state, Error.
- **Tests**: Queue item cards display priority and candidate snippet; status tabs filter by `pending`/`in_review`.

---

### API-UI-008 — Sovereign Review Decision & Claim
- **Frontend Route**: `/reviews/[reviewId]`
- **HTTP Method**: `POST`
- **Endpoints**:
  - Claim: `/v1/reviews/{review_id}/claim` (`claim_review_v1_reviews__review_id__claim_post`)
  - Decide: `/v1/reviews/{review_id}/decisions` (`submit_decision_v1_reviews__review_id__decisions_post`)
- **Request Schemas**:
  - Claim: `{ "expected_version": int }`
  - Decide: `{ "action": "approve"|"correct"|"reject"|"request_evidence", "expected_version": int, "rationale": str, "corrected_value": any, "unit": str }`
- **Response Schemas**: `ReviewItemSchema`, `DecisionResponseSchema`
- **Authentication**: Required (`reviewer` role enforced in `src/engines/governance/policy.py`)
- **Tenant Scope**: Backend enforced
- **UI States**: Claiming, In Review, Submitting Decision, Concurrency Conflict (409 Stale Version), Confirmed.
- **Tests**: 4-way action submission; rationale validation ($\ge 3$ characters); audit event append verification.

---

### API-UI-009 — Processing Job Monitoring & DLQ Recovery
- **Frontend Route**: `/processing` (Planned)
- **HTTP Method**: `GET` / `POST`
- **Endpoints**:
  - List Jobs: `GET /v1/jobs` (`list_jobs_v1_jobs_get`)
  - Job Events: `GET /v1/jobs/{job_id}/events` (`get_job_events_v1_jobs__job_id__events_get`)
  - Retry Job: `POST /v1/jobs/{job_id}/retry` (`retry_job_v1_jobs__job_id__retry_post`)
  - Cancel Job: `POST /v1/jobs/{job_id}/cancel` (`cancel_job_v1_jobs__job_id__cancel_post`)
- **Authentication**: Required (`admin` / `tenant_admin` for retry/cancel)
- **Tenant Scope**: Backend enforced
- **UI States**: Active jobs table, Attempt timeline, Failed job diagnostics, Retry dispatched.
- **Tests**: Reschedule triggers job transition to `queued`; cancel updates status to `cancelled`.
