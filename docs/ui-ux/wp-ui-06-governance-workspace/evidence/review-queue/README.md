# Evidence: Review Queue & Metrics

## Verification Summary
- **Route**: `/reviews`
- **Component**: `ReviewQueue.tsx`, `ReviewQueueFilters.tsx`, `GovernanceMetricsBanner.tsx`
- **Pass Criteria**:
  - Main heading matches `/human governance review queue/i`.
  - Candidate identifier `revenue_q3_2026` renders and is navigable.
  - Metrics banner accurately displays Total Queue, Approval Rate, Correction Rate, Rejection Rate.
  - Status tabs (`all`, `pending`, `in_review`, `approved`, etc.) filter items in real time.
  - Search input filters items by candidate attribute or document ID.

## Automated Test Results
- Vitest: `tests/unit/governance/review-queue.test.tsx` (4 tests passed).
- Playwright: `tests/e2e/governance/review-queue.spec.ts` (3 tests passed).
- Regression: `tests/e2e/workbench.spec.ts:433` (passed).
