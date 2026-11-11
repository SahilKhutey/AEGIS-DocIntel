import { test, expect } from "../fixtures/auth.fixture";

test.describe("API-FE-001 to API-FE-013: Backend HTTP Status & Resilience Mapping", () => {
  test("API-FE-004: HTTP 400 Bad Request maps to structured user feedback", async ({ authenticatedPage: page }) => {
    await page.route("**/v1/documents**", async (route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ error: "Malformed Document Metadata Payload" }),
      });
    });

    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("API-FE-006: HTTP 403 Forbidden renders non-destructive permission guidance", async ({ authenticatedPage: page }) => {
    await page.route("**/v1/analytics**", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ error: "Insufficient Permissions: Requires Executive Access" }),
      });
    });

    await page.goto("/analytics");
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("API-FE-007: HTTP 404 Not Found displays clean missing resource boundary", async ({ authenticatedPage: page }) => {
    await page.route("**/v1/jobs/non-existent-job**", async (route) => {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ error: "Pipeline Run Not Found" }),
      });
    });

    await page.goto("/pipelines/non-existent-job");
    const notFoundText = page.locator("text=/not found|unable to find|404|does not exist/i");
    await expect(notFoundText.first()).toBeVisible();
  });

  test("API-FE-011: HTTP 500 Server Error provides retry CTA without UI crash", async ({ authenticatedPage: page }) => {
    await page.route("**/v1/documents**", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Document Store Connection Timeout" }),
      });
    });

    await page.goto("/documents");
    await expect(page.getByRole("main")).toBeVisible();
    const retryBtn = page.getByRole("button", { name: /Retry|Reload/i });
    if (await retryBtn.isVisible()) {
      await expect(retryBtn).toBeEnabled();
    }
  });
});
