# Evidence: Fact Verification

## Verification Summary
- **Route**: `/reviews/[reviewId]/verification` & `/reviews/[reviewId]` tab
- **Component**: `FactVerificationPanel.tsx`
- **Pass Criteria**:
  - Extracted statement displays subject, attribute, inferred value, and source document metadata.
  - Cited evidence passage shows exact quote and allows entering verified excerpt.
  - Reviewer can select from standardized outcomes (`verified`, `partially_verified`, `not_verified`, `contradicted`, `insufficient_evidence`).
  - Mandatory rationale enforced (min 3 chars).
  - Partially verified outcome prompts for human-corrected value.
  - Verification outcome maps to recommended decision action.

## Automated Test Results
- Vitest: `tests/unit/governance/fact-verification.test.tsx` (2 tests passed).
- Playwright: `tests/e2e/governance/fact-verification.spec.ts` (1 test passed).
