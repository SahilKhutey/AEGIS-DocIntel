# 10 — Component Architecture

## 1. Directory Structure

```
web/src/features/governance/
├── api/
│   ├── review.api.ts
│   ├── decision.api.ts
│   ├── verification.api.ts
│   ├── conflict.api.ts
│   └── audit.api.ts
├── components/
│   ├── ReviewQueue.tsx
│   ├── ReviewQueueFilters.tsx
│   ├── GovernanceMetricsBanner.tsx
│   ├── FactVerificationPanel.tsx
│   ├── ConflictResolutionPanel.tsx
│   ├── DecisionPanel.tsx
│   ├── AuditTimeline.tsx
│   ├── QualityFeedbackForm.tsx
│   └── index.ts
├── hooks/
│   ├── useGovernance.ts
│   └── index.ts
├── schemas/
│   ├── review.schema.ts
│   ├── verification.schema.ts
│   ├── conflict.schema.ts
│   ├── decision.schema.ts
│   └── audit.schema.ts
├── types/
│   └── index.ts
└── utils/
    ├── decision-transitions.ts
    ├── review-status.ts
    ├── verification-utils.ts
    ├── conflict-utils.ts
    └── audit-utils.ts
```

---

## 2. Component Hierarchy and Data Flow

```mermaid
graph TD
    PageReviews[/reviews Page] --> GMB[GovernanceMetricsBanner]
    PageReviews --> RQF[ReviewQueueFilters]
    PageReviews --> RQ[ReviewQueue Table]
    RQ --> LinkDetail[/reviews/[reviewId]]

    PageDetail[/reviews/[reviewId] Page] --> Breadcrumb[Breadcrumb & Status Badge]
    PageDetail --> OverviewCard[Overview & Comparison Cards]
    PageDetail --> Tabs[Navigation Tab Bar]
    Tabs --> FVP[FactVerificationPanel]
    Tabs --> CRP[ConflictResolutionPanel]
    Tabs --> DP[DecisionPanel]
    Tabs --> AT[AuditTimeline]
    Tabs --> QFF[QualityFeedbackForm]

    FVP --> APIVerif[verification.api -> decision.api]
    CRP --> APIConflict[conflict.api -> decision.api]
    DP --> APIDecision[decision.api]
    AT --> APIAudit[audit.api]
```

---

## 3. Hook Contracts

### `useGovernanceQueue()`
- Manages queue state, filter tab selection, candidate type filtering, and metrics.
- Exposes: `{ reviews, allReviews, metrics, loading, error, filters, setFilters, reload }`.

### `useGovernanceDetail(reviewId)`
- Manages review item data, version tracking, audit history, claiming, decision commits, and stale detection.
- Exposes: `{ item, history, loading, submitting, error, staleWarning, successMessage, reload, claim, submitDecision, reopen, sendFeedback }`.
