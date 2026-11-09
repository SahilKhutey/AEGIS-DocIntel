# 10 — Component Architecture

## 1. Directory Hierarchy
All WP-UI-07 components adhere to atomic domain boundaries under `web/src/`:

```
web/src/
├── components/
│   └── advanced/                 # Shared advanced UI primitives
│       ├── DataTable.tsx         # Sortable, paginated, accessible table
│       ├── EmptyMetricState.tsx  # Consistent telemetry empty state
│       ├── JsonViewer.tsx        # Syntax-highlighted payload viewer
│       ├── MetricCard.tsx        # KPI card with trends and formatters
│       ├── MetricTrend.tsx       # Up/Down/Neutral accessible badge
│       └── TimeRangeSelector.tsx # Segmented 24h/7d/30d/90d preset control
├── features/
│   ├── analytics/                # WP-UI-07.1 Analytics Feature
│   │   ├── api/analytics.api.ts
│   │   ├── components/
│   │   ├── hooks/useAnalytics.ts
│   │   ├── schemas/
│   │   └── types.ts
│   ├── mathematics/              # WP-UI-07.2 Mathematics Feature
│   │   ├── api/mathematics.api.ts
│   │   ├── components/
│   │   ├── schemas/
│   │   └── types.ts
│   ├── pipelines/                # WP-UI-07.3 Pipelines Feature
│   │   ├── api/pipeline.api.ts
│   │   ├── components/
│   │   ├── utils/validate-graph.ts
│   │   └── types.ts
│   ├── monitoring/               # WP-UI-07.4 Monitoring Feature
│   │   ├── api/monitoring.api.ts
│   │   ├── components/
│   │   └── types.ts
│   └── developer/                # WP-UI-07.5 Developer Feature
│       ├── api/developer.api.ts
│       ├── components/
│       ├── schemas/developer.schema.ts
│       └── types.ts
└── lib/advanced/                 # Pure utilities
    ├── export-data.ts            # OWASP-safe CSV serialization
    ├── format-metric.ts          # Safe metric formatting & delta math
    └── time-range.ts             # Preset window date math
```
