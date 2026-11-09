# Evidence: Audit History & Evaluation Loop

## Verification Summary
- **Route**: `/reviews/[reviewId]/history` & `/governance/audit`
- **Component**: `AuditTimeline.tsx`, `QualityFeedbackForm.tsx`, `app/governance/audit/page.tsx`
- **Pass Criteria**:
  - Displays ordered, tamper-evident sequence of historical transitions.
  - Formats actor ID, timestamp, action pills, status transitions, version diffs, and rationale.
  - Supports sorting by newest first (descending) and oldest first (ascending).
  - Global `/governance/audit` aggregates audit records across workspace reviews with search and action filters.
  - Quality feedback form records evaluation diagnostics (`/api/v1/reviews/{id}/feedback`).

## Automated Test Results
- Vitest: `tests/unit/governance/audit-timeline.test.tsx` (3 tests passed).
- Playwright: `tests/e2e/governance/audit-history.spec.ts` (2 tests passed).
