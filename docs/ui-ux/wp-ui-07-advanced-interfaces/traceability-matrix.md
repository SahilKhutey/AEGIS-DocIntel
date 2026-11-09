# WP-UI-07 Traceability Matrix

| Requirement ID | Description | Source File / Implementation | Unit Test Verification | Playwright E2E Spec |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-ADV-01** | Operational KPIs & Stats | `features/analytics/components/OverviewMetrics.tsx` | `tests/unit/advanced/analytics.test.tsx` | `tests/e2e/advanced/analytics.spec.ts` |
| **REQ-ADV-02** | Time-range selector & date math | `components/advanced/TimeRangeSelector.tsx`<br>`lib/advanced/time-range.ts` | `tests/unit/advanced/time-range.test.ts` | `tests/e2e/advanced/analytics.spec.ts` |
| **REQ-ADV-03** | Formula injection safe CSV export | `lib/advanced/export-data.ts` (`toCsv`) | `tests/unit/advanced/export-data.test.ts` | `tests/e2e/advanced/analytics.spec.ts` |
| **REQ-ADV-04** | High-dim Vector viewer (heatmap/table) | `features/mathematics/components/VectorViewer.tsx` | `tests/unit/advanced/vector-viewer.test.tsx` | `tests/e2e/advanced/mathematics.spec.ts` |
| **REQ-ADV-05** | Kernel Matrix viewer & cell select | `features/mathematics/components/MatrixViewer.tsx` | `tests/unit/advanced/matrix-viewer.test.tsx` | `tests/e2e/advanced/mathematics.spec.ts` |
| **REQ-ADV-06** | LaTeX Equation catalog & variables | `features/mathematics/components/EquationRenderer.tsx` | `tests/unit/advanced/equation-renderer.test.tsx` | `tests/e2e/advanced/mathematics.spec.ts` |
| **REQ-ADV-07** | Transformation derivation trace | `features/mathematics/components/TransformationTrace.tsx` | Included in Mathematics suites | `tests/e2e/advanced/mathematics.spec.ts` |
| **REQ-ADV-08** | Pipeline runs list & status filters | `features/pipelines/components/PipelineList.tsx` | `tests/unit/advanced/data-table.test.tsx` | `tests/e2e/advanced/pipelines.spec.ts` |
| **REQ-ADV-09** | DAG graph lifecycle visualization | `features/pipelines/components/PipelineGraph.tsx` | `tests/unit/advanced/pipeline-stage.test.tsx` | `tests/e2e/advanced/pipelines.spec.ts` |
| **REQ-ADV-10** | DAG cycle detection & sorting | `features/pipelines/utils/validate-graph.ts` | `tests/unit/advanced/validate-graph.test.ts` | `tests/e2e/advanced/pipelines.spec.ts` |
| **REQ-ADV-11** | Failure diagnostics & run retry | `features/pipelines/components/PipelineDetail.tsx` | `tests/unit/advanced/pipeline-stage.test.tsx` | `tests/e2e/advanced/pipelines.spec.ts` |
| **REQ-ADV-12** | Infrastructure service health cards | `features/monitoring/components/ServiceHealthList.tsx` | `tests/unit/advanced/service-health.test.tsx` | `tests/e2e/advanced/monitoring.spec.ts` |
| **REQ-ADV-13** | Latency percentiles (P50/P90/P95/P99) | `features/monitoring/components/LatencyPercentiles.tsx` | `tests/unit/advanced/service-health.test.tsx` | `tests/e2e/advanced/monitoring.spec.ts` |
| **REQ-ADV-14** | Throughput RPM & concurrency | `features/monitoring/components/ThroughputChart.tsx` | `tests/unit/advanced/service-health.test.tsx` | `tests/e2e/advanced/monitoring.spec.ts` |
| **REQ-ADV-15** | Freshness badge & telemetry reload | `features/monitoring/components/FreshnessBadge.tsx` | Included in monitoring suites | `tests/e2e/advanced/monitoring.spec.ts` |
| **REQ-ADV-16** | OpenAPI schema REST explorer | `features/developer/components/ApiExplorer.tsx` | `tests/unit/advanced/developer.test.tsx` | `tests/e2e/advanced/developer.spec.ts` |
| **REQ-ADV-17** | Multi-language code snippet generator | `features/developer/components/ApiExplorer.tsx` | `tests/unit/advanced/developer.test.tsx` | `tests/e2e/advanced/developer.spec.ts` |
| **REQ-ADV-18** | API Key generation & one-time secret | `features/developer/components/ApiCredentialManager.tsx` | `tests/unit/advanced/developer.test.tsx` | `tests/e2e/advanced/developer.spec.ts` |
| **REQ-ADV-19** | SSRF-safe webhook registration | `features/developer/components/WebhookManager.tsx` | `tests/unit/advanced/developer.test.tsx` | `tests/e2e/advanced/developer.spec.ts` |
| **REQ-ADV-20** | External backing connectors status | `features/developer/components/IntegrationStatusCard.tsx` | Included in developer suites | `tests/e2e/advanced/developer.spec.ts` |
