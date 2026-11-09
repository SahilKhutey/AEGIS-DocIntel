# 08 — Functional Requirements Register

## 1. Functional Requirements (CW-FR-001 through CW-FR-037)

### 1.1 Operational Overview (`/`)
- **CW-FR-001**: System shall display top-level metrics for Total Documents, Processing, Completed, Needs Attention, and Queued.
- **CW-FR-002**: System shall compose overview metrics from live `/api/v1/documents` and `/api/v1/jobs` endpoints without fictional aggregation routes.
- **CW-FR-003**: System shall highlight failed documents and failed jobs in a dedicated Attention Panel.
- **CW-FR-004**: System shall display a Recent Documents widget listing up to 4 most recently updated source documents.
- **CW-FR-005**: System shall display a Processing Summary widget listing active and recent pipeline execution jobs.
- **CW-FR-006**: System shall provide direct navigation links from metrics to respective workspace areas (`/documents`, `/processing`).
- **CW-FR-007**: System shall preserve existing landing page links and cards for Ask, Compare, and Governance Review Queue.

### 1.2 Document Library (`/documents`)
- **CW-FR-008**: System shall list all documents registered in the active workspace with metadata (name, format, size, status, timestamp).
- **CW-FR-009**: System shall filter documents in real time based on search query matching filename or document ID.
- **CW-FR-010**: System shall provide status filter tabs for All, Completed, Processing, Queued, and Failed documents.
- **CW-FR-011**: System shall render accessible status badges (`DocumentStatusBadge`) with distinct text, variant, and ARIA label.
- **CW-FR-012**: System shall provide a manual Refresh button to refetch documents without reloading the webpage.
- **CW-FR-013**: System shall render an informative empty state when no documents match the active filter.
- **CW-FR-014**: System shall render a non-intrusive alert banner with a retry button upon backend fetch errors.
- **CW-FR-015**: System shall provide an "Upload Documents" action button opening the upload modal.

### 1.3 Upload Experience
- **CW-FR-016**: System shall support drag-and-drop file staging within an accessible dropzone area.
- **CW-FR-017**: System shall provide a fallback "Browse files" button that triggers the native OS file picker.
- **CW-FR-018**: System shall enforce pre-flight client-side file size validation rejecting files exceeding 200 MB.
- **CW-FR-019**: System shall reject empty files (0 bytes) before network transmission.
- **CW-FR-020**: System shall enforce MIME type allowlists accepting only PDF, DOCX, PPTX, HTML, TXT, and XLSX files.
- **CW-FR-021**: System shall display validation errors per staged file and prevent starting invalid uploads.
- **CW-FR-022**: System shall allow removing staged files before initiating upload.
- **CW-FR-023**: System shall display an accessible progress bar (`role="progressbar"`) during file upload transmission.
- **CW-FR-024**: System shall submit files via `multipart/form-data` to `POST /api/v1/documents/upload`.
- **CW-FR-025**: System shall display confirmation and newly registered document identifiers upon successful upload.

### 1.4 Document Inspection (`/documents/[documentId]`)
- **CW-FR-026**: System shall display complete document identity (filename, ID, MIME format, size, status, timestamps).
- **CW-FR-027**: System shall provide tabbed inspection sections: Overview, Preview, Extracted Text & Chunks, Extracted Facts, Metadata, and Processing Summary.
- **CW-FR-028**: System shall display key chunk text and extracted fact highlights on the initial Overview tab.
- **CW-FR-029**: System shall render authentic visual previews for supported formats (PDF, HTML).
- **CW-FR-030**: System shall display indexed text passages with page numbers, chunk identifiers, and section titles.
- **CW-FR-031**: System shall display extracted entity-attribute-value facts with confidence scores and evidence citations.
- **CW-FR-032**: System shall provide a button to trigger structured fact extraction via `POST /api/v1/documents/{doc_id}/extract-facts`.
- **CW-FR-033**: System shall provide a direct action link to query the document in Ask AEGIS (`/ask?doc_id=...`).

### 1.5 Processing Monitor (`/processing`)
- **CW-FR-034**: System shall list background jobs from `GET /api/v1/jobs` with document name, job type, progress, attempt, and status.
- **CW-FR-035**: System shall filter background jobs by status (All, Running, Failed, Succeeded, Queued).
- **CW-FR-036**: System shall render an ordered list timeline (`<ol>`) showing pipeline stages, status indicators, and durations.
- **CW-FR-037**: System shall provide a one-click Retry button for failed jobs issuing `POST /api/v1/jobs/{job_id}/retry`.

---

## 2. Non-Functional Requirements (CW-NFR-001 through CW-NFR-010)

- **CW-NFR-001 (Performance)**: First Contentful Paint (FCP) on Core Workspace pages shall remain under 1.5s on standard broadband.
- **CW-NFR-002 (Contract Integrity)**: All API payloads shall strictly conform to Zod schemas defined in `lib/schemas.ts`.
- **CW-NFR-003 (Zero Fake APIs)**: The client shall never mock or fabricate metrics endpoints; all statistics must derive from authentic FastAPI data.
- **CW-NFR-004 (Accessibility)**: All workspace components shall meet WCAG 2.2 AA standards, ensuring full keyboard reachability and semantic ARIA labeling.
- **CW-NFR-005 (Color Independence)**: No operational status (completed, failed, processing, queued) shall be communicated through color alone.
- **CW-NFR-006 (Responsive Density)**: Tables and inspection tabs shall adapt fluidly from 320px mobile viewports up to 1440px+ ultra-wide displays.
- **CW-NFR-007 (Tenant Boundary)**: All document and job API requests shall include authenticated tenant isolation headers.
- **CW-NFR-008 (Test Coverage)**: 100% of core workspace requirements shall be verified through automated Vitest and Playwright test suites.
- **CW-NFR-009 (Zero Regression)**: All pre-existing test suites (WP-UI-01, WP-UI-02, WP-UI-03, `workbench.spec.ts`) must pass without modification.
- **CW-NFR-010 (Error Resilience)**: Network interruptions and backend 5xx errors shall be handled gracefully with visible retry triggers.
