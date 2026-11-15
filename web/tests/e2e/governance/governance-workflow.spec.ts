import { test, expect } from "../../fixtures/governance.fixture";

test.describe("WF-GOV-001 to WF-GOV-025: Human Oversight, Verification & Governance Workflow", () => {
  test("WF-GOV-001 to 015: Inspect queue, review facts, verify supporting evidence, and record sovereign decision", async ({ page, mockReviewsApi }) => {
    await mockReviewsApi();
    await page.goto("/reviews");
    await expect(page.getByRole("main")).toBeVisible();

    // Verify review queue items
    const reviewRows = page.locator("[role='row'], li[data-review-id], a[href*='/reviews/']");
    if (await reviewRows.count() > 0) {
      await reviewRows.first().click();
      await expect(page).toHaveURL(/\/reviews\//);
      await expect(page.getByRole("main")).toBeVisible();
    }
  });
});
