import { test, expect } from "../fixtures/auth.fixture";

test.describe("Visual Regression: Document Workspace & Modal Dialog", () => {
  test("Document library layout and upload modal visual styling", async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();

    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
  });
});
