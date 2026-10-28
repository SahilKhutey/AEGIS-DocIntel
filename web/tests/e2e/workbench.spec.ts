import { test, expect } from "@playwright/test";

test.describe("AEGIS-DocIntel Workbench", () => {
  test("documents page loads with workbench navigation and empty or populated list", async ({ page }) => {
    await page.goto("/documents");
    await expect(page.getByRole("heading", { name: /document workspace/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /ask & evidence/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /review queue/i })).toBeVisible();
  });

  test("ask page renders question form and handles empty evidence gracefully", async ({ page }) => {
    await page.goto("/ask");
    await expect(page.getByRole("heading", { name: /ask & evidence explorer/i })).toBeVisible();
    await expect(page.getByLabel(/your question/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /ask question/i })).toBeVisible();
  });

  test("compare page enforces minimum two documents selection", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.getByRole("heading", { name: /document intelligence & cross-document comparison/i })).toBeVisible();
  });

  test("reviews queue renders governance review heading and metrics", async ({ page }) => {
    await page.goto("/reviews");
    await expect(page.getByRole("heading", { name: /human governance review queue/i })).toBeVisible();
  });
});
