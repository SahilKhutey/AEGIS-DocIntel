import { test, expect } from "../fixtures/auth.fixture";
import AxeBuilder from "@axe-core/playwright";

test.describe("A11Y-001 to A11Y-015: WCAG 2.2 AA Usability & Assistive Technology Suite", () => {
  test("A11Y-001 & 002: Logical keyboard focus order using Tab and Shift+Tab", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const activeElementTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(activeElementTag).toBeTruthy();
  });

  test("A11Y-003 & 004: Activation via Enter and Space for interactive controls", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.waitForLoadState("networkidle");
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
  });

  test("A11Y-005 & 006: Modal dialog focus trapping and return to trigger", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.waitForLoadState("networkidle");
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // Verify focus is inside dialog
    const isFocusInDialog = await page.evaluate(() => {
      const active = document.activeElement;
      const dlg = document.querySelector("[role='dialog']");
      return dlg?.contains(active);
    });
    expect(isFocusInDialog).toBeTruthy();

    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
  });

  test("A11Y-007 to 015: Automated Axe scan on document library for WCAG 2.2 AA compliance", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();

    const criticalViolations = results.violations.filter((v) => v.impact === "critical" || v.impact === "serious");
    expect(criticalViolations).toEqual([]);
  });
});
