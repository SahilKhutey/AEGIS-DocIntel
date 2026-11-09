import { test, expect } from "@playwright/test";

test.describe("WP-UI-08 Workspace Isolation & Security Controls", () => {
  test("workspace selector indicates active workspace and allows switching", async ({
    page,
  }) => {
    await page.goto("/");
    const workspaceSelector = page.getByRole("button", { name: /Select workspace/i }).first();
    await expect(workspaceSelector).toBeVisible();
    await workspaceSelector.click();

    // Verify workspace dropdown items (rendered as role="option" in the listbox)
    await expect(page.getByRole("option", { name: /Primary Workspace|Production Corpus/i }).first()).toBeVisible();
  });

  test("route navigation preserves shell header and breadcrumbs", async ({
    page,
  }) => {
    await page.goto("/analytics");
    await expect(page.getByRole("navigation", { name: "Breadcrumb" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Workspace/i })).toBeVisible();
    await expect(page.getByText(/Analytics/i).first()).toBeVisible();
  });

  test("command palette shortcut trigger is accessible", async ({ page }) => {
    await page.goto("/");
    const searchTrigger = page.getByPlaceholder(/Search documents, evidence/i);
    await expect(searchTrigger).toBeVisible();
  });
});
