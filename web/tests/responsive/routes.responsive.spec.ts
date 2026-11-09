import { test, expect } from "@playwright/test";

const routes = [
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

const viewports = [
  { name: "small-mobile", width: 320, height: 568 },
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet-portrait", width: 768, height: 1024 },
  { name: "tablet-landscape", width: 1024, height: 768 },
  { name: "desktop", width: 1366, height: 768 },
  { name: "wide-desktop", width: 1920, height: 1080 },
];

for (const vp of viewports) {
  test.describe(`Viewport: ${vp.name} (${vp.width}x${vp.height})`, () => {
    for (const route of routes) {
      test(`renders ${route} without unintended page-level horizontal overflow`, async ({
        page,
      }) => {
        await page.setViewportSize({ width: vp.width, height: vp.height });
        await page.goto(route);

        await expect(page.locator("body")).toBeVisible();

        const dimensions = await page.evaluate(() => ({
          viewportWidth: document.documentElement.clientWidth,
          contentWidth: document.documentElement.scrollWidth,
        }));

        // Allow at most 2px margin for subpixel browser rendering
        expect(dimensions.contentWidth).toBeLessThanOrEqual(
          dimensions.viewportWidth + 2
        );
      });
    }
  });
}
