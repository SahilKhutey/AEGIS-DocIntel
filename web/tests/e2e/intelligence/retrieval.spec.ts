import { expect, test } from "@playwright/test";

test.describe("Document Retrieval Interface", () => {
  test("renders retrieval interface with search form", async ({ page }) => {
    await page.goto("/intelligence/retrieval");

    await expect(
      page.getByRole("heading", { name: "Document Retrieval Interface" }),
    ).toBeVisible();

    await expect(page.getByLabel("Search documents")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Search", exact: true }),
    ).toBeDisabled();
  });

  test("enables search button when query is entered", async ({ page }) => {
    await page.goto("/intelligence/retrieval");

    await page.getByLabel("Search documents").fill("governing law and jurisdiction");
    await expect(
      page.getByRole("button", { name: "Search", exact: true }),
    ).toBeEnabled();
  });
});
