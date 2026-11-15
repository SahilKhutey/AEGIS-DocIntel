import { test, expect } from "../../fixtures/auth.fixture";

test.describe("NAV-008 to NAV-010: Deep Links & Nested Routing", () => {
  test("NAV-008: Refresh a nested route reloads cleanly without 404", async ({ authenticatedPage: page }) => {
    await page.goto("/pipelines/job-run-9021");
    await expect(page.getByRole("main")).toBeVisible();

    await page.reload();
    await expect(page).toHaveURL(/\/pipelines\/job-run-9021/);
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByText("job-run-9021")).toBeVisible();
  });

  test("NAV-009: Open a direct URL loads target page and data immediately", async ({ authenticatedPage: page }) => {
    await page.goto("/analytics");
    await expect(page).toHaveURL(/\/analytics/);
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByText(/Operational Analytics|Analytics/i).first()).toBeVisible();
  });

  test("NAV-010: Open an invalid document ID renders meaningful not-found state", async ({ authenticatedPage: page }) => {
    await page.route("**/documents/doc-non-existent-999999**", async (route) => {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Document doc-non-existent-999999 not found" }),
      });
    });
    await page.goto("/documents/doc-non-existent-999999");
    const notFoundText = page.locator("text=/not found|unable to find|inaccessible|404|does not exist/i");
    await expect(notFoundText.first()).toBeVisible();
  });
});
