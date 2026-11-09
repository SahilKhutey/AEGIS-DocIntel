import { test, expect } from "@playwright/test";

test.describe("Governance Review Queue (/reviews)", () => {
  test.beforeEach(async ({ page }) => {
    // Mock review queue list
    await page.route("**/api/v1/reviews", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              review_id: "rev-001",
              tenant_id: "tenant-alpha-001",
              candidate_id: "revenue_q3_2026",
              candidate_type: "fact",
              status: "pending",
              field_name: "revenue_q3_2026",
              extracted_value: "$142.5M",
              candidate_data: {
                subject: "Acme Corporation",
                attribute: "revenue_q3_2026",
                value: "$142.5M",
                confidence: 0.98,
              },
              document_id: "doc-alpha-001",
              page_number: 1,
              confidence: 0.98,
              created_at: "2026-11-04T08:00:00Z",
              updated_at: "2026-11-04T08:00:00Z",
              version: 1,
            },
            {
              review_id: "rev-002",
              tenant_id: "tenant-alpha-001",
              candidate_id: "ebitda_margin_q3",
              candidate_type: "conflict",
              status: "in_review",
              field_name: "ebitda_margin_q3",
              extracted_value: "24.1%",
              candidate_data: {
                subject: "Acme Corporation",
                attribute: "ebitda_margin_q3",
                value: "24.1%",
                confidence: 0.65,
              },
              document_id: "doc-alpha-002",
              page_number: 3,
              confidence: 0.65,
              created_at: "2026-11-04T09:00:00Z",
              updated_at: "2026-11-04T09:00:00Z",
              version: 2,
            },
          ],
        }),
      });
    });

    // Mock metrics
    await page.route("**/api/v1/reviews/metrics", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_items: 24,
          decided_count: 18,
          approval_rate: 0.75,
          correction_rate: 0.15,
          rejection_rate: 0.10,
          evidence_failure_rate: 0.05,
        }),
      });
    });
  });

  test("renders human governance queue with header, metrics, and candidate rows", async ({ page }) => {
    await page.goto("/reviews");

    // Strictly preserve heading check
    await expect(page.getByRole("heading", { name: /human governance review queue/i })).toBeVisible();

    // Verify metrics banner
    await expect(page.getByText("Total Queue")).toBeVisible();
    await expect(page.getByText("75%")).toBeVisible();

    // Verify candidate identifier is visible
    await expect(page.getByText("revenue_q3_2026")).toBeVisible();
    await expect(page.getByText("ebitda_margin_q3")).toBeVisible();
  });

  test("filters queue items by status and candidate type", async ({ page }) => {
    await page.goto("/reviews");

    // Click Pending tab
    await page.getByRole("tab", { name: /pending/i }).click();
    await expect(page.getByText("revenue_q3_2026")).toBeVisible();
    await expect(page.getByText("ebitda_margin_q3")).not.toBeVisible();

    // Click In Review tab
    await page.getByRole("tab", { name: /in review/i }).click();
    await expect(page.getByText("ebitda_margin_q3")).toBeVisible();
    await expect(page.getByText("revenue_q3_2026")).not.toBeVisible();
  });

  test("filters queue items using the search input", async ({ page }) => {
    await page.goto("/reviews");

    const searchInput = page.getByPlaceholder(/search by candidate, attribute/i);
    await searchInput.fill("ebitda");
    await expect(page.getByText("ebitda_margin_q3")).toBeVisible();
    await expect(page.getByText("revenue_q3_2026")).not.toBeVisible();
  });
});
