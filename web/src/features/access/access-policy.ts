import type { Permission } from "@/config/permissions";
import {
  hasAllPermissions,
  hasAnyPermission,
} from "@/config/permissions";

export type AccessDecision =
  | { allowed: true }
  | { allowed: false; reason: "missing_permission" | "not_authenticated" };

export type AccessContext = {
  isAuthenticated: boolean;
  permissions: readonly Permission[];
};

export function canAccess(
  context: AccessContext,
  required: readonly Permission[],
  mode: "all" | "any" = "all",
): AccessDecision {
  if (!context.isAuthenticated) {
    return {
      allowed: false,
      reason: "not_authenticated",
    };
  }

  const allowed =
    mode === "all"
      ? hasAllPermissions(context.permissions, required)
      : hasAnyPermission(context.permissions, required);

  return allowed
    ? { allowed: true }
    : {
        allowed: false,
        reason: "missing_permission",
      };
}
