import type { RouteDefinition } from "@/config/routes";
import { ROUTES } from "@/config/routes";

export function matchesRoute(
  pathname: string,
  route: RouteDefinition,
): boolean {
  const pattern = route.path
    .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\\\[([^\]]+)\\\]/g, "[^/]+");

  return new RegExp(`^${pattern}/?$`).test(pathname);
}

const ROUTE_MATCH_ORDER = [...ROUTES].sort(
  (a, b) => b.path.length - a.path.length,
);

export function findRoute(pathname: string) {
  return ROUTE_MATCH_ORDER
    .find((route) => matchesRoute(pathname, route));
}
