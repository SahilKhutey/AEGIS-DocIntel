import { test, expect } from "@playwright/test";

test.describe("Global Search", () => {
  test("renders search input and supports typing and clearing", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    const searchInput = page.getByLabel("Search AEGIS");
    await expect(searchInput).toBeVisible();

    await searchInput.fill("acme");
    await expect(searchInput).toHaveValue("acme");

    const clearBtn = page.getByRole("button", { name: "Clear search" });
    await expect(clearBtn).toBeVisible();

    await clearBtn.click();
    await expect(searchInput).toHaveValue("");
  });
});
