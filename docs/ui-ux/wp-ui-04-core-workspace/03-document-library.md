# 03 — Document Library

## 1. Document Registry Specification

The Document Library (`/documents`) provides the primary management catalog for all source documents uploaded to the active workspace. It gives operators, analysts, and governance officers full visibility into document states, metadata, and ingestion health.

---

## 2. Interface Anatomy & Features

```
+-----------------------------------------------------------------------------------------+
| Documents / Document Workspace & Library                                                |
| Ingest, inspect, explore documents and track indexing pipelines.                        |
+-----------------------------------------------------------------------------------------+
| [ Search documents by filename...      ] [ Status Filter: All | Comp | Proc | Que | Fail ] |
|                                                               [ Refresh ] [ Upload Doc] |
+-----------------------------------------------------------------------------------------+
| Document                 | Type  | Size    | Status    | Page / Chunks | Ingested | Act |
|--------------------------+-------+---------+-----------+---------------+----------+-----|
| acme_q3_report.pdf       | PDF   | 4.2 MB  | Completed | 12 / 45       | 2h ago   | ... |
| security_policy_v2.docx  | DOCX  | 1.8 MB  | Processing| 8 / 24        | 10m ago  | ... |
| vendor_agreement.pdf     | PDF   | 2.1 MB  | Failed    | 5 / 0         | 1d ago   | ... |
+-----------------------------------------------------------------------------------------+
| Pagination: Showing 1-3 of 3 documents                                                  |
+-----------------------------------------------------------------------------------------+
```

### 2.1 Filter & Search Engine
- **Search Query Filtering**: Client-side and server-side search input matching against `filename` and `doc_id`.
- **Status Filter Toolbar**: Single-selection filter group with options:
  - `All`: Complete document list without lifecycle restrictions.
  - `Completed`: Only documents with backend status `ready` (`DocumentStatus = completed`).
  - `Processing`: Documents currently in `indexing` or `reindexing` stages.
  - `Queued`: Documents in `pending` or `uploaded` states waiting for worker pickup.
  - `Failed`: Documents that failed during validation, extraction, or indexing.
- **Refresh Control**: One-click refresh button with animated spinner that refetches data without a full page reload.

### 2.2 Table Semantics & Accessibility
- **Semantic HTML**: Built using `<table aria-label="Documents list">`, with standard `<thead>`, `<th scope="col">`, `<tbody>`, and `<tr>`.
- **Accessible Status Indicators**: Every document row includes a `DocumentStatusBadge` styled according to design tokens:
  - Completed: `variant="success"`, `aria-label="Document status: Completed"`.
  - Processing: `variant="info"`, `aria-label="Document status: Processing"`.
  - Failed: `variant="danger"`, `aria-label="Document status: Failed"`.
  - Queued: `variant="warning"`, `aria-label="Document status: Queued"`.
  - Never relies on color alone; text labels and distinct iconography are always present.

### 2.3 Empty States and Error Recovery
- **Empty Library State**: When no documents match the search or status filter, an informative empty state displays an icon, clear explanation, and a direct `Select File to Ingest` action button.
- **Error Banner**: When backend connectivity fails, a non-intrusive alert banner notifies the user and provides a `Retry` trigger.
