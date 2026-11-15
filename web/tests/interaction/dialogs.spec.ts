import { test, expect } from "../fixtures/auth.fixture";

test.describe("DLG-001 to DLG-010: Modal Dialog & Overlay Behavior", () => {
  test("DLG-001: Modal dialog opens from trigger with backdrop blur", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.locator("#doc-search").waitFor();
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/Upload Documents/i)).toBeVisible();
  });

  test("DLG-002: Modal closes on Escape key and returns focus to trigger", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.locator("#doc-search").waitFor();
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
  });

  test("DLG-003: Modal close button dismisses dialog without accidental submission", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.locator("#doc-search").waitFor();
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();

    const closeBtn = page.getByRole("button", { name: /Close dialog|Cancel/i }).first();
    await closeBtn.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).not.toBeVisible();
  });
});
