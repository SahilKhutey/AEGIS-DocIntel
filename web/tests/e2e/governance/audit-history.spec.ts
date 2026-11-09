import { test, expect } from "@playwright/test";

test.describe("Governance Audit History Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Mock review item
    await page.route("**/api/v1/reviews/rev-aud-001", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          review_id: "rev-aud-001",
          tenant_id: "tenant-alpha-001",
          candidate_id: "operating_expenses",
          candidate_type: "fact",
          document_id: "doc-alpha-001",
          status: "approved",
          version: 2,
          candidate_data: {
            subject: "Acme Corporation",
            attribute: "operating_expenses",
            value: "$55.2M",
          },
          created_at: "2026-11-04T08:00:00Z",
          updated_at: "2026-11-04T09:00:00Z",
        }),
      });
    });

    // Mock history
    await page.route("**/api/v1/reviews/rev-aud-001/history", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            event_id: "evt-01",
            review_id: "rev-aud-001",
            sequence: 1,
            tenant_id: "tenant-alpha-001",
            actor_id: "reviewer_jane",
            action: "claim",
            previous_status: "pending",
            new_status: "in_review",
            previous_version: 1,
            new_version: 1,
            rationale: "Claimed for audit inspection.",
            timestamp: "2026-11-04T08:30:00Z",
          },
          {
            event_id: "evt-02",
            review_id: "rev-aud-001",
            sequence: 2,
            tenant_id: "tenant-alpha-001",
            actor_id: "reviewer_jane",
            action: "approve",
            previous_status: "in_review",
            new_status: "approved",
            previous_version: 1,
            new_version: 2,
            rationale: "Operating expenses verified against income statement.",
            timestamp: "2026-11-04T09:00:00Z",
          },
        ]),
      });
    });

    // Mock global review queue for /governance/audit
    await page.route("**/api/v1/reviews", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              review_id: "rev-aud-001",
              tenant_id: "tenant-alpha-001",
              candidate_id: "operating_expenses",
              candidate_type: "fact",
              document_id: "doc-alpha-001",
              status: "approved",
              version: 2,
              candidate_data: {
                subject: "Acme Corporation",
                attribute: "operating_expenses",
              },
              created_at: "2026-11-04T08:00:00Z",
              updated_at: "2026-11-04T09:00:00Z",
            },
          ],
        }),
      });
    });
  });

  test("renders audit history table on review detail page", async ({ page }) => {
    await page.goto("/reviews/rev-aud-001");

    // Click Audit Trail tab
    await page.getByRole("tab", { name: /audit trail/i }).click();

    // Verify audit events
    await expect(page.getByText("#1")).toBeVisible();
    await expect(page.getByText("#2")).toBeVisible();
    await expect(page.getByText("reviewer_jane").first()).toBeVisible();
    await expect(page.getByText(/Operating expenses verified against income statement/i)).toBeVisible();
  });

  test("renders global governance audit page at /governance/audit", async ({ page }) => {
    await page.goto("/governance/audit");

    await expect(page.getByRole("heading", { name: /governance audit log/i })).toBeVisible();
    await expect(page.getByText("operating_expenses").first()).toBeVisible();
    await expect(page.getByText(/Operating expenses verified against income statement/i)).toBeVisible();
  });
});
