import { test, expect } from "@playwright/test";

test.describe("Upload Experience", () => {
  test.beforeEach(async ({ page }) => {
    // Intercept document list
    await page.route("**/api/v1/documents*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
        }),
      });
    });

    // Intercept upload endpoint
    await page.route("**/api/v1/documents/upload", async (route) => {
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          document_id: "doc-new-uploaded-001",
          status: "accepted",
          message: "Document uploaded successfully and queued for indexing.",
        }),
      });
    });
  });

  test("validates file and completes upload workflow", async ({ page }) => {
    await page.goto("/documents");

    // Open upload dialog
    await page.getByRole("button", { name: /upload document/i }).click();
    const dialog = page.getByRole("dialog", { name: "Upload Documents" });
    await expect(dialog).toBeVisible();

    // Attach file using file input
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: /browse files/i }).click();
    const fileChooser = await fileChooserPromise;

    await fileChooser.setFiles({
      name: "quarterly_filing.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 mock pdf content"),
    });

    // Verify file is staged in file list
    await expect(page.getByText("quarterly_filing.pdf")).toBeVisible();

    // Click Start Upload
    const uploadBtn = page.getByRole("button", { name: /start upload/i });
    await expect(uploadBtn).toBeEnabled();
    await uploadBtn.click();

    // Verify completion
    await expect(page.getByText(/completed/i).first()).toBeVisible();
  });

  test("rejects unsupported file type with client-side error", async ({ page }) => {
    await page.goto("/documents");

    await page.getByRole("button", { name: /upload document/i }).click();

    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: /browse files/i }).click();
    const fileChooser = await fileChooserPromise;

    await fileChooser.setFiles({
      name: "malicious_script.sh",
      mimeType: "application/x-sh",
      buffer: Buffer.from("#!/bin/sh\necho hello"),
    });

    // Should display validation error
    await expect(page.getByText(/not supported/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /start upload/i })).toBeDisabled();
  });
});
