import { test, expect } from "@playwright/test";

test.describe("Design System Browser Verification", () => {
  test("root styles expose semantic CSS tokens", async ({ page }) => {
    await page.goto("/");

    const primaryColor = await page.evaluate(() => {
      return getComputedStyle(document.documentElement).getPropertyValue("--primary").trim();
    });

    expect(primaryColor).toBe("#2563eb");
  });

  test("skip-link is visually styled upon keyboard focus", async ({ page }) => {
    await page.goto("/");

    // Focus the skip link
    await page.keyboard.press("Tab");
    const skipLink = page.getByRole("link", { name: /skip to main content/i });
    await expect(skipLink).toBeFocused();

    // Verify it is positioned into visible viewport
    const boundingBox = await skipLink.boundingBox();
    expect(boundingBox).not.toBeNull();
    expect(boundingBox!.y).toBeGreaterThanOrEqual(0);
  });

  test("main content container maintains maximum constraint", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    const main = page.getByRole("main");
    await expect(main).toBeVisible();

    const box = await main.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeLessThanOrEqual(1440);
  });
});
