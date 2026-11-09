export const PERMISSIONS = [
  "workspace.read",
  "documents.read",
  "documents.upload",
  "documents.delete",
  "documents.compare",
  "processing.read",
  "intelligence.query",
  "evidence.read",
  "governance.read",
  "governance.review",
  "governance.audit.read",
  "users.manage",
  "workspace.settings.manage",
  "integrations.manage",
] as const;

export type Permission = (typeof PERMISSIONS)[number];

export const ROLES = [
  "workspace_user",
  "analyst",
  "reviewer",
  "administrator",
  "developer",
] as const;

export type ProductRole = (typeof ROLES)[number];

/**
 * Proposed product defaults.
 *
 * These are not backend authorization rules.
 * Map them to the actual API RBAC contract before enabling
 * permission-dependent operations in production.
 */
export const ROLE_PERMISSIONS: Record<ProductRole, Permission[]> = {
  workspace_user: [
    "workspace.read",
    "documents.read",
    "documents.upload",
    "intelligence.query",
    "evidence.read",
  ],
  analyst: [
    "workspace.read",
    "documents.read",
    "documents.upload",
    "documents.compare",
    "processing.read",
    "intelligence.query",
    "evidence.read",
    "governance.read",
  ],
  reviewer: [
    "workspace.read",
    "documents.read",
    "documents.compare",
    "processing.read",
    "intelligence.query",
    "evidence.read",
    "governance.read",
    "governance.review",
    "governance.audit.read",
  ],
  administrator: [
    "workspace.read",
    "documents.read",
    "documents.upload",
    "documents.delete",
    "documents.compare",
    "processing.read",
    "intelligence.query",
    "evidence.read",
    "governance.read",
    "governance.audit.read",
    "users.manage",
    "workspace.settings.manage",
    "integrations.manage",
  ],
  developer: [
    "workspace.read",
    "integrations.manage",
  ],
};

export function hasPermission(
  grantedPermissions: readonly Permission[],
  requiredPermission: Permission,
): boolean {
  return grantedPermissions.includes(requiredPermission);
}

export function hasAllPermissions(
  grantedPermissions: readonly Permission[],
  required: readonly Permission[],
): boolean {
  return required.every((permission) =>
    grantedPermissions.includes(permission),
  );
}

export function hasAnyPermission(
  grantedPermissions: readonly Permission[],
  required: readonly Permission[],
): boolean {
  return required.some((permission) =>
    grantedPermissions.includes(permission),
  );
}

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

export function canPerformGovernanceAction(
  permissions: readonly string[],
  requiredPermission: string,
): boolean {
  return permissions.includes(requiredPermission);
}

