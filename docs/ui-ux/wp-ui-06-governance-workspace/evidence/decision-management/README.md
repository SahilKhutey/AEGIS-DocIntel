# Evidence: Decision Management & Concurrency Control

## Verification Summary
- **Route**: `/reviews/[reviewId]/decisions` & `/reviews/[reviewId]` tab
- **Component**: `DecisionPanel.tsx`
- **Pass Criteria**:
  - Provides formal actions: `approve`, `correct`, `reject`, `request_evidence`.
  - Claim button visible and operational when item is `pending` or `needs_evidence`.
  - Correction mode requires corrected value, type, optional unit, and evidence quote.
  - Mandatory rationale enforced (min 3 chars).
  - Mandatory compliance certification checkbox guard.
  - Generates unique `Idempotency-Key` header on submission.
  - Stale version conflict (HTTP 409) detected and surfaces warning banner with "Reload Latest" button.
  - Administrative reopen requires administrator authority and audited rationale (min 5 chars).

## Automated Test Results
- Vitest: `tests/unit/governance/decision-panel.test.tsx` (2 tests passed).
- Playwright: `tests/e2e/governance/decision-management.spec.ts` (1 test passed).
