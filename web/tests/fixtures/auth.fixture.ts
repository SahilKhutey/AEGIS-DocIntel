import { test as base, expect, Page } from "@playwright/test";
import { TEST_WORKSPACES } from "./test-data";

export interface AuthenticatedUser {
  id: string;
  email: string;
  displayName: string;
  role: "admin" | "analyst" | "reviewer" | "auditor";
  tenantId: string;
  activeWorkspaceId: string;
}

export const DEFAULT_TEST_USER: AuthenticatedUser = {
  id: "usr-sec-agent-01",
  email: "secops.lead@aegis-intel.internal",
  displayName: "Lead Security Auditor",
  role: "admin",
  tenantId: "tenant-aegis-corp",
  activeWorkspaceId: "ws-primary",
};

export const test = base.extend<{
  authenticatedPage: Page;
  testUser: AuthenticatedUser;
}>({
  testUser: async ({}, use) => {
    await use(DEFAULT_TEST_USER);
  },
  authenticatedPage: async ({ page, testUser }, use) => {
    // Inject deterministic session tokens and active workspace headers into localStorage
    await page.addInitScript(
      ({ user, workspaces }) => {
        window.localStorage.setItem("aegis_auth_session", JSON.stringify({
          token: "synth_bearer_token_verified_2026",
          user,
          expiresAt: Date.now() + 3600 * 1000,
        }));
        window.localStorage.setItem("aegis_active_workspace", user.activeWorkspaceId);
        window.localStorage.setItem("aegis_workspaces", JSON.stringify(workspaces));
      },
      { user: testUser, workspaces: TEST_WORKSPACES }
    );

    await use(page);
  },
});

export { expect };
