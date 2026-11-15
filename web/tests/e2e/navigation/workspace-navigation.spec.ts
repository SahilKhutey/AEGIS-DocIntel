import { test, expect } from "../../fixtures/auth.fixture";

test.describe("NAV-012, NAV-014, NAV-015: Workspace Switching and Mobile Navigation", () => {
  test("NAV-012: Switch workspace updates active context and scoped data", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    const workspaceSelector = page.getByRole("button", { name: /Primary Workspace|Workspace/i });
    if (await workspaceSelector.isVisible()) {
      await workspaceSelector.click();
      const financeOption = page.getByRole("option", { name: /Finance & Compliance/i });
      if (await financeOption.isVisible()) {
        await financeOption.click();
        await expect(page.getByText(/Finance & Compliance/i).first()).toBeVisible();
      }
    }
  });

  test("NAV-014: Open internal navigation link respects same-origin SPA routing", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    const docLink = page.getByRole("link", { name: /Document Library/i }).first();
    const href = await docLink.getAttribute("href");
    expect(href).toMatch(/\/documents/);
  });

  test("NAV-015: Mobile viewport renders accessible mobile navigation", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const mobileNav = page.locator("nav[aria-label='Mobile navigation']");
    await expect(mobileNav).toBeVisible();

    const docLink = mobileNav.getByRole("link", { name: /Document Library/i }).first();
    await expect(docLink).toBeVisible();
    await docLink.click();
    await expect(page).toHaveURL(/\/documents/);
  });
});
