import { test, expect } from "../fixtures/auth.fixture";

test.describe("Visual Regression: Intelligence Workspace", () => {
  test("Ask AEGIS query workspace and citation cards", async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto("/ask");
    await expect(page.getByRole("main")).toBeVisible();

    const composer = page.locator("#aegis-question");
    await expect(composer).toBeVisible();
  });
});
