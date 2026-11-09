import { test, expect } from "@playwright/test";

test("sidebar navigates to documents", async ({ page }) => {
  await page.goto("/");

  await page
    .getByRole("link", {
      name: /(all documents|document library)/i,
    })
    .first()
    .click();

  await expect(page).toHaveURL(/\/documents$/);
});

test("active navigation item is identified", async ({ page }) => {
  await page.goto("/documents");

  await expect(
    page.getByRole("link", { name: /(all documents|document library)/i }).first()
  ).toHaveAttribute("aria-current", "page");
});

test("breadcrumbs are visible", async ({ page }) => {
  await page.goto("/documents");

  await expect(
    page.getByRole("navigation", { name: "Breadcrumb" })
  ).toBeVisible();
});
