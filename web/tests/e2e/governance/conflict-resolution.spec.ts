import { test, expect } from "@playwright/test";

test.describe("Conflict Resolution Flow (/reviews/[reviewId])", () => {
  test.beforeEach(async ({ page }) => {
    // Mock conflict review item
    await page.route("**/api/v1/reviews/rev-conf-001", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          review_id: "rev-conf-001",
          tenant_id: "tenant-alpha-001",
          candidate_id: "ebitda_margin_q3",
          candidate_type: "conflict",
          document_id: "doc-alpha-001",
          status: "in_review",
          version: 1,
          candidate_data: {
            subject: "Acme Corporation",
            attribute: "ebitda_margin_q3",
            fact_1: {
              document_id: "doc-alpha-001",
              value: "22.5%",
              evidence_quote: "Preliminary shareholder deck reported EBITDA margin of 22.5%.",
            },
            fact_2: {
              document_id: "doc-alpha-002",
              value: "24.1%",
              evidence_quote: "Certified 10-Q financial filing confirmed EBITDA margin of 24.1%.",
            },
          },
          created_at: "2026-11-04T08:00:00Z",
          updated_at: "2026-11-04T08:00:00Z",
        }),
      });
    });

    // Mock history
    await page.route("**/api/v1/reviews/rev-conf-001/history", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    // Mock decision submission
    await page.route("**/api/v1/reviews/rev-conf-001/decisions", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          item: {
            review_id: "rev-conf-001",
            tenant_id: "tenant-alpha-001",
            candidate_id: "ebitda_margin_q3",
            candidate_type: "conflict",
            document_id: "doc-alpha-002",
            status: "corrected",
            version: 2,
            candidate_data: {
              subject: "Acme Corporation",
              attribute: "ebitda_margin_q3",
              value: "24.1%",
            },
            created_at: "2026-11-04T08:00:00Z",
            updated_at: "2026-11-04T09:00:00Z",
          },
          decision: {
            action: "correct",
            rationale: "Accepted 10-Q filing over preliminary deck.",
          },
          audit_event: {
            event_id: "evt-02",
            sequence: 1,
            action: "correct",
            previous_status: "in_review",
            new_status: "corrected",
            previous_version: 1,
            new_version: 2,
            rationale: "Accepted 10-Q filing over preliminary deck.",
            timestamp: "2026-11-04T09:00:00Z",
          },
        }),
      });
    });
  });

  test("renders side-by-side claims and submits conflict resolution", async ({ page }) => {
    await page.goto("/reviews/rev-conf-001");

    // Click Conflict Resolution tab
    await page.getByRole("tab", { name: /conflict resolution/i }).click();

    // Verify both contradictory claims are shown
    await expect(page.getByText("Claim 1 (Source A)")).toBeVisible();
    await expect(page.getByText("Claim 2 (Source B)")).toBeVisible();
    await expect(page.getByText("22.5%", { exact: true })).toBeVisible();
    await expect(page.getByText("24.1%", { exact: true })).toBeVisible();

    // Select Accept Fact 2
    await page.getByRole("button", { name: /accept fact 2 \(source b\)/i }).click();

    // Fill rationale
    const rationale = page.getByPlaceholder(/document the governance rationale/i);
    await rationale.fill("10-Q filing contains GAAP reconciled figures.");

    // Submit resolution
    await page.getByRole("button", { name: /commit conflict resolution/i }).click();

    // Verify success banner
    await expect(page.getByText(/conflict resolution recorded successfully/i)).toBeVisible();
  });
});
