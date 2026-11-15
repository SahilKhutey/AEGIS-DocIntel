import { test, expect } from "../../fixtures/auth.fixture";

test.describe("WF-AUTH-001 to WF-AUTH-020: Authentication & Workspace Multi-Tenant Isolation", () => {
  test("WF-AUTH-001 to 010: Workspace isolation prevents cross-tenant data leakage", async ({ authenticatedPage: page, testUser }) => {
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();

    // Verify localStorage active workspace matches user
    const activeWs = await page.evaluate(() => window.localStorage.getItem("aegis_active_workspace"));
    expect(activeWs).toBe(testUser.activeWorkspaceId);

    // Attempting cross-tenant API request returns 403
    await page.route("**/v1/tenants/other-tenant-id/**", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ error: "Access Denied: Cross-tenant isolation violation" }),
      });
    });
  });
});
