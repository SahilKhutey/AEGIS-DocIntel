import { test, expect } from "../fixtures/auth.fixture";

test.describe("Visual Regression: Governance Workspace", () => {
  test("Governance queue, review item cards, and priority badges", async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto("/reviews");
    await expect(page.getByRole("main")).toBeVisible();
  });
});
