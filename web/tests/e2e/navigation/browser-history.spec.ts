import { test, expect } from "../../fixtures/auth.fixture";

test.describe("NAV-006 & NAV-007: Browser History Restoration", () => {
  test("NAV-006: Browser Back restores previous route and visual state", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();

    await page.goto("/documents");
    await expect(page).toHaveURL(/\/documents/);

    await page.goBack();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("NAV-007: Browser Forward restores next route and state", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    await page.goto("/documents");
    await page.goBack();
    await expect(page).toHaveURL(/\/$/);

    await page.goForward();
    await expect(page).toHaveURL(/\/documents/);
    await expect(page.getByRole("main")).toBeVisible();
  });
});
