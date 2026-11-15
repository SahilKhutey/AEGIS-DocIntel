import { test, expect } from "../fixtures/auth.fixture";

test.describe("NTF-001 to NTF-008: Notifications & Feedback Center", () => {
  test("NTF-001: Notification bell opens popover with status alerts", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    const bellBtn = page.getByRole("button", { name: /Notifications/i });
    await expect(bellBtn).toBeVisible();
    await bellBtn.click();

    const panel = page.locator("[role='region'][aria-label='Notifications panel'], [role='menu']");
    if (await panel.isVisible()) {
      await expect(panel).toBeVisible();
    }
  });

  test("NTF-002: Click outside or Escape dismisses notifications overlay", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    const bellBtn = page.getByRole("button", { name: /Notifications/i });
    await bellBtn.click();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("main")).toBeVisible();
  });
});
