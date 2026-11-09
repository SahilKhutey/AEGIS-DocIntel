import { test, expect } from "@playwright/test";

test("main content is reachable by keyboard", async ({ page }) => {
  await page.goto("/");

  await page.keyboard.press("Tab");

  await expect(
    page.getByRole("link", { name: /skip to main content/i })
  ).toBeFocused();
});

test("main landmark exists", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("main")).toBeVisible();
});

test("primary buttons have accessible names", async ({ page }) => {
  await page.goto("/");

  const buttons = page.getByRole("button");
  const count = await buttons.count();

  for (let i = 0; i < count; i += 1) {
    await expect(buttons.nth(i)).toHaveAccessibleName(/.+/);
  }
});
