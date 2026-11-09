import { NAVIGATION } from "@/config/navigation";
import type { Permission } from "@/config/permissions";

export function getVisibleNavigation(
  permissions: readonly Permission[],
) {
  return NAVIGATION.map((group) => ({
    ...group,
    items: group.items.filter((item) => {
      if (item.status !== "active") return false;
      return item.requiredPermissions.every((permission) =>
        permissions.includes(permission),
      );
    }),
  })).filter((group) => group.items.length > 0);
}
