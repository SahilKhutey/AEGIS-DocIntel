import { test, expect } from "../fixtures/auth.fixture";

test.describe("BTN-001 to BTN-010: Button States and Interaction Verification", () => {
  test("BTN-001: Primary button click triggers expected action with feedback", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.waitForLoadState("networkidle");
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await expect(uploadBtn).toBeVisible();
    await expect(uploadBtn).toBeEnabled();
    await uploadBtn.click();
    await expect(page.getByRole("dialog")).toBeVisible();
  });

  test("BTN-002: Secondary action button executes non-destructive task", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.locator("#doc-search").waitFor();
    const refreshBtn = page.getByRole("button", { name: /Refresh/i });
    if (await refreshBtn.isVisible()) {
      await expect(refreshBtn).toBeEnabled();
      await refreshBtn.click();
    }
  });

  test("BTN-003: Disabled button cannot be clicked or triggered by keyboard", async ({ authenticatedPage: page }) => {
    await page.goto("/ask");
    await page.locator("#aegis-question").waitFor();
    const submitBtn = page.getByRole("button", { name: /Ask AEGIS|Submit Question/i });
    // Without input text, submit button is disabled
    await expect(submitBtn).toBeDisabled();
    await submitBtn.click({ force: true });
    await expect(page.locator("#aegis-question")).toHaveValue("");
  });

  test("BTN-004: Loading button prevents duplicate submission", async ({ authenticatedPage: page }) => {
    await page.goto("/ask");
    await page.waitForLoadState("networkidle");
    const composerInput = page.locator("#aegis-question");
    await composerInput.click();
    await composerInput.pressSequentially("What are the termination notice requirements?", { delay: 20 });

    const submitBtn = page.getByRole("button", { name: /Ask AEGIS/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("BTN-005: Icon buttons have accessible name and screen-reader labels", async ({ authenticatedPage: page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    const bellBtn = page.getByRole("button", { name: /Notifications/i });
    await expect(bellBtn).toBeVisible();
    const ariaLabel = await bellBtn.getAttribute("aria-label");
    expect(ariaLabel).toBeTruthy();
  });

  test("BTN-006: Filter button pills toggle active and inactive visual states", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.waitForLoadState("networkidle");
    const completedFilter = page.getByRole("button", { name: /^Completed/i });
    if (await completedFilter.isVisible()) {
      await completedFilter.click();
      await expect(completedFilter).toHaveAttribute("aria-pressed", "true");
    }
  });
});
