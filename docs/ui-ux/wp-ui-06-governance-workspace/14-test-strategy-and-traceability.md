# 14 — Test Strategy and Traceability

## 1. Test Architecture

The verification suite for WP-UI-06 spans unit, component contract, state transition, and end-to-end browser tests.

```
Test Pyramid:
▲ E2E Playwright Tests (8 specs in e2e/governance/ + 53 core workbench specs)
├── Component & Hook Unit Tests (7 test suites, 21 tests in tests/unit/governance/)
└── Foundation Unit Tests (118 existing unit tests across workspace)
Total: 139 Vitest unit tests (100% pass) + 61 Playwright E2E tests (100% pass)
```

---

## 2. Vitest Unit Test Suites

1. `tests/unit/governance/decision-transitions.test.ts` (4 tests):
   - Terminal vs non-terminal state validation.
   - Transition permission mapping.
   - Action target state mapping.
2. `tests/unit/governance/review-status.test.ts` (4 tests):
   - Badge configs for all statuses.
   - Unknown status fallback.
   - Confidence-based priority calculation.
3. `tests/unit/governance/review-queue.test.tsx` (4 tests):
   - Review row rendering, attributes, and statuses.
   - Loading and empty state presentation.
   - Filter tab selection callbacks.
4. `tests/unit/governance/fact-verification.test.tsx` (2 tests):
   - Fact statement and evidence quote rendering.
   - Verification outcome selection and rationale submission.
5. `tests/unit/governance/conflict-resolution.test.tsx` (2 tests):
   - Side-by-side comparative card rendering.
   - Conflict resolution outcome selection and rationale.
6. `tests/unit/governance/decision-panel.test.tsx` (2 tests):
   - Action selection, rationale enforcement, and compliance checkbox guard.
   - Claim button rendering when pending.
7. `tests/unit/governance/audit-timeline.test.tsx` (3 tests):
   - Sequence rendering, actor ID attribution, and status diffs.
   - Ascending vs descending chronological sort toggle.
   - Empty state presentation.

---

## 3. Playwright E2E Test Suites

1. `web/tests/e2e/governance/review-queue.spec.ts` (3 tests):
   - Full queue page rendering with header, metrics, and candidate rows.
   - Status tab and candidate type filtering.
   - Real-time search query filtering.
2. `web/tests/e2e/governance/fact-verification.spec.ts` (1 test):
   - Fact inspection, selecting Fully Verified, entering rationale, and committing decision.
3. `web/tests/e2e/governance/conflict-resolution.spec.ts` (1 test):
   - Inspecting conflicting claims from Source A and Source B, selecting Accept Fact 2, and submitting resolution.
4. `web/tests/e2e/governance/decision-management.spec.ts` (1 test):
   - Submitting an Approve decision, verifying rationale requirement, and certifying compliance.
5. `web/tests/e2e/governance/audit-history.spec.ts` (2 tests):
   - Review detail audit trail tab verification.
   - Global `/governance/audit` log page rendering and filtering.
6. Zero regression on all existing core specs:
   - `workbench.spec.ts` (including line 433 review queue check).
   - `navigation.spec.ts`
   - `user-journeys.spec.ts`
