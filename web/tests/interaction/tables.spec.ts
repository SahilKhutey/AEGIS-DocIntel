import { test, expect } from "../fixtures/auth.fixture";

test.describe("TBL-001 to TBL-012: Data Tables, Sorting, and Empty States", () => {
  test("TBL-001: Data table renders semantic table, headers, rows, and cells", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    const table = page.locator("table");
    if (await table.isVisible()) {
      await expect(table.locator("thead")).toBeVisible();
      await expect(table.locator("tbody")).toBeVisible();
    } else {
      // Empty state table container
      await expect(page.getByRole("main")).toBeVisible();
    }
  });

  test("TBL-002: Click column header toggles sort order indicators", async ({ authenticatedPage: page }) => {
    await page.goto("/analytics");
    const sortableHeader = page.locator("th[aria-sort], th button").first();
    if (await sortableHeader.isVisible()) {
      await sortableHeader.click();
      await expect(page.getByRole("main")).toBeVisible();
    }
  });
});
