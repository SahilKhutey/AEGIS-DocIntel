# 11 — Route Register and Navigation

## 1. Route Register
The following routes are implemented and verified in the Next.js App Router:

| Route Path | Type | Component | Description |
| :--- | :--- | :--- | :--- |
| `/analytics` | Static (○) | `AnalyticsPage` | Operational analytics, token breakdown, and governance throughput |
| `/mathematics` | Static (○) | `MathematicsPage` | Mathematical representations, formulas, and evaluation playground |
| `/mathematics/[representationId]` | Dynamic (◐) | `RepresentationDetailPage` | Deep inspection of specific vector or matrix representations |
| `/pipelines` | Static (○) | `PipelinesPage` | Processing pipeline execution runs list and filtering |
| `/pipelines/[runId]` | Dynamic (◐) | `PipelineDetailPage` | DAG graph visualization, stage details, error logs, retry control |
| `/monitoring` | Static (○) | `MonitoringPage` | Service health dependencies, latency SLAs, alerts |
| `/developer` | Static (○) | `DeveloperPage` | Developer platform hub with API credentials manager |
| `/developer/api` | Static (○) | `DeveloperApiPage` | Interactive OpenAPI documentation and code snippets |
| `/developer/integrations` | Static (○) | `DeveloperIntegrationsPage` | External backing connectors status |
| `/developer/webhooks` | Static (○) | `DeveloperWebhooksPage` | SSRF-safe outbound webhook manager |

## 2. Global Shell Breadcrumb Integration
All routes integrate cleanly with the top-level persistent `AppShell` (`web/src/components/shell/app-shell.tsx`), dynamically deriving parent/child path hierarchies automatically from pathname segments.
