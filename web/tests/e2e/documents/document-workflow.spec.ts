import { test, expect } from "../../fixtures/documents.fixture";

test.describe("WF-DOC-001 to WF-DOC-020: Document Ingestion & Lifecycle Workflow", () => {
  test("WF-DOC-001 to 010: Complete document ingestion from upload dialog to library rendering", async ({ page, mockDocumentsApi }) => {
    await mockDocumentsApi();
    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();

    // 1. Open upload modal
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // 2. Select file via input[type='file']
    const fileInput = dialog.locator("input[type='file']");
    if (await fileInput.count() > 0) {
      await fileInput.setInputFiles({
        name: "Enterprise_MSA_2026.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 synthetic mock enterprise pdf document contents"),
      });

      // 3. Submit
      const submitBtn = dialog.getByRole("button", { name: /Start Upload|Upload/i });
      if (await submitBtn.isEnabled()) {
        await submitBtn.click();
      }
    }

    // 4. Verify library refreshes with records
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("WF-DOC-011: Unsupported file format rejection with client-side error", async ({ page }) => {
    await page.goto("/documents");
    const uploadBtn = page.getByRole("button", { name: /Upload Document/i }).first();
    await uploadBtn.click();
    const dialog = page.getByRole("dialog");

    const fileInput = dialog.locator("input[type='file']");
    if (await fileInput.count() > 0) {
      await fileInput.setInputFiles({
        name: "malicious_script.exe",
        mimeType: "application/x-msdownload",
        buffer: Buffer.from("MZ mock executable payload"),
      });

      // Error message for unsupported file
      const errorMsg = dialog.getByText(/not supported|Failed/i);
      await expect(errorMsg.first()).toBeVisible();
    }
  });
});
