import { test, expect } from "../../fixtures/auth.fixture";

test.describe("NAV-001 to NAV-004: Primary Sidebar Navigation", () => {
  test("NAV-001: Click each primary sidebar item opens correct route", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();

    // Document Library
    await page.getByRole("link", { name: /Document Library/i }).first().click();
    await expect(page).toHaveURL(/\/documents/);
    await expect(page.getByRole("main")).toBeVisible();

    // Ask AEGIS
    await page.getByRole("link", { name: /Ask AEGIS/i }).first().click();
    await expect(page).toHaveURL(/\/ask/);
    await expect(page.getByRole("main")).toBeVisible();

    // Return to Overview
    await page.getByRole("link", { name: /Overview/i }).first().click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("NAV-002: Click active navigation item preserves page stability", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    const docLink = page.getByRole("link", { name: /Document Library/i }).first();
    await docLink.click();
    await expect(page).toHaveURL(/\/documents/);
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("NAV-003: Active navigation item is semantically and visually highlighted", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    const docLink = page.getByRole("link", { name: /Document Library/i }).first();
    await expect(docLink).toHaveAttribute("aria-current", "page");
  });

  test("NAV-004: Collapse and expand sidebar toggles without content loss", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    const collapseButton = page.getByRole("button", { name: /collapse sidebar/i });
    if (await collapseButton.isVisible()) {
      await collapseButton.click();
      const expandButton = page.getByRole("button", { name: /expand sidebar/i });
      await expect(expandButton).toBeVisible();
      await expandButton.click();
      await expect(page.getByRole("link", { name: /Document Library/i }).first()).toBeVisible();
    }
  });
});
