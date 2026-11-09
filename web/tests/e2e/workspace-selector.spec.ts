import { test, expect } from "@playwright/test";

test.describe("Workspace Selector", () => {
  test("displays current workspace and opens listbox", async ({ page }) => {
    await page.goto("/");

    const selector = page.getByRole("button", { name: /select workspace/i });
    await expect(selector).toBeVisible();

    await selector.click();

    const listbox = page.getByRole("listbox", { name: "Available workspaces" });
    await expect(listbox).toBeVisible();

    // Verify Escape key closes listbox
    await page.keyboard.press("Escape");
    await expect(listbox).toHaveCount(0);
  });
});
