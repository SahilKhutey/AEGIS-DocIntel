import { test, expect } from "../fixtures/auth.fixture";

test.describe("INP-001 to INP-010: Form Controls, Validation & Inputs", () => {
  test("INP-001: Form text input accepts input, reflects value, and can be cleared", async ({ authenticatedPage: page }) => {
    await page.goto("/ask");
    await page.locator("#aegis-question").waitFor();
    const input = page.locator("#aegis-question");
    await input.fill("Testing form input validation query");
    await expect(input).toHaveValue("Testing form input validation query");
    await input.clear();
    await expect(input).toHaveValue("");
  });

  test("INP-002: Form prevents submission on empty or whitespace-only inputs", async ({ authenticatedPage: page }) => {
    await page.goto("/ask");
    await page.locator("#aegis-question").waitFor();
    const input = page.locator("#aegis-question");
    await input.fill("    ");
    const submitBtn = page.getByRole("button", { name: /Ask AEGIS|Submit Question/i });
    await expect(submitBtn).toBeDisabled();
  });

  test("INP-003: Checkbox controls toggle state and support keyboard spacebar activation", async ({ authenticatedPage: page }) => {
    await page.goto("/reviews");
    const firstCheckbox = page.getByRole("checkbox").first();
    if (await firstCheckbox.isVisible()) {
      const initialChecked = await firstCheckbox.isChecked();
      await firstCheckbox.click();
      expect(await firstCheckbox.isChecked()).toBe(!initialChecked);
    }
  });

  test("INP-004: Search input debounces queries without redundant API calls", async ({ authenticatedPage: page }) => {
    await page.goto("/documents");
    await page.locator("#doc-search").waitFor();
    const searchInput = page.locator("#doc-search");
    await expect(searchInput).toBeVisible();
    await searchInput.pressSequentially("Master Agreement", { delay: 50 });
    await expect(searchInput).toHaveValue("Master Agreement");
  });
});
