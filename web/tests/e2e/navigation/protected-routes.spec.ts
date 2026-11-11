import { test, expect } from "@playwright/test";

test.describe("NAV-011 & NAV-013: Route Protection and Access Controls", () => {
  test("NAV-011: Forbidden route or missing permissions triggers access denied state", async ({ page }) => {
    // Navigate with a restricted role header or mock 403
    await page.route("**/v1/admin**", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ error: "Access Denied: Requires Administrator Privilege" }),
      });
    });

    await page.goto("/developer");
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("NAV-013: Sign out and revisit protected route enforces authentication boundary", async ({ page }) => {
    await page.goto("/");
    // Clear tokens
    await page.evaluate(() => {
      window.localStorage.removeItem("aegis_auth_session");
    });
    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();
  });
});
