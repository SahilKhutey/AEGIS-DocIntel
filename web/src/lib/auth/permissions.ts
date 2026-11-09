/**
 * Unified Permissions & Role Reconciliation for AEGIS-DocIntel
 * Maps frontend capability checks to canonical backend roles.
 */

export const PERMISSIONS = [
  "workspace.read",
  "workspace.manage",
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
  "analytics.read",
  "representations.read",
  "pipelines.read",
  "monitoring.read",
  "developer.read",
  "integrations.read",
] as const;

export type Permission = (typeof PERMISSIONS)[number];

export const BACKEND_ROLES = [
  "viewer",
  "editor",
  "reviewer",
  "review_admin",
  "tenant_admin",
  "platform_admin",
  "admin",
] as const;

export type BackendRole = (typeof BACKEND_ROLES)[number];

/**
 * Canonical mapping from backend role to granted permissions.
 * Matches policies in src/core/security_context.py and src/api/auth.py
 */
export const ROLE_PERMISSION_MAP: Record<BackendRole, readonly Permission[]> = {
  viewer: [
    "workspace.read",
    "documents.read",
    "intelligence.query",
    "evidence.read",
  ],
  editor: [
    "workspace.read",
    "documents.read",
    "documents.upload",
    "documents.compare",
    "processing.read",
    "intelligence.query",
    "evidence.read",
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
  review_admin: [
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
  tenant_admin: [
    "workspace.read",
    "workspace.manage",
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
    "analytics.read",
    "representations.read",
    "pipelines.read",
    "monitoring.read",
  ],
  platform_admin: [
    "workspace.read",
    "workspace.manage",
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
    "analytics.read",
    "representations.read",
    "pipelines.read",
    "monitoring.read",
    "developer.read",
    "integrations.read",
  ],
  admin: [
    "workspace.read",
    "workspace.manage",
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
    "analytics.read",
    "representations.read",
    "pipelines.read",
    "monitoring.read",
    "developer.read",
    "integrations.read",
  ],
};

export function hasPermission(
  granted: readonly string[],
  required: Permission
): boolean {
  return granted.includes(required);
}

export function hasAnyPermission(
  granted: readonly string[],
  required: readonly Permission[]
): boolean {
  return required.some((perm) => granted.includes(perm));
}

export function hasAllPermissions(
  granted: readonly string[],
  required: readonly Permission[]
): boolean {
  return required.every((perm) => granted.includes(perm));
}

export function getPermissionsForRole(role: string): Permission[] {
  if (role in ROLE_PERMISSION_MAP) {
    return [...ROLE_PERMISSION_MAP[role as BackendRole]];
  }
  return [...ROLE_PERMISSION_MAP.viewer];
}
