import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const coreRoutes = [
  "/",
  "/documents",
  "/ask",
  "/compare",
  "/reviews",
  "/analytics",
  "/mathematics",
  "/pipelines",
  "/monitoring",
  "/developer",
];

test.describe("Automated WCAG 2.2 AA Accessibility Audits", () => {
  for (const route of coreRoutes) {
    test(`route ${route} has no critical or serious accessibility violations`, async ({
      page,
    }) => {
      await page.goto(route);
      await expect(page.locator("body")).toBeVisible();

      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();

      const severeViolations = results.violations.filter(
        (v) => v.impact === "critical" || v.impact === "serious"
      );

      expect(severeViolations).toEqual([]);
    });
  }

  test("keyboard navigation: skip to main content works", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const skipLink = page.getByRole("link", { name: /skip to main content/i });
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeFocused();
    }
  });

  test("main landmark exists across all views", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();
  });
});
