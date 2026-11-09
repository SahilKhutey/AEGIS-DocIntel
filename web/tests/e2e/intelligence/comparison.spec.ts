import { expect, test } from "@playwright/test";

test.describe("Comparison Workspace", () => {
  test("renders comparison interface with document selection", async ({ page }) => {
    await page.route("**/api/v1/documents*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              doc_id: "doc-cmp-1",
              filename: "Contract_v1.pdf",
              status: "ready",
              is_scanned: false,
              language: "en",
              created_at: "2026-11-01T00:00:00Z",
            },
            {
              doc_id: "doc-cmp-2",
              filename: "Contract_v2.pdf",
              status: "ready",
              is_scanned: false,
              language: "en",
              created_at: "2026-11-02T00:00:00Z",
            },
          ],
          total: 2,
          page: 1,
          page_size: 50,
        }),
      });
    });

    await page.goto("/compare");

    await expect(
      page.getByRole("heading", { name: /Document Intelligence & Cross-Document Comparison/i }),
    ).toBeVisible();

    await expect(
      page.getByText(/Select Documents to Compare/i),
    ).toBeVisible();
  });
});
