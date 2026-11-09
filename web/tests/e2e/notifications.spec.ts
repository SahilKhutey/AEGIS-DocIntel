import { test, expect } from "@playwright/test";

test.describe("Notification Center", () => {
  test("displays bell trigger and opens panel", async ({ page }) => {
    await page.goto("/");

    const trigger = page.getByRole("button", { name: /notifications/i });
    await expect(trigger).toBeVisible();

    await trigger.click();

    const panel = page.locator("#notification-panel");
    await expect(panel).toBeVisible();
    await expect(panel.getByRole("heading", { name: "Notifications" })).toBeVisible();

    // Verify Escape key closes panel
    await page.keyboard.press("Escape");
    await expect(panel).toHaveCount(0);
  });
});
