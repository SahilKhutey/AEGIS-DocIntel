import { Permission, hasPermission } from "./permissions";
import { UserSession } from "./session";

export interface RouteAccessRule {
  pathPrefix: string;
  requiredPermission?: Permission;
  minRole?: string;
}

export const ROUTE_ACCESS_RULES: RouteAccessRule[] = [
  { pathPrefix: "/documents", requiredPermission: "documents.read" },
  { pathPrefix: "/processing", requiredPermission: "processing.read" },
  { pathPrefix: "/ask", requiredPermission: "intelligence.query" },
  { pathPrefix: "/compare", requiredPermission: "documents.compare" },
  { pathPrefix: "/reviews", requiredPermission: "governance.read" },
  { pathPrefix: "/analytics", requiredPermission: "analytics.read" },
  { pathPrefix: "/mathematics", requiredPermission: "representations.read" },
  { pathPrefix: "/pipelines", requiredPermission: "pipelines.read" },
  { pathPrefix: "/monitoring", requiredPermission: "monitoring.read" },
  { pathPrefix: "/developer", requiredPermission: "developer.read" },
];

export interface RouteCheckResult {
  allowed: boolean;
  requiredPermission?: Permission;
  reason?: string;
}

export function checkRouteAccess(
  pathname: string,
  session: UserSession | null
): RouteCheckResult {
  // Public routes (if any)
  if (pathname === "/login" || pathname === "/sign-in") {
    return { allowed: true };
  }

  // If no session exists
  if (!session) {
    return {
      allowed: false,
      reason: "UNAUTHENTICATED",
    };
  }

  // Find matching rule
  const matchedRule = ROUTE_ACCESS_RULES.find((rule) =>
    pathname.startsWith(rule.pathPrefix)
  );

  if (!matchedRule || !matchedRule.requiredPermission) {
    return { allowed: true };
  }

  const isGranted = hasPermission(
    session.permissions,
    matchedRule.requiredPermission
  );

  if (!isGranted) {
    return {
      allowed: false,
      requiredPermission: matchedRule.requiredPermission,
      reason: "FORBIDDEN",
    };
  }

  return { allowed: true };
}
