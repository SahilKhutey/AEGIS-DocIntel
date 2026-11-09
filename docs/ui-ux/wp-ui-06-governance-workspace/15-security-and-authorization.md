# 15 — Security and Authorization

## 1. Multi-Tenant Isolation

All governance resources are strictly bound to tenant context:
- Backend review items are retrieved using compound keys `(tenant_id, review_id)`.
- Client requests validate that the active workspace matches the review item's `tenant_id`.
- Cross-tenant data leakage is structurally impossible.

---

## 2. Role-Based Access Control (RBAC)

The frontend reflects permissions defined in `web/src/config/permissions.ts`:

```typescript
export const GOVERNANCE_PERMISSIONS = {
  REVIEW_READ: "governance.read",
  REVIEW_CREATE: "governance.review.create",
  REVIEW_ASSIGN: "governance.review.assign",
  FACT_READ: "governance.fact.read",
  FACT_VERIFY: "governance.fact.verify",
  CONFLICT_READ: "governance.conflict.read",
  CONFLICT_RESOLVE: "governance.conflict.resolve",
  CONFLICT_ESCALATE: "governance.conflict.escalate",
  DECISION_READ: "governance.decision.read",
  DECISION_SUBMIT: "governance.decision.submit",
  DECISION_APPROVE: "governance.decision.approve",
  AUDIT_READ: "governance.audit.read",
} as const;
```

### Role Mapping
- **`workspace_user`**: Read-only document access; no governance review privileges.
- **`analyst`**: Can read review items and inspect evidence citations (`governance.read`).
- **`reviewer`**: Can claim items, perform fact verification, resolve conflicts, and commit formal decisions (`governance.review`, `governance.audit.read`).
- **`administrator`**: All reviewer permissions plus administrative reopen capability for completed items.

---

## 3. Separation of Reviewer Duties

Per `src/engines/governance/policy.py`:
- Only the **assigned reviewer** or an authorized **administrator** can submit decisions on an item once claimed (`is_assigned_reviewer or is_admin`).
- Unassigned reviewers cannot commit decisions on items claimed by peers.
