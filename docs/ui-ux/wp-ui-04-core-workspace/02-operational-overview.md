# 02 — Operational Overview

## 1. Overview Philosophy: Zero Fictional Endpoints

In accordance with the foundational engineering rules established in WP-UI-01, the AEGIS frontend never invents fictional backend endpoints (such as `/dashboard/metrics` or `/workspace/summary`). Instead, the Operational Overview module (`features/workspace-overview`) aggregates authentic runtime data concurrently from the two verified FastAPI service routers:
- `GET /api/v1/documents` (`DocumentListSchema`)
- `GET /api/v1/jobs` (`JobListSchema`)

```
               +--------------------------------------+
               |    fetchWorkspaceOverview()          |
               +--------------------------------------+
                   /                              \
                  /                                \
  Promise.allSettled                               Promise.allSettled
                /                                    \
               v                                      v
    GET /api/v1/documents                      GET /api/v1/jobs
  (items, total, statuses)                 (items, errors, attempts)
               \                                      /
                \                                    /
                 v                                  v
  +-------------------------------------------------------------+
  | Metrics Calculation:                                        |
  |  - totalDocuments = docs.total || docs.items.length         |
  |  - processingDocuments = docs[status == 'processing'].count |
  |  - completedDocuments  = docs[status == 'completed'].count  |
  |  - failedDocuments     = docs[status == 'failed'].count     |
  |  - queuedDocuments     = docs[status == 'queued'].count     |
  |  - activeJobs          = jobs[status in ('running', ...)]   |
  |  - attentionItems      = failedDocs + failedJobs            |
  +-------------------------------------------------------------+
```

---

## 2. Dashboard Widgets & Anatomy

### 2.1 Workspace Operational State (Metric Cards)
Five responsive KPI cards display tabular-num values with accessible semantic icons and variant styling:
- **Total Documents**: Total documents registered in the active workspace. Direct link to `/documents`.
- **Processing**: Ingestions currently progressing through the indexing pipeline. Direct link to `/processing`.
- **Completed**: Ingestion and indexing successfully finished; document is queryable and ready for citation. Direct link to `/documents`.
- **Needs Attention**: Total failed documents and failed background jobs. Displays danger variant if count > 0; default variant when zero.
- **Queued**: Documents uploaded and awaiting background worker lease. Direct link to `/documents`.

### 2.2 Attention Panel (`AttentionPanel`)
The attention panel acts as a triage inbox:
- **Zero Errors State**: Displays an accessible, calming green status alert indicating all systems are operating normally.
- **Active Failures State**: Lists up to 5 items requiring immediate operator intervention:
  - Document indexing failures with direct links to the document inspector.
  - Job execution failures with the error reason and direct links to the processing monitor to retry.

### 2.3 Activity Feeds
Two side-by-side feeds keep operators informed:
- **Recent Documents (`RecentDocuments`)**: Displays the 4 latest documents, formatted MIME badges, size in megabytes, relative upload timestamps, and direct inspection links.
- **Processing Summary (`ProcessingSummary`)**: Displays the 4 latest jobs, stage progress percentages, status badges, and a direct link to the Processing Monitor.

### 2.4 Workbench Capability Entry Cards
Four persistent entry cards ensure analysts can transition seamlessly to analytical workflows:
- **Document Workspace** (`/documents`)
- **Ask & Evidence Explorer** (`/ask`)
- **Intelligence & Compare** (`/compare`)
- **Human Review & Audit** (`/reviews`)
