import { expect, test } from "@playwright/test";

test.describe("Knowledge Visualization", () => {
  test("renders knowledge graph workspace with view modes", async ({ page }) => {
    await page.route("**/api/v1/documents*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              doc_id: "doc-kg-1",
              filename: "Agreement.pdf",
              status: "ready",
              is_scanned: false,
              language: "en",
              created_at: "2026-11-01T00:00:00Z",
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
        }),
      });
    });

    await page.goto("/intelligence/knowledge");

    await expect(
      page.getByRole("heading", { name: /Knowledge Graph & Entity Relationships/i }),
    ).toBeVisible();

    await expect(page.getByRole("button", { name: /Visual graph view/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Accessible table view/i })).toBeVisible();
  });
});
