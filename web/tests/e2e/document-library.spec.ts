import { test, expect } from "@playwright/test";

test.describe("Document Library", () => {
  test.beforeEach(async ({ page }) => {
    // Intercept document list endpoint
    await page.route("**/api/v1/documents*", async (route) => {
      const url = new URL(route.request().url());
      const statusParam = url.searchParams.get("status");

      const allItems = [
        {
          doc_id: "doc-alpha-001",
          tenant_id: "default",
          filename: "acme_q3_financial_report.pdf",
          content_hash: "hash001",
          page_count: 12,
          chunk_count: 45,
          status: "ready",
          created_at: "2026-11-01T10:00:00Z",
          indexed_at: "2026-11-01T10:05:00Z",
          language: "en",
        },
        {
          doc_id: "doc-beta-002",
          tenant_id: "default",
          filename: "security_policy_v2.docx",
          content_hash: "hash002",
          page_count: 8,
          chunk_count: 24,
          status: "indexing",
          created_at: "2026-11-02T10:00:00Z",
          indexed_at: null,
          language: "en",
        },
        {
          doc_id: "doc-gamma-003",
          tenant_id: "default",
          filename: "vendor_contract_2026.pdf",
          content_hash: "hash003",
          page_count: 5,
          chunk_count: 15,
          status: "failed",
          created_at: "2026-11-03T10:00:00Z",
          indexed_at: null,
          language: "en",
        },
      ];

      let filtered = allItems;
      if (statusParam) {
        filtered = allItems.filter((item) => item.status === statusParam);
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: filtered,
          total: filtered.length,
          page: 1,
          page_size: 20,
        }),
      });
    });
  });

  test("displays document library with records and status badges", async ({ page }) => {
    await page.goto("/documents");

    await expect(page.getByRole("heading", { name: "Documents", level: 1 })).toBeVisible();
    await expect(page.getByText("acme_q3_financial_report.pdf")).toBeVisible();
    await expect(page.getByText("security_policy_v2.docx")).toBeVisible();
    await expect(page.getByText("vendor_contract_2026.pdf")).toBeVisible();

    await expect(page.getByLabel("Document status: Completed")).toBeVisible();
    await expect(page.getByLabel("Document status: Processing")).toBeVisible();
    await expect(page.getByLabel("Document status: Failed")).toBeVisible();
  });

  test("filters documents by search query", async ({ page }) => {
    await page.goto("/documents");

    const searchInput = page.getByPlaceholder("Search documents by filename...");
    await searchInput.fill("security");

    await expect(page.getByText("security_policy_v2.docx")).toBeVisible();
    await expect(page.getByText("acme_q3_financial_report.pdf")).not.toBeVisible();
  });

  test("filters documents by status tabs", async ({ page }) => {
    await page.goto("/documents");

    // Click "Completed" status filter
    await page.getByRole("button", { name: "Completed" }).click();
    await expect(page.getByText("acme_q3_financial_report.pdf")).toBeVisible();
    await expect(page.getByText("security_policy_v2.docx")).not.toBeVisible();
  });

  test("opens upload documents modal dialog", async ({ page }) => {
    await page.goto("/documents");

    const uploadButton = page.getByRole("button", { name: /upload document/i });
    await uploadButton.click();

    await expect(page.getByRole("dialog", { name: "Upload Documents" })).toBeVisible();
    await expect(page.getByText(/drag (and|&) drop files here/i)).toBeVisible();
  });
});
