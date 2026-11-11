import { test, expect } from "../fixtures/auth.fixture";

const VIEWPORTS = [
  { name: "small-mobile", width: 320, height: 568 },
  { name: "standard-mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1366, height: 768 },
];

const TARGET_ROUTES = ["/", "/documents", "/ask", "/compare", "/reviews", "/pipelines/job-run-9021"];

test.describe("Visual Regression: Responsive Multi-Viewport Audit", () => {
  for (const vp of VIEWPORTS) {
    for (const route of TARGET_ROUTES) {
      test(`Verify ${route} fits ${vp.name} (${vp.width}x${vp.height}) without unintentional horizontal overflow`, async ({ authenticatedPage: page }) => {
        await page.setViewportSize({ width: vp.width, height: vp.height });
        await page.goto(route);
        await expect(page.getByRole("main")).toBeVisible();

        const overflow = await page.evaluate(() => ({
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: document.documentElement.clientWidth,
        }));
        expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth + 2); // 2px margin tolerance for subpixel rounding
      });
    }
  }
});
