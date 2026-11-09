import { SHELL_NAVIGATION } from "@/config/shell";

export function getVisibleNavigation(permissions: readonly string[]) {
  const granted = new Set(permissions);

  return SHELL_NAVIGATION.map((group) => ({
    ...group,
    items: group.items.filter((item) => {
      if (item.status !== "active") return false;

      return item.requiredPermissions.every((permission) =>
        granted.has(permission)
      );
    }),
  })).filter((group) => group.items.length > 0);
}
