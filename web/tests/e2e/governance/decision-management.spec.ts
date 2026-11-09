import { test, expect } from "@playwright/test";

test.describe("Decision Management Flow (/reviews/[reviewId])", () => {
  test.beforeEach(async ({ page }) => {
    // Mock review item
    await page.route("**/api/v1/reviews/rev-dec-001", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          review_id: "rev-dec-001",
          tenant_id: "tenant-alpha-001",
          candidate_id: "tax_expense",
          candidate_type: "fact",
          document_id: "doc-alpha-001",
          status: "in_review",
          version: 1,
          candidate_data: {
            subject: "Acme Corporation",
            attribute: "tax_expense",
            value: "$12.0M",
          },
          created_at: "2026-11-04T08:00:00Z",
          updated_at: "2026-11-04T08:00:00Z",
        }),
      });
    });

    // Mock history
    await page.route("**/api/v1/reviews/rev-dec-001/history", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    // Mock decision submission
    await page.route("**/api/v1/reviews/rev-dec-001/decisions", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          item: {
            review_id: "rev-dec-001",
            tenant_id: "tenant-alpha-001",
            candidate_id: "tax_expense",
            candidate_type: "fact",
            document_id: "doc-alpha-001",
            status: "approved",
            version: 2,
            candidate_data: {
              subject: "Acme Corporation",
              attribute: "tax_expense",
              value: "$12.0M",
            },
            created_at: "2026-11-04T08:00:00Z",
            updated_at: "2026-11-04T09:00:00Z",
          },
          decision: {
            action: "approve",
            rationale: "Tax expense figures match audited tax provisions on page 18.",
          },
          audit_event: {
            event_id: "evt-dec-01",
            sequence: 1,
            action: "approve",
            previous_status: "in_review",
            new_status: "approved",
            previous_version: 1,
            new_version: 2,
            rationale: "Tax expense figures match audited tax provisions on page 18.",
            timestamp: "2026-11-04T09:00:00Z",
          },
        }),
      });
    });
  });

  test("requires rationale and compliance certification before committing a decision", async ({ page }) => {
    await page.goto("/reviews/rev-dec-001");

    // Click Decision Management tab
    await page.getByRole("tab", { name: /decision management/i }).click();

    // Verify Decision Panel header
    await expect(page.getByText(/governance decision management/i)).toBeVisible();

    const submitBtn = page.getByRole("button", { name: /submit approve/i });
    await expect(submitBtn).toBeDisabled();

    // Fill rationale
    const rationaleInput = page.getByPlaceholder(/explain the reason for this decision/i);
    await rationaleInput.fill("Tax expense figures match audited tax provisions on page 18.");

    // Submit button still disabled without checkbox
    await expect(submitBtn).toBeDisabled();

    // Check compliance certificate checkbox
    await page.getByRole("checkbox").check();

    // Now enabled
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify success banner
    await expect(page.getByText(/decision 'APPROVE' committed successfully/i)).toBeVisible();
  });
});
