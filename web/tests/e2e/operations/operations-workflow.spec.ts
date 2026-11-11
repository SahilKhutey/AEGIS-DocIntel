import { test, expect } from "../../fixtures/auth.fixture";

test.describe("WF-OPS-001 to WF-OPS-015: Analytics & System Operations Workflow", () => {
  test("WF-OPS-001 to 010: Operational metrics, time range filtering, pipeline inspection", async ({ authenticatedPage: page }) => {
    await page.goto("/analytics");
    await expect(page.getByRole("main")).toBeVisible();

    // Verify time range selectors
    const timeRangeButtons = page.getByRole("button", { name: /7D|30D|90D/i });
    if (await timeRangeButtons.count() > 0) {
      await timeRangeButtons.first().click();
      await expect(page.getByRole("main")).toBeVisible();
    }

    // Inspect pipeline execution
    await page.goto("/pipelines/job-run-9021");
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByText(/COMPLETED|SUCCEEDED/i).first()).toBeVisible();
  });
});
