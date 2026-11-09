# Evidence: Security, Authorization & Separation of Duties

## Verification Summary
- **Configuration**: `web/src/config/permissions.ts`
- **Pass Criteria**:
  - `GOVERNANCE_PERMISSIONS` and `canPerformGovernanceAction` defined.
  - Review actions enforce separation of duties per `src/engines/governance/policy.py`.
  - Claim requires `reviewer` or `admin` role.
  - Decision submission requires assigned reviewer or admin.
  - Administrative reopen strictly restricted to administrators.
  - Multi-tenant boundary isolation enforced on all review queries.

## Automated Test Results
- Vitest: `tests/unit/permissions.test.ts` (7 tests passed).
- Vitest: `tests/unit/governance/decision-transitions.test.ts` (4 tests passed).
