import { test, expect } from "@playwright/test";

test.describe("AEGIS user journey entry points", () => {
  test("workspace user can enter document library", async ({ page }) => {
    await page.goto("/");
    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Document Library/i })
      .click();
    await expect(page).toHaveURL(/\/documents$/);
  });

  test("analyst can enter Ask AEGIS", async ({ page }) => {
    await page.goto("/");
    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Ask AEGIS/i })
      .click();
    await expect(page).toHaveURL(/\/ask$/);
  });

  test("analyst can enter document comparison", async ({ page }) => {
    await page.goto("/");
    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Compare Documents/i })
      .click();
    await expect(page).toHaveURL(/\/compare$/);
  });

  test("reviewer can enter governance queue", async ({ page }) => {
    await page.goto("/");
    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: /Review Queue/i })
      .click();
    await expect(page).toHaveURL(/\/reviews$/);
  });

  test("planned pages are not presented as operational", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("link", { name: "Evidence Explorer" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("link", { name: "Processing Jobs" }),
    ).toHaveCount(0);
  });
});
