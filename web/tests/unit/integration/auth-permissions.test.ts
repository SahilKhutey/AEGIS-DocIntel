import { describe, it, expect } from "vitest";
import {
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  getPermissionsForRole,
  ROLE_PERMISSION_MAP,
} from "@/lib/auth/permissions";
import { resolveSessionFromToken, defaultSessionProvider, validateSessionResponse } from "@/lib/auth/session";
import { checkRouteAccess } from "@/lib/auth/route-guard";

describe("Authentication, Roles & RBAC System", () => {
  it("maps viewer role to minimum necessary read-only permissions", () => {
    const perms = getPermissionsForRole("viewer");
    expect(perms).toContain("workspace.read");
    expect(perms).toContain("documents.read");
    expect(perms).toContain("intelligence.query");
    expect(perms).not.toContain("documents.upload");
    expect(perms).not.toContain("governance.review");
    expect(perms).not.toContain("developer.read");
  });

  it("maps reviewer role to governance review privileges", () => {
    expect(ROLE_PERMISSION_MAP.reviewer).toBeDefined();
    const perms = getPermissionsForRole("reviewer");
    expect(perms).toContain("governance.read");
    expect(perms).toContain("governance.review");
    expect(perms).toContain("governance.audit.read");
    expect(perms).not.toContain("developer.read");
  });

  it("provides defaultSessionProvider interface methods", async () => {
    const session = await defaultSessionProvider.getSession();
    expect(session).toBeDefined();
    await defaultSessionProvider.signOut();
  });

  it("maps admin to full workspace and engineering permissions", () => {
    const perms = getPermissionsForRole("admin");
    expect(perms).toContain("workspace.manage");
    expect(perms).toContain("developer.read");
    expect(perms).toContain("integrations.read");
    expect(perms).toContain("analytics.read");
  });

  it("correctly evaluates hasPermission, hasAnyPermission, hasAllPermissions", () => {
    const granted = ["documents.read", "intelligence.query"];
    expect(hasPermission(granted, "documents.read")).toBe(true);
    expect(hasPermission(granted, "documents.upload")).toBe(false);

    expect(hasAnyPermission(granted, ["documents.upload", "documents.read"])).toBe(true);
    expect(hasAnyPermission(granted, ["documents.upload", "workspace.manage"])).toBe(false);

    expect(hasAllPermissions(granted, ["documents.read", "intelligence.query"])).toBe(true);
    expect(hasAllPermissions(granted, ["documents.read", "documents.upload"])).toBe(false);
  });

  it("rejects development token unconditionally in production auth model", () => {
    const session = resolveSessionFromToken("dev-custom-tenant");
    expect(session).toBeNull();
  });

  it("validates trusted server session response correctly", () => {
    const serverPayload = {
      user_id: "user-eval-99",
      license_id: "lic-prod-alpha",
      device_id: "dev-key-hash",
      role: "viewer",
      tier: "pro_evaluation",
      authenticated: true,
    };
    const session = validateSessionResponse(serverPayload);
    expect(session).not.toBeNull();
    expect(session.user.id).toBe("user-eval-99");
    expect(session.tenantId).toBe("lic-prod-alpha");
    expect(session.role).toBe("viewer");
    expect(session.permissions).toContain("documents.read");
  });

  it("checks route access and blocks unauthenticated users from protected routes", () => {
    const res = checkRouteAccess("/documents", null);
    expect(res.allowed).toBe(false);
    expect(res.reason).toBe("UNAUTHENTICATED");
  });

  it("allows public routes without authentication", () => {
    const res = checkRouteAccess("/login", null);
    expect(res.allowed).toBe(true);
  });

  it("enforces RBAC route rules against user permissions", () => {
    const viewerSession = {
      user: { id: "viewer-1" },
      workspaceId: "ws-1",
      tenantId: "t-1",
      role: "viewer",
      permissions: getPermissionsForRole("viewer"),
    };

    // Viewer can access /documents
    expect(checkRouteAccess("/documents", viewerSession).allowed).toBe(true);

    // Viewer cannot access /developer
    const devAccess = checkRouteAccess("/developer", viewerSession);
    expect(devAccess.allowed).toBe(false);
    expect(devAccess.requiredPermission).toBe("developer.read");

    // Viewer cannot access /reviews
    const reviewAccess = checkRouteAccess("/reviews", viewerSession);
    expect(reviewAccess.allowed).toBe(false);
    expect(reviewAccess.requiredPermission).toBe("governance.read");
  });
});
