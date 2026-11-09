# User Journey Maps & Operational Workflows

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Product Engineering |
| Dependencies | `web/src/config/workflows.ts`, OpenAPI contracts |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Specifies the executable state transitions, user actions, system responses, and failure branches for the four primary user workflows of AEGIS Workbench 2.0.

## 2. Core Workflows

### Workflow A: Document Ingestion
- **Entry Route**: `/documents`
- **Required Permission**: `documents.upload`
- **Steps**:
  1. `select`: User selects a local document artifact (PDF, DOCX, XLSX, image, audio).
  2. `validate`: Client checks file constraints (size $< 100\text{MB}$, MIME type).
  3. `upload`: Dispatches multipart request `POST /v1/documents/upload` with client-generated idempotency key.
  4. `process`: Subscribes via SSE / polling to `/v1/documents/{id}/status` and tracks pipeline stages (OCR $\to$ Layout $\to$ Table Matrix $\to$ Embeddings).
  5. `inspect`: Opens document detail view (`/documents/{id}`) upon reaching `ready`.
- **Failure States**: `invalid_file`, `upload_failed`, `processing_failed`, `unauthorized`, `network_error`.

---

### Workflow B: Intelligence Analysis ("Ask AEGIS")
- **Entry Route**: `/ask`
- **Required Permission**: `intelligence.query`
- **Steps**:
  1. `scope`: User selects one or more authorized documents or collections.
  2. `query`: Submits natural language inquiry (`POST /v1/answers`).
  3. `evidence`: Inspects streamed answer with interactive numbered citation pills (`[1]`, `[2]`).
- **Inspection**: Clicking citation badges opens the Contextual Evidence Studio, scrolling the PDF canvas to the target page and highlighting the exact bounding box.
- **Failure States**: `empty_query`, `insufficient_evidence`, `conflicting_evidence`, `unauthorized`, `network_error`.

---

### Workflow C: Document Comparison
- **Entry Route**: `/compare`
- **Required Permission**: `documents.compare`
- **Steps**:
  1. `select-a`: Selects authorized Document A.
  2. `select-b`: Selects authorized Document B (or alternate revision).
  3. `compare`: Dispatches comparison request (`POST /v1/intelligence/compare`).
  4. `inspect`: Renders side-by-side assertion matrix highlighting matched facts vs conflicting clauses.
- **Escalation**: Detected contradictions can be pushed directly to the Governance Review Queue with one click.
- **Failure States**: `same_document`, `missing_document`, `unauthorized`, `comparison_failed`, `network_error`.

---

### Workflow D: Governance Review
- **Entry Route**: `/reviews`
- **Required Permission**: `governance.review`
- **Steps**:
  1. `queue`: Loads pending review items filterable by status and candidate type.
  2. `inspect`: Claims review item (`POST /v1/reviews/{id}/claim`) and inspects source evidence quotes side-by-side.
  3. `decide`: Submits sovereign decision (`approve`, `correct`, `reject`, `request_evidence`) with mandatory rationale (`POST /v1/reviews/{id}/decisions`).
  4. `audit`: Server commits decision, increments revision counter, and appends an immutable audit event.
- **Failure States**: `stale_review`, `decision_not_allowed`, `evidence_missing`, `unauthorized`, `submission_failed`.
