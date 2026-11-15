import { test, expect } from "../fixtures/auth.fixture";

const MATRIX_VIEWPORTS = [
  { profile: "Small mobile", width: 320, height: 568 },
  { profile: "Standard mobile", width: 390, height: 844 },
  { profile: "Large mobile", width: 430, height: 932 },
  { profile: "Tablet", width: 768, height: 1024 },
  { profile: "Small desktop", width: 1024, height: 768 },
  { profile: "Desktop", width: 1366, height: 768 },
  { profile: "Large desktop", width: 1920, height: 1080 },
];

test.describe("Responsive Viewport Validation Matrix", () => {
  for (const vp of MATRIX_VIEWPORTS) {
    test(`Overview and Document Workspace fit ${vp.profile} (${vp.width}x${vp.height})`, async ({ authenticatedPage: page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/documents");
      await expect(page.getByRole("main")).toBeVisible();

      const overflow = await page.evaluate(() => ({
        documentWidth: document.documentElement.scrollWidth,
        viewportWidth: document.documentElement.clientWidth,
      }));
      expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth + 2);
    });
  }
});
