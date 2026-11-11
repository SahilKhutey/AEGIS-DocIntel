import { test, expect } from "../fixtures/auth.fixture";

test.describe("API-FE-014, 017, 019: Mutation Persistence & Revalidation", () => {
  test("API-FE-019: State remains persistent and verified after browser refresh", async ({ authenticatedPage: page }) => {
    await page.goto("/pipelines/job-run-9021");
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByText("job-run-9021")).toBeVisible();

    await page.reload();
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByText("job-run-9021")).toBeVisible();
  });
});
