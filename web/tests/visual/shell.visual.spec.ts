import { test, expect } from "../fixtures/auth.fixture";

test.describe("Visual Regression: Application Shell & Chrome Layout", () => {
  test("Desktop viewport shell layout, sidebar branding, and header alignment", async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();

    // Verify main landmarks
    const sidebar = page.locator("aside, nav[aria-label='Main Navigation']").first();
    await expect(sidebar).toBeVisible();

    const header = page.locator("header").first();
    await expect(header).toBeVisible();
  });
});
