import { test, expect } from "../../fixtures/auth.fixture";

test.describe("NAV-005: Breadcrumb Navigation Hierarchy", () => {
  test("NAV-005: Navigate using breadcrumbs returns to correct parent hierarchy", async ({ authenticatedPage: page }) => {
    await page.goto("/pipelines/job-run-9021");
    await expect(page.getByRole("main")).toBeVisible();

    const breadcrumbs = page.locator("nav[aria-label='Breadcrumb']");
    await expect(breadcrumbs).toBeVisible();

    // Click parent breadcrumb link 'Pipelines'
    const parentLink = breadcrumbs.getByRole("link", { name: /Pipelines/i });
    await expect(parentLink).toBeVisible();
    await parentLink.click();

    await expect(page).toHaveURL(/\/pipelines$/);
    await expect(page.getByRole("main")).toBeVisible();
  });
});
