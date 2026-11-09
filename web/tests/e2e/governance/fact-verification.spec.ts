import { test, expect } from "@playwright/test";

test.describe("Fact Verification Flow (/reviews/[reviewId])", () => {
  test.beforeEach(async ({ page }) => {
    // Mock review item
    await page.route("**/api/v1/reviews/rev-fact-001", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          review_id: "rev-fact-001",
          tenant_id: "tenant-alpha-001",
          candidate_id: "revenue_q3_2026",
          candidate_type: "fact",
          document_id: "doc-alpha-001",
          status: "in_review",
          version: 1,
          candidate_data: {
            subject: "Acme Corporation",
            attribute: "revenue_q3_2026",
            value: "$142.5M",
            raw_value: "revenue of $142.5 million",
            evidence_quote: "Acme Corporation reported Q3 2026 revenue of $142.5 million.",
            confidence: 0.98,
            page_number: 1,
          },
          created_at: "2026-11-04T08:00:00Z",
          updated_at: "2026-11-04T08:00:00Z",
        }),
      });
    });

    // Mock history
    await page.route("**/api/v1/reviews/rev-fact-001/history", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    // Mock decision submission
    await page.route("**/api/v1/reviews/rev-fact-001/decisions", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          item: {
            review_id: "rev-fact-001",
            tenant_id: "tenant-alpha-001",
            candidate_id: "revenue_q3_2026",
            candidate_type: "fact",
            document_id: "doc-alpha-001",
            status: "approved",
            version: 2,
            candidate_data: {
              subject: "Acme Corporation",
              attribute: "revenue_q3_2026",
              value: "$142.5M",
            },
            created_at: "2026-11-04T08:00:00Z",
            updated_at: "2026-11-04T08:30:00Z",
          },
          decision: {
            action: "approve",
            rationale: "Numbers validated against quarterly revenue report.",
          },
          audit_event: {
            event_id: "evt-01",
            sequence: 1,
            action: "approve",
            previous_status: "in_review",
            new_status: "approved",
            previous_version: 1,
            new_version: 2,
            rationale: "Numbers validated against quarterly revenue report.",
            timestamp: "2026-11-04T08:30:00Z",
          },
        }),
      });
    });
  });

  test("inspects fact statement, selects verified outcome, and submits decision", async ({ page }) => {
    await page.goto("/reviews/rev-fact-001");

    // Click Fact Verification tab
    await page.getByRole("tab", { name: /fact verification/i }).click();

    // Verify candidate fact info
    await expect(page.getByText(/Fact Verification: Acme Corporation • revenue_q3_2026/i)).toBeVisible();
    await expect(page.getByText(/Acme Corporation reported Q3 2026 revenue of \$142.5 million/i).first()).toBeVisible();

    // Select Fully Verified
    await page.getByRole("button", { name: /fully verified/i }).click();

    // Enter rationale
    const rationaleInput = page.getByPlaceholder(/explain why this verification outcome was reached/i);
    await rationaleInput.fill("Confirmed by audited 10-Q filing table.");

    // Click Record Verification
    await page.getByRole("button", { name: /record verification & proceed/i }).click();

    // Verify success banner appears
    await expect(page.getByText(/verification recorded successfully/i)).toBeVisible();
  });
});
