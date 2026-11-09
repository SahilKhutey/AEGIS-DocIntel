import { describe, expect, it } from "vitest";
import {
  ROLE_PERMISSIONS,
  hasPermission,
  hasAllPermissions,
  hasAnyPermission,
} from "@/config/permissions";

describe("AEGIS permission architecture", () => {
  it("grants workspace read to all proposed personas", () => {
    for (const permissions of Object.values(ROLE_PERMISSIONS)) {
      expect(
        hasPermission(permissions, "workspace.read"),
      ).toBe(true);
    }
  });

  it("does not grant governance review to a basic user", () => {
    expect(
      hasPermission(
        ROLE_PERMISSIONS.workspace_user,
        "governance.review",
      ),
    ).toBe(false);
  });

  it("grants governance review to reviewer", () => {
    expect(
      hasPermission(
        ROLE_PERMISSIONS.reviewer,
        "governance.review",
      ),
    ).toBe(true);
  });

  it("does not grant user management to analyst", () => {
    expect(
      hasPermission(
        ROLE_PERMISSIONS.analyst,
        "users.manage",
      ),
    ).toBe(false);
  });

  it("checks all required permissions", () => {
    expect(
      hasAllPermissions(
        ROLE_PERMISSIONS.analyst,
        ["documents.read", "intelligence.query"],
      ),
    ).toBe(true);
  });

  it("rejects when one required permission is missing", () => {
    expect(
      hasAllPermissions(
        ROLE_PERMISSIONS.workspace_user,
        ["documents.read", "governance.review"],
      ),
    ).toBe(false);
  });

  it("checks any required permission", () => {
    expect(
      hasAnyPermission(
        ROLE_PERMISSIONS.workspace_user,
        ["governance.review", "documents.read"],
      ),
    ).toBe(true);
  });
});
