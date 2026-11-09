# 01 — Workspace Architecture

## 1. Architectural Vision

The Core Workspace is the operational cockpit of AEGIS-DocIntel. It integrates five core frontend modules into a cohesive workbench environment:

```
+-----------------------------------------------------------------------------------+
| Application Shell (WP-UI-03: Header, Sidebar, Tenant Selector, Breadcrumbs)       |
+-----------------------------------------------------------------------------------+
| Core Workspace Layer (WP-UI-04)                                                   |
|                                                                                   |
|  +--------------------+  +--------------------+  +--------------------+           |
|  | Overview Dashboard |  |  Document Library  |  | Processing Monitor |           |
|  | (/)                |  |  (/documents)      |  | (/processing)      |           |
|  +--------------------+  +--------------------+  +--------------------+           |
|            |                       |                       |                      |
|            |                       v                       v                      |
|            |             +--------------------+  +--------------------+           |
|            |             | Upload Experience  |  | Job Stage Timeline |           |
|            |             | (Modal Dialog)     |  | (<ol role="list">) |           |
|            |             +--------------------+  +--------------------+           |
|            |                       |                                              |
|            v                       v                                              |
|  +--------------------+  +--------------------+                                   |
|  | Attention Panel    |  | Document Inspector |                                   |
|  | (Failures/Triage)  |  | (/documents/:id)   |                                   |
|  +--------------------+  +--------------------+                                   |
+-----------------------------------------------------------------------------------+
| Design System Tokens & Components (WP-UI-02: Tailwind, Radix, Lucide, CSS Vars)   |
+-----------------------------------------------------------------------------------+
| Backend Service APIs (FastAPI: /v1/documents, /v1/jobs)                           |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Structure and Feature Isolation

Following the domain-driven feature folder architecture established in WP-UI-01, all core workspace capabilities are modularized under `web/src/features/`:

```
web/src/
├── app/
│   ├── page.tsx                           # Operational Overview Page
│   ├── documents/
│   │   ├── page.tsx                       # Document Library Page
│   │   └── [documentId]/
│   │       └── page.tsx                   # Document Inspection Page
│   └── processing/
│       └── page.tsx                       # Processing Monitor Page
├── features/
│   ├── workspace-overview/                # Operational Overview Domain
│   │   ├── types.ts                       # Overview data types
│   │   ├── api.ts                         # Overview aggregator service
│   │   └── components/
│   │       ├── metric-card.tsx            # KPI metric cards
│   │       ├── recent-documents.tsx       # Recent activity widget
│   │       ├── processing-summary.tsx     # Processing activity widget
│   │       └── attention-panel.tsx        # High-priority triage panel
│   ├── documents/                         # Document Domain
│   │   ├── types.ts                       # Document & Inspection schemas
│   │   ├── api.ts                         # Document REST service adapter
│   │   ├── upload-modal.tsx               # Backward compatibility wrapper
│   │   └── components/
│   │       ├── document-status.tsx        # Status badge component
│   │       ├── document-library.tsx       # Document table & toolbar
│   │       └── document-inspector.tsx     # Multi-tab deep inspector
│   ├── uploads/                           # Upload Experience Domain
│   │   ├── types.ts                       # Upload policy & item states
│   │   ├── upload-validation.ts           # Pure pre-flight validation rules
│   │   ├── api.ts                         # FormData multipart uploader
│   │   └── components/
│   │       ├── upload-dropzone.tsx        # Drag-and-drop dropzone
│   │       ├── upload-progress.tsx        # Accessible progress indicator
│   │       └── upload-dialog.tsx          # Complete modal dialog
│   └── processing/                        # Background Job Domain
│       ├── types.ts                       # Job & Pipeline Stage types
│       ├── api.ts                         # Job telemetry & retry service
│       └── components/
│           ├── processing-timeline.tsx    # Ordered stage list (<ol>)
│           └── processing-monitor.tsx     # Job table, filters & actions
```

---

## 3. Interaction Design & Data Flow

1. **Upload to Library**:
   - The user opens the upload modal from the Document Library or empty state.
   - Files are validated client-side against the upload policy before submission.
   - On submission, `POST /api/v1/documents/upload` registers the file.
   - The document library table automatically refreshes, displaying the new document in `queued` status.

2. **Ingestion to Processing Monitor**:
   - As backend background workers ingest and index the file, job events are published to `/api/v1/jobs`.
   - The Processing Monitor polls `/api/v1/jobs` to display stage progress, execution duration, and errors.
   - If a failure occurs, the user triggers `POST /api/v1/jobs/{job_id}/retry` directly from the UI.

3. **Inspection to Knowledge Downstream**:
   - Clicking a document navigates to `/documents/[documentId]`.
   - The Document Inspector loads chunks (`/api/v1/documents/{doc_id}/chunks`) and structured facts (`/api/v1/documents/{doc_id}/facts`).
   - The user triggers fact extraction on demand (`POST /api/v1/documents/{doc_id}/extract-facts`).
   - A direct link initiates a query in Ask AEGIS with `doc_id` pre-filtered (`/ask?doc_id=...`).
