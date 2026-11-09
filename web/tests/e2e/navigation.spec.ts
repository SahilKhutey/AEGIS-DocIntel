import { test, expect } from "@playwright/test";

test.describe("AEGIS product navigation", () => {
  test("renders the workspace home page", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("link", { name: /AEGIS/i }).first(),
    ).toBeVisible();

    await expect(
      page.locator("#main-content"),
    ).toBeVisible();
  });

  test("navigates to the document workspace", async ({ page }) => {
    await page.goto("/");

    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Document Library/i })
      .click();

    await expect(page).toHaveURL(/\/documents$/);
  });

  test("navigates to Ask AEGIS", async ({ page }) => {
    await page.goto("/");

    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Ask AEGIS/i })
      .click();

    await expect(page).toHaveURL(/\/ask$/);
  });

  test("navigates to the review queue", async ({ page }) => {
    await page.goto("/");

    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Review Queue/i })
      .click();

    await expect(page).toHaveURL(/\/reviews$/);
  });

  test("does not expose planned routes in navigation", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("link", { name: "Processing Jobs" }),
    ).toHaveCount(0);

    await expect(
      page.getByRole("link", { name: "Analytics" }),
    ).toHaveCount(0);
  });

  test("primary navigation has an accessible name", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("navigation", {
        name: "Primary navigation",
      }),
    ).toBeAttached();
  });

  test("mobile navigation remains available", async ({ page }) => {
    await page.setViewportSize({
      width: 390,
      height: 844,
    });

    await page.goto("/");

    await expect(
      page.getByRole("navigation", {
        name: "Mobile navigation",
      }),
    ).toBeVisible();
  });
});
