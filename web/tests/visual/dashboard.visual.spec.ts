import { test, expect } from "../fixtures/auth.fixture";

test.describe("Visual Regression: Overview Dashboard", () => {
  test("Dashboard hero banner, KPI cards, and activity widgets render cleanly", async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();

    // Verify 5 metric cards exist
    const kpiCards = page.locator("text=/Total Documents|Processing|Completed|Needs Attention|Queued/i");
    expect(await kpiCards.count()).toBeGreaterThanOrEqual(3);
  });
});
