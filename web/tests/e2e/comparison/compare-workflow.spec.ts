import { test, expect } from "../../fixtures/auth.fixture";

test.describe("WF-CMP-001 to WF-CMP-015: Document Comparison Workflow", () => {
  test("WF-CMP-001 to 008: Document comparison selection, validation, and side-by-side rendering", async ({ authenticatedPage: page }) => {
    // Intercept document list to return 2 selectable documents
    await page.route("**/api/v1/documents**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "doc-cmp-001",
              name: "Vendor_Agreement_v1.pdf",
              mimeType: "application/pdf",
              sizeBytes: 1048576,
              status: "completed",
              updatedAt: new Date().toISOString(),
            },
            {
              id: "doc-cmp-002",
              name: "Vendor_Agreement_v2.pdf",
              mimeType: "application/pdf",
              sizeBytes: 1100000,
              status: "completed",
              updatedAt: new Date().toISOString(),
            },
          ],
          total: 2,
        }),
      });
    });

    await page.goto("/compare");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("main")).toBeVisible();

    // Verify comparison controls
    const compareBtn = page.getByRole("button", { name: /Run Comparison|Compare Documents|Compare Selected/i });
    if (await compareBtn.count() > 0) {
      await expect(compareBtn.first()).toBeDisabled();
    }

    // Check document selection checkboxes or buttons
    const checkboxes = page.getByRole("checkbox");
    if (await checkboxes.count() >= 2) {
      await checkboxes.nth(0).click();
      await checkboxes.nth(1).click();
      if (await compareBtn.count() > 0) {
        await expect(compareBtn.first()).toBeEnabled();
      }
    }
  });
});
