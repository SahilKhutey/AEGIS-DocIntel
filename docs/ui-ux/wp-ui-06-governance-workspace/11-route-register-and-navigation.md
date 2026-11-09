# 11 — Route Register and Navigation

## 1. Route Register

| Path | Name | Component | Access Permission | Status |
| :--- | :--- | :--- | :--- | :--- |
| `/reviews` | Review Queue | `app/reviews/page.tsx` | `governance.read` | Operational |
| `/reviews/[reviewId]` | Review Workspace | `app/reviews/[reviewId]/page.tsx` | `governance.review` | Operational |
| `/reviews/[reviewId]/verification` | Fact Verification | `app/reviews/[reviewId]/verification/page.tsx` | `governance.review` | Operational |
| `/reviews/[reviewId]/conflicts` | Conflict Resolution | `app/reviews/[reviewId]/conflicts/page.tsx` | `governance.review` | Operational |
| `/reviews/[reviewId]/decisions` | Decisions Workspace | `app/reviews/[reviewId]/decisions/page.tsx` | `governance.review` | Operational |
| `/reviews/[reviewId]/history` | Audit History | `app/reviews/[reviewId]/history/page.tsx` | `governance.audit.read` | Operational |
| `/governance/audit` | Global Audit Log | `app/governance/audit/page.tsx` | `governance.audit.read` | Operational |

---

## 2. Navigation Shell Integration

In accordance with WP-UI-01 and WP-UI-03:
- The persistent application shell highlights the `Review Queue` sidebar link when matching `/reviews`.
- Top header breadcrumbs dynamically reflect the hierarchy:
  `Review Queue / [Candidate Identifier] / [Active View]`
- Direct deep links are fully supported for bookmarking or sharing audit evidence across teams.
