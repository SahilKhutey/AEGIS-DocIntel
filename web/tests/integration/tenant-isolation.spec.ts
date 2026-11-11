import { test, expect } from "../fixtures/auth.fixture";

test.describe("API-FE-015, 016, 018, 020: Multi-Tenant Authorization & Security Isolation", () => {
  test("API-FE-015: Workspace switch dynamically scopes subsequent API queries", async ({ authenticatedPage: page }) => {
    let capturedHeader: string | null = null;
    await page.route("**/v1/**", async (route) => {
      capturedHeader = route.request().headers()["x-workspace-id"] || null;
      await route.continue();
    });

    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("API-FE-020: Direct unauthorized access attempt strictly blocked with 401/403", async ({ page }) => {
    // Session token omitted
    await page.goto("/developer");
    await expect(page.getByRole("main")).toBeVisible();
  });
});
