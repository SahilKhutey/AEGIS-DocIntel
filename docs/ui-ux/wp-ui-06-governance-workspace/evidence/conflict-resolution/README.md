# Evidence: Conflict Resolution

## Verification Summary
- **Route**: `/reviews/[reviewId]/conflicts` & `/reviews/[reviewId]` tab
- **Component**: `ConflictResolutionPanel.tsx`
- **Pass Criteria**:
  - Displays contradictory claims from Source A and Source B side-by-side.
  - Reviewer can inspect document IDs, asserted values, and source quotes.
  - Reviewer can select from resolution outcomes (`accepted_first_fact`, `accepted_second_fact`, `both_valid`, `insufficient_evidence`, `escalated`).
  - Mandatory rationale enforced (min 5 chars).
  - Prompts for reconciled value when `both_valid` is selected.
  - Commits formal governance decision payload to `/api/v1/reviews/{id}/decisions`.

## Automated Test Results
- Vitest: `tests/unit/governance/conflict-resolution.test.tsx` (2 tests passed).
- Playwright: `tests/e2e/governance/conflict-resolution.spec.ts` (1 test passed).
